import os
from apps import load_app


if __name__ == "__main__":
    os.environ["PROXY"] = "http://192.168.7.1:7890"
    app = load_app()
    reply = app.ask("北京今天的天气怎么样？")
    print(reply)
