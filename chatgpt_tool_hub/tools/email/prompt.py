from ...prompts import PromptTemplate

PROMPT = """
Your task is to comprehend the requests sent via email from users and translate them into a JSON format. 
You should accurately identify the recipient, subject, and content of the email, and package them into JSON fields to return to me:

to_addr: The recipient, which could be an email address or a nickname.
subject: The subject line of the email, summarizing it as per the requirements.
body: The main content of the email, meeting the user's demands. This is an informal email scenario and needs to return Chinese.

INPUT: {input}
"""

QUERY_PROMPT = PromptTemplate(
    input_variables=["input"],
    template=PROMPT,
)