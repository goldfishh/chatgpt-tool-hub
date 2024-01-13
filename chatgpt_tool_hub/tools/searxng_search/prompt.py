from ...prompts import PromptTemplate

PROMPT = """
Your task is to convert user queries into a format acceptable by the search engine. 
You need to fully understand user needs and provide as complete and accurate search keywords as possible.
Separate multiple keywords with spaces. 
Please avoid providing any extra text, so that I can directly pass the keywords to the search engine.

INPUT: {input}
"""


QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)