"""Lightweight wrapper around requests library, with async support."""
from typing import Any, Dict, Optional

import aiohttp
import requests
from pydantic import BaseModel, Extra, root_validator
from chatgpt_tool_hub.common.utils import get_from_dict_or_env

from chatgpt_tool_hub.tools.web_requests import DEFAULT_HEADER


class RequestsWrapper(BaseModel):
    """Lightweight wrapper around requests library."""

    headers: Optional[Dict[str, str]] = dict()
    aiosession: Optional[aiohttp.ClientSession] = None

    browser: Any  # PhantomJSWebDriver or None
    phantomjs_exec_path: Optional[str]  # download link: https://phantomjs.org/download.html

    proxy: Optional[str]

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that browser param exists in environment."""
        phantomjs_exec_path = get_from_dict_or_env(
            values, "phantomjs_exec_path", "PHANTOMJS_EXEC_PATH", ""
        )
        if not phantomjs_exec_path:
            values["browser"] = None
            return values
        proxy = get_from_dict_or_env(
            values, 'proxy', "PROXY", ""
        )
        try:
            from selenium import webdriver

            values["browser"] = cls._build_browser_option(phantomjs_exec_path, proxy)
        except ImportError:
            raise ImportError(
                "selenium is not installed. "
                "Please install it with `pip install selenium==2.48.0`"
            )


        return values

    @classmethod
    def _build_browser_option(self, exec_path: str, proxy: str = ""):
        from selenium import webdriver

        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        from selenium.webdriver.common.proxy import ProxyType

        dcap = dict(DesiredCapabilities.PHANTOMJS)

        # 设置user-agent请求头
        dcap["phantomjs.page.settings.userAgent"] = DEFAULT_HEADER.get('User-Agent', '')
        # 禁止加载图片
        dcap["phantomjs.page.settings.loadImages"] = False

        browser = webdriver.PhantomJS(desired_capabilities=dcap, executable_path=exec_path)

        # 设置代理
        # todo proxy is not working now
        if False:
            _proxy = webdriver.Proxy()
            _proxy.proxy_type = ProxyType.MANUAL
            _proxy.http_proxy = proxy
            # 将代理设置添加到webdriver.DesiredCapabilities.PHANTOMJS中
            _proxy.add_to_capabilities(webdriver.DesiredCapabilities.PHANTOMJS)

        browser.start_session(webdriver.DesiredCapabilities.PHANTOMJS)

        return browser

    def get(self, url: str, params: Dict[str, Any] = None, raise_for_status: bool = False) -> str:
        """GET the URL and return the text."""
        if self.browser:
            self.browser.get(url)
            _content = self.browser.page_source
            self.browser.close()  # 退出当前页面, 节省内存
            return _content
        else:
            self.headers.update(DEFAULT_HEADER)
            response = requests.get(url, headers=self.headers, params=params)
            if raise_for_status:
                response.raise_for_status()
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
