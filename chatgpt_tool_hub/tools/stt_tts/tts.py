"""azure tts tool"""
import os, tempfile

import azure.cognitiveservices.speech as speechsdk
from langid import classify

from typing import Any, Optional

from rich.console import Console
from ...models.calculate_token import count_string_tokens as get_token_num
from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ...models import build_model_params
from ..tool_register import main_tool_register
from .. import BaseTool

default_tool_name = "tts"

class TTSTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        ""
    )

    api_key: Optional[str] = None
    api_region: Optional[str] = None
    speech_config: Optional[speechsdk.SpeechConfig] = None
    tts_auto_detect: Optional[bool] = None
    default_zh_speech_id: str = "zh-CN-XiaozhenNeural"
    default_speech_id: dict = {
        "speech_synthesis_zh": "zh-CN-XiaozhenNeural",
        "speech_synthesis_en": "en-US-JacobNeural",
        "speech_synthesis_ja": "ja-JP-AoiNeural",
        "speech_synthesis_ko": "ko-KR-SoonBokNeural",
        "speech_synthesis_de": "de-DE-LouisaNeural",
        "speech_synthesis_fr": "fr-FR-BrigitteNeural",
        "speech_synthesis_es": "es-ES-LaiaNeural",
    }

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        self.api_key = get_from_dict_or_env(tool_kwargs, "tts_api_key", "TTS_API_KEY")
        # api_region etc. "eastasia"
        self.api_region = get_from_dict_or_env(tool_kwargs, "tts_api_region", "TTS_API_REGION")
        
        self.tts_auto_detect = get_from_dict_or_env(tool_kwargs, "tts_auto_detect", "TTS_AUTO_DETECT", True)
        
        self.speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.api_region)
        # https://speech.microsoft.com/portal/voicegallery
        self.speech_config.speech_synthesis_voice_name = get_from_dict_or_env(tool_kwargs, "tts_speech_id", "TTS_SPEECH_ID", self.default_zh_speech_id)

    def _classify_language(self, text):
        if self.tts_auto_detect:
            lang = classify(text)[0]
            key = "speech_synthesis_" + lang
            if self.speech_config.speech_synthesis_voice_name and lang == self.speech_config.speech_synthesis_voice_name[:2]:
                # use the init one
                return
            if key in self.default_speech_id:
                LOG.info("[tts] tts auto detect language={}, voice={}".format(lang, self.config[key]))
                self.speech_config.speech_synthesis_voice_name = self.default_speech_id[key]
            else:
                self.speech_config.speech_synthesis_voice_name = self.default_speech_id["speech_synthesis_zh"]

    def speaker(self, text: str) -> str:
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            LOG.info("[tts] text={}".format(text))
        else:
            cancel_details = result.cancellation_details
            LOG.error("[tts] error, result={}, errordetails={}".format(result, cancel_details.error_details))

    def _run(self, text: str) -> str:
        """run the tool"""
        self._classify_language(text)

        # Avoid the same filename under multithreading
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        audio_config = speechsdk.AudioConfig(filename=temp_file.name)
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = speech_synthesizer.speak_text(text)
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            LOG.info("[tts] text={} voice file name={}".format(text, temp_file.name))
        else:
            cancel_details = result.cancellation_details
            LOG.error("[tts] error, result={}, errordetails={}".format(result, cancel_details.error_details))
        return temp_file.name

    async def _arun(self, tool_input: str) -> str:
        """use this tool async."""
        raise NotImplementedError("tts tool not support async yet")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: TTSTool(console, **kwargs), [])

if __name__ == "__main__":
    tool = TTSTool()
    result = tool.speaker()
    print(result)
