"""Chain that makes API calls and summarizes the responses to answer a question."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator
from rich.console import Console

from chatgpt_tool_hub.chains.api.prompt import API_RESPONSE_PROMPT, API_URL_PROMPT
from chatgpt_tool_hub.chains.base import Chain
from chatgpt_tool_hub.chains.llm import LLMChain
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.schema import BaseLanguageModel
from chatgpt_tool_hub.prompts import BasePromptTemplate
from chatgpt_tool_hub.tools.web_requests import RequestsWrapper


class APIChain(Chain, BaseModel):
    """Chain that makes API calls and summarizes the responses to answer a question."""

    api_request_chain: LLMChain
    api_answer_chain: LLMChain
    requests_wrapper: RequestsWrapper = Field(exclude=True)
    api_docs: str
    console: Console = None
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:

    @property
    def input_keys(self) -> List[str]:
        """Expect input key.

        :meta private:
        """
        return [self.question_key]

    @property
    def output_keys(self) -> List[str]:
        """Expect output key.

        :meta private:
        """
        return [self.output_key]

    @root_validator(pre=True)
    def validate_api_request_prompt(cls, values: Dict) -> Dict:
        """Check that api request prompt expects the right variables."""
        input_vars = values["api_request_chain"].prompt.input_variables
        expected_vars = {"question", "api_docs"}
        if set(input_vars) != expected_vars:
            raise ValueError(
                f"Input variables should be {expected_vars}, got {input_vars}"
            )
        return values

    @root_validator(pre=True)
    def validate_api_answer_prompt(cls, values: Dict) -> Dict:
        """Check that api answer prompt expects the right variables."""
        input_vars = values["api_answer_chain"].prompt.input_variables
        expected_vars = {"question", "api_docs", "api_url", "api_response"}
        if set(input_vars) != expected_vars:
            raise ValueError(
                f"Input variables should be {expected_vars}, got {input_vars}"
            )
        return values

    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        question = inputs[self.question_key]
        api_url = self.api_request_chain.predict(
            question=question, api_docs=self.api_docs
        )
        LOG.debug(f"[API] generate url: {str(api_url)}")
        self.callback_manager.on_text(
            api_url, color="green", end="\n", verbose=self.verbose
        )
        api_response = self.requests_wrapper.get(api_url)
        LOG.debug(f"[API] response: {str(api_response)}")
        self.callback_manager.on_text(
            api_response, color="yellow", end="\n", verbose=self.verbose
        )
        # api_docs chunking
        api_docs = "Here represents the API documentation that you previously used to generate API url."

        answer = self.api_answer_chain.predict(
            question=question,
            api_docs=api_docs,
            api_url=api_url,
            api_response=api_response,
        )
        return {self.output_key: answer}

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        api_docs: str,
        console: Console = Console(),
        headers: Optional[dict] = None,
        api_url_prompt: BasePromptTemplate = API_URL_PROMPT,
        api_response_prompt: BasePromptTemplate = API_RESPONSE_PROMPT,
        **kwargs: Any,
    ) -> APIChain:
        """Load chain from just an LLM and the api docs."""
        if headers is None:
            headers = {}
        get_request_chain = LLMChain(llm=llm, prompt=api_url_prompt)
        requests_wrapper = RequestsWrapper(headers=headers)
        get_answer_chain = LLMChain(llm=llm, prompt=api_response_prompt)
        return cls(
            api_request_chain=get_request_chain,
            api_answer_chain=get_answer_chain,
            console=console,
            requests_wrapper=requests_wrapper,
            api_docs=api_docs,
            **kwargs,
        )

    @property
    def _chain_type(self) -> str:
        return "api_chain"
