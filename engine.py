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
  return uuid1().hex

def get_answer(answer):
  global _answer
  if 'Text' in answer:
    _answer = { 'url': answer['URL'], 'text': answer['Text'], 'caption': answer['Caption'] }
  else:
    _answer = { "url": answer['url'], "text": answer['snippet'], 'caption': answer['name'] }
  return _answer

def _prepare(text, index=None):
  if index is not None:
    if len(text) > index:
      text = text[index]
    else:
      return
  return str(text).lower().strip()

def _strip(a=None):
  if a is None:
    a = _answer or {}
  caption = a.get('Caption', a.get('caption', a.get('name', '')))
  url = a.get('URL', a.get('url', ''))
  for sep in '|-':
    parts = caption.rsplit(sep, 1)
    site = _prepare(parts, 1)
    if site is None:
      continue
    if site in URL(url).netloc:
      return parts[0].strip()
  return caption.strip()

def _similarity(a, b=None, scaling=True):
  return similarity(_strip(a), _strip(b), scaling=scaling)

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

  _text = [text, _strip()] if _answer else text
  questions = ((similarity(_text, q['Text']), q) for q in table_service.query_entities('Questions'))
  s, question = max(questions, key=lambda e: e[0], default=(0, None))
  if s > 0.8:
    _question = f"Question eq '{question['RowKey']}'"
    if _answer:
      answers = table_service.query_entities('Answers', filter=_question)
      answer = max(answers, key=lambda a: _similarity(a))
    else:
      answer = table_service.query_entities('Answers', filter=f"{_question} and Rank eq 1")[0]
    return json_response(get_answer(answer))

  query = re.sub(r'\s+', '+', text)
  res = answer_search(params={ 'q': query })
  if not res.ok:
    return text_response(res.reason, res.status_code)
  data = res.json()
  answers = data["webPages"]["value"]
  _quora = [i for (i, a) in enumerate(answers[:5]) if URL(a['url']).netloc == 'www.quora.com']
  for i in reversed(_quora):
    answers.insert(0, answers.pop(i))

  if _answer:
    _answers = ((_similarity(a), a) for a in answers[:5])
    s, a = max(_answers, key=lambda a: a[0])
    answer = a if s > 0.8 else answers[0]
  else:
    answer = answers[0]

  question = { 'PartitionKey': 'default', 'Text': text, 'RowKey': uuid() }

  for i, a in enumerate(answers):
    table_service.insert_entity('Answers', {
      'PartitionKey': 'default',
      'RowKey': uuid(),
      'Question': question['RowKey'],
      'URL': a['url'],
      'Text': a['snippet'],
      'Caption': a['name'],
      'Rank': i + 1
    })
  table_service.insert_entity('Questions', question)

  return json_response(get_answer(answer))
