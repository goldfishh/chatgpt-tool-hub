from typing import Any

from rich.console import Console

from chatgpt_tool_hub.engine import ToolEngine
from chatgpt_tool_hub.engine.initialize import init_tool_engine
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.load_tools import load_tools
from chatgpt_tool_hub.tools.news import news_tool_register

default_tool_name = "news"


class NewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "当你想要获取实时新闻资讯时可以使用该工具，你能获取任何与新闻有关的信息。"
        "该工具包含了金融、早报和news-api三个子工具，访问这些工具前你需要先访问本工具。"
        "工具输入：草稿的总结, 用户想获取的新闻内容"
    )
    engine: ToolEngine = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=True)
        # todo
        tools = load_tools(["finance-news", "morning-news", "news-api"], news_tool_register, console, **tool_kwargs)
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        # subtool 思考深度暂时固定为2
        self.engine = init_tool_engine(tools, llm, bot="qa-bot", verbose=True, console=self.console,
                                       max_iterations=2, early_stopping_method="force")

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"
        return (
            self.engine.run(query)
            if self.engine
            else "the tool was not initialized"
        )

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")

    def get_tool_list(self):
        return news_tool_register.get_registered_tool_names()


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: NewsTool(console, **kwargs), [])
