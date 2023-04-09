from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.apps.load_app import load_app
from chatgpt_tool_hub.bots.initialize import initialize_bot
from chatgpt_tool_hub.common.constants import MEMORY_MAX_TOKENS_NUM
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.database import ConversationTokenBufferMemory
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.load_tools import load_tools


class Victorinox(App):
    def __init__(self, **app_kwargs):
        super().__init__()
        if not self.init_flag:
            self.llm = ModelFactory().create_llm_model(**app_kwargs)

            self.memory = ConversationTokenBufferMemory(llm=self.llm, memory_key="chat_history",
                                                        output_key='output', max_token_limit=MEMORY_MAX_TOKENS_NUM)
            self.init_flag = True

    def create(self, tools_list: list, **tools_kwargs):
        if tools_list is None:
            tools_list = []
        if not self._check_mandatory_tools(tools_list):
            raise ValueError("check mandatory tools failed")
        if self.tools or self.tools_kwargs:
            LOG.warning("refresh the config of tools")

        map(self.tools.add, tools_list)
        self.tools_kwargs = tools_kwargs

        try:
            tools = load_tools(tools_list, **tools_kwargs)
        except ValueError as e:
            LOG.error(str(e))
            raise RuntimeError("tool初始化失败")

        # loading tools from config.
        LOG.info(f"Initializing {self.get_class_name()} success, "
                 f"use_tools={tools_list}, params: {str(tools_kwargs)}")

        # create bots
        self.bot = initialize_bot(tools, self.llm, bot="chat-bot", verbose=True,
                                  memory=self.memory, max_iterations=3, early_stopping_method="generate")

    def add_tool(self, tools_list: list, **tools_kwargs):
        """todo: I think there have better way to implement"""
        if not tools_list:
            LOG.info("no tool to add")
            return

        map(self.tools.add, tools_list)
        for tool_key in tools_kwargs:
            self.tools_kwargs[tool_key] = tools_kwargs[tool_key]

        try:
            new_tools_list = load_tools(list(self.tools), **self.tools_kwargs)
        except ValueError as e:
            LOG.error(str(e))
            raise RuntimeError("tool初始化失败")

        # loading tools from config.
        LOG.info(f"add_tool {self.get_class_name()} success, "
                 f"use_tools={new_tools_list}, params: {str(self.tools_kwargs)}")

        # create bots
        self.bot = initialize_bot(new_tools_list, self.llm, bot="chat-bot", verbose=True,
                                  memory=self.memory, max_iterations=2, early_stopping_method="generate")

    def ask(self, query: str, chat_history: list = None, retry_num: int = 0) -> str:
        if self.bot is None:
            LOG.error("before calling the ask method, you should use create bot firstly")
            raise RuntimeError("app初始化失败")

        if not query:
            LOG.warning("[APP]: query is zero value")
            raise ValueError("请求为空")

        # 更新session
        if chat_history is not None:
            self._refresh_memory(chat_history)

        try:
            return self.bot.run(query)
        except Exception as e:
            LOG.error(f"[APP] catch a Exception: {str(e)}")
            if retry_num < 1:
                return self.ask(query, chat_history, retry_num + 1)
            else:
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

        LOG.debug("Now memory: {}".format(self.memory.chat_memory.messages))


if __name__ == "__main__":
    bot = load_app(tools_list=["wikipedia"])
    content = bot.ask("")
    print(content)
