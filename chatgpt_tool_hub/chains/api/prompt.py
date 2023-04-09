
from chatgpt_tool_hub.prompts.prompt import PromptTemplate

API_URL_PROMPT_TEMPLATE = """You are given the below API Documentation: {api_docs} 
Using this documentation, generate the full API url to call for answering the user question. 
You should build the API url in order to get a response that is as short as possible, 
while still getting the necessary information to answer the question. 
Pay attention to deliberately exclude any unnecessary pieces of data in the API call.

Question:{question}
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

Here is the response from the API:

{api_response}

You can answer my question step by step according to api response.

You should provide feedback on whether the question can be answered, 
explain what you have done, what you have seen and what the outcome was to the Human. 
Don't make up you response!

Your final answer:"""
)

API_RESPONSE_PROMPT = PromptTemplate(
    input_variables=["api_docs", "question", "api_url", "api_response"],
    template=API_RESPONSE_PROMPT_TEMPLATE,
)
