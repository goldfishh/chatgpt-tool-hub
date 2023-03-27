import logging
import os

from apps.app import App
from bots.initialize import initialize_bot
from database import ConversationTokenBufferMemory
from models.chatgpt import ChatOpenAI
from tools.load_tools import load_tools
from common.log import LOG


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
                "model_name": "gpt-3.5-turbo",  # 对话模型的名称
                "top_p": 1,
                "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "request_timeout": 12,
                "max_retries": 3
            }
            self.llm = ChatOpenAI(temperature=0, **model_kwargs)

            self.memory = ConversationTokenBufferMemory(llm=self.llm, memory_key="chat_history",
                                                        output_key='output', max_token_limit=1600)
            self.init_flag = True

    def create(self, tools_list: list, **tools_kwargs):
        if tools_list is None:
            tools_list = []

        LOG.debug(f"Initializing {self.get_class_name()}, use_tools={tools_list}")

        if not self._check_mandatory_tools(tools_list):
            raise ValueError("_check_mandatory_tools failed")

        # loading tools from config.
        LOG.info(str(tools_kwargs))

        tools = load_tools(tools_list, llm=self.llm, **tools_kwargs)

        # create bots
        self.bot = initialize_bot(tools, self.llm, bot="chat-bot", verbose=True,
                                  memory=self.memory, max_iterations=2, early_stopping_method="generate")

    def ask(self, query: str, session: list = None, retry_num: int = 0) -> str:
        assert self.bot is not None
        if not query:
            LOG.warning("[APP]: query is zero value")
            return "query is empty"
        if session is not None:
            self._refresh_memory(session)
        try:
            return self.bot.run(query)
        except ValueError as e:
            LOG.exception(e)
            LOG.error(f"[APP] catch a ValueError: {str(e)}")
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
        LOG.debug("Now memory: {}".format(self.memory.chat_memory))

    def _check_mandatory_tools(self, use_tools: list) -> bool:
        for tool in self.mandatory_tools:
            if tool not in use_tools:
                LOG.error(f"You have to load {tool} as a basic tool for f{self.get_class_name()}")
                return False
        return True


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    bot = Victorinox()
    bot.create([])
    bot.ask("https://www.36kr.com/p/2186160784654466 总结这个链接的内容")
    # bot.ask("这周世界发生了什么？")
