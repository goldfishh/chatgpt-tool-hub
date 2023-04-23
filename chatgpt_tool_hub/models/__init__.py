import os
from typing import Optional

from chatgpt_tool_hub.common.cache import BaseCache
from chatgpt_tool_hub.common.utils import get_from_dict_or_env

verbose: bool = False
llm_cache: Optional[BaseCache] = None

# default for gpt-3.5
ALL_MAX_TOKENS_NUM = 4000

# token manage strategy
BOT_PROMPT = 1000
MEMORY_MAX_TOKENS_NUM = 600
BOT_SCRATCHPAD_MAX_TOKENS_NUM = ALL_MAX_TOKENS_NUM - BOT_PROMPT - MEMORY_MAX_TOKENS_NUM - 200


def change_memory_max_tokens(memory_max_tokens_num: int):
    global MEMORY_MAX_TOKENS_NUM, BOT_SCRATCHPAD_MAX_TOKENS_NUM
    MEMORY_MAX_TOKENS_NUM = memory_max_tokens_num
    BOT_SCRATCHPAD_MAX_TOKENS_NUM = ALL_MAX_TOKENS_NUM - BOT_PROMPT - MEMORY_MAX_TOKENS_NUM - 200


def build_model_params(kwargs: dict) -> dict:
    _api_key = get_from_dict_or_env(kwargs, "openai_api_key", "OPENAI_API_KEY")
    _proxy = get_from_dict_or_env(kwargs, "proxy", "PROXY", "")
    _model = get_from_dict_or_env(kwargs, "model_name", "MODEL_NAME", "gpt-3.5-turbo")
    _timeout = get_from_dict_or_env(kwargs, "request_timeout", "REQUEST_TIMEOUT", 120)
    # tool llm need them
    os.environ["OPENAI_API_KEY"] = str(_api_key)
    os.environ["PROXY"] = str(_proxy)
    os.environ["MODEL_NAME"] = str(_model)
    os.environ["REQUEST_TIMEOUT"] = str(_timeout)
    return {
        "temperature": get_from_dict_or_env(kwargs, "temperature", "TEMPERATURE", 0),
        "openai_api_key": _api_key,
        "proxy": _proxy,
        "model_name": _model,  # 对话模型的名称
        "top_p": 1,
        "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "request_timeout": _timeout,
        "max_retries": 2
    }


from chatgpt_tool_hub.models.base import BaseLLM, LLM
from chatgpt_tool_hub.models.chatgpt.chatgpt import ChatOpenAI
from chatgpt_tool_hub.models.openai import OpenAI, AzureOpenAI


__all__ = [
    "ALL_MAX_TOKENS_NUM",
    "MEMORY_MAX_TOKENS_NUM",
    "BOT_SCRATCHPAD_MAX_TOKENS_NUM",

    "BaseLLM",
    "LLM",
    "OpenAI",
    "AzureOpenAI",
    "ChatOpenAI"
]