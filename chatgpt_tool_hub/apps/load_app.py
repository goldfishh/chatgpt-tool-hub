import logging

from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.common.log import LOG


def init_env(**kwargs):
    """ 自定义环境参数 """
    global default_tools_list
    # debug mode
    debug_flag = get_from_dict_or_env(kwargs, "debug", "DEBUG", "")
    if debug_flag:
        LOG.setLevel(logging.DEBUG)
    # default tools
    no_default_tools_flag = get_from_dict_or_env(kwargs, "no_default_tools", "NO_DEFAULT_TOOLS", "")
    if no_default_tools_flag:
        default_tools_list = []


def load_app(app_type: str = 'victorinox', tools_list: list = None, **kwargs) -> App:
    tools_list = [] if not tools_list else tools_list

    init_env(**kwargs)

    if app_type == 'lite':
        from chatgpt_tool_hub.apps.lite_app import LiteApp
        app = LiteApp()
        app.create(tools_list, **kwargs)
        return app

    elif app_type == 'victorinox':
        from chatgpt_tool_hub.apps.victorinox import Victorinox

        for tool in default_tools_list:
            if tool not in tools_list:
                tools_list.append(tool)

        app = Victorinox()
        app.create(tools_list, **kwargs)
        return app

    else:
        raise NotImplementedError


default_tools_list = ["python", "requests", "terminal", "meteo-weather"]
