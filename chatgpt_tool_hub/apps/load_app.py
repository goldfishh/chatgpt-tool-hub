import logging

from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.common.log import LOG


def init_env(**kwargs):
    """ 环境初始化 """
    # debug mode
    debug_flag = get_from_dict_or_env(kwargs, "debug", "DEBUG", "")
    if debug_flag:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)

    # default tools
    no_default_flag = get_from_dict_or_env(kwargs, "no_default", "NO_DEFAULT", "")
    global default_tools_list
    if no_default_flag:
        default_tools_list = []
    else:
        default_tools_list = ["python", "requests", "terminal", "meteo-weather"]


def get_app_kwargs(kwargs: dict) -> dict:
    return {
        "openai_api_key": get_from_dict_or_env(kwargs, "openai_api_key", "OPENAI_API_KEY"),
        "proxy": get_from_dict_or_env(kwargs, "proxy", "PROXY", ""),
        "model_name": get_from_dict_or_env(kwargs, "model_name", "MODEL_NAME", "gpt-3.5-turbo"),  # 对话模型的名称
        "top_p": 1,
        "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        "request_timeout": 60,
        "max_retries": 2
    }


def load_app(app_type: str = 'victorinox', tools_list: list = None, **kwargs) -> App:
    tools_list = [] if not tools_list else tools_list

    init_env(**kwargs)

    if app_type == 'lite':
        from chatgpt_tool_hub.apps.lite_app import LiteApp
        app = LiteApp(**get_app_kwargs(kwargs))
        app.create(tools_list, **kwargs)
        return app

    elif app_type == 'victorinox':
        from chatgpt_tool_hub.apps.victorinox import Victorinox

        for tool in default_tools_list:
            if tool not in tools_list:
                tools_list.append(tool)

        app = Victorinox(**get_app_kwargs(kwargs))
        app.create(tools_list, **kwargs)
        return app

    else:
        raise NotImplementedError


default_tools_list = []
