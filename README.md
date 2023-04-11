<h2 align='center'> chatgpt-tool-hub / ChatGPT工具引擎 </h2>
<p align='center'>给ChatGPT装上手和脚，拿起工具提高你的生产力</p>

<p align="center">
  <a style="text-decoration:none" href="https://aianything.netlify.app" target="_blank">
    <img src="https://img.shields.io/badge/language-python-blue" alt="Language" />
  </a>
  <a style="text-decoration:none" href="https://github.com/KeJunMao" target="_blank">
    <img src="https://img.shields.io/github/license/goldfishh/chatgpt-tool-hub" alt="license " />
  </a>
  <a style="text-decoration:none" href="https://github.com/KeJunMao" target="_blank">
    <img src="https://img.shields.io/github/last-commit/goldfishh/chatgpt-tool-hub" alt="last commit " />
  </a>
</p>


---
简体中文 | [English](./docs/README_en.md)

## 简介

---

这是一个能让ChatGPT使用多个神奇工具的执行引擎，你能用自然语言命令ChatGPT使用联网、搜索、数学运算、控制电脑、执行代码等工具，扩大ChatGPT使用范围提高你的生产力。

本项目因关注到ChatGPT开放插件而诞生，该插件定制性较差，且生态封闭，这不是一个好的趋势，我相信未来国内LLM一定百花齐放，同时我从ChatGPT看到了使用工具的可行性，和潜在价值，因此我希望做一个能兼容未来LLM的工具生态。

如果把ChatGPT的插件比作Apple的App Store，那么这个项目最终形态就是Android OS的开放式生态，简称LLM-OS。在这个生态里所有工具组成一个操作系统，用户仅需输入或传述文字即可做任何事情。  

鉴于目前状况，本项目的定位是：一个开源的ChatGPT工具生态系统，您可以将工具与ChatGPT结合使用，使用自然语言来完成任何事情。

<p align="center">
  <img src="./assets/llm-os.jpg" width="50%" height="50%">
</p>

## 特性

---

- 支持中文输入输出
- 支持上下文记忆
- 支持proxy
- 支持多种工具： 
  - terminal
  - python
  - url-get
  - wikipedia
  - meteo-weather
  - news
  - morning-news
  - bing-search
  - wolfram-alpha


## 快速开始

---
### 1.  使用shell运行demo

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

#### (4). `python3 run.py 你的问题1 [你的问题2 ......]`

> chatgpt判断回复是否使用工具，你可要求chatgpt使用工具（更进一步地使用哪个工具）来帮助它更好回答你的问题

#### (5). 给项目点个star & 有能力pr，支持项目作者继续开发...

--- 

### 2. 去[chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat)使用本项目开发的tool插件：[tool README](https://github.com/goldfishh/chatgpt-on-wechat/blob/master/plugins/tool/README.md)

> 你可以在微信用到本项目为chatgpt提供的工具能力

---

### 3. 你是其他项目开发者，想要接入本工具引擎

#### (1). 安装chatgpt-tool-hub包

`pip install -i https://pypi.python.org/simple chatgpt-tool-hub`

#### (2). 示例代码：

```python
import os
from chatgpt_tool_hub.apps import load_app
os.environ["OPENAI_API_KEY"] = YOUR_OPENAI_API_KEY
os.environ["PROXY"] = "http://192.168.7.1:7890"
app = load_app()
reply = app.ask(YOUR_QUESTION_TO_HERE)
print(reply)
```
  
> 如果有需求，我会更新接入的文档，欢迎提issue

---

## 工具指南

---

> 工具名末尾加*表示使用该工具需要额外申请服务key, 超出免费额度需给服务提供商**支付费用** 

#### 1. terminal

在你运行的电脑里执行shell命令，可以配合你想要ChatGPT生成的代码使用，给予你通过自然语言控制电脑手段 

```text
1. 使用Terminal执行curl cip.cc    
2. wget下载 https://static.runoob.com/images/demo/demo2.jpg 到 xxx 路径    
```

#### 2. python

python解释器，使用它来解释执行python指令，可以配合你想要ChatGPT生成的代码输出结果或执行事务

```text
1. 使用python查询今天日期    
2. eval this expression: hex(123456)-123    
```

#### 3. url-get

往往用来获取某个网站具体内容，结果可能会被反爬策略影响

```
1. 总结信息 https://github.com/goldfishh/chatgpt-tool-hub    
2. 可以作为信息入口配合其他工具   
```

#### 4. wikipedia

可以回答你想要知道确切的人事物

```
1. wikipedia 查找：小红帽   
```

#### 5. meteo-weather

回答你有关天气的询问, 需要获取时间、地点上下文信息，本工具使用了[meteo open api](https://open-meteo.com/)

```text
1. 查询2023.4.1 南京未来七天的天气情况   
2. 现在时间是2023.4.1 北京明天会不会下雨   
```

#### 6. news *

获取实时新闻，从全球 80,000 多个信息源中获取当前和历史新闻文章

```text
1. 最近美国有什么热点新闻？   
```

#### 7. bing-search *

bing搜索引擎，从此你不用再烦恼搜索要用哪些关键词
```text
1. 使用bing-search工具获取任何你想搜索的内容
``` 

#### 8. wolfram-alpha *

知识搜索引擎、科学问答系统，常用于专业学科计算

```text
1. 使用wolfram gdp china vs. usa   
2. 使用wolfram solve a x^2 + b x + c = 0 for x   
```

#### 申请可选工具：[方法](./docs/apply_optional_tool.md)  

## 原理

---

工具引擎的实现原理本质是**Chain-of-Thought**：[Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)
  
我将通过用6个自问自答的问题解释chatgpt-tool-hub的工作原理  

#### 1. 事务型工具（如terminal、python）是在哪运行，以及如何执行的

事务型工具是在你本地运行的，事务型工具本质是一个python编写的函数，terminal、python、url-get工具分别用到了封装调用subprocess库、python解释器和requests库的函数

--- 

#### 2. ChatGPT是如何触发调用这些函数

借助ChatGPT api提供的temperature参数，该参数越低，ChatGPT输出的结果会更集中和确定，当temperature为0时，相同的问题会得到统一回答  
我在prompt构建时会提供给ChatGPT此时用到的工具列表信息，每个工具信息包含：工具名 和 工具描述：

```text
TOOLS:  
------  
  
You have access to the following tools:  

> Python REPL: A Python shell. Use this to execute python commands. 
> url-get: A portal to the internet. Use this when you need to get specific content from a website. 
> Terminal: Executes commands in a terminal. 
> Bing Search: A wrapper around Bing Search. Useful for when you need to answer questions about current events. 
```

有了工具prompt，这时ChatGPT就能理解这些工具名字和使用场景，调用事务函数还需要进一步细化我和ChatGPT之间的通信协议（仍是通过prompt）：
通信协议限制ChatGPT使用工具时返回内容的格式，只能返回三种前缀的内容：

```text
1. Thought: Do I need to use a tool? Yes or No
2. Action: 工具名字
3. Action Input: 工具的输入
```

通信协议完整prompt：  
```text
To use a tool, please use the following format:


Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [Python REPL, url-get, Terminal, Bing Search]
Action Input: the input to the action
Observation: the result of the action
```

此时，工具引擎有专用的文本解析模块负责解析这些内容，当解析成功后，将调度到具体事务函数执行，然后返回固定前缀的结果：

```text
Observation: 当事务函数执行完成返回时的内容
```

带Observation前缀的内容往往是使用事务型工具的用户想知道的答案

--- 
  
#### 3. ChatGPT怎么知道该用的工具和输入，是否每次都严格按照prompt生成格式化内容

ChatGPT微调时进行大量Q&A、CoT预料的学习和RLHF调优，目前ChatGPT对于工具和内容生成的质量是有保证的  
但是目前不是100%，因为会有低质量prompt或者不合适工具的输入，这些问题在工具引擎会进行鲁棒性的处理来保证生成内容的稳定性  

我创建一个issue，可以方便大家来获取和分享使用tool过程解决的有趣问题和思路、每个tool使用时prompt技巧、遇到问题的处理办法：
[更好的使用tool的技巧交流](https://github.com/goldfishh/chatgpt-tool-hub/issues/3)

--- 

#### 4. 如果需要多个工具交替配合解决某个问题，引擎是怎么做的？

当事务函数处理完成返回结果后，默认不会直接返回给用户，而是根据结果内容CoT，在整个prompt中，还有两个子prompt负责用户对话历史记录和中间结果

用户对话历史记录：
```text
Human: A question
AI: A answer
......
```

中间结果：
```text
Thought: Do I need to use a tool? Yes
Action: Wolfram Alpha
Action Input: gdp china vs. usa
Observation: China\nUnited States | GDP | nominal \nAnswer: China | $14.72 trillion per year\nUnited States | $20.95 trillion per year\n(2020 estimates)
Thought:
```

每轮工具CoT过程均会作为下次推理判断工具的依据，由此迭代地进行工具判断、执行，最后当识别到特定前缀时，CoT结果将返回给用户    
  
CoT结束prompt：
```text
When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
AI: the response to the original input question in chinese

```


ChatGPT使用工具过程并不顺利：当遇到迭代次数到达预设值时，会根据历史过程，返回给用户最后结果    

--- 

#### 5. 事务性工具交给ChatGPT是否具有不可预料的危险性？

是的，当你用事务性工具时，你就给予了ChatGPT在你本地运行程序的权利，你需要权限限制来规避可能的风险      
如果无法信任ChatGPT主导你的机器，请不要使用  

--- 

#### 6. 非事务型工具的实现原理是什么

参考[ChatGPT 官方插件](https://github.com/openai/chatgpt-retrieval-plugin)，非事务性工具也称为插件型工具，该工具可视为开放性的ChatGPT插件

---



## 计划

---
 
### feature todolist
  
[✓] 结果可解释性输出  
[○] 长文本场景, tool token溢出的问题    
[○] gpt_index长文本(pdf、html)检索  
[○] 接口并发支持  
[○] support zero-shot tool && no tool    
[○] 长工具顺序控制  
[○] 工具中断、定时  
[○] 粒度配置  
[○] 语音输入  
[✗] 一个前端demo   
  
### tool todolist  
   
[○] stable-diffusion 中文prompt翻译    
[✓] ImageCaptioning   
[○] 小米智能家居控制   
[○] 支持ChatGPT官方插件  
[○] 支持图片处理工具   
[○] 支持视频处理工具  
[✗] Wechat  

## Q&A

---

我将在之后更新这部分内容  

## 工具开发指南

---
 
目前工具分为两类：事务型工具、插件型工具   
 
我等待有需求之后更新这部分内容    

## 更新日志

---



## 背景

---

我将很快更新这部分内容   
