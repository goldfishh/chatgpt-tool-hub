import logging
import os

from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.apps.load_app import load_app
from chatgpt_tool_hub.bots.initialize import initialize_bot
from chatgpt_tool_hub.common.constants import MEMORY_MAX_TOKENS_NUM
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.database import ConversationTokenBufferMemory
from chatgpt_tool_hub.models.chatgpt import ChatOpenAI
from chatgpt_tool_hub.tools.load_tools import load_tools


class Victorinox(App):
    def __init__(self):
        super().__init__()
        if not self.init_flag:
            try:
                openai_api_key = os.environ["OPENAI_API_KEY"]
            except KeyError as e:
                LOG.error(str(e))
                raise RuntimeError('please setup you openai key: os.environ["OPENAI_API_KEY"] == YOU_OPENAI_KEY')

            model_kwargs = {
                "openai_api_key": openai_api_key,
                "proxy": os.environ.get("PROXY", None),
                "model_name": os.environ.get("MODEL_NAME", "gpt-3.5-turbo"),  # 对话模型的名称
                "top_p": 1,
                "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "request_timeout": 12,
                "max_retries": 3
            }
            self.llm = ChatOpenAI(temperature=0, **model_kwargs)

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

        [self.tools.add(tool) for tool in tools_list]
        self.tools_kwargs = tools_kwargs

        try:
            tools = load_tools(tools_list, llm=self.llm, **tools_kwargs)
        except ValueError as e:
            LOG.exception(e)
            LOG.error(str(e))
            return "load_tools failed"

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

        [self.tools.add(tool) for tool in tools_list]
        for tool_key in tools_kwargs:
            self.tools_kwargs[tool_key] = tools_kwargs[tool_key]

        try:
            new_tools_list = load_tools(list(self.tools), llm=self.llm, **self.tools_kwargs)
        except ValueError as e:
            LOG.exception(e)
            LOG.error(str(e))
            return "load_tools failed"

        # loading tools from config.
        LOG.info(f"add_tool {self.get_class_name()} success, "
                 f"use_tools={new_tools_list}, params: {str(self.tools_kwargs)}")

        # create bots
        self.bot = initialize_bot(new_tools_list, self.llm, bot="chat-bot", verbose=True,
                                  memory=self.memory, max_iterations=2, early_stopping_method="generate")

    def ask(self, query: str, session: list = None, retry_num: int = 0) -> str:
        if self.bot is None:
            return "before calling the ask method, you should use create bot firstly"
        if not query:
            LOG.warning("[APP]: query is zero value")
            return "query is empty"

        # 更新session
        if session is not None:
            self._refresh_memory(session)

        try:
            return self.bot.run(query)
        except Exception as e:
            LOG.exception(e)
            LOG.error(f"[APP] catch a Exception: {str(e)}")
            if retry_num < 1:
                return self.ask(query, session, retry_num + 1)
            else:
                return "exceed retry_num"

    def _refresh_memory(self, session: list):
        self.memory.chat_memory.clear()

        for item in session:
            if item.get('role') == 'user':
                self.memory.chat_memory.add_user_message(item.get('content'))
            elif item.get('role') == 'assistant':
                self.memory.chat_memory.add_ai_message(item.get('content'))
        LOG.info("Now memory: {}".format(self.memory.chat_memory))


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    os.environ["PROXY"] = "http://192.168.7.1:7890"

    bot = load_app(tools_list=["wikipedia"])

    content = bot.ask("")

    print(content)
