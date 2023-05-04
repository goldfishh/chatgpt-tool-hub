from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import ChatOpenAI


class ModelFactory:

    def __init__(self):
        self.available_models_prefix = {
            "text-davinci": "chatgpt",
            "gpt-3.5-turbo": "chatgpt",
            "gpt-4": "chatgpt",
            "gpt-4-32k": "chatgpt",
        }
        pass

    def match_model(self, name: str) -> str:
        for k, v in self.available_models_prefix.items():
            if name.startswith(k):
                return v
        return ""

    def create_llm_model(self, **model_kwargs):
        _model = get_from_dict_or_env(model_kwargs, "model_name", "MODEL_NAME", "gpt-3.5-turbo")
        match_llm_model = self.match_model(_model)
        if match_llm_model == "chatgpt":
            return ChatOpenAI(**model_kwargs)
        else:
            raise NotImplementedError("implement me!")
