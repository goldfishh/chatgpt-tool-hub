from typing import Any

from rich.console import Console

from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool

default_tool_name = "exit"


class ExitTool(BaseTool):
    """Tool for answering User."""

    name = default_tool_name
    description = (
        "To provide your final answer, or if no other tool is needed, use this tool to communicate with humans. "
        "User cannot see your scratchpad and thoughts, You need to convey to the user whether you have completed "
        "the task and provide details on the completion status."
        "The input MUST be in Chinese and not empty."
    )

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

    def _run(self, query: str) -> str:
        """Use the ExitTool tool."""
        return query

    async def _arun(self, query: str) -> str:
        """Use the ExitTool asynchronously."""
        raise NotImplementedError("ExitTool does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: ExitTool(console, **kwargs), [])
