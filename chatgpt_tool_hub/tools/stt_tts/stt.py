"""azure stt tool"""
import os, tempfile

import azure.cognitiveservices.speech as speechsdk

from typing import Any, Optional

from rich.console import Console
from ...models.calculate_token import count_string_tokens as get_token_num
from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ...models import build_model_params
from ..tool_register import main_tool_register
from .. import BaseTool

default_tool_name = "stt"

class STTTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        ""
    )

    api_key: Optional[str] = None
    api_region: Optional[str] = None
    speech_config: Optional[speechsdk.SpeechConfig] = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        self.api_key = get_from_dict_or_env(tool_kwargs, "stt_api_key", "STT_API_KEY")
        # api_region etc. "eastasia"
        self.api_region = get_from_dict_or_env(tool_kwargs, "stt_api_region", "STT_API_REGION")

        self.speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.api_region)
        # 语言支持列表：https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/language-support?tabs=stt
        # en-US ja-JP ko-KR yue-CN zh-CN
        self.speech_config.speech_recognition_language = get_from_dict_or_env(tool_kwargs, "stt_recognition_language", "STT_RECOGNITION_LANGUAGE", "zh-CN")

    def path(self, path: str) -> str:
        return self._run(path)

    def url(self, voice_url: str) -> str:
        try:
            import requests
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

            response = requests.get(voice_url, stream=True)
            response.raise_for_status()

            # 将文件写入临时文件
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return self._run(temp_file.name)
        except Exception as e:
            LOG.error(f"Error downloading voice file: {e}")
            return "download voice file failed"

    def microphone(self) -> str:
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
        
        print("Speak into your microphone.")
        result = speech_recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            LOG.info("[stt] microphone text={}".format(result.text))
        else:
            cancel_details = result.cancellation_details
            LOG.error("[stt] result={}, errordetails={}".format(result, cancel_details.error_details))


    def _run(self, tool_input: str) -> str:
        """run the tool"""
        if not os.path.isfile(tool_input):
            LOG.debug("[stt] voice_file_path: {tool_input}")
            return f"voice file path not exist"
        try:
            audio_config = speechsdk.AudioConfig(filename=tool_input)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
            result = speech_recognizer.recognize_once()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                LOG.info("[stt] voice file name={} text={}".format(tool_input, result.text))
            else:
                cancel_details = result.cancellation_details
                LOG.error("[stt] result={}, errordetails={}".format(result, cancel_details.error_details))
        except Exception as e:
            LOG.error(repr(e))
            return "unknown error"
        return result.text

    async def _arun(self, tool_input: str) -> str:
        """use this tool async."""
        raise NotImplementedError("stt tool not support async yet")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: STTTool(console, **kwargs), [])

if __name__ == "__main__":
    tool = STTTool()
    result = tool.microphone()
    print(result)
