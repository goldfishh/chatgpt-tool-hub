MAP_PROMPT = """
You are a research analyst. I will provide you with a section of a document and you will create a summary from it. 
You will use your editing and writing skills to create a summary in the style of a Confidential Information Memorandum. 
You will preserve as many details as possible. You will maintain context across the summary. 
Your section will be combined with the other sections to create summary of the entire document.

Your summary must be no longer than 650 characters long.

Input: {text} 

Output:
"""