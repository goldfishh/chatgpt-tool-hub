from chatgpt_tool_hub.apps import App
from chatgpt_tool_hub.apps import AppFactory
from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.prompts import PromptTemplate


class LiteApp(App):

    def __init__(self, **app_kwargs):
        super().__init__()
        if not self.init_flag:
            self.llm = ModelFactory.create_llm_model(temperature=0.9, **app_kwargs)

            self.prompt = PromptTemplate(
                input_variables=["question"],
                template="{question}?",
            )

            self.init_flag = True

    def create(self, tools_list: list, **tools_kwargs):
        assert not tools_list

        self.bot = LLMChain(llm=self.llm, prompt=self.prompt)

    def ask(self, query: str, chat_history: list = None, retry_num: int = 0) -> str:
        if self.bot is None:
            LOG.error("before calling the ask method, you should use create bot firstly")
            raise RuntimeError("初始化失败")
        if chat_history is not None:
            LOG.error("you cannot pass chat_history into LiteApp")
            raise ValueError("历史非空")

        if not query:
            LOG.warning("[APP]: query is zero value")
            raise ValueError("请求为空")

        try:
            response = self.bot.run(query)
            LOG.info(f"[APP] response: {str(response)}")
            return str(response)
        except ValueError as e:
            LOG.error(f"[APP] catch a ValueError: {str(e)}")
            if retry_num < 1:
                return self.ask(query, chat_history, retry_num + 1)
            LOG.error("exceed retry_num")
            raise TimeoutError("超过重试次数")


if __name__ == "__main__":
    bot = AppFactory().create_app('lite', tools_list=["wikipedia"])
    response = bot.ask("")
    print(response)
