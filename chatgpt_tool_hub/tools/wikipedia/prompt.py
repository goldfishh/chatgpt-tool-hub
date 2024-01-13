from ...prompts import PromptTemplate

PROMPT = """
Your task is to convert user queries into a format acceptable by Wikipedia. 
You need to fully understand user needs and provide as complete and accurate search keywords as possible. 
Keywords can include names of people, historical events, geographical locations, scientific terms, literary works, biological species, artists and their works, economic or political concepts, scientific fields, and emerging technologies or concepts. 
Separate multiple keywords with spaces. 
Please avoid providing any extra text, so that I can directly pass them to Wikipedia.

INPUT: {input}
"""


QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)