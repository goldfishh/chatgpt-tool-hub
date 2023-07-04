""" A frontend of LLM-OS, it's just a prototype for now."""

import argparse
import json
import logging
import os
from datetime import datetime

import pyperclip
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
from chatgpt_tool_hub.tools.news import news_tool_register

logging.basicConfig(filename=f'{os.getcwd()}/llmos.log', format=LOGGING_FMT,
                    datefmt=LOGGING_DATEFMT, level=logging.INFO)

LOG = logging.getLogger("llmos")

console = Console()

style = Style.from_dict({
    "prompt": "ansigreen",  # 将提示符设置为绿色
})

input_dialog_style = Style.from_dict({
    'dialog': 'bg:#000000',
    'dialog.body': 'bg:#ffffff',
})

who = ""

init_chat_history = []

tools_with_api_key = {
    "bing-search": ["bing_subscription_key"],
    "google-search": ["google_api_key", "google_cse_id"],
    "searxng-search": ["searx_search_host"],
    "morning-news": ["morning_news_api_key"],
    "news-api": ["news_api_key"],
    "wolfram-alpha": ["wolfram_alpha_appid"],
}

# todo consider higher tree
# Dynamic addition and deletion of subtools are currently not supported.
subtool_parent = {
    "morning-news": "news",
    "news-api": "news"
}


def read_config_json() -> dict:
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    tool_config = {"tools": [], "kwargs": {"nolog": True}}
    if not os.path.exists(config_path):
        return tool_config
    with open(config_path, "r") as f:
        tool_config = json.load(f)
    # todo test it
    tool_config.get("kwargs", {})["nolog"] = True

    return tool_config


def save_config_json():
    global config
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f)


config = read_config_json()


class ChatMode:
    debug_mode = False
    raw_mode = False
    multi_line_mode = False

    @classmethod
    def toggle_debug_mode(cls):
        cls.debug_mode = not cls.debug_mode
        console.print(
            f"[dim]Debug 模式 {'已开启' if cls.debug_mode else '已关闭'}")

    @classmethod
    def toggle_raw_mode(cls):
        cls.raw_mode = not cls.raw_mode
        console.print(
            f"[dim]Raw 模式 {'已开启' if cls.raw_mode else '已关闭'}, "
            "使用 `/last` 来显示 LLM-OS 上次回复 .")

    @classmethod
    def toggle_multi_line_mode(cls):
        cls.multi_line_mode = not cls.multi_line_mode
        if cls.multi_line_mode:
            console.print(
                "[dim]Multi-line 模式 已开启, 使用 [[bright_magenta]Esc[/]] + [[bright_magenta]ENTER[/]] 提交跨行文本."
            )
        else:
            console.print("[dim]Multi-line 模式 已关闭.")


class LLMOS:
    def __init__(self, timeout: int):
        self.messages = init_chat_history

        self.app = self.create_app()

        self.model = 'gpt-35-turbo'
        self.timeout = timeout

        # todo 需要llm-os model支持
        self.tokens_limit = 4096
        self.total_tokens_spent = 0
        self.current_tokens = count_message_tokens(self.messages)

    def create_app(self):
        return AppFactory().create_app(tools_list=config["tools"], console=console, **config["kwargs"])

    @property
    def get_app(self) -> App:
        return self.app

    def handle(self, message: str):
        try:
            self.messages.append({"role": "user", "content": message})

            response = self.send_request(message)

            if response is None:
                self.messages.pop()
                return

            LOG.info(f"LLM-OS response: {response}")
            _message = {"role": "assistant", "content": f"{response}"}
            print_message(_message)
            self.messages.append(_message)
            # todo
            self.current_tokens = count_message_tokens(self.messages)
            self.total_tokens_spent += self.current_tokens

        except Exception as e:
            console.print(f"[red]系统错误: {str(e)}. 请检查日志获取更多信息")
            LOG.exception(e)
            # todo
            self.save_chat_history(f'chat_history_backup_{datetime.now().strftime("%Y-%m-%d_%H,%M,%S")}.json')
            raise EOFError

        return response

    def send_request(self, message: str):
        try:
            with console.status("[bold cyan]LLM-OS 分析中...\n", spinner="earth"):
                response = self.app.ask(message, chat_history=self.messages)

            return response
        except KeyboardInterrupt:
            console.print("[bold cyan]主动中断. 分析已停止.")
            raise
        except Exception as e:
            console.print(f"[red]错误: {str(e)}. ")
            LOG.exception(e)
            return None

    def save_chat_history(self, filename):
        # 默认存放路径在本文件下的log目录
        file_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
        if not os.path.exists(file_dir_path):
            os.mkdir(file_dir_path)
        try:
            with open(f"{os.path.join(file_dir_path, filename)}", 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            console.print(f"[dim]聊天记录保存成功: [bright_magenta]{filename}", highlight=False)
        except Exception as e:
            console.print(f"[red]聊天记录保存失败: {str(e)}. ")
            LOG.exception(e)

    def get_credit_usage(self):
        # todo
        # tool-hub暂时不支持统计tokens cost
        return {
            'total_granted': "tool-hub暂时不支持统计tokens cost",
            'total_used': '',
            'total_available': ''
        }

    def modify_system_prompt(self, new_content):
        # todo
        # tool-hub暂时不支持修改系统prompt
        return new_content

    def set_model(self, new_model: str):
        old_model = self.model
        if not new_model:
            console.print(f"[dim]我没有收到新模型名，模型未变更: [bold cyan]{old_model}[/].")
            return
        # todo test gpt-4
        if self.model.startswith("gpt-4-32k"):
            tokens_limit = 32768
        elif self.model.startswith("gpt-4"):
            tokens_limit = 8192
        elif self.model.startswith("gpt-35-turbo"):
            tokens_limit = 4096
        else:
            console.print(f"[red]没有该模型 {new_model} tokens信息，模型未变更: [bold cyan]{old_model}[/].")
            return

        config["kwargs"]["model_name"] = new_model
        self.model = new_model
        self.tokens_limit = tokens_limit
        console.print(f"[dim]模型将发生变更 [bold cyan]{old_model}[/] -> [bold red]{new_model}[/].")
        self.app = self.create_app()

    def set_timeout(self, timeout):
        old_timeout = self.timeout
        try:
            self.timeout = float(timeout)
        except ValueError:
            console.print("[red]我没有收到数字")
            return
        config["kwargs"]["request_timeout"] = self.timeout
        console.print(f"[dim] LLM-OS超时时间将发生变更 [bold cyan]{old_timeout}[/] -> [bold red]{self.timeout}[/].")
        self.app = self.create_app()


class CustomCompleter(Completer):
    commands = [
        '/debug', '/raw', '/multi', '/tool', '/add', '/del', '/depth', '/reset', '/model',
        '/last', '/save', '/clear', '/timeout', '/undo', '/exit', '/copy', '/help'
    ]

    available_models = [
        "gpt-35-turbo",
        "gpt-35-turbo-0301",
        "gpt-35-turbo-0613",
        "gpt-35-turbo-16k",
        "gpt-35-turbo-16k-0613",
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
            if text.startswith('/add '):
                tool_prefix = text[5:]
                available_tools = main_tool_register.get_registered_tool_names() \
                                  + news_tool_register.get_registered_tool_names()
                for tool in available_tools:
                    if tool.startswith(tool_prefix):
                        yield Completion(tool, start_position=-len(tool_prefix))
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
        # todo 有时会吞数据
        console.print("LLM-OS: ", end='', style="bold cyan")
        if ChatMode.raw_mode:
            print(content)
        else:
            console.print(Markdown(content), new_line_start=True)


def handle_command(command: str, llm_os: LLMOS):
    """处理斜杠(/)命令"""
    global config

    if command == '/raw':
        ChatMode.toggle_raw_mode()
    elif command == '/multi':
        ChatMode.toggle_multi_line_mode()
    elif command == '/debug':
        ChatMode.toggle_debug_mode()
        config["kwargs"]['nolog'] = not ChatMode.debug_mode
        config["kwargs"]['debug'] = ChatMode.debug_mode
        llm_os.app = llm_os.create_app()
    elif command == '/tool':
        tools_list = llm_os.get_app.get_tool_list()
        # todo beautify below Panel
        console.print(Panel(repr(tools_list), title='工具列表', style='dim'))

    elif command.startswith('/add'):
        args = command.split()
        if len(args) > 1:
            add_tool = args[1]
        else:
            add_tool = prompt("请输入想要添加的工具名: ", default="", style=style)

        if not add_tool:
            console.print("tool未改变.")
            return

        tools_kwargs = {}
        if tools_with_api_key.get(add_tool):
            console.print(f"添加 [bold cyan]{add_tool}[/] 工具必须额外申请服务key")
            for tool_args in tools_with_api_key.get(add_tool):
                add_tool_args = ""
                while not add_tool_args:
                    # ControlC or ControlD to break this loop
                    add_tool_args = prompt(f"{tool_args}: ", default="", style=style)
                tools_kwargs[tool_args] = add_tool_args

        # todo 目前tool-hub不支持subtool粒度增删tool
        if add_tool not in main_tool_register.get_registered_tool_names():
            if add_tool not in subtool_parent.keys():
                console.print(f"发现未知工具: {add_tool}")
                return
            elif subtool_parent[add_tool] not in llm_os.get_app.get_tool_list():
                add_tool = subtool_parent[add_tool]

        app = llm_os.get_app
        app.add_tool(add_tool, **tools_kwargs)

        tools_list = app.get_tool_list()
        # todo beautify below Panel
        console.print(Panel(repr(tools_list), title='工具列表', style='dim'))

    elif command.startswith('/del'):
        args = command.split()
        if len(args) > 1:
            del_tool = args[1]
        else:
            del_tool = prompt("请输入想要删除的工具名: ", default="", style=style)

        if not del_tool:
            console.print("tool未改变.")
            return

        app = llm_os.get_app
        app.del_tool(del_tool)

        tools_list = app.get_tool_list()
        # todo beautify below Panel
        console.print(Panel(repr(tools_list), title='工具列表', style='dim'))

    elif command.startswith('/depth'):
        args = command.split()
        if len(args) > 1:
            new_think_depth = args[1]
        else:
            new_think_depth = prompt("请输入LLM-OS设定的思考深度: ", default="2", style=style)

        if not new_think_depth:
            console.print("depth未改变.")
            return

        try:
            new_think_depth = int(new_think_depth)
        except Exception as e:
            LOG.error(f"parsing new_think_depth error: {repr(e)}")
            console.print("思考深度类型必须为整数，depth未改变.")

        app = llm_os.get_app
        app.think_depth = new_think_depth
        app.load_tools_into_bot()

    elif command == '/reset':
        # todo bug 这里没有清空历史记录
        config = read_config_json()
        llm_os.app = llm_os.create_app()
        llm_os.messages = init_chat_history

    elif command.startswith('/model'):
        args = command.split()
        if len(args) > 1:
            new_model = args[1]
        else:
            new_model = prompt("请输入要更改的LLM名称: ", default=llm_os.model, style=style)

        if new_model != llm_os.model:
            llm_os.set_model(new_model)
        else:
            console.print("[dim]model未改变.")

    elif command == '/last':
        if len(llm_os.messages) > 1:
            reply = llm_os.messages[-1]
            print_message(reply)
        else:
            console.print("[dim]没有要做的事情.")

    elif command.startswith('/save'):
        args = command.split()
        if len(args) > 1:
            filename = args[1]
        else:
            date_filename = f'chat_history_{datetime.now().strftime("%Y-%m-%d_%H,%M,%S")}.json'
            filename = prompt("Save to: ", default=date_filename, style=style)
        llm_os.save_chat_history(filename)

    elif command == '/clear':
        clear()

    elif command.startswith('/timeout'):
        args = command.split()
        if len(args) > 1:
            new_timeout = args[1]
        else:
            new_timeout = prompt("请输入更改后的超时时间 [bold red]整数[/]: ", default=str(llm_os.timeout), style=style)
        if new_timeout != str(llm_os.timeout):
            llm_os.set_timeout(new_timeout)
        else:
            console.print("[dim]timeout未改变. ")

    elif command == '/undo':
        if len(llm_os.messages) >= 2:
            question = llm_os.messages.pop()
            if question['role'] == "assistant":
                question = llm_os.messages.pop()
            # print undo question
            truncated_question = question['content'].split('\n')[0]
            if len(question['content']) > len(truncated_question):
                truncated_question += "..."
            console.print(f"[dim]上个问题: [bold dim]'{truncated_question}'[/] 和对应回复已清除")
        else:
            console.print("[dim]没有要做的事情.")

    elif command.startswith('/copy'):
        if len(llm_os.messages) > 1:
            reply = llm_os.messages[-1]
            pyperclip.copy(reply["content"])
            console.print("[dim]LLM-OS上次回复已复制到粘贴板")
        else:
            console.print("[dim]没有要做的事情.")

    elif command == '/exit':
        raise EOFError

    else:
        # todo 为 /help 专门做一个页面
        console.print("""[bold]Available commands:[/]
    /debug                   - 切换debug模式开关
    /raw                     - 切换raw模式开关 (禁用富文本)
    /multi                   - 切换multi-line模式开关 (允许多行输入)
    /tool                    - 查看当前加载工具列表
    /add     \[tool_name]     - 增加工具
    /del     \[tool_name]     - 删除工具
    /depth                   - 设置LLM-OS思考深度 (设置过大可能无法停止)
    /reset                   - LLM-OS重置 (重新加载配置并重置聊天记录)
    /timeout \[new_timeout]   - 修改访问llm的请求超时时间
    /model   \[model_name]    - 切换模型 (目前仅支持gpt-35)
    /last                    - 显示上一次LLM-OS的回复内容
    /copy                    - 复制上一次LLM-OS的回复内容到粘贴板
    /undo                    - 清除上一次与llm的对话记录 (包含问题和回复)
    /save    \[filename]      - 保存聊天记录
    /clear                   - 清屏
    /exit                    - 离开
    /help                    - 显示帮助信息""")


def create_key_bindings():
    """自定义回车事件绑定，实现斜杠命令的提交忽略多行模式"""
    key_bindings = KeyBindings()

    @key_bindings.add(Keys.Enter, eager=True)
    def _(event):
        buffer = event.current_buffer
        text = str(buffer.text).strip()
        if text.startswith('/') or not ChatMode.multi_line_mode:
            buffer.validate_and_handle()
        else:
            buffer.insert_text('\n')

    return key_bindings


def main(args):
    # 从 .env 文件加载环境变量
    load_dotenv()

    if args.key:
        api_key = str(args.key)
    elif config.get("kwargs", {}).get("llm_api_key", ""):
        api_key = config["kwargs"]["llm_api_key"]
    else:
        api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        api_key = prompt("我没有找到OpenAI API Key, 请输入: ", style=style)
    os.environ["LLM_API_KEY"] = api_key

    if args.timeout:
        request_timeout = args.timeout
    elif config.get("kwargs", {}).get("request_timeout", ""):
        request_timeout = config["kwargs"]["request_timeout"]
    else:
        request_timeout = os.environ.get("REQUEST_TIMEOUT")

    request_timeout = int(request_timeout) if request_timeout else 90
    os.environ["REQUEST_TIMEOUT"] = str(request_timeout)

    if args.debug or str(os.environ.get("DEBUG")).lower() in {
        'true',
        'enable',
        'yes',
    }:
        ChatMode.toggle_debug_mode()

    if args.multi:
        ChatMode.toggle_multi_line_mode()

    if args.raw:
        ChatMode.toggle_raw_mode()

    global who
    if not ChatMode.debug_mode:
        who = input_dialog(
            title='个性化设置',
            text='让我知道你的名字: ',
            ok_text='确认',
            cancel_text='跳过',
            style=input_dialog_style).run()
    if not who:
        who = 'user'

    config["kwargs"]["human_prefix"] = who

    llm_os = LLMOS(request_timeout)

    if args.model:
        llm_os.set_model(args.model)

    clear()

    console.print(
        f"[dim]{who} 你好 :wave:  欢迎进入 LLM-OS! \n"
        "输入 `[bright_magenta]/help[/]` 可以获得帮助信息 \n"
        "目前LLM-OS开发者只有我 能预见有大量:wrench:不能兼顾 请见谅 :persevere: \n"
        "欢迎提issue和pr 希望这个项目变得更好 :chart_with_upwards_trend:"
    )

    session = PromptSession()

    # 自定义命令补全，保证输入‘/’后继续显示补全
    commands = CustomCompleter()

    # 绑定回车事件，达到自定义多行模式的效果
    key_bindings = create_key_bindings()

    while True:
        try:
            message = session.prompt(f'> {who}: ', completer=commands,
                                     complete_while_typing=True, key_bindings=key_bindings)

            if message.startswith('/'):
                command = str(message).strip().lower()
                handle_command(command, llm_os)
            else:
                if not message:
                    continue

                if message.lower() in ['bye', 'goodbye', 'end', 'exit', 'quit']:
                    break

                LOG.info(f"> {who}: {message}")
                llm_os.handle(message)

        except KeyboardInterrupt:
            # raises KeyboardInterrupt when ControlC has been pressed
            continue
        except EOFError:
            # EOFError when ControlD has been pressed
            break

    save_config_json()
    console.print("[bright_magenta]拜拜~ 👋🏻")
    # todo
    # LOG.info(f"这次互动用了 {llm_os.total_tokens_spent} tokens")
    # console.print(
    #     f"[bright_magenta]这次互动用了:  [bold]{llm_os.total_tokens_spent} tokens")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Welcome to chat with LLM-OS.')
    parser.add_argument('-k', '--key', type=str, help='OpenAI API key to load')
    parser.add_argument('-t', '--timeout', type=int, help='set llm request timeout')
    parser.add_argument('--model', type=str, help='choose the AI model to use')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('-m', '--multi', action='store_true',
                        help='Enable multi-line mode')
    parser.add_argument('-r', '--raw', action='store_true',
                        help='Enable raw mode')
    args = parser.parse_args()

    main(args)
