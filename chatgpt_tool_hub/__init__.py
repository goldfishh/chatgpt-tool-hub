from .version import __version__
from chatgpt_tool_hub.common.input import print_text

print("chatgpt-tool-hub version: " + str(__version__))


# todo remove it in the future
print_text("chatgpt-tool-hub 0.3.8后，部分工具名将变更：requests -> url-get", color="red", end="\n")
