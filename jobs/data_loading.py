from elasticsearch import Elasticsearch
import os, re, logging
import json
import certifi
from settings import ELASTICSEARCH_URL, USERNAME, PASSWORD


# Log transport details (optional):
logging.basicConfig(level=logging.INFO)

# Parse the auth and host from env:
#bonsai = os.environ['BONSAI_URL'] # Production
url = ELASTICSEARCH_URL  # Local
print(url)

# Connect to cluster over SSL using auth for best security:
es = Elasticsearch(
        [ELASTICSEARCH_URL],
        port=9243,
        http_auth=USERNAME + ":" + PASSWORD,
        use_ssl=True,
        verify_certs=True,
        ca_certs=certifi.where()
    )

# Instantiate the new Elasticsearch connection:

print("Is cluster alive? " + str(es.ping()))

# Load mapping
with open("../data/answer_mapping.json", mode='r') as mapping:
	answer_mapping = json.load(mapping)
with open("../data/question_mapping.json", mode='r') as mapping:
	question_mapping = json.load(mapping)

ANSWER_INDEX = "answers"
QUESTION_INDEX = "questions"

# Create index
if es.indices.exists(ANSWER_INDEX):
	print("The index {0} already exists".format(ANSWER_INDEX))
	print("Removing index")
	es.indices.delete(index=ANSWER_INDEX)

es.indices.create(index=ANSWER_INDEX, body=answer_mapping)
print("Index {0} created".format(ANSWER_INDEX))

# Create index
if es.indices.exists(QUESTION_INDEX):
	print("The index {0} already exists".format(QUESTION_INDEX))
	print("Removing index")
	es.indices.delete(index=QUESTION_INDEX)

es.indices.create(index=QUESTION_INDEX, body=question_mapping)
print("Index {0} created".format(QUESTION_INDEX))

# Load and insert data
with open("../data/answers.json", mode='r') as answers_file:
	answers = json.load(answers_file)

for answer in answers["answers"]:
	body = {"value": answer["value"]}
	if "url" in answer:
		body["url"] = answer["url"]
	if "url_API" in answer:
		body["url_API"] = answer["url_API"]
	es.create(index=ANSWER_INDEX, doc_type="answer", id=answer["id"], body=body)

with open("../data/questions.json", mode='r') as questions_file:
	questions = json.load(questions_file)

for question in questions["questions"]:
	body = {"value": question["value"], "type": question["type"]}
	es.create(index=QUESTION_INDEX, doc_type="question", id=question["id"], body=body, parent=question["parent"])

#  Verify that Python can talk to Bonsai (optional):
#  es.ping()
