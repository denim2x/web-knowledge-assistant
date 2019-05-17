import re
from uuid import uuid1

from azure.storage.table.tableservice import TableService

from _bareasgi import text_reader, text_response, json_response
import config
from config import azure_storage
from util import Request, URL
from phrase_metric import similarity

table_service = TableService(account_name=azure_storage['account'], account_key=azure_storage['key'])

answer_search = Request('GET',
                        config.answer_search.url,
                        params={ 'mkt': 'en-us' },
                        headers={ 'Ocp-Apim-Subscription-Key': config.answer_search.key })

qna_maker = Request('POST',
                    config.qna_maker.url,
                    headers={ 'Authorization': f'EndpointKey {config.qna_maker.key}'})

def uuid():
  return str(uuid1())

def get_answer(answer):
  global _answer
  if 'Text' in answer:
    _answer = { 'url': answer['URL'], 'text': answer['Text'], 'caption': answer['Caption'] }
  else:
    _answer = { "url": answer['url'], "text": answer['snippet'], 'caption': answer['name'] }
  return _answer

def _caption():
  return _answer['caption'].rstrip(' - Wikipedia')

_answer = None
async def message(scope, info, matches, content):
  text, score = (await text_reader(content)).strip().lstrip('.').lstrip(), 85
  if text == '':
    text, score = 'who are you?', 0

  text = re.sub(r'\s+', ' ', text)
  res = qna_maker(json={'question': text})
  if not res.ok:
    return text_response(res.reason, res.status_code)
  data = res.json()
  answer = sorted(data['answers'], key=lambda a: a['score'])[-1]
  if answer['score'] > score:
    return json_response({ "url": None, "text": answer['answer'], 'caption': answer["source"] })

  _text = [text, _caption()] if _answer else text
  questions = ((similarity(_text, q['Text']), q) for q in table_service.query_entities('Questions'))
  s, question = max(questions, key=lambda e: e[0], default=(0, None))
  if s > 0.8:
    answers = list(table_service.query_entities('Answers',
                                           filter=f"Question eq '{question['RowKey']}' and Rank eq 1"))
    if answers:
      return json_response(get_answer(answers[0]))

  query = re.sub(r'\s+', '+', text)
  res = answer_search(params={ 'q': query })
  if not res.ok:
    return text_response(res.reason, res.status_code)
  data = res.json()
  answers = data["webPages"]["value"]
  _quora = [i for (i, a) in enumerate(answers[:5]) if URL(a['url']).netloc == 'www.quora.com']
  if _quora:
    answers.insert(0, answers.pop(_quora[0]))
  if _answer:
    answers.sort(key=lambda a: similarity(_caption(), a['name']), reverse=True)
  question = { 'PartitionKey': 'default', 'Text': text, 'RowKey': uuid() }

  for i, answer in enumerate(answers):
    table_service.insert_entity('Answers', {
      'PartitionKey': 'default',
      'RowKey': uuid(),
      'Question': question['RowKey'],
      'URL': answer['url'],
      'Text': answer['snippet'],
      'Caption': answer['name'],
      'Rank': i + 1
    })
  table_service.insert_entity('Questions', question)

  return json_response(get_answer(answers[0]))
