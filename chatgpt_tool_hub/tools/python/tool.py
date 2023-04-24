"""A tool for running python code in a REPL."""

import sys
from io import StringIO
from typing import Any
from typing import Dict, Optional

from pydantic import Field, BaseModel
from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool

default_tool_name = "python"


class PythonREPL(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")

    def run(self, command: str) -> str:
        """Run command with own globals/locals and returns anything printed."""
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        # 过滤markdown
        command = "\n".join(filter(lambda s: "```" not in s, command.split("\n"))).replace("`", "").strip()

        try:
            exec(command, self.globals, self.locals)
            sys.stdout = old_stdout
            output = mystdout.getvalue()
            LOG.debug(f"[python] output: {str(output)}")
        except Exception as e:
            output = repr(e)
            sys.stdout = old_stdout
            LOG.error(f"[python] {output}")
        return output


def _get_default_python_repl() -> PythonREPL:
    return PythonREPL(_globals=globals(), _locals=None)


class PythonREPLTool(BaseTool):
    """A tool for running python code in a REPL."""

    name = default_tool_name
    description = (
        "A Python shell. Use this to execute python commands. "
        "Input should be a valid python command. "
        "If you want to see the output of a value, you should print it out with `print(...)`."
    )
    python_repl: PythonREPL = Field(default_factory=_get_default_python_repl)

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.python_repl.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("PythonReplTool does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: PythonREPLTool(console, **kwargs), [])
