from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.agents import llm, nodes
from src.agents.graph import build_graph, route_after_image


def test_all_tasks_use_deepseek_flash(monkeypatch):
    llm.get_primary_chat_model.cache_clear()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-not-real")
    monkeypatch.delenv("DEEPSEEK_MODEL_NAME", raising=False)
    construct = Mock(return_value=object())
    monkeypatch.setattr(llm, "ChatOpenAI", construct)
    model = llm.get_primary_chat_model()
    assert llm.get_vision_chat_model() is model
    assert llm.get_scoring_chat_model() is model
    assert llm.get_chat_model_with_fallback() is model
    assert construct.call_args.kwargs["model"] == "deepseek-flash"
    assert construct.call_args.kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
    llm.get_primary_chat_model.cache_clear()


def test_missing_key_fails_early(monkeypatch):
    llm.get_primary_chat_model.cache_clear()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        llm.get_primary_chat_model()


@pytest.mark.parametrize("mime", ["image/png", "image/jpeg", "image/webp"])
def test_image_node_preserves_mime(monkeypatch, mime):
    model = Mock()
    model.invoke.return_value = SimpleNamespace(content="客观的图像描述")
    monkeypatch.setattr(llm, "get_vision_chat_model", lambda: model)
    result = nodes.image_analysis_node({"essay_image_b64": "abcd", "essay_image_mime": mime})
    assert result["image_analysis"] == "客观的图像描述"
    message = model.invoke.call_args.args[0][0]
    assert message.content[1]["image_url"]["url"] == f"data:{mime};base64,abcd"


def test_image_failure_stops_graph_before_scoring_and_database(monkeypatch):
    model = Mock()
    model.invoke.side_effect = RuntimeError("unavailable")
    monkeypatch.setattr(llm, "get_vision_chat_model", lambda: model)
    expensive = Mock(side_effect=AssertionError("must not execute"))
    for name in [
        "retrieval_agent_node",
        "grammar_check_node",
        "feedback_agent_node",
        "critic_agent_node",
        "coach_agent_node",
        "progress_tracker_node",
    ]:
        monkeypatch.setattr(nodes, name, expensive)
    with pytest.warns(UserWarning, match="图片理解失败"):
        result = build_graph().invoke({"essay_text": "word " * 25, "essay_image_b64": "abcd"})
    assert result["image_analysis_error"]
    expensive.assert_not_called()
    assert route_after_image(result) == "short_circuit_reject"
    assert route_after_image({}) == "retrieval_agent"
