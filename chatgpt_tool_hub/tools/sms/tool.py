"""Tool for the SMS."""
import re
import json
import requests

from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from ..tool_register import main_tool_register
from .. import BaseTool
from .prompt import QUERY_PROMPT

default_tool_name = "sms"


class SMSTool(BaseTool):
    """Tool that sends short sessage.
    https://www.smsbao.com/openapi"""

    name: str = default_tool_name
    description: str = (
        "A Tool can send short sessage. "
    )
    debug: bool = False
    sms_url: str = "https://api.smsbao.com/sms"
    sms_username: str = ""
    sms_apikey: str = ""
    sms_content_template: str = '【toolhub】{content}'

    nickname_mapping: dict = {}

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)
        self.debug = get_from_dict_or_env(tool_kwargs, "sms_debug", "SMS_DEBUG", False)
        self.nickname_mapping = json.loads(get_from_dict_or_env(tool_kwargs, "sms_nickname_mapping", "SMS_NICKNAME_MAPPING", "{}"))

        self.sms_username = get_from_dict_or_env(tool_kwargs, "sms_username", "SMS_USERNAME")
        self.sms_apikey = get_from_dict_or_env(tool_kwargs, "sms_apikey", "SMS_APIKEY")

    def _send(self, command: str) -> str:
        def valid_phone(addr: str = ""): return bool(re.match(r"^1\d{10}$", str(addr)))
        try:
            _json = json.loads(command)
            _to_addr = _json["to_addr"]
            _body = _json["body"]
            
            if not valid_phone(_to_addr):
                _to_addr = self.nickname_mapping[_to_addr]
            assert(valid_phone(_to_addr)), f"phone_number: {_to_addr} is not valid"

            params = {
                'u': self.sms_username, 
                'p': self.sms_apikey, 
                'm': _to_addr, 
                'c': self.sms_content_template.format(content=_body)
            }
            response = requests.get(self.sms_url, params=params)
            status_code = {
                '0': '短信发送成功',
                '-1': '参数不全',
                '-2': '服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间',
                '30': '密码错误',
                '40': '账号不存在',
                '41': '余额不足',
                '42': '账户已过期',
                '43': 'IP地址限制',
                '50': '内容含有敏感词'
            }[response.text]
            return status_code
        except Exception as e:
            LOG.error(f"[sms] send mail error: {repr(e)}")
            return "find error"
        
    def _run(self, query: str) -> str:
        """Use the tool."""
        command = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: sms command: {command}")
        if self.debug:
            return command

        return self._send(command["text"])

    async def _arun(self, _: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("SMSTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: SMSTool(console, **kwargs),[])

if __name__ == "__main__":
    tool = SMSTool(sms_debug=False)
    result = tool.run("向 fish 问候一下，提醒他天冷多添衣，注意休息")
    print(result)
