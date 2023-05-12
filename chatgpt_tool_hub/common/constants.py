import logging

LOGGING_LEVEL = logging.INFO

LOGGING_FMT = '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s'
LOGGING_DATEFMT = '%Y-%m-%d %H:%M:%S'

openai_default_api_base = "https://api.openai.com/v1"
# example:
# openai-sb https://api.openai-sb.com/v1
# azure https://xxx.openai.azure.com/


TRUE_VALUES_SET = {'true', 'enable', 'yes'}
