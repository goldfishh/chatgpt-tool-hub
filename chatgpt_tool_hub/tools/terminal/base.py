import string
import subprocess
import sys
from typing import Any
from typing import List, Union

from pydantic import Field
from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool

default_tool_name = "terminal"


class BashProcess:
    """Executes bash commands and returns the output."""

    def __init__(self, use_nsfc_filter: bool = True, return_err_output: bool = True, timeout: float = 20):
        # 是否过滤命令
        self.use_nsfc_filter = use_nsfc_filter
        # 是否返回llm错误信息
        self.return_err_output = return_err_output
        # terminal执行超时时间
        self.timeout = timeout

    def nsfc_filter(self, commands: Union[str, List[str]]) -> (bool, str):
        if isinstance(commands, str):
            commands = commands.split()
        _commands = " ".join(commands)

        # filter punctuation
        for i in string.punctuation:
            _commands = _commands.replace(i, ' ')

        command_ban_set = {"halt", "poweroff", "shutdown", "reboot", "rm", "kill",
                           "exit", "sudo", "su", "userdel", "groupdel", "logout", "alias"}
        if not (
            _both_have := command_ban_set.intersection(set(_commands.split()))
        ):
            return True, "success"
        LOG.info(f"[terminal] nsfc_filter: unsupported command: {repr(_both_have)}")
        return (
            False,
            f"this command: {repr(_both_have)} is dangerous for you, you are not allowed to use it",
        )

    def reprocess(self, commands: str) -> str:
        # ```xxx
        # real commands is here
        # ```
        commands = "\n".join(filter(lambda s: "```" not in s, commands.split("\n")))
        return commands.strip('`')

    def run(self, commands: Union[str, List[str]]) -> str:
        """Run commands and return final output."""
        if isinstance(commands, str):
            commands = self.reprocess(commands)

            commands = commands.split('\n')

        if self.use_nsfc_filter:
            sfc, result = self.nsfc_filter(commands)
            if not sfc:
                return result

        # 统一传入string格式
        commands = ";".join(commands)

        try:
            # 阻塞
            output = subprocess.run(
                commands,
                shell=True,
                check=True,  # raises a CalledProcessError when exit code is non-zero
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout  # raises TimeoutExpired after running 20s
            ).stdout.decode()
        except subprocess.CalledProcessError as error:
            LOG.error(f"[Terminal] {str(error)}")
            if self.return_err_output:
                return error.stdout.decode()
            return "this tool can't run there commands"
        except subprocess.TimeoutExpired as error:
            LOG.error(f"[Terminal] {str(error)}")
            return f"you input commands exceeds the time limit: `{self.timeout} seconds` " \
                   "supported by the tool for executing commands."
        LOG.debug(f"[Terminal] output: {str(output)}")
        return output


def _get_default_bash_process() -> BashProcess:
    return BashProcess()


class TerminalTool(BaseTool):
    name = default_tool_name
    description = (
        f"Executes commands in a terminal. Input should be valid commands in {sys.platform} platform, "
        "and the output will be any output from running that command."
        "Don't input any backquote to this tool."
    )

    bash_process: BashProcess = Field(default_factory=_get_default_bash_process)

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.bash_process.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("[Terminal] does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: TerminalTool(console, **kwargs), [])


if __name__ == "__main__":
    bash = BashProcess()
    content = bash.run("`poweroff; sudo ls -l; pwd`")
    print(content)
