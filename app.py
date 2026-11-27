"""慧笔 v2 入口：uvicorn app:app --host 127.0.0.1 --port 8000。"""
from src.api.main import app

__all__ = ["app"]
