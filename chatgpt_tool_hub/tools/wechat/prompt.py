from ...prompts import PromptTemplate

PROMPT = """

Your task is to understand the user's WeChat message requirements and translate them into JSON format. 
You need to accurately identify the recipient's address and the main content of the WeChat message, packaged as JSON fields to return to me:

to_addr: Recipient's address, which could be a person's name or a group's name
body: The main content of the WeChat message, in Chinese and meeting the user's requirements. 

This is an informal scenario, and the content can have a lively tone, with the possibility of using some emoticons.

INPUT: {input}
"""

QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)