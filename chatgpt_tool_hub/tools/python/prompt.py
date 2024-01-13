from ...prompts import PromptTemplate

PROMPT = """
You're a senior Python developer tasked with implementing user requirements using Python. 
Your goal is to understand the user's needs as much as possible and provide me with valid and concise Python 3 code to fulfill them.

The implementation should print the results using the print function. 
Please avoid providing any text unrelated to Python code, enabling me to directly execute the code you provide in the Python interpreter.

INPUT: {input}
"""


QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)
