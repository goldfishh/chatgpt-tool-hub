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

> 所有tool api-key有两种配置方式：config.json、或设置环境变量（变量名为对应英文大写）

> json配置示例以本项目demo（见README）为准，用到本项目的其他项目配置可能有差异，请自行阅读相应文档配置

### 1. news 

申请URL: https://newsapi.org/

```json
{
  "tools": ["news"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "news_api_key": "29bb38s9a9584b0498asdfs12551b64e"  // sample key
  }
}
```

API限制：  
```text
free: 100 / day
Articles available with 24 hour delay, Search articles up to a month old
```

---

### 2. bing-search

申请URL: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api  
教程：https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e  


```json
{
  "tools": ["bing-search"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "bing_subscription_key": "13bab6no0valid43d3a889sx8e9d374e22"  // sample key
  }
}
```

API限制：
```text
1,000 API calls a month
```

---

### 3. wolfram-alpha

申请URL: https://products.wolframalpha.com/api/
  
```json
{
  "tools": ["wolfram-alpha"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "wolfram_alpha_appid": "WXXEXX-WH299999QX9"  // sample key
  }
}
```

API限制
```text
2,000 non-commercial API calls per month
```

--- 

### 4. google-search
  
申请URL:    
api: https://console.cloud.google.com/apis/credentials?hl=zh-cn    
cse: https://programmablesearchengine.google.com/cse/setup/basic?cx=ac35de3babcf9d8ca
  
申请教程参考:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. If you don't already have an account, create one and log in.
3. Create a new project by clicking on the "Select a Project" dropdown at the top of the page and clicking "New Project". Give it a name and click "Create".
4. Go to the [APIs & Services Dashboard](https://console.cloud.google.com/apis/dashboard) and click "Enable APIs and Services". Search for "Custom Search API" and click on it, then click "Enable".
5. Go to the [Credentials](https://console.cloud.google.com/apis/credentials) page and click "Create Credentials". Choose "API Key".
6. Copy the API key and set it as an environment variable named `GOOGLE_API_KEY` on your machine. See setting up environment variables below.
7. Go to the [Custom Search Engine](https://cse.google.com/cse/all) page and click "Add".
8. Set up your search engine by following the prompts. You can choose to search the entire web or specific sites.
9. Once you've created your search engine, click on "Control Panel" and then "Basics". Copy the "Search engine ID" and set it as an environment variable named `GOOGLE_CSE_ID` on your machine. See setting up environment variables below.


```json
{
  "tools": ["google-search"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "google_api_key": "AIzaSyCppotSb8CTiliuNKuk4yKPUMtFMBDT_wM",
      "google_cse_id": "ac35de3babcf9d8ca"  // sample key
  }
}
```

API限制：
```text
每天令牌授予率上限为每天10,000 个授权
```

--- 

### 5. morning-news

申请URL: https://alapi.cn/

```json
{
  "tools": ["morning-news"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "morning_news_api_key": "s32C6sdfdsSPnn6wC"  // sample key
  }
}
```

API限制
```text
限制QPS: 1
```

--- 

### 6. searxng-search

该工具需要本地部署  
教程URL: https://docs.searxng.org/admin/installation.html

```json
{
  "tools": ["searxng-search"],
  "kwargs": {
      "llm_api_key": "",
      "proxy": "",
      "debug": false,
      "no_default": false,
      "model_name": "gpt-3.5-turbo",
      "searx_search_host": "http://192.168.7.3:7780"  // sample key
  }
}
```


---