"""Chain that just formats a prompt and calls an LLM."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic import BaseModel, Extra

from chatgpt_tool_hub.chains.base import Chain
from chatgpt_tool_hub.common.input import get_colored_text
from chatgpt_tool_hub.common.schema import BaseLanguageModel, LLMResult, PromptValue
from chatgpt_tool_hub.prompts.base import BasePromptTemplate
from chatgpt_tool_hub.prompts.prompt import PromptTemplate


class LLMChain(Chain, BaseModel):
    """Chain to run queries against LLMs.

    Example:
        .. code-block:: python

            from lib.langchain_lite.chains import LLMChain, OpenAI, PromptTemplate
            prompt_template = "Tell me a {adjective} joke"
            prompt = PromptTemplate(
                input_variables=["adjective"], template=prompt_template
            )
            llm = LLMChain(llm=OpenAI(), prompt=prompt)
    """

    prompt: BasePromptTemplate
    """Prompt object to use."""
    llm: BaseLanguageModel
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return self.prompt.input_variables

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        return self.apply([inputs])[0]

    def generate(self, input_list: List[Dict[str, Any]]) -> LLMResult:
        """Generate LLM result from inputs."""
        prompts, stop = self.prep_prompts(input_list)
        return self.llm.generate_prompt(prompts, stop)

    async def agenerate(self, input_list: List[Dict[str, Any]]) -> LLMResult:
        """Generate LLM result from inputs."""
        prompts, stop = await self.aprep_prompts(input_list)
        return await self.llm.agenerate_prompt(prompts, stop)

    def prep_prompts(
        self, input_list: List[Dict[str, Any]]
    ) -> Tuple[List[PromptValue], Optional[List[str]]]:
        """Prepare prompts from inputs."""
        stop = input_list[0]["stop"] if "stop" in input_list[0] else None
        prompts = []
        for inputs in input_list:
            selected_inputs = {k: inputs[k] for k in self.prompt.input_variables}
            prompt = self.prompt.format_prompt(**selected_inputs)
            _colored_text = get_colored_text(prompt.to_string(), "green")
            _text = "Prompt after formatting:\n" + _colored_text
            self.callback_manager.on_text(_text, end="\n", verbose=self.verbose)
            if "stop" in inputs and inputs["stop"] != stop:
                raise ValueError(
                    "If `stop` is present in any inputs, should be present in all."
                )
            prompts.append(prompt)
        return prompts, stop

    async def aprep_prompts(
        self, input_list: List[Dict[str, Any]]
    ) -> Tuple[List[PromptValue], Optional[List[str]]]:
        """Prepare prompts from inputs."""
        stop = input_list[0]["stop"] if "stop" in input_list[0] else None
        prompts = []
        for inputs in input_list:
            selected_inputs = {k: inputs[k] for k in self.prompt.input_variables}
            prompt = self.prompt.format_prompt(**selected_inputs)
            _colored_text = get_colored_text(prompt.to_string(), "green")
            _text = "Prompt after formatting:\n" + _colored_text
            if self.callback_manager.is_async:
                await self.callback_manager.on_text(
                    _text, end="\n", verbose=self.verbose
                )
            else:
                self.callback_manager.on_text(_text, end="\n", verbose=self.verbose)
            if "stop" in inputs and inputs["stop"] != stop:
                raise ValueError(
                    "If `stop` is present in any inputs, should be present in all."
                )
            prompts.append(prompt)
        return prompts, stop

    def apply(self, input_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Utilize the LLM generate method for speed gains."""
        response = self.generate(input_list)
        return self.create_outputs(response)

    async def aapply(self, input_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Utilize the LLM generate method for speed gains."""
        response = await self.agenerate(input_list)
        return self.create_outputs(response)

    def create_outputs(self, response: LLMResult) -> List[Dict[str, str]]:
        """Create outputs from response."""
        return [
            # Get the text of the top generated string.
            {self.output_key: generation[0].text}
            for generation in response.generations
        ]

    async def _acall(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        return (await self.aapply([inputs]))[0]

    def predict(self, **kwargs: Any) -> str:
        """Format prompt with kwargs and pass to LLM.

        Args:
            **kwargs: Keys to pass to prompt template.

        Returns:
            Completion from LLM.

        Example:
            .. code-block:: python

                completion = llm.predict(adjective="funny")
        """
        return self(kwargs)[self.output_key]

    async def apredict(self, **kwargs: Any) -> str:
        """Format prompt with kwargs and pass to LLM.

        Args:
            **kwargs: Keys to pass to prompt template.

        Returns:
            Completion from LLM.

        Example:
            .. code-block:: python

                completion = llm.predict(adjective="funny")
        """
        return (await self.acall(kwargs))[self.output_key]

    def predict_and_parse(self, **kwargs: Any) -> Union[str, List[str], Dict[str, str]]:
        """Call predict and then parse the results."""
        result = self.predict(**kwargs)
        if self.prompt.output_parser is not None:
            return self.prompt.output_parser.parse(result)
        else:
            return result

    def apply_and_parse(
        self, input_list: List[Dict[str, Any]]
    ) -> Sequence[Union[str, List[str], Dict[str, str]]]:
        """Call apply and then parse the results."""
        result = self.apply(input_list)
        return self._parse_result(result)

    def _parse_result(
        self, result: List[Dict[str, str]]
    ) -> Sequence[Union[str, List[str], Dict[str, str]]]:
        if self.prompt.output_parser is not None:
            return [
                self.prompt.output_parser.parse(res[self.output_key]) for res in result
            ]
        else:
            return result

    async def aapply_and_parse(
        self, input_list: List[Dict[str, Any]]
    ) -> Sequence[Union[str, List[str], Dict[str, str]]]:
        """Call apply and then parse the results."""
        result = await self.aapply(input_list)
        return self._parse_result(result)

    @property
    def _chain_type(self) -> str:
        return "llm_chain"

    @classmethod
    def from_string(cls, llm: BaseLanguageModel, template: str) -> Chain:
        """Create LLMChain from LLM and template."""
        prompt_template = PromptTemplate.from_template(template)
        return cls(llm=llm, prompt=prompt_template)
