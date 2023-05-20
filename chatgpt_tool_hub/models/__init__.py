import os
from typing import Optional

from chatgpt_tool_hub.common.cache import BaseCache
from chatgpt_tool_hub.common.constants import openai_default_api_base
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
    _api_key = get_from_dict_or_env(kwargs, "llm_api_key", "LLM_API_KEY")
    _proxy = get_from_dict_or_env(kwargs, "proxy", "PROXY", "")
    _model = get_from_dict_or_env(kwargs, "model_name", "MODEL_NAME", "gpt-3.5-turbo")
    _timeout = get_from_dict_or_env(kwargs, "request_timeout", "REQUEST_TIMEOUT", 120)
    _llm_api_base_url = get_from_dict_or_env(kwargs, "llm_api_base_url", "LLM_API_BASE_URL", openai_default_api_base)
    _deployment_id = get_from_dict_or_env(kwargs, "deployment_id", "DEPLOYMENT_ID", "")

    # tool llm need them
    os.environ["LLM_API_KEY"] = str(_api_key)
    if _proxy and not _proxy.startswith("http://") and not _proxy.startswith("https://"):
        _proxy = "http://" + _proxy
    os.environ["PROXY"] = str(_proxy)
    os.environ["MODEL_NAME"] = str(_model)
    os.environ["REQUEST_TIMEOUT"] = str(_timeout)
    os.environ["LLM_API_BASE_URL"] = str(_llm_api_base_url)
    os.environ["DEPLOYMENT_ID"] = str(_deployment_id)

    model_params_dict = {
        "temperature": get_from_dict_or_env(kwargs, "temperature", "TEMPERATURE", 0),
        "llm_api_key": _api_key,
        "llm_api_base_url": _llm_api_base_url,
        "proxy": _proxy,
        "model_name": _model,  # 对话模型的名称
        "top_p": 1,
        "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "request_timeout": _timeout,
        "max_retries": 2
    }

    if _deployment_id:
        model_params_dict["model_kwargs"] = {
            "deployment_id": _deployment_id
        }

    return model_params_dict


from chatgpt_tool_hub.models.base import BaseLLM, LLM
from chatgpt_tool_hub.models.chatgpt.chatgpt import ChatOpenAI


__all__ = [
    "ALL_MAX_TOKENS_NUM",
    "MEMORY_MAX_TOKENS_NUM",
    "BOT_SCRATCHPAD_MAX_TOKENS_NUM",

    "BaseLLM",
    "LLM",
    "ChatOpenAI"
]