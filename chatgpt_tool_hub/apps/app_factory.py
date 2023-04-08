import logging

from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.models import build_model_params


class AppFactory:
    def __init__(self):
        self.default_tools_list = []
        pass

    def init_env(self, **kwargs):
        """ 环境初始化 """
        # debug mode
        debug_flag = get_from_dict_or_env(kwargs, "debug", "DEBUG", "")
        if debug_flag:
            LOG.setLevel(logging.DEBUG)
        else:
            LOG.setLevel(logging.INFO)

        # default tools
        no_default_flag = get_from_dict_or_env(kwargs, "no_default", "NO_DEFAULT", "")
        if no_default_flag:
            self.default_tools_list = []
        else:
            self.default_tools_list = ["python", "url-get", "terminal", "meteo-weather"]

    def create_app(self, app_type: str = 'victorinox', tools_list: list = None, **kwargs) -> App:
        tools_list = [] if not tools_list else tools_list

        self.init_env(**kwargs)

        if app_type == 'lite':
            from chatgpt_tool_hub.apps.lite_app import LiteApp
            app = LiteApp(**build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app

        elif app_type == 'victorinox':
            from chatgpt_tool_hub.apps.victorinox import Victorinox

            for default_tool in self.default_tools_list:
                if default_tool not in tools_list:
                    tools_list.append(default_tool)

            app = Victorinox(**build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app

        else:
            raise NotImplementedError
