""" subtool prompt """
PREFIX = """Answer the following questions as best you can. You have access to the following tools:"""
FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question in chinese"""
SUFFIX = """Begin!

Question: {input}
Thought:{bot_scratchpad}

You should try to retain as much information as possible that you know.
Please note that the prefix "Final Answer: " is very important for me to parse your response, remember to add this prefix.
Don't make up you response.
"""
