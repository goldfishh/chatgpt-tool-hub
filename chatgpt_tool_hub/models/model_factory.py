from chatgpt_tool_hub.models import ChatOpenAI, OpenAI, AzureOpenAI


class ModelFactory:

    def __init__(self):
        pass

    def create_llm_model(self, llm_type: str = "chatgpt", **model_kwargs):
        if llm_type == "chatgpt":

            return ChatOpenAI(**model_kwargs)
        elif llm_type == "openai":

            return OpenAI(**model_kwargs)
        elif llm_type == "azure_openai":

            return AzureOpenAI(**model_kwargs)
        else:
            raise NotImplementedError("implement me!")
