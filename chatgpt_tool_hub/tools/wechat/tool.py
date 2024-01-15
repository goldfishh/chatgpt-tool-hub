"""Tool for the WeChat."""
from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from ..tool_register import main_tool_register
from .. import BaseTool
from .prompt import QUERY_PROMPT
from .wrapper import WechatWrapper

default_tool_name = "wechat"


class WeChatTool(BaseTool):
    """Tool that sends wechat."""
    name: str = default_tool_name
    description: str = (
        "A Tool can send wechat. "
    )
    debug: bool = False
    wrapper: WechatWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)
        self.wrapper = WechatWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)
        self.debug = get_from_dict_or_env(tool_kwargs, "wechat_debug", "WECHAT_DEBUG", False)

    def login(self) -> str:
        try:
            self.wrapper.login()
        except Exception as e:
            LOG.exception(e)
            return "error"
        return "success"

    def _run(self, query: str) -> str:
        """Use the tool."""
        command = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: wechat command: {command}")
        if self.debug:
            return command

        return self.wrapper.run(command["text"])

    async def _arun(self, _: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("WeChatTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: WeChatTool(console, **kwargs),[])

if __name__ == "__main__":
    tool = WeChatTool(wechat_debug=False)
    result = tool.run("在迪奥娜的粉丝群里发条问候大家的短信")
    print(result)









