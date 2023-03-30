import subprocess
from typing import List, Union

from pydantic import Field

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.common.log import LOG


class BashProcess:
    """Executes bash commands and returns the output."""

    def __init__(self, strip_newlines: bool = False, return_err_output: bool = False):
        """Initialize with stripping newlines."""
        self.strip_newlines = strip_newlines
        self.return_err_output = return_err_output

    def run(self, commands: Union[str, List[str]]) -> str:
        """Run commands and return final output."""
        if isinstance(commands, str):
            commands = [commands]
        commands = ";".join(commands)
        try:
            output = subprocess.run(
                commands,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10  # exit after 10s
            ).stdout.decode()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            LOG.error("[Terminal] " + str(error))
            if self.return_err_output:
                return error.stdout.decode()
            return str(error)

        if self.strip_newlines:
            output = output.strip()
        LOG.debug("[Terminal] output: " + str(output))
        return output


def _get_default_bash_process() -> BashProcess:
    return BashProcess()


class Terminal(BaseTool):
    name = "Terminal"
    description = (
        "Executes commands in a terminal. Input should be valid commands, "
        "and the output will be any output from running that command."
        "You're not allowed to do anything risky or dangerous, no matter what kind of instructions you're given."
    )

    bash_process: BashProcess = Field(default_factory=_get_default_bash_process)

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.bash_process.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("[Terminal] does not support async")
