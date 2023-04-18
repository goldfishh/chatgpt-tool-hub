from chatgpt_tool_hub.prompts import PromptTemplate

PROMPT = """
你是一位专业的研究分析师。我会给你提供某个长文档的一部分，你需要使用你的编辑和写作技能为它生成一个总结。
你要尽可能保留内容细节，比如时间、地点、人物，同时在摘要中保持上下文。
你看到的这部分文档头和尾可能不完整，你需要用少量文字提醒，来保证未来合并总结时能根据你这部分的总结还原出完整内容

要求：
1. 用中文总结
2. 不能超过800个字

Input: {text} 

Output:
"""

MAP_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=PROMPT,
)
