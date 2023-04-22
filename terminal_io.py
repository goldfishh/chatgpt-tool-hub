import argparse
import json
import logging
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import input_dialog, clear
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from chatgpt_tool_hub.apps import AppFactory, App
from chatgpt_tool_hub.common.calculate_token import count_message_tokens
from chatgpt_tool_hub.common.constants import LOGGING_FMT, LOGGING_DATEFMT
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register

logging.basicConfig(filename=f'{os.getcwd()}/llmos.log', format=LOGGING_FMT,
                    datefmt=LOGGING_DATEFMT, level=logging.INFO)

LOG = logging.getLogger("llmos")

console = Console()

style = Style.from_dict({
    "prompt": "ansigreen",  # 将提示符设置为绿色
})

who = "user"

tools_with_api_key = {
    "bing-search": ["bing_subscription_key"],
    "google-search": ["google_api_key", "google_cse_id"],
    "searxng-search": ["searx_search_host"],
    "morning-news": ["morning_news_api_key"],
    "news-api": ["news_api_key"],
    "wolfram-alpha": ["wolfram_alpha_appid"],
}

# todo consider higher tree
subtool_parent = {
    "morning-news": "news",
    "news-api": "news"
}


class ChatMode:
    debug_mode = False
    raw_mode = False
    multi_line_mode = False

    @classmethod
    def toggle_debug_mode(cls):
        cls.debug_mode = not cls.debug_mode
        console.print(
            f"[dim]Debug mode {'enabled' if cls.debug_mode else 'disabled'}")

    @classmethod
    def toggle_raw_mode(cls):
        cls.raw_mode = not cls.raw_mode
        console.print(
            f"[dim]Raw mode {'enabled' if cls.raw_mode else 'disabled'}, use `/last` to display the last answer.")

    @classmethod
    def toggle_multi_line_mode(cls):
        cls.multi_line_mode = not cls.multi_line_mode
        if cls.multi_line_mode:
            console.print(
                f"[dim]Multi-line mode enabled, press [[bright_magenta]Esc[/]] + [[bright_magenta]ENTER[/]] to submit.")
        else:
            console.print(f"[dim]Multi-line mode disabled.")


def read_json() -> dict:
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    tool_config = {"tools": [], "kwargs": {}}
    if not os.path.exists(config_path):
        return tool_config
    else:
        with open(config_path, "r") as f:
            tool_config = json.load(f)
    # llmos should not log
    tool_config["kwargs"]["nolog"] = True
    return tool_config


init_messages = [{"role": "system", "content": "You are a helpful assistant."}]

config = read_json()

class LLMOS:
    def __init__(self, api_key: str, timeout: int):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

        self.app = AppFactory().create_app(tools_list=config["tools"], **config["kwargs"])

        self.model = 'gpt-3.5-turbo'
        self.tokens_limit = 4096
        self.total_tokens_spent = 0
        self.current_tokens = count_message_tokens(self.messages)

        self.api_key = api_key
        self.timeout = timeout

    @property
    def get_app(self) -> App:
        """Will be whatever keys the prompt expects."""
        return self.app

    def handle(self, message: str):
        try:
            self.messages.append({"role": "user", "content": message})

            response = self.send_request(message)

            if response is None:
                self.messages.pop()
                return

            if response is not None:
                LOG.info(f"LLM-OS: {response}")
                _message = {"role": "assistant", "content": f"{response}"}
                print_message(_message)
                self.messages.append(_message)
                self.current_tokens = count_message_tokens(self.messages)
                self.total_tokens_spent += self.current_tokens

        except Exception as e:
            console.print(
                f"[red]Error: {str(e)}. Check LOG for more information")
            LOG.exception(e)
            self.save_chat_history(
                f'{sys.path[0]}/chat_history_backup_{datetime.now().strftime("%Y-%m-%d_%H,%M,%S")}.json')
            raise EOFError

        return response

    def send_request(self, message: str):
        try:
            with console.status("[bold cyan]LLM-OS 分析中...\n", spinner="earth"):
                response = self.app.ask(message, chat_history=self.messages)

            return response
        except KeyboardInterrupt:
            console.print("[bold cyan]主动中断.")
            raise
        except Exception as e:
            console.print(f"[red]错误: {str(e)}")
            LOG.exception(e)
            return None

    def save_chat_history(self, filename):
        with open(f"{filename}", 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)
        console.print(
            f"[dim]Chat history saved to: [bright_magenta]{filename}", highlight=False)

    def get_credit_usage(self):
        url = 'https://api.openai.com/dashboard/billing/credit_grants'
        try:
            response = requests.get(url, headers=self.headers)
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error: {str(e)}")
            LOG.exception(e)
            return None
        except Exception as e:
            console.print(
                f"[red]Error: {str(e)}. Check LOG for more information")
            LOG.exception(e)
            self.save_chat_history(
                f'{sys.path[0]}/chat_history_backup_{datetime.now().strftime("%Y-%m-%d_%H,%M,%S")}.json')
            raise EOFError
        return response.json()

    def modify_system_prompt(self, new_content):
        if self.messages[0]['role'] == 'system':
            old_content = self.messages[0]['content']
            self.messages[0]['content'] = new_content
            console.print(
                f"[dim]System prompt has been modified from '{old_content}' to '{new_content}'.")
            self.current_tokens = count_message_tokens(self.messages)
            # recount current tokens
            if len(self.messages) > 1:
                console.print(
                    "[dim]Note this is not a new chat, modifications to the system prompt have limited impact on answers.")
        else:
            console.print(
                f"[dim]No system prompt found in messages.")

    def set_model(self, new_model: str):
        old_model = self.model
        if not new_model:
            console.print(
                f"[dim]Empty input, the model remains '{old_model}'.")
            return
        self.model = str(new_model)
        if "gpt-4-32k" in self.model:
            self.tokens_limit = 32768
        elif "gpt-4" in self.model:
            self.tokens_limit = 8192
        elif "gpt-3.5-turbo" in self.model:
            self.tokens_limit = 4096
        else:
            self.tokens_limit = -1
        console.print(
            f"[dim]Model has been set from '{old_model}' to '{new_model}'.")

    def set_timeout(self, timeout):
        try:
            self.timeout = float(timeout)
        except ValueError:
            console.print("[red]Input must be a number")
            return
        console.print(f"[dim]API timeout set to [green]{timeout}s[/].")


class CustomCompleter(Completer):
    commands = [
        '/raw', '/multi', '/stream', '/tokens', '/last', '/copy',
        '/model', '/save', '/system', '/timeout', '/undo', '/delete', '/help', '/exit'
    ]

    copy_actions = [
        "code",
        "all"
    ]

    delete_actions = [
        "first",
        "all"
    ]

    available_models = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0301",
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-32k",
        "gpt-4-32k-0314",
    ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            # Check if it's a /model command
            if text.startswith('/model '):
                model_prefix = text[7:]
                for model in self.available_models:
                    if model.startswith(model_prefix):
                        yield Completion(model, start_position=-len(model_prefix))
            # Check if it's a /copy command
            elif text.startswith('/copy '):
                copy_prefix = text[6:]
                for copy in self.copy_actions:
                    if copy.startswith(copy_prefix):
                        yield Completion(copy, start_position=-len(copy_prefix))

            # Check if it's a /delete command
            elif text.startswith('/delete '):
                delete_prefix = text[8:]
                for delete in self.delete_actions:
                    if delete.startswith(delete_prefix):
                        yield Completion(delete, start_position=-len(delete_prefix))

            else:
                for command in self.commands:
                    if command.startswith(text):
                        yield Completion(command, start_position=-len(text))


class NumberValidator(Validator):
    def validate(self, document):
        text = document.text
        if not text.isdigit():
            raise ValidationError(message="Please input an Integer!", cursor_position=len(text))


def print_message(message):
    """打印单条来自 LLM-OS 或用户的消息"""
    role = message["role"]
    content = message["content"]
    if role == "user":
        print(f"> {who}: {content}")
    elif role == "assistant":
        console.print("LLM-OS: ", end='', style="bold cyan")
        if ChatMode.raw_mode:
            print(content)
        else:
            console.print(Markdown(content), new_line_start=True)


def handle_command(command: str, llm_os: LLMOS):
    """处理斜杠(/)命令"""
    if command == '/raw':
        ChatMode.toggle_raw_mode()
    elif command == '/multi':
        ChatMode.toggle_multi_line_mode()

    elif command == '/tokens':
        # here: tokens count may be wrong because of the support of changing AI models, because gpt-4 API allows max 8192 tokens (gpt-4-32k up to 32768)
        # one possible solution is: there are only 6 models under '/v1/chat/completions' now, and with if-elif-else all cases can be enumerated
        # but that means, when the model list is updated, here needs to be updated too

        # tokens limit judge moved to LLM-OS.set_model function

        console.print(Panel(f"[bold bright_magenta]Total Tokens Spent:[/]\t{llm_os.total_tokens_spent}\n"
                            f"[bold green]Current Tokens:[/]\t\t{llm_os.current_tokens}/[bold]{llm_os.tokens_limit}",
                            title='token_summary', title_align='left', width=40, style='dim'))

    elif command == '/tool':

        tools_list = llm_os.get_app.get_tool_list()
        # todo format below list
        console.print(Panel(repr(tools_list), title='工具列表', width=80, style='dim'))

    elif command.startswith('/add'):
        args = command.split()
        tools_kwargs = {}
        if len(args) > 1:
            add_tool = args[1]
        else:
            add_tool = prompt("请输入想要添加的工具名: ", default="", style=style)

        if tools_with_api_key.get(add_tool):
            for tool_args in tools_with_api_key.get(add_tool):
                console.print(f"添加{add_tool}工具必须额外申请服务key")
                add_tool_args = ""
                while not add_tool_args:
                    add_tool_args = prompt(
                        f"{tool_args}: ", default="", style=style)
                tools_kwargs[tool_args] = add_tool_args

        # todo
        parent_tool = subtool_parent.get(add_tool, None)
        if parent_tool:
            add_tool = parent_tool

        if add_tool not in main_tool_register.get_registered_tool_names():
            console.print(f"发现未知工具：{add_tool}")
            return

        app = llm_os.get_app
        app.add_tool(add_tool, **tools_kwargs)

        tools_list = app.get_tool_list()
        # todo format below list
        console.print(Panel(repr(tools_list), title='工具列表', width=80, style='dim'))

    elif command.startswith('/del'):
        args = command.split()
        if len(args) > 1:
            del_tool = args[1]
        else:
            del_tool = prompt("请输入想要删除的工具名: ", default="", style=style)

        app = llm_os.get_app
        app.del_tool(del_tool)

        tools_list = app.get_tool_list()
        # todo format below list
        console.print(Panel(repr(tools_list), title='工具列表', width=80, style='dim'))

    elif command.startswith('/depth'):
        args = command.split()
        if len(args) > 1:
            new_think_depth = args[1]
        else:
            new_think_depth = prompt("请输入LLM-OS设定的思考深度: ", default="", style=style)

        app = llm_os.get_app
        app.think_depth = new_think_depth
        app.load_tools_into_bot()

    elif command == '/reset':
        global config
        config = read_json()
        llm_os.messages = init_messages

    elif command == '/usage':
        with console.status("Getting credit usage...") as status:
            credit_usage = llm_os.get_credit_usage()
        if not credit_usage:
            return
        console.print(Panel(f"[bold blue]Total Granted:[/]\t${credit_usage.get('total_granted')}\n"
                            f"[bold bright_yellow]Used:[/]\t\t${credit_usage.get('total_used')}\n"
                            f"[bold green]Available:[/]\t${credit_usage.get('total_available')}",
                            title=credit_usage.get('object'), title_align='left', width=35, style='dim'))
        console.print(
            "[red]`[bright_magenta]/usage[/]` command is currently unavailable, it's not sure if this command will be available again or not.")

    elif command.startswith('/model'):
        args = command.split()
        if len(args) > 1:
            new_model = args[1]
        else:
            new_model = prompt(
                "OpenAI API model: ", default=llm_os.model, style=style)
        if new_model != llm_os.model:
            llm_os.set_model(new_model)
        else:
            console.print("[dim]No change.")

    elif command == '/last':
        reply = llm_os.messages[-1]
        print_message(reply)

    elif command.startswith('/save'):
        args = command.split()
        if len(args) > 1:
            filename = args[1]
        else:
            date_filename = f'./chat_history_{datetime.now().strftime("%Y-%m-%d_%H,%M,%S")}.json'
            filename = prompt("Save to: ", default=date_filename, style=style)
        llm_os.save_chat_history(filename)

    elif command.startswith('/system'):
        args = command.split()
        if len(args) > 1:
            new_content = ' '.join(args[1:])
        else:
            new_content = prompt(
                "System prompt: ", default=llm_os.messages[0]['content'], style=style)
        if new_content != llm_os.messages[0]['content']:
            llm_os.modify_system_prompt(new_content)
        else:
            console.print("[dim]No change.")

    elif command == '/clear':
        clear()

    elif command.startswith('/timeout'):
        args = command.split()
        if len(args) > 1:
            new_timeout = args[1]
        else:
            new_timeout = prompt(
                "OpenAI API timeout: ", default=str(llm_os.timeout), style=style)
        if new_timeout != str(llm_os.timeout):
            llm_os.set_timeout(new_timeout)
        else:
            console.print("[dim]No change.")

    elif command == '/undo':
        if len(llm_os.messages) > 2:
            question = llm_os.messages.pop()
            if question['role'] == "assistant":
                question = llm_os.messages.pop()
            truncated_question = question['content'].split('\n')[0]
            if len(question['content']) > len(truncated_question):
                truncated_question += "..."
            console.print(
                f"[dim]Last question: '{truncated_question}' and it's answer has been removed.")
        else:
            console.print("[dim]Nothing to undo.")

    elif command == '/exit':
        raise EOFError

    else:
        console.print("""[bold]Available commands:[/]
    /raw                     - Toggle raw mode (showing raw text of LLM-OS's reply)
    /multi                   - Toggle multi-line mode (allow multi-line input)
    /stream                  - Toggle stream output mode (flow print the answer)
    /tokens                  - Show the total tokens spent and the tokens for the current conversation
    /last                    - Display last LLM-OS's reply
    /copy (all)              - Copy the full LLM-OS's last reply (raw) to Clipboard
    /copy code \[index]       - Copy the code in LLM-OS's last reply to Clipboard
    /save \[filename_or_path] - Save the chat history to a file
    /model \[model_name]      - Change AI model
    /system \[new_prompt]     - Modify the system prompt
    /timeout \[new_timeout]   - Modify the api timeout
    /undo                    - Undo the last question and remove its answer
    /delete (first)          - Delete the first conversation in current chat
    /delete all              - Clear all messages and conversations current chat
    /help                    - Show this help message
    /exit                    - Exit the application""")


def create_key_bindings():
    """自定义回车事件绑定，实现斜杠命令的提交忽略多行模式"""
    key_bindings = KeyBindings()

    @key_bindings.add(Keys.Enter, eager=True)
    def _(event):
        buffer = event.current_buffer
        text = buffer.text.strip()
        if text.startswith('/') or not ChatMode.multi_line_mode:
            buffer.validate_and_handle()
        else:
            buffer.insert_text('\n')

    return key_bindings


def main(args):
    # 从 .env 文件中读取 OPENAI_API_KEY
    load_dotenv()
    clear()

    if args.key:
        api_key = os.environ.get(args.key)
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = prompt("OpenAI API Key not found, please input: ")

    api_timeout = int(os.environ.get("OPENAI_API_TIMEOUT", "30"))

    if args.debug:
        ChatMode.debug_mode = True

    global who
    example_style = Style.from_dict({
        'dialog': 'bg:#000000',
        # 'dialog frame.label': 'bg:#ffffff #000000',
        'dialog.body': 'bg:#ffffff',
        # 'dialog shadow': 'bg:#00aa00',
    })

    if not ChatMode.debug_mode:
        who = input_dialog(
            title='个性化设置',
            text='让我知道你的名字：',
            ok_text='确认',
            cancel_text='跳过',
            style=example_style).run()
        if not who:
            who = 'user'

    config["human_prefix"] = who

    llm_os = LLMOS(api_key, api_timeout)

    console.print(
        f"[dim]{who} 你好:wave: , 欢迎进入 LLM-OS! \n"
        "输入 `[bright_magenta]/help[/]` 可以获得帮助信息 \n"
        "目前LLM-OS开发者只有我，能预见有大量:wrench:不能兼顾，请见谅 :persevere: \n"
        "欢迎提issue和pr，希望这个项目变得更好 :chart_with_upwards_trend:"
    )

    if args.model:
        llm_os.set_model(args.model)

    if args.debug:
        ChatMode.toggle_debug_mode()

    if args.multi:
        ChatMode.toggle_multi_line_mode()

    if args.raw:
        ChatMode.toggle_raw_mode()

    session = PromptSession()

    # 自定义命令补全，保证输入‘/’后继续显示补全
    commands = CustomCompleter()

    # 绑定回车事件，达到自定义多行模式的效果
    key_bindings = create_key_bindings()

    while True:
        try:
            # todo color of `who`
            message = session.prompt(
                f'> {who}: ', completer=commands, complete_while_typing=True, key_bindings=key_bindings)

            if message.startswith('/'):
                command = message.strip().lower()
                handle_command(command, llm_os)
            else:
                if not message:
                    continue

                LOG.info(f"> {who}: {message}")
                llm_os.handle(message)

                if message.lower() in ['再见', 'bye', 'goodbye', '结束', 'end', '退出', 'exit', 'quit']:
                    break

        except KeyboardInterrupt:
            # raises KeyboardInterrupt when ControlC has been pressed
            continue
        except EOFError:
            # EOFError when ControlD has been pressed
            console.print("拜拜~ 👋🏻")
            break

    LOG.info(f"这次互动用了 {llm_os.total_tokens_spent} tokens")
    console.print(
        f"[bright_magenta]这次互动用了： [bold]{llm_os.total_tokens_spent} tokens")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Welcome to chat with LLM-OS.')
    parser.add_argument('-k', '--key', type=str, help='choose the API key to load')
    parser.add_argument('-t', '--timeout', type=int, help='set llm request timeout')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--model', type=str, help='choose the AI model to use')
    parser.add_argument('-m', '--multi', action='store_true',
                        help='Enable multi-line mode')
    parser.add_argument('-r', '--raw', action='store_true',
                        help='Enable raw mode')
    args = parser.parse_args()

    main(args)
