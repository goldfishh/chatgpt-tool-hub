from chatgpt_tool_hub.apps import App
from chatgpt_tool_hub.apps import AppFactory
from chatgpt_tool_hub.bots import initialize_bot
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.database import ConversationTokenBufferMemory
from chatgpt_tool_hub.models import MEMORY_MAX_TOKENS_NUM
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.load_tools import load_tools


class AutoApp(App):
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

        for tool in tools_list:
            self.tools.add(tool)
        self.tools_kwargs = tools_kwargs

        try:
            tools = load_tools(list(self.tools), main_tool_register, **tools_kwargs)
        except ValueError as e:
            LOG.error(str(e))
            raise RuntimeError("tool初始化失败")

        # loading tools from config.
        LOG.info(f"use_tools={[tool.name for tool in tools]}, params: {str(tools_kwargs)}")

        # create bots
        self.bot = initialize_bot(tools, self.llm, bot="chat-bot", verbose=True,
                                  memory=self.memory, max_iterations=10, early_stopping_method="generate")

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
    bot = AppFactory().create_app("auto", tools_list=["wikipedia"])
    content = bot.ask("")
    print(content)
