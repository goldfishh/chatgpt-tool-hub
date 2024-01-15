from typing import Any

from rich.console import Console

from .. import BaseTool
from ..tool_register import main_tool_register

default_tool_name = "answer-user"


class AnswerUserTool(BaseTool):
    """Tool for answering User."""

    name: str = default_tool_name
    description: str = (
        "To provide your final answer, or if no other tool is needed, use this tool to communicate with user."
        "The input is the words you wish to say to the user."
    )

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

    def _run(self, query: str) -> str:
        """Use the AnswerUserTool tool."""
        return query

    async def _arun(self, query: str) -> str:
        """Use the AnswerUserTool asynchronously."""
        raise NotImplementedError("AnswerUserTool does not support async")

# register the tool
# main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: AnswerUserTool(console, **kwargs), [])
