<h2 align='center'> chatgpt-tool-hub / ChatGPT工具引擎 </h2>
<p align='center'>给ChatGPT装上手和脚，拿起工具提高你的生产力</p>

<p align="center">
  <a style="text-decoration:none" href="https://github.com/goldfishh" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/chatgpt-tool-hub" alt="Language" />
  </a>
  <a style="text-decoration:none" href="https://github.com/goldfishh" target="_blank">
    <img src="https://img.shields.io/github/license/goldfishh/chatgpt-tool-hub" alt="license " />
  </a>
  <a style="text-decoration:none" href="https://github.com/goldfishh" target="_blank">
    <img src="https://img.shields.io/github/commit-activity/w/goldfishh/chatgpt-tool-hub" alt="commit-activity-week " />
  </a>
  <a style="text-decoration:none" href="https://pypi.org/project/chatgpt-tool-hub/" target="_blank">
    <img src="https://img.shields.io/pypi/dw/chatgpt-tool-hub" alt="pypi-download-dw" />
  </a>
</p>

---

#### (1). 克隆源代码

```bash
git clone git@github.com:goldfishh/chatgpt-tool-hub.git
```

#### (2). `pip install -r requirements.txt`

#### (3). 编辑config.json，填入你的openai_api_key

```json
{
  "tools": [],  // 这里填入你想加载的工具名，默认工具无需填入自动加载
  "kwargs": {
      "openai_api_key": "",  // 必填
      "proxy": "",  // 代理配置，国外ip可忽略
      "debug": false,  // 当你遇到问题提issue前请设置debug为true，提交输出日志
      "no_default": false,  // 控制是否加载默认工具
      "model_name": "gpt-3.5-turbo"  // 默认，其他模型暂未测试
  }
}
```

#### (4). `python3 test.py 你的问题1 [你的问题2 ......]`

> chatgpt判断回复是否使用工具，你可要求chatgpt使用工具（更进一步地使用哪个工具）来帮助它更好回答你的问题