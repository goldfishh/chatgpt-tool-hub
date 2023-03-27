import logging
import os

from apps.app import App
from chains import LLMChain
from common.log import LOG
from models.chatgpt import ChatOpenAI
from prompts import PromptTemplate


class LiteApp(App):

    def __init__(self):
        super().__init__()
        if not self.init_flag:
            try:
                openai_api_key = os.environ["OPENAI_API_KEY"]
            except KeyError as e:
                LOG.error(str(e))
                raise RuntimeError('please setup you openai key: os.environ["OPENAI_API_KEY"] == YOU_OPENAI_KEY_HERE')

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
            self.llm = ChatOpenAI(temperature=0.9, **model_kwargs)

            self.prompt = PromptTemplate(
                input_variables=["question"],
                template="{question}?",
            )

            self.init_flag = True

    def create(self, tools_list: list, **tools_kwargs):
        assert not tools_list

        self.bot = LLMChain(llm=self.llm, prompt=self.prompt)

    def ask(self, query: str, session: list = None, retry_num: int = 0) -> str:
        assert self.bot is not None
        assert session is None
        if not query:
            LOG.warning("[APP]: query is zero value")
            return ""
        try:
            response = self.bot.run(query)
            LOG.info(f"[APP] response: {str(response)}")
            return str(response)
        except ValueError as e:
            LOG.exception(e)
            LOG.error(f"[APP] catch a ValueError: {str(e)}")
            if retry_num < 1:
                return self.ask(query, session, retry_num + 1)


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    bot = LiteApp()
    bot.create([])
    response = bot.ask("最近中国的新闻有哪些")
    print(str(response))
