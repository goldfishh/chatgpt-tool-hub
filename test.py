import json
import sys

from chatgpt_tool_hub.apps import AppFactory
from chatgpt_tool_hub.common.log import LOG

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("没有收到你的问题")
    else:
        try:
            with open("config.json.template", "r") as f:
                config = json.load(f)
        except Exception as e:
            LOG.error(repr(e))
            config = {"tools": [], "kwargs": {}}

        app = AppFactory().create_app(tools_list=config["tools"], **config["kwargs"])

        for i in range(1, len(sys.argv)):
            reply = app.ask(sys.argv[i])
            print(reply)
