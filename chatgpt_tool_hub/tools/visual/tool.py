import time
from http import HTTPStatus
from typing import Any, Dict, Optional

from pydantic import BaseModel, model_validator
from rich.console import Console

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from .. import BaseTool
from ..tool_register import main_tool_register


default_tool_name = "visual"


class DashScopeWrapper(BaseModel):
    """Wrapper for modelscope."""
    caption_client: Any
    caption_model: str = 'qwen-vl-plus'
    caption_api_key: Optional[str]

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate python package exists in environment."""
        try:
            import dashscope
            values["caption_client"] = dashscope.MultiModalConversation
        except ImportError:
            raise ImportError(
                "dashscope are not installed. "
                "Please install them with `pip install dashscope`"
            )
        
        values["caption_api_key"] = get_from_dict_or_env(values, "caption_api_key", "CAPTION_API_KEY")

        return values

    def path(self, file_path: str) -> str:
        """Sample of use local file.
            linux&mac file schema: file:///home/images/test.png
            windows file schema: file://D:/images/abc.png
        """
        local_file_path = f'file://{file_path}'
        messages = [{
            'role': 'system',
            'content': [{'text': 'You are a helpful assistant.'}]
        }, {
            'role': 'user',
            'content': [
                {'image': local_file_path},
                {'text': '图片里有什么东西?'},
            ]
        }]
        response = self.caption_client.call(model='qwen-vl-plus', 
                                            messages=messages,
                                            api_key=self.caption_api_key)
        # The response status_code is HTTPStatus.OK indicate success,
        # otherwise indicate request is failed, you can get error code
        # and message from code and message.
        if response.status_code == HTTPStatus.OK:
            LOG.debug(f"[caption] {self.caption_model} response: {response}")
            LOG.info(f"[caption] output: {response.output.choices[0].message.content[0]['text']}")
            return response.output.choices[0].message.content[0]['text']
        else:
            time.sleep(1)
            LOG.error(f"[caption] code: {response.code}, message: {response.message}")
            return "unknown error"

    def run(self, image_url: str) -> str:
        """Simple single round multimodal conversation call."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": image_url.strip()},
                    {"text": "这是什么?"}
                ]
            }
        ]
        response = self.caption_client.call(model=self.caption_model,
                                            messages=messages,
                                            api_key=self.caption_api_key)
        # The response status_code is HTTPStatus.OK indicate success,
        # otherwise indicate request is failed, you can get error code
        # and message from code and message.
        if response.status_code == HTTPStatus.OK:
            LOG.debug(f"[caption] {self.caption_model} response: {response}")
            LOG.info(f"[caption] output: {response.output.choices[0].message.content[0]['text']}")
            return response.output.choices[0].message.content[0]['text']
        else:
            time.sleep(1)
            LOG.error(f"[caption] code: {response.code}, message: {response.message}")
            return "unknown error"


class ImageCaptionTool(BaseTool):
    """Tool for get image captioning from image_path or url"""

    name: str = default_tool_name
    description: str = (
        "useful when you want to know what is inside the photo. receives image_path as input."
        "The input to this tool should be a string, representing the image_path, you MUST use absolute path."
    )
    wrapper: DashScopeWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)
        self.wrapper = DashScopeWrapper(**tool_kwargs)

    def path(self, path: str) -> str:
        return self.wrapper.path(path)

    def _run(self, image_url: str) -> str:
        # todo support image URL
        return self.wrapper.run(image_url)

    def _arun(self, query: str) -> str:
        """Use the ImageCaptioningTool asynchronously."""
        raise NotImplementedError("ImageCaptioningTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: ImageCaptionTool(console, **kwargs), [])


if __name__ == "__main__":
    tool = ImageCaptionTool()
    content = tool.run("https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg")
    print(content)
