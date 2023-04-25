from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic import BaseModel, root_validator
from rich.console import Console
from rich.panel import Panel

from chatgpt_tool_hub.chains.base import Chain
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.input import get_color_mapping
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.schema import BotAction, BotFinish
from chatgpt_tool_hub.engine import Bot
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.tool import InvalidTool


class ToolEngine(Chain, BaseModel):
    """Consists of an bot using tools."""

    bot: Bot
    tools: Sequence[BaseTool]
    return_intermediate_steps: bool = False
    max_iterations: Optional[int] = 10
    early_stopping_method: str = "force"

    console: Console = None

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @classmethod
    def from_bot_and_tools(
        cls,
        bot: Bot,
        tools: Sequence[BaseTool],
        console: Console = Console(),
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Create from bot and tools."""
        return cls(
            bot=bot, tools=tools, console=console, callback_manager=callback_manager, **kwargs
        )

    @root_validator(allow_reuse=True)
    def validate_tools(cls, values: Dict) -> Dict:
        """Validate that tools are compatible with bot."""
        bot = values["bot"]
        tools = values["tools"]
        if bot.allowed_tools is not None and set(bot.allowed_tools) != {
            tool.name for tool in tools
        }:
            raise ValueError(
                f"Allowed tools ({bot.allowed_tools}) different than "
                f"provided tools ({[tool.name for tool in tools]})"
            )
        return values

    def save(self, file_path: Union[Path, str]) -> None:
        """Raise error - saving not supported for Bot Executors."""
        raise ValueError(
            "Saving not supported for bot executors. "
            "If you are trying to save the bot, please use the "
            "`.save_bot(...)`"
        )

    def save_bot(self, file_path: Union[Path, str]) -> None:
        """Save the underlying bot."""
        return self.bot.save(file_path)

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        return self.bot.input_keys

    @property
    def output_keys(self) -> List[str]:
        """Return the singular output key.

        :meta private:
        """
        if self.return_intermediate_steps:
            return self.bot.return_values + ["intermediate_steps"]
        else:
            return self.bot.return_values

    def _should_continue(self, iterations: int) -> bool:
        if self.max_iterations is None:
            return True
        else:
            return iterations < self.max_iterations

    def _return(self, output: BotFinish, intermediate_steps: list) -> Dict[str, Any]:
        self.callback_manager.on_bot_finish(
            output, color="green", verbose=self.verbose
        )
        final_output = output.return_values
        if self.return_intermediate_steps:
            final_output["intermediate_steps"] = intermediate_steps
        return final_output

    def _take_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[BotAction, str]],
    ) -> Union[BotFinish, Tuple[BotAction, str]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the bot makes and acts on choices.
        """
        # Call the LLM to see what to do.
        output = self.bot.plan(intermediate_steps, **inputs)
        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, BotFinish):
            return output

        self.callback_manager.on_bot_action(
            output, verbose=self.verbose, color="green"
        )
        # Otherwise we lookup the tool
        if output.tool in name_to_tool_map:
            self.console.print(Panel(f"{output.tool_input}",
                                     title=f"我将给工具 [bright_magenta]{output.tool}[/] 发送如下信息",
                                     highlight=True))
            
            LOG.info(f"我将给工具发送如下信息: \n{output.tool_input}")
            tool = name_to_tool_map[output.tool]
            return_direct = tool.return_direct
            # color = color_mapping[output.tool]
            llm_prefix = "" if return_direct else self.bot.llm_prefix
            # We then call the tool on the tool input to get an observation
            observation = tool.run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                llm_prefix=llm_prefix,
                observation_prefix=self.bot.observation_prefix,
            )
        else:
            self.console.print(f"× 该工具 [bright_magenta]{output.tool}[/] 无效")
            
            LOG.info(f"该工具 {output.tool} 无效")
            observation = InvalidTool().run(
                output.tool,
                verbose=self.verbose,
                color=None,
                llm_prefix="",
                observation_prefix=self.bot.observation_prefix,
            )

        self.console.print(Panel(observation + "\n",
                                 title=f"工具 [bright_magenta]{output.tool}[/] 返回内容",
                                 highlight=True, style='dim'))
        
        LOG.info(f"工具 {output.tool} 返回内容: {observation}")
        return output, observation

    def _call(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        """Run text through and get bot response."""
        # Do any preparation necessary when receiving a new input.
        self.bot.prepare_for_new_call()
        # Construct a mapping of tool name to tool for easy lookup
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # We construct a mapping from each tool to a color, used for logging.
        color_mapping = get_color_mapping(
            [tool.name for tool in self.tools], excluded_colors=["green"]
        )
        intermediate_steps: List[Tuple[BotAction, str]] = []
        # Let's start tracking the iterations the bot has gone through
        iterations = 0
        # We now enter the bot loop (until it returns something).
        while self._should_continue(iterations):
            # LOG.debug("CoT 迭代次数: {}\n".format(str(iterations+1)))
            next_step_output = self._take_next_step(
                name_to_tool_map,
                color_mapping,
                inputs, intermediate_steps
            )
            if isinstance(next_step_output, BotFinish):
                return self._return(next_step_output, intermediate_steps)

            # todo test below
            try:
                action, observation = next_step_output
                LOG.info(f"我从[{action.tool}]中获得了一些信息：\n{repr(observation.strip())}")
            except Exception as e:
                LOG.debug(f"parsing next_step_output error: {repr(e)}")

            intermediate_steps.append(next_step_output)
            # See if tool should return directly
            tool_return = self._get_tool_return(next_step_output)
            if tool_return is not None:
                return self._return(tool_return, intermediate_steps)
            iterations += 1
        # 超出迭代次数
        output = self.bot.return_stopped_response(
            self.early_stopping_method, intermediate_steps, self.max_iterations, **inputs
        )
        return self._return(output, intermediate_steps)

    def _get_tool_return(
        self, next_step_output: Tuple[BotAction, str]
    ) -> Optional[BotFinish]:
        """Check if the tool is a returning tool."""
        bot_action, observation = next_step_output
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # Invalid tools won't be in the map, so we return False.
        if (
            bot_action.tool in name_to_tool_map
            and name_to_tool_map[bot_action.tool].return_direct
        ):
            return BotFinish(
                {self.bot.return_values[0]: observation},
                "",
            )
        return None

    async def _acall(self, inputs: Dict[str, str]) -> Dict[str, str]:
        """Run text through and get bot response."""
        # Do any preparation necessary when receiving a new input.
        self.bot.prepare_for_new_call()
        # Construct a mapping of tool name to tool for easy lookup
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # We construct a mapping from each tool to a color, used for logging.
        color_mapping = get_color_mapping(
            [tool.name for tool in self.tools], excluded_colors=["green"]
        )
        intermediate_steps: List[Tuple[BotAction, str]] = []
        # Let's start tracking the iterations the bot has gone through
        iterations = 0
        # We now enter the bot loop (until it returns something).
        while self._should_continue(iterations):
            next_step_output = await self._atake_next_step(
                name_to_tool_map, color_mapping, inputs, intermediate_steps
            )
            if isinstance(next_step_output, BotFinish):
                return await self._areturn(next_step_output, intermediate_steps)

            intermediate_steps.append(next_step_output)
            # See if tool should return directly
            tool_return = self._get_tool_return(next_step_output)
            if tool_return is not None:
                return await self._areturn(tool_return, intermediate_steps)

            iterations += 1
        output = self.bot.return_stopped_response(
            self.early_stopping_method, intermediate_steps, self.max_iterations, **inputs
        )
        return await self._areturn(output, intermediate_steps)

    async def _atake_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[BotAction, str]],
    ) -> Union[BotFinish, Tuple[BotAction, str]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the bot makes and acts on choices.
        """
        # Call the LLM to see what to do.
        output = await self.bot.aplan(intermediate_steps, **inputs)
        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, BotFinish):
            return output
        if self.callback_manager.is_async:
            await self.callback_manager.on_bot_action(
                output, verbose=self.verbose, color="green"
            )
        else:
            self.callback_manager.on_bot_action(
                output, verbose=self.verbose, color="green"
            )

        # Otherwise we lookup the tool
        if output.tool in name_to_tool_map:
            tool = name_to_tool_map[output.tool]
            return_direct = tool.return_direct
            color = color_mapping[output.tool]
            llm_prefix = "" if return_direct else self.bot.llm_prefix
            # We then call the tool on the tool input to get an observation
            observation = await tool.arun(
                output.tool_input,
                verbose=self.verbose,
                color=color,
                llm_prefix=llm_prefix,
                observation_prefix=self.bot.observation_prefix,
            )
        else:
            observation = await InvalidTool().arun(
                output.tool,
                verbose=self.verbose,
                color=None,
                llm_prefix="",
                observation_prefix=self.bot.observation_prefix,
            )
            return_direct = False
        return output, observation

    async def _areturn(
        self, output: BotFinish, intermediate_steps: list
    ) -> Dict[str, Any]:
        if self.callback_manager.is_async:
            await self.callback_manager.on_bot_finish(
                output, color="green", verbose=self.verbose
            )
        else:
            self.callback_manager.on_bot_finish(
                output, color="green", verbose=self.verbose
            )
        final_output = output.return_values
        if self.return_intermediate_steps:
            final_output["intermediate_steps"] = intermediate_steps
        return final_output

    def get_tool_list(self) -> List[str]:
        _tool_list = []
        for tool in self.tools:
            _tool_list.extend(tool.get_tool_list())
        return _tool_list
