
from chatgpt_tool_hub.prompts.prompt import PromptTemplate

API_URL_PROMPT_TEMPLATE = """你收到一个的调用API文档: {api_docs}
你的任务是使用这个文档，生成完整的API URL以回答用户的问题

生成URL要求如下：
1. 你必须按文档给出的BASE URL和endpoint构造URL，不能随意编造
2. 构建的API URL要保证能获得回答问题所需的必要信息
3. 请注意，有意排除API调用中不必要的数据

问题: {question}

API url:"""

API_URL_PROMPT = PromptTemplate(
    input_variables=[
        "api_docs",
        "question",
    ],
    template=API_URL_PROMPT_TEMPLATE,
)

API_RESPONSE_PROMPT_TEMPLATE = (
    API_URL_PROMPT_TEMPLATE
    + """ {api_url}

以下是API的响应结果：

{api_response}

你应该一步一步思考：
1. 你从API的响应结果看到了什么，有哪些内容和问题有关系
2. 进一步分析该响应结果能否回答问题
3. 用科学工作者严谨的口吻来组织你的语言去回答用户提出的这个问题，你需要提供问题的答案和依据
4. 请勿编造你的回答

你对问题的回复:"""
)

API_RESPONSE_PROMPT = PromptTemplate(
    input_variables=["api_docs", "question", "api_url", "api_response"],
    template=API_RESPONSE_PROMPT_TEMPLATE,
)
