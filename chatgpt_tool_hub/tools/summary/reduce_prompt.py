from chatgpt_tool_hub.prompts import PromptTemplate

PROMPT = """
为下面的内容做一个精确的总结:

{text} 

总结要求：
1. 生成的总结必须是中文
2. 生成的总结应该简明扼要，能让人容易理解
3. 你应该分门别类地（比如时间、地点、人物）来组织你的总结，你可以精简每条的内容，但不能捏造信息

Output:
"""

REDUCE_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=PROMPT,
)
