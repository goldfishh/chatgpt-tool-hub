import sys
import os

"""由于itchat 使用pickle保存用户登录状态，即itchat.pkl，会记录部分类的import路径，
错误路径将无法读取该pickle，因此itchat在lib/itchat位置需要与chatgpt-on-wechat保持一致"""
current_script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_script_directory)

from .tool import WeChatTool

__all__ = [
    "WeChatTool"
]