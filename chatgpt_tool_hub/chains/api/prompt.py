from ...prompts.prompt import PromptTemplate

API_URL_PROMPT_TEMPLATE = """You have received an API documentation: 

{api_docs}

Your task is to use this document to generate a complete API URL to answer the user's question.

Requirements for generating the URL:
You must construct the URL according to the BASE URL and endpoint provided in the document; no arbitrary creation is allowed.
The constructed API URL must ensure access to the necessary information to answer the question.
Please be mindful to exclude any unnecessary data from the API call.

Question: {question}

API URL:"""

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

1. 从API的响应结果中你看到了什么，有哪些内容和问题有关系
2. 进一步分析该响应结果是否能够回答问题
3. 用科学工作者严谨的口吻组织你的语言去回答用户提出的这个问题，你需要提供问题的答案和依据
4. 请勿编造你的回答

你对问题的回复:"""
)

API_RESPONSE_PROMPT = PromptTemplate(
    input_variables=["api_docs", "question", "api_url", "api_response"],
    template=API_RESPONSE_PROMPT_TEMPLATE,
)
