from typing import Any

from rich.console import Console

from chatgpt_tool_hub.tools.base_tool import BaseTool


default_tool_name = "hello-tool"


class HelloTool(BaseTool):
    name = default_tool_name
    description = (
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


from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
main_tool_register.register_tool(default_tool_name,
                                 lambda console, kwargs: HelloTool(console, **kwargs),
                                 tool_input_keys=[])
