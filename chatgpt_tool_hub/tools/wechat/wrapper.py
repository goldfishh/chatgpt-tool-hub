import os
import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, model_validator

from ...common.utils import get_from_dict_or_env
from ...common.log import LOG


def qrCallback(uuid, status, qrcode):
    """
    reference to https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechat/wechat_channel.py
    """
    if status == "0":
        try:
            import io
            import threading
            from PIL import Image

            img = Image.open(io.BytesIO(qrcode))
            _thread = threading.Thread(target=img.show, args=("QRCode",))
            _thread.setDaemon(True)
            _thread.start()
        except Exception as e:
            pass

        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr_api1 = "https://api.isoyu.com/qr/?m=1&e=L&p=20&url={}".format(url)
        qr_api2 = "https://api.qrserver.com/v1/create-qr-code/?size=400×400&data={}".format(url)
        qr_api3 = "https://api.pwmqr.com/qrcode/create/?url={}".format(url)
        qr_api4 = "https://my.tv.sohu.com/user/a/wvideo/getQRCode.do?text={}".format(url)
        print("You can also scan QRCode in any website below:")
        print(qr_api3)
        print(qr_api4)
        print(qr_api2)
        print(qr_api1)

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)

class Response(BaseModel):
    code: int = 0
    msg: str

class WechatWrapper(BaseModel):
    """Wrapper around itchat API."""
    wechat_client: Any
    max_retry_num: int = 3
    
    wechat_hot_reload: Optional[bool]
    wechat_cpt_path: Optional[str]
    wechat_send_group: Optional[bool]
    wechat_nickname_mapping: Optional[dict]

    class Config:
        """Configuration for this pydantic object."""
        extra = 'ignore'

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        import tempfile
        try:
            from lib import itchat
            values["wechat_client"] = itchat.instance
            values["wechat_client"].receivingRetryCount = 600  # 修改断线超时时间

            values["wechat_hot_reload"] = get_from_dict_or_env(values, "wechat_hot_reload", "WECHAT_HOT_RELOAD", False)
            if str(values["wechat_hot_reload"]).lower() == 'true':
                values["wechat_cpt_path"] =  get_from_dict_or_env(values, "wechat_cpt_path", "WECHAT_CPT_PATH")
                load_result = values["wechat_client"].load_login_status(fileDir=values["wechat_cpt_path"])
                # load_result: {'BaseResponse': {'ErrMsg': '请求成功', 'Ret': 0, 'RawMsg': 'loading login status succeeded.'}}
                LOG.debug(f"[Wechat] hot_reload result: {load_result}")
                if load_result:
                    user_id, name = values["wechat_client"].storageClass.userName, values["wechat_client"].storageClass.nickName
                    LOG.info("[wechat] login success, user_id: {}, nickname: {}".format(user_id, name))
                else:
                    LOG.error(f"[wechat] Login expired, load_result: {load_result}")
                    values["wechat_client"].logout()
                    raise RuntimeError("Login expired, please renew `itchat.pkl`")
            else:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
                values["wechat_cpt_path"] = temp_file.name
                LOG.debug(f"[wechat] use default path: {values['wechat_cpt_path']} to save.")
            values["wechat_send_group"] = get_from_dict_or_env(values, "wechat_send_group", "WECHAT_SEND_GROUP", False)
            if str(values["wechat_send_group"]).lower() == 'true':
                values["wechat_send_group"] = True

            values["wechat_nickname_mapping"] = json.loads(get_from_dict_or_env(values, "wechat_nickname_mapping", "WECHAT_NICKNAME_MAPPING", "{}"))
        except ImportError:
            raise ValueError(
                "Could not import itchat python package. "
                f"Please it install it with `pip install itchat-uos==1.5.0.dev0 -t {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')}`."
            )
        return values

    def login(self):
        self.wechat_client.auto_login(
            enableCmdQR=2,
            hotReload=True,  # must be true to save cpt file
            statusStorageDir=self.wechat_cpt_path,
            qrCallback=qrCallback,
        )

    def _default_json_config(self):
        return {
            "indent": 4
        }

    def run(self, command: str, **kwargs) -> str:
        login_status = self.wechat_client.load_login_status(fileDir=self.wechat_cpt_path)
        LOG.debug(f"[Wechat] load_login_status result: {login_status}")
        if not login_status:
            return Response(code=-1, msg="login expired, please log in and try again.").model_dump_json()
                
        try:
            _json = json.loads(command)
            _to_addr, _body = str(_json["to_addr"]), str(_json["body"])
            if not _to_addr or not _body:
                return Response(code=-1, msg=f"无需发送").model_dump_json()
        except Exception as e:
            LOG.error(f"[wechat] parse json error : {repr(e)}, command: {command}")
            return Response(code=-1, msg=f"文本解析错误").model_dump_json()
        
        try:
            author_list = self.wechat_client.search_friends(name=_to_addr)
            for author in author_list:
                if author.userName == self.wechat_client.search_friends().userName:  # 排除自己
                    continue
                author.send(_body)
                return Response(msg=f"send wechat to people:{author.NickName} success").model_dump_json()
            if self.wechat_send_group:
                _to_addr = _to_addr.replace("群", "")  # todo
                group_list = self.wechat_client.search_chatrooms(name=_to_addr)
                for group in group_list:
                    group.send(_body)
                    return Response(msg=f"send wechat to group:{group.NickName} success").model_dump_json()
            return Response(code=-1, msg=f"我找不到这个地址：{_to_addr}.").model_dump_json()
        except Exception as e:
            LOG.error(f"[wechat]: {repr(e)}")
            return Response(code=-1, msg="未知错误").model_dump_json()
