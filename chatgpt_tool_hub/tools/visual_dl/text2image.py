from typing import Any

import torch
from PIL import Image
from rich.console import Console
from transformers import BlipProcessor, BlipForConditionalGeneration

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool

default_tool_name = "image2text"


class ImageCaptionTool(BaseTool):
    """Tool for get image captioning from image_path or url"""

    name = default_tool_name
    description = (
        "useful when you want to know what is inside the photo. receives image_path as input."
        "The input to this tool should be a string, representing the image_path, you MUST use absolute path."
    )
    device: str = "cpu"
    torch_dtype: torch.dtype = torch.float32
    processor: Any = None
    model: Any = None

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)
        self.device = get_from_dict_or_env(tool_kwargs, "cuda_device", "CUDA_DEVICE", "cpu")
        self.torch_dtype = torch.float16 if 'cuda' in self.device else torch.float32
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base", torch_dtype=self.torch_dtype).to(self.device)

    def _run(self, image_path: str) -> str:
        # todo support image URL
        inputs = self.processor(Image.open(image_path), return_tensors="pt").to(self.device, self.torch_dtype)
        out = self.model.generate(**inputs)
        captions = self.processor.decode(out[0], skip_special_tokens=True)
        LOG.info(f"[image2text]: Processed ImageCaptioning, Input Image: {image_path}, Output Text: {captions}")
        return captions

    def _arun(self, query: str) -> str:
        """Use the ImageCaptioningTool asynchronously."""
        raise NotImplementedError("ImageCaptioningTool does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: ImageCaptionTool(console, **kwargs), [])


if __name__ == "__main__":
    tool = ImageCaptionTool()
    content = tool.run("/Users/goldfish/PycharmProjects/chatgpt-tool-hub/chatgpt_tool_hub/demo2.jpg")
    print(content)
