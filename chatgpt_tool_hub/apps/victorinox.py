from typing import List

from rich.console import Console

from chatgpt_tool_hub.apps import App
from chatgpt_tool_hub.apps import AppFactory
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.database import ConversationTokenBufferMemory
from chatgpt_tool_hub.engine.initialize import init_tool_engine as init_engine
from chatgpt_tool_hub.models import MEMORY_MAX_TOKENS_NUM
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.load_tools import load_tools


class Victorinox(App):
    def __init__(self, console=Console(), **app_kwargs):
        super().__init__()
        if not self.init_flag:
            self.llm = ModelFactory().create_llm_model(**app_kwargs)

            self.memory = ConversationTokenBufferMemory(llm=self.llm, memory_key="chat_history",
                                                        output_key='output', max_token_limit=MEMORY_MAX_TOKENS_NUM)
            self.bot_type = "chat-bot"

            self.think_depth = get_from_dict_or_env(app_kwargs, "think_depth", "THINK_DEPTH", 3)

            self.console = console

            # todo don't remove it
            self.init_flag = True

    def create(self, tools_list: list, **tools_kwargs):
        if tools_list is None:
            tools_list = []
        if not self._check_mandatory_tools(tools_list):
            raise ValueError("check mandatory tools failed")
        if self.tools or self.tools_kwargs:
            LOG.warning("refresh the config of tools")

        self.update_tool_args(tools_list, **tools_kwargs)
        self.load_tools_into_bot(**tools_kwargs)

    def add_tool(self, tool: str, **tools_kwargs):
        if not tool:
            LOG.info("no tool to add")
            return

        self.update_tool_args([tool], **tools_kwargs)
        self.load_tools_into_bot()

    def del_tool(self, tool: str, **tools_kwargs):
        if not tool:
            LOG.info("no tool to add")
            return

        self.update_tool_args([tool], is_del=True, **tools_kwargs)
        self.load_tools_into_bot()

    def update_tool_args(self, tools_list: list, is_del: bool = False, **tools_kwargs):
        if not tools_list:
            return

        if is_del:
            for tool in tools_list:
                self.tools.remove(tool)
            return

        for tool in tools_list:
            self.tools.add(tool)

        for tool_key in tools_kwargs:
            self.tools_kwargs[tool_key] = tools_kwargs[tool_key]

    def load_tools_into_bot(self, **tools_kwargs):
        try:
            tools = load_tools(list(self.tools), main_tool_register, console=self.console, **self.tools_kwargs)
        except ValueError as e:
            LOG.error(repr(e))
            raise RuntimeError("loading tool failed")

        # tool可能注册失败
        self.tools = {tool.name for tool in tools}
        LOG.info(f"use_tools={list(self.tools)}, params: {str(self.tools_kwargs)}")

        self.init_tool_engine(tools, **tools_kwargs)

    def init_tool_engine(self, tools: List[BaseTool] = list, **bot_kwargs):
        # create bots
        # todo fix verbose params
        self.engine = init_engine(tools, self.llm, bot=self.bot_type, verbose=True, memory=self.memory,
                                  max_iterations=self.think_depth, early_stopping_method="generate",
                                  console=self.console, bot_kwargs=bot_kwargs)

    def ask(self, query: str, chat_history: list = None, retry_num: int = 0) -> str:
        if self.engine is None:
            LOG.error("before calling the ask method, you should use create bot firstly")
            raise RuntimeError("app初始化失败")

        if not query:
            LOG.warning("[APP]: query is zero value")
            raise ValueError("请求为空")

        # 更新session
        if chat_history is not None:
            self._refresh_memory(chat_history)

        try:
            LOG.info(f"提问: {query}")
            return self.engine.run(query)
        except Exception as e:
            LOG.error(f"[APP] catch a Exception: {str(e)}")
            if retry_num < 1:
                return self.ask(query, chat_history, retry_num + 1)
            LOG.error("exceed retry_num")
            raise TimeoutError("超过重试次数")

    def _refresh_memory(self, chat_history: list):
        self.memory.chat_memory.clear()
        inputs = {
            "input": ""
        }
        outputs = {
            "output": ""
        }

        for item in chat_history:
            if item.get('role') == 'user':
                inputs["input"] = item.get('content')
            elif item.get('role') == 'assistant':
                outputs["output"] = item.get('content')
                self.memory.save_context(inputs, outputs)

        LOG.debug(f"Now memory: {repr(self.memory.chat_memory.messages)}")


if __name__ == "__main__":
    bot = AppFactory().create_app(tools_list=["wikipedia"])
    content = bot.ask("")
    print(content)
