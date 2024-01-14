import os
from typing import Optional

from ..common.log import LOG
from ..common.cache import BaseCache
from ..common.constants import openai_default_api_base
from ..common.utils import get_from_dict_or_env

verbose: bool = False
llm_cache: Optional[BaseCache] = None

# default model
DEFAULT_MODEL_NAME = "gpt-3.5-turbo-16k"

# token manage strategy
ALL_MAX_TOKENS_NUM = 4000
BOT_PROMPT = 1000
MEMORY_MAX_TOKENS_NUM = 600
BOT_SCRATCHPAD_MAX_TOKENS_NUM = ALL_MAX_TOKENS_NUM - BOT_PROMPT - MEMORY_MAX_TOKENS_NUM - 200


def list_openai_models(api_key: str):
    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        from ..tools.web_requests.wrapper import RequestsWrapper
        wrapper = RequestsWrapper(headers=headers)
        response = wrapper.get(url, headers=headers, raise_for_status=True)

        models_data = response.json()
        model_ids = [model["id"] for model in models_data.get("data", [])]

        return model_ids
    except Exception as e:
        LOG.error(f"(list_openai_models) Error calling OpenAI API: {e}")
        return None

def build_model_params(kwargs: dict) -> dict:
    _api_key = get_from_dict_or_env(kwargs, "llm_api_key", "LLM_API_KEY")
    _proxy = get_from_dict_or_env(kwargs, "proxy", "PROXY", "")
    _model = get_from_dict_or_env(kwargs, "model_name", "MODEL_NAME", DEFAULT_MODEL_NAME)
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
        "llm_api_key": _api_key,
        "llm_api_base_url": _llm_api_base_url,
        "llm_model_name": _model,  # 对话模型的名称
        "top_p": 1,
        "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "temperature": get_from_dict_or_env(kwargs, "temperature", "TEMPERATURE", 0),
        "proxy": _proxy,
        "request_timeout": _timeout,
        "max_retries": 2
    }

    if _deployment_id:
        model_params_dict["llm_model_kwargs"] = {
            "deployment_id": _deployment_id
        }

    return model_params_dict


from .base import BaseLLM, LLM
from .chatgpt.chatgpt import ChatOpenAI


__all__ = [
    "ALL_MAX_TOKENS_NUM",
    "MEMORY_MAX_TOKENS_NUM",
    "BOT_SCRATCHPAD_MAX_TOKENS_NUM",

    "BaseLLM",
    "LLM",
    "ChatOpenAI"
]