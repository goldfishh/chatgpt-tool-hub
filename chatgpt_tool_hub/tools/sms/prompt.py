from ...prompts import PromptTemplate

PROMPT = """
Your task is to understand the user's requirements for sending a text message and translate it into JSON format. 
You need to accurately identify the recipient's address and the content of the text message, and package them into JSON fields to return to me:

to_addr: The recipient's address, which can be a phone number or a nickname.
body: The main content of the text message, meeting the user's needs. 

Since text messages incur charges, you can use your creativity to create richer content.


Your task is to understand the user's needs for sending a text message and translate it into JSON format. 
You need to accurately identify the recipient's address and package it into a JSON field to return to me:

to_addr: The recipient's address, which can be a phone number or a nickname.
body: The main content of the text message. While meeting the user's needs, you can use your creativity to create richer content. 

Since text messages incur charges, please avoid sending meaningless content and ensure it does not exceed 325 characters. 
Please use Chinese.

INPUT: {input}
"""

QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)