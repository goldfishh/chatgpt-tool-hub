import io
import json
import os.path
import threading
from typing import Any, Dict
from pydantic import BaseModel, Extra, root_validator

from ...common.utils import get_from_dict_or_env
from ...common.log import LOG


def qrCallback(uuid, status, qrcode):
    """
    reference to https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechat/wechat_channel.py
    """
    # logger.debug("qrCallback: {} {}".format(uuid,status))
    if status == "0":
        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)


class Response(BaseModel):
    msg: str
    qr_url: str = ""

class WechatWrapper(BaseModel):
    """Wrapper around itchat API."""
    wechat_client: Any
    max_retry_num: int = 3
    
    wechat_hot_reload: bool
    wechat_cpt_path: str
    nickname_mapping: dict

    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.ignore

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            import itchat
            values["wechat_client"] = itchat.instance
            values["wechat_client"].receivingRetryCount = 600  # 修改断线超时时间

            values["wechat_hot_reload"] = get_from_dict_or_env(values, "wechat_hot_reload", "WECHAT_HOT_RELOAD", False)
            if values["wechat_hot_reload"]:
                values["wechat_cpt_path"] =  get_from_dict_or_env(values, "wechat_cpt_path", "WECHAT_CPT_PATH")
                load_result = values["wechat_client"].load_login_status(fileDir=values["wechat_cpt_path"])
                LOG.info(f"[Wechat] hot_reload result: {load_result}")

            values["nickname_mapping"] = json.loads(get_from_dict_or_env(values, "wechat_nickname_mapping", "WECHAT_NICKNAME_MAPPING", "{}"))
        except ImportError:
            raise ValueError(
                "Could not import wechat python package. "
                "Please it install it with `pip install wechat`."
            )
        return values

    def _login(self):
        self.wechat_client.auto_login(
            enableCmdQR=2,
            hotReload=self.wechat_hot_reload,
            statusStorageDir=self.wechat_cpt_path,
            qrCallback=qrCallback,
        )

    def run(self, command: str, **kwargs) -> str:
        try:
            uuid = self.wechat_client.get_QRuuid()
            if self.check_login(uuid) != "200":
                return Response(msg="login expired, please log in again.", 
                                qr_url=f"https://api.isoyu.com/qr/?m=1&e=L&p=20&url=https://login.weixin.qq.com/l/{uuid}").json()

            _json = json.loads(command)
            _to_addr, _body = _json["to_addr"], _json["body"]

            user_id, name = self.wechat_client.storageClass.userName, self.wechat_client.storageClass.nickName
            LOG.info("Wechat login success, user_id: {}, nickname: {}".format(user_id, name))
            
            author_list = self.wechat_client.search_friends(name=_to_addr)
            if len(author_list) != 0:
                author = author_list[0]
                author.send(_body)
                return Response(msg=f"send wechat to people:{author} success").json()

            group_list = self.wechat_client.search_chatrooms(name=_to_addr)
            if len(group_list) == 1:
                group = group_list[0]
                group.send(_body)
                return Response(msg=f"send wechat to group:{group} success").json()
            return Response(msg=f"I don't know how to send to {_to_addr}.").json()
        except Exception as e:
            LOG.error(f"[wechat]: {repr(e)}")
            return Response(msg="unknown error").json()
