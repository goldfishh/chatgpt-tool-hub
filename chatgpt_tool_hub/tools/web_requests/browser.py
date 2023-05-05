import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Extra, root_validator
from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import filter_text
default_tool_name = "browser"


browser: Any = None  # ChromeWebDriver or None


class ChromeBrowser(BaseModel):
    """Lightweight wrapper around requests library."""

    headers: Optional[Dict[str, str]] = dict()

    proxy: Optional[str]

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.ignore
        arbitrary_types_allowed = True

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that browser param exists in environment."""
        proxy = get_from_dict_or_env(
            values, 'proxy', "PROXY", ""
        )
        values["proxy"] = proxy

        try:
            from selenium import webdriver
        except ImportError:
            raise ImportError(
                "selenium is not installed. "
                "Please install it with `pip install selenium`"
            )

        try:
            global browser
            if browser is None:
                browser = cls._build_browser_option(proxy)
        except ImportError:
            raise ImportError(
                "webdriver_manager is not installed. "
                "Please install it with `pip install webdriver_manager`"
            )

        return values

    @classmethod
    def _build_browser_option(cls, proxy: str = ""):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        options.add_argument("--headless")
        options.add_argument('blink-settings=imagesEnabled=false')
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--no-sandbox")
        options.add_argument(f"--proxy-server={proxy}")

        # 设置代理
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=options
        )

    def get(self, url: str, **kwargs) -> str:
        """GET the URL and return the text."""
        if not browser:
            return "chrome browser was not initialized"
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By

        # Network.setExtraHTTPHeaders command to the browser's DevTools.
        # This method allows setting multiple headers at once.
        # browser.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": self.headers})

        browser.get(url)

        # inspired by auto-gpt
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Get the HTML content directly from the browser's DOM
        _content = browser.execute_script("return document.body.outerHTML;")

        if len(browser.window_handles) > 2:
            browser.close()  # 退出多余页面, 节省内存

        return _content


class BrowserTool(BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = default_tool_name
    description = (
        "A Google Chrome browser. Use this when you need to get specific content from a website. "
        "Input should be a url (i.e. https://github.com/goldfishh/chatgpt-tool-hub). "
        "The output will be the text response of browser. "
    )

    browser: ChromeBrowser = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=False)

        self.browser = ChromeBrowser(**tool_kwargs)

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.browser.get(url)
            _content = filter_text(html)
            LOG.debug(f"[browser] output: {str(_content)}")
        except Exception as e:
            LOG.error(f"[browser] {str(e)}")
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        raise NotImplementedError("not support run this tool in async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: BrowserTool(console, **kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    tool = BrowserTool()
    content = tool.run("https://github.com/goldfishh/chatgpt-tool-hub")
    print(content)
