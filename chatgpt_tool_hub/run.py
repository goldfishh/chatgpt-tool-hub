import logging
import os

from chatgpt_tool_hub.apps import load_app
from chatgpt_tool_hub.common.log import LOG

if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    os.environ["PROXY"] = "http://192.168.7.1:7890"
    app = load_app()
    reply = app.ask("帮我看看能不能访问到google.com")
    print(reply)
