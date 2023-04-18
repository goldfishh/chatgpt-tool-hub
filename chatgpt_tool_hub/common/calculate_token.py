from chatgpt_tool_hub.common.log import LOG


# refer to https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def count_message_tokens(messages, model: str = "gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    import tiktoken
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        LOG.debug("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        return count_message_tokens(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        return count_message_tokens(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        LOG.warn(f"count_message_tokens() is not implemented for model {model}. "
                 f"Returning num tokens assuming gpt-3.5-turbo-0301.")
        return count_message_tokens(messages, model="gpt-3.5-turbo-0301")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def count_string_tokens(string: str, model_name: str = "gpt-3.5-turbo") -> int:
    """
    Returns the number of tokens in a text string.

    Args:
    string (str): The text string.
    model_name (str): The name of the encoding to use. (e.g., "gpt-3.5-turbo")

    Returns:
    int: The number of tokens in the text string.
    """
    import tiktoken
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(string))
