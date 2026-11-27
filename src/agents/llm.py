"""DeepSeek Flash：评分、反馈、辅导、问答和视觉共用服务端模型。"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.3


@lru_cache(maxsize=1)
def get_primary_chat_model() -> ChatOpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key or key.startswith("your_"):
        raise RuntimeError("请在服务端 .env 中配置 DEEPSEEK_API_KEY")
    return ChatOpenAI(
        model=os.environ.get("DEEPSEEK_MODEL_NAME", "deepseek-flash"),
        api_key=key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        timeout=120,
        max_retries=1,
        # JSON + 工具调用不需要推理内容，避免 token 预算被推理耗尽。
        extra_body={"thinking": {"type": "disabled"}},
    )


def get_chat_model_with_fallback() -> ChatOpenAI:
    """兼容原调用方；v2 不再静默切换供应商。"""
    return get_primary_chat_model()


def get_scoring_chat_model() -> ChatOpenAI:
    return get_primary_chat_model()


def get_vision_chat_model() -> ChatOpenAI:
    return get_primary_chat_model()
