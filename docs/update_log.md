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

## 更新日志

### 0.1X ~ 0.3X

远古版本，不建议使用

---

### 0.4.1

版本管理从此开始

---

### 0.4.3

#### tool-hub

1. 新增私有部署的搜索工具： searxng-search

2. 修复win系统使用summary临时创建文件后删除的异常 #30

3. morning-news 新增可配置参数：morning_news_use_llm 用于开关api返回后再处理

4. 新增arxiv工具，用于搜索论文

5. 更改tool engine 核心prompt，使用json格式输出llm-os内心独白、工具和工具输入

6. 修复news子工具返回内容包含乱码信息 #26 #27

#### llm-os

1. llm-os问世，目前已支持tool-hub所有功能

`pip install -i https://pypi.python.org/simple chatgpt-tool-hub==0.4.2`

---

### 0.4.4

#### tool-hub

1. 支持azure、api转发服务

2. 修复browser代理无前缀报错的问题

3. 优化core prompt

4. 修复系列issue提到的问题

#### llm-os

1. google-colab demo