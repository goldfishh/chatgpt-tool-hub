import os
from typing import Optional

from chatgpt_tool_hub.common.cache import BaseCache
from chatgpt_tool_hub.common.utils import get_from_dict_or_env

verbose: bool = False
llm_cache: Optional[BaseCache] = None


def build_model_params(kwargs: dict) -> dict:
    _openai_api_key = get_from_dict_or_env(kwargs, "openai_api_key", "OPENAI_API_KEY")
    # tool llm need it
    os.environ["OPENAI_API_KEY"] = _openai_api_key
    return {
        "temperature": get_from_dict_or_env(kwargs, "temperature", "TEMPERATURE", 0),
        "openai_api_key": _openai_api_key,
        "proxy": get_from_dict_or_env(kwargs, "proxy", "PROXY", ""),
        "model_name": get_from_dict_or_env(kwargs, "model_name", "MODEL_NAME", "gpt-3.5-turbo"),  # 对话模型的名称
        "top_p": 1,
        "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "request_timeout": get_from_dict_or_env(kwargs, "request_timeout", "REQUEST_TIMEOUT", 60),
        "max_retries": 2
    }


from chatgpt_tool_hub.models.base import BaseLLM, LLM
from chatgpt_tool_hub.models.chatgpt.chatgpt import ChatOpenAI
from chatgpt_tool_hub.models.openai import OpenAI, AzureOpenAI


__all__ = [
    "BaseLLM",
    "LLM",
    "OpenAI",
    "AzureOpenAI",
    "ChatOpenAI"
]