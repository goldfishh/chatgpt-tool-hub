import logging

from chatgpt_tool_hub.apps import App
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.tools import dynamic_tool_loader
from rich.console import Console


class AppFactory:
    def __init__(self, console=Console()):
        self.default_tools_list = []
        self.console = console
        pass

    def init_env(self, **kwargs):
        """ 环境初始化 """
        # set log level
        nolog_flag = get_from_dict_or_env(kwargs, "nolog", "NOLOG", False)
        debug_flag = get_from_dict_or_env(kwargs, "debug", "DEBUG", False)
        if nolog_flag:
            LOG.setLevel(logging.CRITICAL)
        elif debug_flag:
            LOG.setLevel(logging.DEBUG)
        else:
            LOG.setLevel(logging.INFO)

        # default tools
        no_default_flag = get_from_dict_or_env(kwargs, "no_default", "NO_DEFAULT", "")
        if no_default_flag:
            self.default_tools_list = ["exit"]
        else:
            self.default_tools_list = ["exit", "python", "terminal", "url-get", "meteo-weather", "news"]

        # dynamic loading tool
        dynamic_tool_loader()

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
            # todo refactor
            if "browser" in tools_list:
                tools_list = list(filter(lambda tool: tool != "url-get", tools_list))

            app = Victorinox(**build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app
        elif app_type == 'auto':
            from chatgpt_tool_hub.apps.auto_app import AutoApp

            # todo no default

            app = AutoApp(**build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app
        else:
            raise NotImplementedError
