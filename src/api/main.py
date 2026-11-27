"""同源 Vue + FastAPI。API key 永远不发送给浏览器。"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import threading
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.schemas import Credentials, QuestionRequest, ReviewRequest
from src.storage import db

load_dotenv()
logger = logging.getLogger(__name__)
app = FastAPI(title="慧笔 API", version="2.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
COOKIE = "huibi_session"
SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS web_sessions (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + interval '7 days'
);
"""
_active_users: set[str] = set()
_active_lock = threading.Lock()


@app.middleware("http")
async def request_guard(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        allowed = {str(request.base_url).rstrip("/"), os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")}
        if origin and origin not in allowed:
            return JSONResponse({"detail": "不允许的请求来源"}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "不允许的跨站请求"}, status_code=403)
    # Includes chunked bodies: do not trust Content-Length alone.
    if request.url.path.startswith("/api/") and request.method == "POST":
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 7 * 1024 * 1024:
                return JSONResponse({"detail": "请求内容过大"}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(db.psycopg.Error)
async def database_error(request: Request, exc: Exception):
    logger.error("Database request failed: %s", type(exc).__name__)
    return JSONResponse({"detail": "数据库暂不可用，请检查 PostgreSQL 配置"}, status_code=503)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request) -> str:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "请先登录")
    with db.get_connection() as conn:
        conn.execute(SESSION_SCHEMA)
        row = conn.execute(
            "SELECT username FROM web_sessions WHERE token_hash = %s AND expires_at > now()",
            (_token_hash(token),),
        ).fetchone()
    if not row:
        raise HTTPException(401, "登录已过期，请重新登录")
    return row[0]


@contextmanager
def user_job(username: str):
    with _active_lock:
        if username in _active_users:
            raise HTTPException(429, "上一项任务仍在进行，请稍候")
        _active_users.add(username)
    try:
        yield
    finally:
        with _active_lock:
            _active_users.discard(username)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "model": os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-flash")}


@app.post("/api/auth/register", status_code=201)
def register(credentials: Credentials):
    success, message = db.create_user(credentials.username, credentials.password)
    if not success:
        raise HTTPException(409, message)
    return {"message": message}


@app.post("/api/auth/login")
def login(credentials: Credentials, response: Response):
    if not db.verify_user(credentials.username, credentials.password):
        raise HTTPException(401, "用户名或密码错误")
    token = secrets.token_urlsafe(32)
    with db.get_connection() as conn:
        conn.execute(SESSION_SCHEMA)
        conn.execute("DELETE FROM web_sessions WHERE expires_at <= now()")
        conn.execute(
            "INSERT INTO web_sessions (token_hash, username) VALUES (%s, %s)",
            (_token_hash(token), credentials.username),
        )
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        path="/",
    )
    return {"username": credentials.username}


@app.get("/api/auth/me")
def me(username: str = Depends(current_user)):
    return {"username": username}


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if token:
        with db.get_connection() as conn:
            conn.execute(SESSION_SCHEMA)
            conn.execute("DELETE FROM web_sessions WHERE token_hash = %s", (_token_hash(token),))
    response.delete_cookie(COOKIE, path="/")


def public_record(record: dict) -> dict:
    result = {k: v for k, v in record.items() if k not in {"essay_image_b64", "essay_image_path", "user_id"}}
    if record.get("essay_image_path") or (record.get("essay_image_b64") and record.get("id")):
        result["image_url"] = f"/api/submissions/{record['id']}/image"
    return result


@app.post("/api/reviews", status_code=201)
def review(payload: ReviewRequest, username: str = Depends(current_user)):
    from src.agents.graph import build_graph

    with user_job(username):
        try:
            state = build_graph().invoke({**payload.model_dump(), "user_id": username})
        except db.psycopg.Error:
            raise
        except Exception as exc:
            logger.error("Review failed: %s", type(exc).__name__)
            raise HTTPException(502, "批改服务暂不可用，请检查模型配置或稍后重试") from exc
    if not state.get("is_valid"):
        raise HTTPException(422, state.get("reject_reason") or "作文不符合要求")
    if state.get("image_analysis_error"):
        raise HTTPException(502, "题图识别失败，本次未评分或保存，请重试")
    state["id"] = state.get("submission_id")
    return public_record(state)


@app.get("/api/submissions")
def history(username: str = Depends(current_user)):
    return [public_record(row) for row in reversed(db.get_user_history(username))]


def owned_submission(submission_id: int, username: str) -> dict:
    for row in db.get_user_history(username):
        if row["id"] == submission_id:
            return row
    raise HTTPException(404, "记录不存在")


@app.get("/api/submissions/{submission_id}/image")
def submission_image(submission_id: int, username: str = Depends(current_user)):
    row = owned_submission(submission_id, username)
    root = db._UPLOADS_DIR.resolve()
    path = (db._PROJECT_ROOT / (row.get("essay_image_path") or "")).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "图片不存在")
    return FileResponse(path, headers={"Cache-Control": "no-store"})


@app.delete("/api/submissions/{submission_id}", status_code=204)
def delete(submission_id: int, username: str = Depends(current_user)):
    if not db.delete_submission(submission_id, username):
        raise HTTPException(404, "记录不存在")


@app.post("/api/questions")
def question(payload: QuestionRequest, username: str = Depends(current_user)):
    from src.agents.nodes import answer_kb_question

    if not payload.question.strip():
        raise HTTPException(422, "请输入问题")
    with user_job(username):
        try:
            return {"answer": answer_kb_question(payload.question, payload.exam_type)}
        except Exception as exc:
            logger.error("Question failed: %s", type(exc).__name__)
            raise HTTPException(502, "问答服务暂不可用，请稍后重试") from exc


# Production serves the compiled Vue app; development uses Vite's /api proxy.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    app.mount("/images", StaticFiles(directory=DIST / "images"), name="images")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "接口不存在")
        return FileResponse(DIST / "index.html")
