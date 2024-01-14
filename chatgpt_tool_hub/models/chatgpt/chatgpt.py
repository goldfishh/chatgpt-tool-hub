"""OpenAI chatgpt wrapper."""
from __future__ import annotations

import logging
import sys
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from pydantic import BaseModel, Field, model_validator
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .base import BaseChatModel
from .. import DEFAULT_MODEL_NAME
from ...common.constants import openai_default_api_base
from ...common.log import LOG
from ...common.schema import (
    AIMessage,
    BaseMessage,
    ChatGeneration,
    ChatMessage,
    ChatResult,
    HumanMessage,
    SystemMessage,
)
from ...common.utils import get_from_dict_or_env


def _create_retry_decorator(llm: ChatOpenAI) -> Callable[[Any], Any]:
    import openai

    min_seconds = 15
    max_seconds = 30
    # Wait 2^x * 1 second between each retry starting with
    # 4 seconds, then up to 10 seconds, then 10 seconds afterwards
    return retry(
        reraise=True,
        stop=stop_after_attempt(llm.max_retries),
        wait=wait_exponential(multiplier=1, min=min_seconds, max=max_seconds),
        retry=(
            retry_if_exception_type(openai.error.Timeout)
            | retry_if_exception_type(openai.error.APIError)
            | retry_if_exception_type(openai.error.APIConnectionError)
            | retry_if_exception_type(openai.error.RateLimitError)
            | retry_if_exception_type(openai.error.ServiceUnavailableError)
        ),
        before_sleep=before_sleep_log(LOG, logging.WARNING),
    )


async def acompletion_with_retry(llm: ChatOpenAI, **kwargs: Any) -> Any:
    """Use tenacity to retry the async completion call."""
    retry_decorator = _create_retry_decorator(llm)

    @retry_decorator
    async def _completion_with_retry(**kwargs: Any) -> Any:
        # Use OpenAI's async api https://github.com/openai/openai-python#async-api
        return await llm.client.acreate(**kwargs)

    return await _completion_with_retry(**kwargs)


def _convert_dict_to_message(_dict: dict) -> BaseMessage:
    role = _dict["role"]
    if role == "user":
        return HumanMessage(content=_dict["content"])
    elif role == "assistant":
        return AIMessage(content=_dict["content"])
    elif role == "system":
        return SystemMessage(content=_dict["content"])
    else:
        return ChatMessage(content=_dict["content"], role=role)


def _convert_message_to_dict(message: BaseMessage) -> dict:
    if isinstance(message, ChatMessage):
        message_dict = {"role": message.role, "content": message.content}
    elif isinstance(message, HumanMessage):
        message_dict = {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        message_dict = {"role": "assistant", "content": message.content}
    elif isinstance(message, SystemMessage):
        message_dict = {"role": "system", "content": message.content}
    else:
        raise ValueError(f"Got unknown type {message}")
    if "name" in message.additional_kwargs:
        message_dict["name"] = message.additional_kwargs["name"]
    return message_dict


def _create_chat_result(response: Mapping[str, Any]) -> ChatResult:
    generations = []
    for res in response["choices"]:
        message = _convert_dict_to_message(res["message"])
        gen = ChatGeneration(message=message)
        generations.append(gen)
    llm_output = {"token_usage": response["usage"]}
    return ChatResult(generations=generations, llm_output=llm_output)


class ChatOpenAI(BaseChatModel, BaseModel):
    f"""Wrapper around OpenAI Chat large language models.

    To use, you should have the ``openai`` python package installed, and the
    environment variable ``LLM_API_KEY`` set with your API key.

    Any parameters that are valid to be passed to the openai.create call can be passed
    in, even if not explicitly saved on this class.

    Example:
        .. code-block:: python

            from lib.chat_models import ChatOpenAI
            openai = ChatOpenAI(llm_model_name={DEFAULT_MODEL_NAME})
    """

    client: Any  #: :meta private:
    """Model name to use."""
    llm_model_name: str = Field(default=DEFAULT_MODEL_NAME)
    """Holds any model parameters valid for `create` call not explicitly specified."""
    llm_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """llm api base url"""
    llm_api_base_url: Optional[str]
    """a key to call llm api server"""
    llm_api_key: Optional[str]
    """Timeout in seconds for the OpenAPI request."""
    request_timeout: int = Field(default=60)
    """Maximum number of retries to make when generating."""
    max_retries: int = Field(default=6)
    """Whether to stream the results or not."""
    streaming: bool = Field(default=False)
    """Number of chat completions to generate for each prompt."""
    n: int = Field(default=1)
    """Maximum number of tokens to generate."""
    max_tokens: Optional[int] = Field(default=4096)
    """the proxy to use"""
    proxy: Optional[str] = Field(default="")
    """"""

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'

    # 用于跟踪是否已经执行过验证
    _validation_executed = False

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        
        all_required_field_names = {field for field in cls.model_fields.keys()}

        extra = values.get("llm_model_kwargs", {})
        values_copy = values.copy()  # 创建 values 的副本

        for field_name in list(values_copy):
            if field_name not in all_required_field_names:
                if field_name in extra:
                    raise ValueError(f"Found {field_name} supplied twice.")
                extra[field_name] = values_copy.pop(field_name)

        values["llm_model_kwargs"] = extra


        _llm_api_key = get_from_dict_or_env(
            values, "llm_api_key", "LLM_API_KEY"
        )
        _llm_api_base_url = get_from_dict_or_env(
            values, "llm_api_base_url", "LLM_API_BASE_URL",
            openai_default_api_base)
        _proxy = get_from_dict_or_env(
            values, "proxy", "PROXY", ""
        )
        _deployment_id = get_from_dict_or_env(
            values, "deployment_id", "DEPLOYMENT_ID", ""
        )
        try:
            import openai

            if openai.proxy != _proxy:
                if _proxy:
                    openai.proxy = _proxy
                    values["proxy"] = _proxy
                    if not cls._validation_executed:
                        LOG.info(f"success use proxy: {_proxy}")
                elif not cls._validation_executed:
                    LOG.info("proxy no find, directly request to chatgpt instead")

            if openai.api_base != _llm_api_base_url:
                openai.api_base = _llm_api_base_url
                values["llm_api_base_url"] = _llm_api_base_url
                if not cls._validation_executed:
                    LOG.info(f"success use customized api base url: {_llm_api_base_url}")

            if openai.api_key != _llm_api_key:
                openai.api_key = _llm_api_key
                values["llm_api_key"] = _llm_api_key
                if not cls._validation_executed:
                    LOG.debug(f"success use llm api key: {_llm_api_key}")

            if _deployment_id:
                openai.api_type = "azure"
                openai.api_version = "2023-03-15-preview"

        except ImportError:
            raise ValueError(
                "Could not import openai python package. "
                "Please it install it with `pip install openai`."
            )

        try:
            values["client"] = openai.ChatCompletion
        except AttributeError:
            raise ValueError(
                "`openai` has no `ChatCompletion` attribute, this is likely "
                "due to an old version of the openai package. Try upgrading it "
                "with `pip install --upgrade openai`."
            )
        if values.get("n") and values["n"] < 1:
            raise ValueError("n must be at least 1.")
        if values.get("n") and values["n"] > 1 and values.get("streaming"):
            raise ValueError("n must be 1 when streaming.")
        
        cls._validation_executed = True
        return values

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling OpenAI API."""
        return {
            "model": self.llm_model_name,
            "request_timeout": self.request_timeout,
            "max_tokens": self.max_tokens,
            "stream": self.streaming,
            "n": self.n,
            **self.llm_model_kwargs,
        }

    def _create_retry_decorator(self) -> Callable[[Any], Any]:
        import openai

        min_seconds = 15
        max_seconds = 30
        # Wait 2^x * 1 second between each retry starting with
        # 4 seconds, then up to 10 seconds, then 10 seconds afterwards
        return retry(
            reraise=True,
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=min_seconds, max=max_seconds),
            # todo RateLimitError
            retry=(
                retry_if_exception_type(openai.error.Timeout)
                | retry_if_exception_type(openai.error.APIError)
                | retry_if_exception_type(openai.error.APIConnectionError)
                | retry_if_exception_type(openai.error.RateLimitError)
                | retry_if_exception_type(openai.error.ServiceUnavailableError)
            ),
            before_sleep=before_sleep_log(LOG, logging.WARNING),
        )

    def completion_with_retry(self, **kwargs: Any) -> Any:
        """Use tenacity to retry the completion call."""
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def _completion_with_retry(**kwargs: Any) -> Any:
            return self.client.create(**kwargs)

        return _completion_with_retry(**kwargs)

    def _combine_llm_outputs(self, llm_outputs: List[Optional[dict]]) -> dict:
        overall_token_usage: dict = {}
        for output in llm_outputs:
            if output is None:
                # Happens in streaming
                continue
            token_usage = output["token_usage"]
            for k, v in token_usage.items():
                if k in overall_token_usage:
                    overall_token_usage[k] += v
                else:
                    overall_token_usage[k] = v
        return {"token_usage": overall_token_usage}

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        message_dicts, params = self._create_message_dicts(messages, stop)

        if self.streaming:
            inner_completion = ""
            role = "assistant"
            params["stream"] = True
            for stream_resp in self.completion_with_retry(
                messages=message_dicts, **params
            ):
                role = stream_resp["choices"][0]["delta"].get("role", role)
                token = stream_resp["choices"][0]["delta"].get("content", "")
                inner_completion += token
                self.callback_manager.on_llm_new_token(
                    token,
                    verbose=self.verbose,
                )
            message = _convert_dict_to_message(
                {"content": inner_completion, "role": role}
            )
            return ChatResult(generations=[ChatGeneration(message=message)])

        response = self.completion_with_retry(messages=message_dicts, **params)
        return _create_chat_result(response)

    def _create_message_dicts(
        self, messages: List[BaseMessage], stop: Optional[List[str]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        params: Dict[str, Any] = {**{"model": self.llm_model_name}, **self._default_params}
        if stop is not None:
            if "stop" in params:
                raise ValueError("`stop` found in both the input and default params.")
            params["stop"] = stop
        message_dicts = [_convert_message_to_dict(m) for m in messages]
        return message_dicts, params

    async def _agenerate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        message_dicts, params = self._create_message_dicts(messages, stop)
        if self.streaming:
            inner_completion = ""
            role = "assistant"
            params["stream"] = True
            async for stream_resp in await acompletion_with_retry(
                self, messages=message_dicts, **params
            ):
                role = stream_resp["choices"][0]["delta"].get("role", role)
                token = stream_resp["choices"][0]["delta"].get("content", "")
                inner_completion += token
                if self.callback_manager.is_async:
                    await self.callback_manager.on_llm_new_token(
                        token,
                        verbose=self.verbose,
                    )
                else:
                    self.callback_manager.on_llm_new_token(
                        token,
                        verbose=self.verbose,
                    )
            message = _convert_dict_to_message(
                {"content": inner_completion, "role": role}
            )
            return ChatResult(generations=[ChatGeneration(message=message)])
        else:
            response = await acompletion_with_retry(
                self, messages=message_dicts, **params
            )
            return _create_chat_result(response)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {**{"llm_model_name": self.llm_model_name}, **self._default_params}

    def get_num_tokens(self, text: str) -> int:
        """Calculate num tokens with tiktoken package."""
        # tiktoken NOT supported for Python 3.8 or below
        if sys.version_info[1] <= 8:
            return super().get_num_tokens(text)
        try:
            import tiktoken
        except ImportError:
            raise ValueError(
                "Could not import tiktoken python package. "
                "This is needed in order to calculate get_num_tokens. "
                "Please it install it with `pip install tiktoken`."
            )
        # create a gpt-3.5-Turbo encoder instance
        enc = tiktoken.encoding_for_model(self.llm_model_name)

        # encode the text using the gpt-3.5-Turbo encoder
        tokenized_text = enc.encode(text)

        # calculate the number of tokens in the encoded text
        return len(tokenized_text)

    def get_num_tokens_from_messages(
        self, messages: List[BaseMessage], model: str = DEFAULT_MODEL_NAME
    ) -> int:
        """Calculate num tokens for gpt-3.5-turbo with tiktoken package."""
        try:
            import tiktoken
        except ImportError:
            raise ValueError(
                "Could not import tiktoken python package. "
                "This is needed in order to calculate get_num_tokens. "
                "Please it install it with `pip install tiktoken`."
            )

        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        if not model.startswith("gpt-3.5-turbo"):
            raise NotImplementedError(
                f"get_num_tokens_from_messages() is not presently implemented "
                f"for model {model}."
                "See https://github.com/openai/openai-python/blob/main/chatml.md for "
                "information on how messages are converted to tokens."
            )
        num_tokens = 0
        messages_dict = [_convert_message_to_dict(m) for m in messages]
        for message in messages_dict:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
