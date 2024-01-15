from ..common.utils import get_from_dict_or_env
from . import ChatOpenAI
from . import DEFAULT_MODEL_NAME

class ModelFactory:

    def __init__(self):
        self.available_models_prefix = {
            "gpt-3.5-turbo": "chatgpt",
            "gpt-3.5-turbo-0301": "chatgpt",
            "gpt-3.5-turbo-0613": "chatgpt",
            "gpt-3.5-turbo-1106": "chatgpt",
            "gpt-3.5-turbo-instruct": "chatgpt",
            "gpt-3.5-turbo-16k": "chatgpt",
            "gpt-3.5-turbo-16k-0613": "chatgpt",
            "gpt-4": "chatgpt",
            "gpt-4-0613": "chatgpt",
            "gpt-4-32k": "chatgpt",
            "gpt-4-32k-0613": "chatgpt",
            "gpt-4-1106-preview": "chatgpt",
        }
        pass

    def match_model(self, name: str) -> str:
        for k, v in self.available_models_prefix.items():
            if name.startswith(k):
                return v
        return ""

    def create_llm_model(self, **llm_model_kwargs):
        _model = get_from_dict_or_env(llm_model_kwargs, "model_name", "MODEL_NAME", DEFAULT_MODEL_NAME)
        match_llm_model = self.match_model(_model)
        if True or match_llm_model == "chatgpt":
            return ChatOpenAI(**llm_model_kwargs)
        else:
            raise NotImplementedError("implement me!")
