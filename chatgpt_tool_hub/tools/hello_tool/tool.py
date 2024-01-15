from typing import Any

from rich.console import Console

from .. import BaseTool
from ..tool_register import main_tool_register

default_tool_name = "hello-tool"


class HelloTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "This is a Starship launch controller, "
        "using which one can initiate the launch of a Starship named SpaceX to Mars."
    )

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

    def launch_starship(self):
        pass

    def _run(self, query: str) -> str:
        self.launch_starship()
        return "the starship have been launched"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("HelloTool does not support async")


# register the tool
# main_tool_register.register_tool(default_tool_name,
#                                  lambda console=None, **kwargs: HelloTool(console, **kwargs),
#                                  tool_input_keys=[])
