"""Lightweight wrapper around requests library, with async support."""
from typing import Any, Dict, Optional

import aiohttp
import requests
from pydantic import BaseModel, Extra, root_validator

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.web_requests import DEFAULT_HEADER
from webdriver_manager.chrome import ChromeDriverManager


class RequestsWrapper(BaseModel):
    """Lightweight wrapper around requests library."""

    headers: Optional[Dict[str, str]] = dict()
    aiosession: Optional[aiohttp.ClientSession] = None

    browser: Any = None  # PhantomJSWebDriver or None

    proxy: Optional[str]

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that browser param exists in environment."""
        proxy = get_from_dict_or_env(
            values, 'proxy', "PROXY", ""
        )

        try:
            from selenium import webdriver

            values["browser"] = cls._build_browser_option(proxy)
        except ImportError:
            raise ImportError(
                "selenium is not installed. "
                "Please install it with `pip install selenium==2.48.0`"
            )
        return values

    @classmethod
    def _build_browser_option(self, proxy: str = ""):
        from selenium.webdriver.chrome.options import Options
        from selenium import webdriver

        options = Options()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--no-sandbox")
        browser = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=options
        )

        # todo 设置代理

        return browser

    def get(self, url: str, params: Dict[str, Any] = None, raise_for_status: bool = False, **kwargs) -> str:
        """GET the URL and return the text."""
        if self.browser:
            self.browser.get(url)
            _content = self.browser.page_source
            # todo raise_for_status?
            self.browser.close()  # 退出当前页面, 节省内存
            return _content
        else:
            self.headers.update(DEFAULT_HEADER)
            response = requests.get(url, headers=self.headers, params=params, **kwargs)
            if raise_for_status:
                try:
                    response.raise_for_status()
                except Exception as e:
                    LOG.error("RequestsWrapper.get status_code is not good: " + repr(e))

            return response.text

    def post(self, url: str, data: Dict[str, Any]) -> str:
        """POST to the URL and return the text."""
        self.headers = dict().update(DEFAULT_HEADER) if not self.headers else self.headers.update(DEFAULT_HEADER)
        return requests.post(url, data=data, headers=self.headers).text

    def patch(self, url: str, data: Dict[str, Any]) -> str:
        """PATCH the URL and return the text."""
        self.headers = dict().update(DEFAULT_HEADER) if not self.headers else self.headers.update(DEFAULT_HEADER)
        return requests.patch(url, json=data, headers=self.headers).text

    def put(self, url: str, data: Dict[str, Any]) -> str:
        """PUT the URL and return the text."""
        self.headers = dict().update(DEFAULT_HEADER) if not self.headers else self.headers.update(DEFAULT_HEADER)
        return requests.put(url, json=data, headers=self.headers).text

    def delete(self, url: str) -> str:
        """DELETE the URL and return the text."""
        self.headers = dict().update(DEFAULT_HEADER) if not self.headers else self.headers.update(DEFAULT_HEADER)
        return requests.delete(url, headers=self.headers).text

    async def _arequest(self, method: str, url: str, **kwargs: Any) -> str:
        """Make an async request."""
        self.headers = dict().update(DEFAULT_HEADER) if not self.headers else self.headers.update(DEFAULT_HEADER)
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=self.headers, **kwargs
                ) as response:
                    return await response.text()
        else:
            async with self.aiosession.request(
                method, url, headers=self.headers, **kwargs
            ) as response:
                return await response.text()

    async def aget(self, url: str) -> str:
        """GET the URL and return the text asynchronously."""
        return await self._arequest("GET", url)

    async def apost(self, url: str, data: Dict[str, Any]) -> str:
        """POST to the URL and return the text asynchronously."""
        return await self._arequest("POST", url, json=data)

    async def apatch(self, url: str, data: Dict[str, Any]) -> str:
        """PATCH the URL and return the text asynchronously."""
        return await self._arequest("PATCH", url, json=data)

    async def aput(self, url: str, data: Dict[str, Any]) -> str:
        """PUT the URL and return the text asynchronously."""
        return await self._arequest("PUT", url, json=data)

    async def adelete(self, url: str) -> str:
        """DELETE the URL and return the text asynchronously."""
        return await self._arequest("DELETE", url)
