# chatgpt-tool-hub
An open-source chatgpt tool ecosystem where you can combine tools with chatgpt and use natural language to do anything.
If plugins are the App store for ChatGPT, then ChatGPT-Tool-Hub is the APK installer for Android.  
  
## I will update this doc later

### Installation
You can install directly using **pip** by doing `chatgpt-tool-hub`

### Example
```python
import os
from chatgpt_tool_hub.apps import load_app
os.environ["OPENAI_API_KEY"] = YOUR_OPENAI_API_KEY
os.environ["PROXY"] = "http://192.168.7.1:7890"
app = load_app()
reply = app.ask("你现在有哪些能力？")
print(reply)
```


### Tool
- python_repl
- requests(GET by default)
- terminal
- meteo-weather
- wikipedia
- news-api(you need news_api_key from https://newsapi.org/)
- wolfram-alpha(you need wolfram_alpha_appid from https://developer.wolframalpha.com/)
- google-search(you need google_api_key and google_cse_id described here https://cloud.google.com/docs/authentication/api-keys?visit_id=638154342880239948-3750907574&rd=1&hl=zh-cn)


## todo list
