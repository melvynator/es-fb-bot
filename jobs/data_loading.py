from elasticsearch import Elasticsearch
import os, re, logging
import json
# from settings import BONSAI_URL

# Log transport details (optional):
logging.basicConfig(level=logging.INFO)

# Parse the auth and host from env:
bonsai = os.environ['BONSAI_URL'] # Production
# bonsai = BONSAI_URL  # Local
print(bonsai)

auth = re.search('https://(.*)@', bonsai).group(1).split(':')
host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')

# Connect to cluster over SSL using auth for best security:
es_header = [{
	'host': host,
	'port': 443,
	'use_ssl': True,
	'http_auth': (auth[0], auth[1])
}]

print(es_header)
# Instantiate the new Elasticsearch connection:
es = Elasticsearch(es_header)


# Load mapping
with open("../data/mapping.json", mode='r') as mapping:
	index_data = json.load(mapping)

INDEX_NAME = "bot_data"

# Create index
if es.indices.exists(INDEX_NAME):
	print("The index {0} already exists".format(INDEX_NAME))
	print("Removing index")
	es.indices.delete(index=INDEX_NAME)

es.indices.create(index="bot_data", body=index_data)
print("Index {0} created".format(INDEX_NAME))


# Load and insert data
with open("../data/answers.json", mode='r') as answers_file:
	answers = json.load(answers_file)

for answer in answers["answers"]:
	body = {"value": answer["value"]}
	if "url" in answer:
		body["url"] = answer["url"]
	if "url_API" in answer:
		body["url_API"] = answer["url_API"]
	es.create(index=INDEX_NAME, doc_type="answer", id=answer["id"], body=body)

with open("../data/questions.json", mode='r') as questions_file:
	questions = json.load(questions_file)

for question in questions["questions"]:
	body = {"value": question["value"], "type": question["type"]}
	es.create(index=INDEX_NAME, doc_type="question", id=question["id"], body=body, parent=question["parent"])

#  Verify that Python can talk to Bonsai (optional):
#  es.ping()
