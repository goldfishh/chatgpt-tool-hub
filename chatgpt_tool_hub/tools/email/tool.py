"""Tool for the Email."""
import json
import smtplib
from typing import Any
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from ..tool_register import main_tool_register
from .. import BaseTool
from .prompt import QUERY_PROMPT

default_tool_name = "email"


class EmailTool(BaseTool):
    """Tool that sends email.
    qq邮箱密码并非登录密码而是授权码，申请路径如下: 
    邮箱设置 > 账号 > POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 > 显示服务已开启 并 获取授权码
    https://service.mail.qq.com/detail/0/75"""

    name: str = default_tool_name
    description: str = (
        "A Tool can send email. "
    )
    debug: bool = False
    smtp_client: smtplib.SMTP = None
    sender: str = ""
    authorization_code: str = ""
    nickname_mapping: dict = {}

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)
        self.debug = get_from_dict_or_env(tool_kwargs, "email_debug", "EMAIL_DEBUG", False)
        self.nickname_mapping = json.loads(get_from_dict_or_env(tool_kwargs, "email_nickname_mapping", "EMAIL_NICKNAME_MAPPING", "{}"))

        smtp_host = get_from_dict_or_env(tool_kwargs, "email_smtp_host", "EMAIL_SMTP_HOST", 'smtp.qq.com')
        smtp_port = get_from_dict_or_env(tool_kwargs, "email_smtp_port", "EMAIL_SMTP_PORT", 587)

        self.smtp_client = smtplib.SMTP(smtp_host,smtp_port)
        self.smtp_client.ehlo()  # 1. 发送SMTP的“HELLO”消息
        self.smtp_client.starttls()  # 2. 开始TLS加密

        self.sender = get_from_dict_or_env(tool_kwargs, "email_sender", "EMAIL_SENDER")
        self.authorization_code = get_from_dict_or_env(tool_kwargs, "email_authorization_code", "EMAIL_AUTHORIZATION_CODE")

    def _send(self, command: str) -> str:
        try:
            _json = json.loads(command)
            _to_addr = _json["to_addr"]
            _subject = _json["subject"]
            _body = _json["body"]
            
            self.smtp_client.login(self.sender, self.authorization_code)

            if '@' not in _to_addr:
                _to_addr = self.nickname_mapping[_to_addr]

            message = MIMEText(_body, 'plain', 'utf-8')  # 正文
            message['From'] = self.sender  # 发件人
            message['To'] =  _to_addr  # 收件人

            subject = _subject
            message['Subject'] = Header(subject, 'utf-8')    #主题

            self.smtp_client.sendmail(self.sender, [_to_addr], message.as_string())
            self.smtp_client.quit()
            return "success"
        except Exception as e:
            LOG.error(f"[email] send mail error: {repr(e)}")
            return "find error"
        
    def _run(self, query: str) -> str:
        """Use the tool."""
        command = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: email command: {command}")
        if self.debug:
            return command

        return self._send(command["text"])

    async def _arun(self, _: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("EmailTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: EmailTool(console, **kwargs),[])

if __name__ == "__main__":
    tool = EmailTool()
    result = tool.run("给 fish 发条问候的邮件")
    print(result)