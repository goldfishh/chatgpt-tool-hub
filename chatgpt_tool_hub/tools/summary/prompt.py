from ...prompts import PromptTemplate

MAP_PROMPT = """
你是一名专业文字研究员。
你将处理某个长文档的一部分时，你的任务是利用编辑和写作技能，摒弃大部分无关内容，提炼出最关键的文字内容，对这部分文档的进行简短的归纳总结。

要求用中文总结，字数尽可能少。

Input: {text} 

Output:
"""

MAP_QUERY_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=MAP_PROMPT,
)


REDUCE_PROMPT = """

你是一名文案编辑，需要将以下文本进行组合，并进行一些转述。

在组合文本时，请确保保留所有细节，使得整体衔接流畅。
请以通俗易懂、无歧义的方式进行转述，同时确保组合的文本忠实于原文，不添加虚构的信息。

Input: {text}

Output:
"""

REDUCE_QUERY_PROMPT = PromptTemplate(
    input_variables=["text"],
    template=REDUCE_PROMPT,
)
