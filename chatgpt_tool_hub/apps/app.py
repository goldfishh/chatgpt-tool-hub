from abc import abstractmethod

from typing import List

from chatgpt_tool_hub.engine.tool_engine import ToolEngine
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.base_tool import BaseTool


class App:
    _instance = None  # 存储单例实例
    init_flag = False  # 记录是否执行过初始化动作

    engine: ToolEngine = None

    # 当前已加载工具
    tools: set = set()
    tools_kwargs: dict = {}

    # 创建时必须包含的工具列表
    mandatory_tools: list = []

    @classmethod
    def get_class_name(cls) -> str:
        return str(cls.__name__)

    def __new__(cls, *args, **kwargs):
        instance_name = f"{cls.__name__}_instance"
        cls._instance = getattr(cls, instance_name, None)
        if not cls._instance:
            cls._instance = super(App, cls).__new__(cls)
            setattr(cls, instance_name, cls._instance)
        return cls._instance

    def __init__(self):
        return

    @abstractmethod
    def create(self, tools_list: list, **tools_kwargs):
        """overload this method to create a bot"""

    def add_tool(self, tool: str, **tools_kwargs):
        raise ValueError("add_tool not implemented for this app.")

    def del_tool(self, tool: str, **tools_kwargs):
        raise ValueError("del_tool not implemented for this app.")

    def init_tool_engine(self, tools: List[BaseTool] = list):
        raise ValueError("init_tool_engine not implemented for this app.")

    def load_tools_into_bot(self, **tools_kwargs):
        raise ValueError("load_tools_into_bot not implemented for this app.")

    def update_tool_args(self, tools_list: list, is_del: bool = False, **tools_kwargs):
        if is_del:
            for tool in tools_list:
                self.tools.remove(tool)
            return

        for tool in tools_list:
            self.tools.add(tool)

        for tool_key in tools_kwargs:
            self.tools_kwargs[tool_key] = tools_kwargs[tool_key]

    @abstractmethod
    def ask(self, query: str, chat_history: list = None, retry_num: int = 0) -> str:
        """use this method to interactive with bot"""

    def _check_mandatory_tools(self, use_tools: list) -> bool:
        for tool in self.mandatory_tools:
            if tool not in use_tools:
                LOG.error(f"You have to load {tool} as a basic tool for f{self.get_class_name()}")
                return False
        return True

    def get_tool_list(self) -> List[str]:
        return list(self.engine.get_tool_list())
