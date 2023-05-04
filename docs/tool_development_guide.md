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

## 如何开发一个工具

> `chatgpt_tool_hub/tools/hello_tool` 展示一个自定义tool的实现例子

### 1. 克隆仓库

```bash
git clone https://github.com/goldfishh/chatgpt-tool-hub.git
cd chatgpt-tool-hub
```

### 2. 在chatgpt_tool_hub/tools新建一个Python Package `example_tool`

### 3. 在package里新建一个tool.py，用于实现tool执行逻辑

```python
from typing import Any
from rich.console import Console
from chatgpt_tool_hub.tools.base_tool import BaseTool


default_tool_name = "your-tool-name"


class ExampleTool(BaseTool):
    name = default_tool_name
    description = (
        "Introduce your tool to LLM and decide on which scenarios to use the tool."
    )

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

    def _run(self, query: str) -> str:
        return "return string"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("ExampleTool does not support async")
```

### 4. 注册工具

#### (1). __init__.py

```python
from chatgpt_tool_hub.tools.example_tool.tool import ExampleTool
```

#### (2). tool.py

```python
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
main_tool_register.register_tool(default_tool_name,
                                 lambda console, kwargs: ExampleTool(console, **kwargs),
                                 tool_input_keys=[])
```

> 如果该tool必须要申请api-key，则api-key名称需要传入tool_input_keys中，用于检测kwargs是否传入api-key

### 5. 使用工具

```json
{
  "tools": ["your-tool-name"],
  "kwargs": {
      // ...
  }
}
```

向llm提问，由llm判断是否使用该tool
