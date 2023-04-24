import logging
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools import BrowserTool
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news import news_tool_register

default_tool_name = "finance-news"


class FinanceNewsTool(BaseTool):
    
    name: str = default_tool_name
    description: str = (
        "Useful when you want to stay up-to-date on global real-time financial news."
        "The tool aggregates various types of data and information from the financial investment industry."
        "input is needless for this tool."
    )

    jin10_url: str = "https://www.jin10.com/example/jin10.com.html"

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

    def _run(self, tool_input: str) -> str:
        """ finance-news 仅仅是一个 browser tool 的封装吗？ """
        return BrowserTool().run(self.jin10_url)

    async def _arun(self, tool_input: str) -> str:
        pass


news_tool_register.register_tool(default_tool_name, lambda console, kwargs: FinanceNewsTool(console, **kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    tool = FinanceNewsTool()
    content = tool.run("")
    print(content)
