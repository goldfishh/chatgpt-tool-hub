import sys
import string
import subprocess
from typing import Any, List, Union, Optional

from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from .. import BaseTool
from ..tool_register import main_tool_register
from .prompt import QUERY_PROMPT

default_tool_name = "terminal"


class BashProcess:
    """Executes bash commands and returns the output."""

    def __init__(self, **tool_kwargs: Any):
        # 是否过滤命令
        self.use_nsfc_filter = get_from_dict_or_env(tool_kwargs, "terminal_nsfc_filter", "TERMINAL_NSFC_FILTER", True)
        # 是否返回llm错误信息
        self.return_err_output = get_from_dict_or_env(tool_kwargs, "terminal_return_err_output", "TERMINAL_RETURN_ERR_OUTPUT", True)
        # terminal执行超时时间
        self.timeout = get_from_dict_or_env(tool_kwargs, "terminal_timeout", "TERMINAL_TIMEOUT", 20)

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
        LOG.warning(f"[terminal] nsfc_filter: unsupported command: {repr(_both_have)}")
        return (
            False,
            f"this command: {repr(_both_have)} is dangerous for you, you are not allowed to use it",
        )

    def reprocess(self, commands: str) -> str:
        # ```xxx
        # real commands is here
        # ```
        return "\n".join(filter(lambda s: s and "```" not in s, commands.split("\n"))).replace("`", "").strip()

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
        LOG.info(f"[terminal] command: {commands}")
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
                return f"(code): {error.returncode}, (cmd): {error.cmd}, (output): {error.output.decode()}"
            return "this tool can't run there commands"
        except subprocess.TimeoutExpired as error:
            LOG.error(f"[Terminal] {str(error)}")
            return f"you input commands exceeds the time limit: `{self.timeout} seconds` "
        LOG.debug(f"[Terminal] success, output: {str(output)}")
        return output if output else "success"


class TerminalTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        f"Executes commands in a terminal. Input should be valid commands in {sys.platform} platform, "
        "and the output will be any output from running that command."
        "Don't input any backquote to this tool."
    )

    bash_process: Optional[BashProcess] = None
    debug: Optional[bool] = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "terminal_debug", "TERMINAL_DEBUG", False)

        self.bash_process = BashProcess(**tool_kwargs)

    def _run(self, query: str) -> str:
        """Use the tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        
        return self.bash_process.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TerminalTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: TerminalTool(console, **kwargs), [])


if __name__ == "__main__":
    bash = BashProcess()
    content = bash.run("`poweroff; sudo ls -l; pwd`")
    print(content)
