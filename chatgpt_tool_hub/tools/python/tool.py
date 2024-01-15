"""A tool for running python code in a REPL."""

import sys
from io import StringIO
from typing import Any
from typing import Dict, Optional

from pydantic import Field, BaseModel
from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from .. import BaseTool
from ..tool_register import main_tool_register
from .prompt import QUERY_PROMPT

default_tool_name = "python"


class PythonREPL(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")

    def run(self, command: str) -> str:
        """Run command with own globals/locals and returns anything printed."""
        # Stores the original stdout for later use
        old_stdout = sys.stdout
        # Redirects the stdout to a StringIO object for capturing printed output
        sys.stdout = mystdout = StringIO()

        # 过滤所有`字符，换行符统一单行
        command = "\n".join(filter(lambda s: s, command.split("\n"))).replace("`", "").strip()

        try:
            exec(command, self.globals, self.locals)
            sys.stdout = old_stdout
            # Retrieves the captured output from the StringIO object
            output = mystdout.getvalue()
            LOG.debug(f"[python] output: {str(output)}")
        except Exception as e:
            sys.stdout = old_stdout
            output = repr(e)
            LOG.error(f"[python] {output}")
        return output


def _get_default_python_repl() -> PythonREPL:
    return PythonREPL(_globals=globals(), _locals=None)


class PythonTool(BaseTool):
    """A tool for running python code in a REPL."""

    name: str = default_tool_name
    description: str = (
        "A Python shell. Use this to execute python commands. "
        "Input should be a valid python command. "
        "If you want to see the output of a value, you should print it out with `print(...)`."
    )
    python_repl: PythonREPL = Field(default_factory=_get_default_python_repl)
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "python_debug", "PYTHON_DEBUG", False)

    def _run(self, query: str) -> str:
        """Use the tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        
        return self.python_repl.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("PythonTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: PythonTool(console, **kwargs), [])
