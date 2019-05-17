import os, yaml, json

from util import realpath
from collections import namedtuple


with open(realpath('config.yaml')) as f:
  locals().update(yaml.load(f, Loader=yaml.SafeLoader))

Api = namedtuple('Api', ('url', 'key'))

azure_storage = azure['storage']

cognitive_api = 'https://api.labs.cognitive.microsoft.com'
cognitive = azure['cognitive']
answer_search = Api(f'{cognitive_api}/answerSearch/v7.0/search', cognitive['answer_search'])

_qna = azure['qna_maker']
qna_maker = Api(f"{_qna['host']}/knowledgebases/{_qna['kb']}/generateAnswer", _qna['key'])

__all__ = (
  'azure', 'azure_storage', 'cognitive_api', 'cognitive', 'answer_search', 'qna_maker'
)
