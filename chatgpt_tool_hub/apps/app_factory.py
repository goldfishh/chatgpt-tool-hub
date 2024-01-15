import logging

from rich.console import Console

from . import App
from ..common.constants import TRUE_VALUES_SET
from ..common.log import refresh
from ..common.utils import get_from_dict_or_env
from ..models import build_model_params
from ..tools import dynamic_tool_loader


class AppFactory:
    def __init__(self, console=Console(quiet=True)):
        self.default_tools_list = []
        self.console = console

    def init_env(self, **kwargs):
        """ 环境初始化 """
        # set log level
        use_log = get_from_dict_or_env(kwargs, "log", "LOG", True)
        debug_flag = get_from_dict_or_env(kwargs, "debug", "DEBUG", False)
        if str(use_log).lower() == "false":
            refresh(logging.CRITICAL)
        elif str(debug_flag).lower() == "true":
            refresh(logging.DEBUG)
        else:
            refresh(logging.INFO)

        # default tools
        no_default_flag = get_from_dict_or_env(kwargs, "no_default", "NO_DEFAULT", False)
        if str(no_default_flag).lower() == "true":
            self.default_tools_list = []
        else:
            from ..tools.python.tool import default_tool_name as python_tool_name
            from ..tools.terminal.tool import default_tool_name as terminal_tool_name
            from ..tools.web_requests.get import default_tool_name as get_tool_name
            from ..tools.meteo.tool import default_tool_name as meteo_name
            self.default_tools_list = [python_tool_name, terminal_tool_name, get_tool_name, meteo_name]

        # dynamic loading tool
        dynamic_tool_loader(**kwargs)

    def create_app(self, app_type: str = 'victorinox', tools_list: list = None, **kwargs) -> App:
        tools_list = tools_list if tools_list else []

        # todo remove it
        if kwargs.get("openai_api_key"):
            kwargs["llm_api_key"] = kwargs.get("openai_api_key")
        if kwargs.get("open_ai_api_base"):
            kwargs["llm_api_base_url"] = kwargs.get("open_ai_api_base")

        self.init_env(**kwargs)

        if app_type == 'lite':
            from ..apps.lite_app import LiteApp
            app = LiteApp(**build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app

        elif app_type == 'victorinox':
            from ..apps.victorinox import Victorinox

            for default_tool in self.default_tools_list:
                if default_tool not in tools_list:
                    tools_list.append(default_tool)

            from ..tools.tool_register import main_tool_register
            if "browser" in main_tool_register.get_registered_tool_names():
                tools_list = ["browser" if tool == "url-get" else tool for tool in tools_list]

            app = Victorinox(self.console, **build_model_params(kwargs))
            app.create(tools_list, **kwargs)
            return app
        else:
            raise NotImplementedError
