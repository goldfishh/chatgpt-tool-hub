from chatgpt_tool_hub.prompts import PromptTemplate

PROMPT = """
你是文案编辑，你的工作是组合下列的文本，同时做一些转述

{text} 

组合要求：
1. 组合时必须是中文
2. 组合时必须保留所有内容细节和前后关系
3. 需要你用容易理解的方式转述
4. 不低于120字，不超过800字
5. 你不能捏造信息

Output:
"""

REDUCE_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=PROMPT,
)
