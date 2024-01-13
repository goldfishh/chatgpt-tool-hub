import sys
from ...prompts import PromptTemplate

PROMPT = f"""
Your task is to fulfill user requirements using terminal commands and send them to me. 
You need to understand the user's needs as much as possible and provide me with valid and concise terminal commands for {sys.platform} platform.

Do not provide any text that cannot be executed in the terminal so that I can directly copy and paste the code you give me into the Terminal for execution.

INPUT: {{input}}
OUTPUT: """


QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)
