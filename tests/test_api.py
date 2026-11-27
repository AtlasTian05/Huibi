"""HTTP contract tests; external models and persistence are replaced at boundaries."""

import base64
import io
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.agents import graph
from src.api.main import app, current_user, public_record, user_job
from src.exam_types import GENERAL, IELTS, IELTS_TASK1, IELTS_TASK2

ESSAY = "This is a practice essay about learning English and developing clear ideas through regular writing with thoughtful feedback and careful revision."


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authed(client):
    app.dependency_overrides[current_user] = lambda: "learner"
    return client


def image_payload(fmt="PNG"):
    output = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(output, format=fmt)
    return base64.b64encode(output.getvalue()).decode()


def review_payload(**kwargs):
    return {"essay_text": ESSAY, "exam_type": GENERAL, **kwargs}


def test_health_without_database_or_key(client):
    assert client.get("/api/health").json()["model"] == "deepseek-flash"


@pytest.mark.parametrize("path", ["/api/auth/me", "/api/submissions"])
def test_auth_required(client, path):
    assert client.get(path).status_code == 401


def test_review_requires_login(client):
    assert client.post("/api/reviews", json=review_payload()).status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        review_payload(essay_text="Too short"),
        review_payload(essay_text="word " * 1001),
        review_payload(exam_type="unknown"),
        review_payload(exam_type=IELTS, exam_subtype="unknown"),
        review_payload(exam_subtype=IELTS_TASK1),
        review_payload(
            exam_type=IELTS, exam_subtype=IELTS_TASK2, essay_image_b64=image_payload(), essay_image_mime="image/png"
        ),
        review_payload(
            exam_type=IELTS, exam_subtype=IELTS_TASK1, essay_image_b64="not base64", essay_image_mime="image/png"
        ),
        review_payload(
            exam_type=IELTS, exam_subtype=IELTS_TASK1, essay_image_b64=image_payload(), essay_image_mime="image/jpeg"
        ),
        review_payload(
            exam_type=IELTS,
            exam_subtype=IELTS_TASK1,
            essay_image_b64=base64.b64encode(b"not an image").decode(),
            essay_image_mime="image/png",
        ),
    ],
)
def test_invalid_review_never_calls_model(authed, monkeypatch, payload):
    build = Mock()
    monkeypatch.setattr(graph, "build_graph", build)
    assert authed.post("/api/reviews", json=payload).status_code == 422
    build.assert_not_called()


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_task1_accepts_verified_images(authed, monkeypatch, fmt, mime):
    model = Mock()
    model.invoke.return_value = {
        "is_valid": True,
        "submission_id": 42,
        "primary_score": 6.5,
        "essay_image_b64": "private",
    }
    monkeypatch.setattr(graph, "build_graph", lambda: model)
    response = authed.post(
        "/api/reviews",
        json=review_payload(
            exam_type=IELTS, exam_subtype=IELTS_TASK1, essay_image_b64=image_payload(fmt), essay_image_mime=mime
        ),
    )
    assert response.status_code == 201
    assert response.json()["id"] == 42
    assert "essay_image_b64" not in response.json()
    assert model.invoke.call_args.args[0]["user_id"] == "learner"
    assert model.invoke.call_args.args[0]["essay_image_mime"] == mime


def test_chart_failure_is_explicit(authed, monkeypatch):
    model = Mock()
    model.invoke.return_value = {"is_valid": True, "image_analysis_error": "secret internal error"}
    monkeypatch.setattr(graph, "build_graph", lambda: model)
    response = authed.post("/api/reviews", json=review_payload())
    assert response.status_code == 502
    assert "secret" not in response.text


def test_model_failure_does_not_leak_secrets(authed, monkeypatch):
    model = Mock()
    model.invoke.side_effect = RuntimeError("sk-private-secret")
    monkeypatch.setattr(graph, "build_graph", lambda: model)
    response = authed.post("/api/reviews", json=review_payload())
    assert response.status_code == 502
    assert "sk-private-secret" not in response.text


def test_cross_origin_rejected(client):
    assert client.post("/api/auth/login", json={}, headers={"Origin": "https://evil.example"}).status_code == 403


def test_payload_limit(client):
    assert client.post("/api/reviews", content=b"x" * (7 * 1024 * 1024 + 1)).status_code == 413


def test_history_hides_server_paths():
    assert public_record({"id": 4, "essay_image_path": "private/path", "user_id": "someone"}) == {
        "id": 4,
        "image_url": "/api/submissions/4/image",
    }


def test_duplicate_job_rejected_and_lock_released():
    with user_job("learner"):
        with pytest.raises(Exception) as err:
            with user_job("learner"):
                pass
        assert err.value.status_code == 429
    with user_job("learner"):
        pass


def test_image_route_checks_ownership(authed, monkeypatch):
    from src.storage import db

    monkeypatch.setattr(db, "get_user_history", lambda user: [])
    assert authed.get("/api/submissions/123/image").status_code == 404


def test_delete_passes_authenticated_user(authed, monkeypatch):
    from src.storage import db

    delete = Mock(return_value=False)
    monkeypatch.setattr(db, "delete_submission", delete)
    assert authed.delete("/api/submissions/1").status_code == 404
    delete.assert_called_once_with(1, "learner")


def test_questions(authed, monkeypatch):
    from src.agents import nodes

    monkeypatch.setattr(nodes, "answer_kb_question", lambda question, exam: "Use a clear topic sentence.")
    assert (
        authed.post("/api/questions", json={"question": "How to organize an essay?"}).json()["answer"].startswith("Use")
    )
    assert authed.post("/api/questions", json={"question": "   "}).status_code == 422
