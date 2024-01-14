"""Lightweight wrapper around requests library, with async support."""
from typing import Any, Dict, Optional

import aiohttp
import requests
from pydantic import BaseModel, model_validator

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from .  import DEFAULT_HEADER


class RequestsWrapper(BaseModel):
    """Lightweight wrapper around requests library."""

    headers: Dict[str, str] = dict()
    aiosession: Optional[aiohttp.ClientSession] = None

    proxy: Optional[str]

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'
        arbitrary_types_allowed = True

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """get proxy param from environment."""
        proxy = get_from_dict_or_env(
            values, 'proxy', "PROXY", ""
        )
        values["proxy"] = proxy

        return values

    def get(self, url: str, params: Dict[str, Any] = None, raise_for_status: bool = False, **kwargs) -> str:
        """GET the URL and return the text."""
        self.headers.update(DEFAULT_HEADER)
        proxies = {
            'http': self.proxy,
            'https': self.proxy,
        }
        response = requests.get(url, headers=self.headers, params=params, proxies=proxies, **kwargs)
        if raise_for_status:
            try:
                response.raise_for_status()
            except Exception as e:
                LOG.error(f"RequestsWrapper.get status_code is not good: {repr(e)}")

        return response.text

    def post(self, url: str, data: Dict[str, Any], **kwargs) -> str:
        """POST to the URL and return the text."""
        self.headers.update(DEFAULT_HEADER)
        proxies = {
            'http': self.proxy,
            'https': self.proxy,
        }
        return requests.post(url, data=data, headers=self.headers, proxies=proxies, **kwargs).text

    def patch(self, url: str, data: Dict[str, Any]) -> str:
        """PATCH the URL and return the text."""
        self.headers = (
            self.headers.update(DEFAULT_HEADER)
            if self.headers
            else {}.update(DEFAULT_HEADER)
        )
        return requests.patch(url, json=data, headers=self.headers).text

    def put(self, url: str, data: Dict[str, Any]) -> str:
        """PUT the URL and return the text."""
        self.headers = (
            self.headers.update(DEFAULT_HEADER)
            if self.headers
            else {}.update(DEFAULT_HEADER)
        )
        return requests.put(url, json=data, headers=self.headers).text

    def delete(self, url: str) -> str:
        """DELETE the URL and return the text."""
        self.headers = (
            self.headers.update(DEFAULT_HEADER)
            if self.headers
            else {}.update(DEFAULT_HEADER)
        )
        return requests.delete(url, headers=self.headers).text

    async def _arequest(self, method: str, url: str, **kwargs: Any) -> str:
        """Make an async request."""
        self.headers.update(DEFAULT_HEADER)
        proxies = {
            'http': self.proxy,
            'https': self.proxy,
        }
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=self.headers, proxies=proxies, **kwargs
                ) as response:
                    return await response.text()
        else:
            async with self.aiosession.request(
                method, url, headers=self.headers, proxies=proxies, **kwargs
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
