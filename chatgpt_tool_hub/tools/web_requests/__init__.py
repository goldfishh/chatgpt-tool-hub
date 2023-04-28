"""Tools for making requests to an API endpoint."""
import json
import os
import tempfile
from typing import Any, Dict

from bs4 import BeautifulSoup
from pydantic import BaseModel

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools import SummaryTool


def filter_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # compress text size
    temp_file = tempfile.mkstemp()
    file_path = temp_file[1]

    with open(file_path, "w") as f:
        f.write(text + "\n")
    # todo should input console
    _summary = SummaryTool().run(f"{str(file_path)}, 0")
    try:
        os.remove(file_path)
    except Exception as e:
        LOG.debug(f"remove {file_path} failed... error_info: {repr(e)}")

    return _summary.encode('utf-8').decode()


def _parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)


DEFAULT_HEADER = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/54.0.2840.100 Safari/537.36",
    "Accept-Encoding": "*"
}

from chatgpt_tool_hub.tools.web_requests.wrapper import RequestsWrapper


class BaseRequestsTool(BaseModel):
    """Base class for requests tools."""

    requests_wrapper: RequestsWrapper


from chatgpt_tool_hub.tools.web_requests.browser import BrowserTool
from chatgpt_tool_hub.tools.web_requests.delete import RequestsDeleteTool
from chatgpt_tool_hub.tools.web_requests.get import RequestsGetTool
from chatgpt_tool_hub.tools.web_requests.patch import RequestsPatchTool
from chatgpt_tool_hub.tools.web_requests.post import RequestsPostTool
from chatgpt_tool_hub.tools.web_requests.put import RequestsPutTool


__all__ = (
    "BrowserTool",
    "BaseRequestsTool",
    "RequestsWrapper",
    "RequestsDeleteTool",
    "RequestsGetTool",
    "RequestsPatchTool",
    "RequestsPostTool",
    "RequestsPutTool"
)
