from abc import abstractmethod

from typing import List

from chatgpt_tool_hub.chains.base import Chain
from chatgpt_tool_hub.common.log import LOG


class App:
    _instance = None  # 存储单例实例
    init_flag = False  # 记录是否执行过初始化动作

    bot: Chain = None

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
        return list(self.tools)
