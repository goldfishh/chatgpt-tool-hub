from ...prompts import PromptTemplate

PROMPT = """
Your task is to convert user queries into a format acceptable by Wolfram Alpha. 
You need to fully understand user needs and provide as complete and accurate search keywords as possible. 

Below are examples of potential search queries:
Mathematical calculations: Such as "integral of x^2", "solve for x in 2x + 5 = 10", and other mathematical computation problems.
Physics formulas: Like "speed of light in vacuum", "gravitational force equation", and other physics-related queries.
Chemical formulas: For instance, "chemical structure of caffeine", "molecular weight of water", and other chemistry-related content.
Geographical information: Such as "population of New York City", "height of Mount Everest", and other geographic queries.
Financial and currency conversions: For example, "current price of gold", "convert 100 USD to EUR", and other financial and currency-related queries.
Medical terminology: Such as "functions of the liver", "symptoms of common cold", and other medical knowledge queries.
Historical events: For instance, "what happened on this day in history", "famous battles in World War II", and other historical event queries.
Technology news: Like "latest discoveries in astronomy", "recent advances in artificial intelligence", and other technology-related news.
Music theory: For example, "C major scale notes", "how to play a G chord on guitar", and other music theory queries.
Language translation: Such as "translate 'hello' to French", "common phrases in Spanish", and other language translation queries.

English output only. 
Please avoid providing any extra text, so that I can directly pass them to Wolfram Alpha.

INPUT: {input}
"""


QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)