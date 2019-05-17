# Web Knowledge Assistant

An engaging virtual assistant capable of answering arbitrary open-ended questions

## Architecture
- designed for [Microsoft Azure](https://azure.microsoft.com/en-us/)
- [Python *server*](https://bareasgi.readthedocs.io/en/latest/), running on [*Azure App Service*](https://azure.microsoft.com/en-us/services/app-service/)
- [*QnA Maker*](https://www.qnamaker.ai/) instance with the `qna_chitchat_professional` dialog pack
- [*Azure Storage*](https://azure.microsoft.com/en-us/services/storage/) account for [*Table storage*](https://azure.microsoft.com/en-us/services/storage/tables/)
- [*Cognitive Answer Search*](https://labs.cognitive.microsoft.com/en-us/project-answer-search) for finding relevant (and succint) answers around the Web

## Workflow
- the user is greeted with an introductory *message* from *QnA Maker*
- the user may submit a message (usually a question) using the input area
- the server sends the question to *QnA Maker* and obtains a preliminary list of *answers*
- if there are no relevant answers in the list, the query is first searched in the *database*, according to a specialized *similarity metric*
- if any relevant entries are found then the best answer is shown; otherwise the query is forwarded to *Answer Search*
- the *search* results are then sorted according to the same *similarity metric* against the query together with the previous answer's *caption* (if available)
- the best answer, if available, is shown to the user
- this process can be repeated indefinitely

## Setup
### Requirements
- *\<project root>/config.yaml* with the following:
```yaml
azure:
  storage:
    account: ...
    key: <admin key>
  qna_maker:
    host: ...
    kb: ...
    key: ...
  cognitive:
    answer_search: <api_key>
```

## MIT License
