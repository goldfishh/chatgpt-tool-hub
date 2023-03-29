import logging
import os
from common.log import LOG
from chatgpt_tool_hub.apps import load_app


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    os.environ["PROXY"] = "http://192.168.7.1:7890"
    app = load_app()
    reply = app.ask("使用Terminal执行curl cip.cc")
    print(reply)
