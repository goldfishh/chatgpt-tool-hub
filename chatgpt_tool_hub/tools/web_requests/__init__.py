"""Tools for making requests to an API endpoint."""
import re
import os
import tempfile

from bs4 import BeautifulSoup
from pydantic import BaseModel
from rich.console import Console

from ...common.log import LOG
from ..summary import SummaryTool


def filter_text(html: str, use_summary=False, console: Console=None) -> str:
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

    # Remove all HTML tags and contents
    text = re.sub(r'<[^>]*>', '', str(text))

    # compress text size
    if use_summary:
        try:
            temp_file = tempfile.mkstemp()
            file_path = temp_file[1]

            with open(file_path, "w") as f:
                f.write(text + "\n")

            _summary = SummaryTool(console=console).path(file_path)
            os.remove(file_path)
        except Exception as e:
            LOG.error(f"summary {file_path} failed... error_info: {repr(e)}")
            # fake summary
            _text_list = text.split()
            if len(_text_list) >= 500:
                text = _text_list[:3000]  # english or any others
            else:
                text = text[:3000]  # chinese
    _summary = text
    return _summary.encode('utf-8').decode()


DEFAULT_HEADER = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/54.0.2840.100 Safari/537.36",
    "Accept-Encoding": "*"
}

from .wrapper import RequestsWrapper


class BaseRequestsTool(BaseModel):
    """Base class for requests tools."""

    requests_wrapper: RequestsWrapper


from .browser import BrowserTool
from .get import RequestsGetTool
from .post import RequestsPostTool


__all__ = (
    "BaseRequestsTool",
    "RequestsWrapper",

    "BrowserTool",
    "RequestsGetTool",
    "RequestsPostTool"
)
