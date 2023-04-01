

### 1. news 

申请URL: https://newsapi.org/

```python
from chatgpt_tool_hub.apps import load_app
tool_kwargs = {"news_api_key": "29bb38s9a9584b0498asdfs12551b64e"}  # sample_key
app = load_app(tools_list="wolfram-alpha", **tool_kwargs)
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


```python
from chatgpt_tool_hub.apps import load_app
tool_kwargs = {"bing_subscription_key": "13bab6no0valid43d3a889sx8e9d374e22"}  # sample_key
app = load_app(tools_list="bing-search", **tool_kwargs)
```

API限制：
```text
1,000 API calls a month
```

---

### 3. wolfram-alpha

申请URL: https://products.wolframalpha.com/api/
  
```python
from chatgpt_tool_hub.apps import load_app
tool_kwargs = {"wolfram_alpha_appid": "WXXEXX-WH299999QX9"} # sample_key
app = load_app(tools_list="wolfram-alpha", **tool_kwargs)
```

API限制
```text
2,000 non-commercial API calls per month
```

--- 
