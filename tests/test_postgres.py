"""Real PostgreSQL tests. Set TEST_DATABASE_DSN to an isolated database (CI does this)."""

import base64
import io
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api.main import app
from src.storage import db

pytestmark = pytest.mark.postgres


@pytest.fixture
def database(monkeypatch, tmp_path):
    dsn = os.getenv("TEST_DATABASE_DSN")
    if not dsn:
        pytest.skip("TEST_DATABASE_DSN not set; requires isolated PostgreSQL")
    # Isolated schema means tests never TRUNCATE or DROP existing user data.
    schema = "test_" + uuid4().hex
    with psycopg.connect(dsn) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
    original = db.get_connection

    def connection(dsn_override=None):
        from psycopg.conninfo import make_conninfo

        return original(make_conninfo(dsn, options=f"-c search_path={schema}"))

    monkeypatch.setattr(db, "get_connection", connection)
    monkeypatch.setattr(db, "_UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr(db, "_PROJECT_ROOT", tmp_path)
    # storage uses a stable relative prefix for uploads
    monkeypatch.setattr(db, "_UPLOADS_DIR", tmp_path / "data" / "uploads")
    yield
    with psycopg.connect(dsn) as conn:
        conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


def test_auth_sessions_survive_new_client_and_are_revoked(database):
    with TestClient(app) as client:
        credentials = {"username": "learner", "password": "example-password"}
        assert client.post("/api/auth/register", json=credentials).status_code == 201
        assert client.post("/api/auth/register", json=credentials).status_code == 409
        assert client.post("/api/auth/login", json={**credentials, "password": "incorrect"}).status_code == 401
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 200
        assert "httponly" in response.headers["set-cookie"].lower()
        token = client.cookies.get("huibi_session")
        with TestClient(app) as second:
            second.cookies.set("huibi_session", token)
            assert second.get("/api/auth/me").json() == {"username": "learner"}
        assert client.post("/api/auth/logout").status_code == 204
        client.cookies.set("huibi_session", token)
        assert client.get("/api/auth/me").status_code == 401


def test_submission_roundtrip_and_image_ownership(database):
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(output, format="PNG")
    submission_id = db.save_submission(
        {
            "user_id": "alice",
            "essay_text": "Original essay",
            "primary_score": 75,
            "feedback_dimensions": {"grammar": {"strengths": "Clear"}},
            "essay_image_b64": base64.b64encode(output.getvalue()).decode(),
        }
    )
    rows = db.get_user_history("alice")
    assert rows[0]["id"] == submission_id
    assert rows[0]["essay_text"] == "Original essay"
    assert rows[0]["feedback_dimensions"]["grammar"]["strengths"] == "Clear"
    assert not db.get_user_history("bob")
    path = db._PROJECT_ROOT / rows[0]["essay_image_path"]
    assert path.exists()
    for name in ("alice", "bob"):
        db.create_user(name, "example-password")
    with TestClient(app) as client:
        client.post("/api/auth/login", json={"username": "bob", "password": "example-password"})
        assert client.get(f"/api/submissions/{submission_id}/image").status_code == 404
        assert client.delete(f"/api/submissions/{submission_id}").status_code == 404
        assert path.exists()
        client.post("/api/auth/login", json={"username": "alice", "password": "example-password"})
        history = client.get("/api/submissions").json()
        assert "essay_image_path" not in history[0]
        assert "user_id" not in history[0]
        assert client.get(history[0]["image_url"]).content == output.getvalue()
        assert client.delete(f"/api/submissions/{submission_id}").status_code == 204
    assert not path.exists()
    assert not db.get_user_history("alice")


def test_upgrade_from_v1_keeps_existing_records(database):
    with db.get_connection() as conn:
        conn.execute("INSERT INTO submissions (user_id, essay_topic) VALUES ('v1user', 'Old practice')")
        conn.execute("ALTER TABLE submissions DROP COLUMN essay_text")
    rows = db.get_user_history("v1user")
    assert rows[0]["essay_topic"] == "Old practice"
    assert rows[0]["essay_text"] is None


def test_review_graph_to_database_roundtrip(database, monkeypatch):
    """Real HTTP + graph + PostgreSQL; only external model/grammar/RAG are stubbed."""
    import json
    from unittest.mock import Mock

    from langchain_core.messages import AIMessage

    from src.agents import llm, nodes
    from src.exam_types import GENERAL

    model = Mock()
    model.bind.return_value = model
    model.bind_tools.return_value = model

    def invoke(prompt):
        text = prompt if isinstance(prompt, str) else prompt[0].content
        if '"rubric_scores"' in text:
            payload = {
                "rubric_scores": {
                    "content_score": 20,
                    "organization_score": 18,
                    "language_score": 19,
                    "grammar_score": 18,
                }
            }
        elif '"approved"' in text:
            payload = {"approved": True, "notes": ""}
        elif '"action_items"' in text:
            payload = {"action_items": [{"title": "Add detail", "detail": "Support your argument with an example."}]}
        else:
            payload = {
                "overall_summary": "Clear ideas.",
                "dimension_feedback": {"content": {"strengths": "Clear", "improvements": "More examples", "tips": []}},
            }
        return AIMessage(content=json.dumps(payload))

    model.invoke.side_effect = invoke
    for getter in ["get_primary_chat_model", "get_scoring_chat_model", "get_chat_model_with_fallback"]:
        monkeypatch.setattr(llm, getter, lambda: model)
    monkeypatch.setattr(nodes, "grammar_check_node", lambda state: {**state, "grammar_errors": []})
    monkeypatch.setattr(
        nodes, "retrieval_agent_node", lambda state: {**state, "retrieved_context": ["Use clear arguments."]}
    )
    with TestClient(app) as client:
        credentials = {"username": "writer", "password": "example-password"}
        assert client.post("/api/auth/register", json=credentials).status_code == 201
        assert client.post("/api/auth/login", json=credentials).status_code == 200
        response = client.post(
            "/api/reviews",
            json={
                "exam_type": GENERAL,
                "essay_text": "Learning to write well requires regular practice and thoughtful feedback. Students should develop clear ideas and support their arguments with specific examples from everyday life.",
            },
        )
        assert response.status_code == 201
        result = response.json()
        assert result["primary_score"] == 75
        assert result["id"] > 0
        history = client.get("/api/submissions").json()
        assert history[0]["primary_score"] == result["primary_score"]
        assert history[0]["essay_text"].startswith("Learning to write")
        assert history[0]["coach_plan"]["action_items"][0]["title"] == "Add detail"
