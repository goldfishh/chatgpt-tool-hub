import logging
import os

from chatgpt_tool_hub.apps.app import App
from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.models.chatgpt import ChatOpenAI
from chatgpt_tool_hub.prompts import PromptTemplate


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
                "model_name": os.environ.get("MODEL_NAME", "gpt-3.5-turbo"),  # 对话模型的名称
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
        if self.bot is None:
            return "before calling the ask method, you should use create bot firstly"
        if session is not None:
            return "you should not pass session into LiteApp"
        if not query:
            LOG.warning("[APP]: query is zero value")
            return "query is empty"

        try:
            response = self.bot.run(query)
            LOG.info(f"[APP] response: {str(response)}")
            return str(response)
        except ValueError as e:
            LOG.exception(e)
            LOG.error(f"[APP] catch a ValueError: {str(e)}")
            if retry_num < 1:
                return self.ask(query, session, retry_num + 1)
            else:
                return "exceed retry_num"


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    bot = LiteApp()
    bot.create([])
    response = bot.ask("")
    print(str(response))
