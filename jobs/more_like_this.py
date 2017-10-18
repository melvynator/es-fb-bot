from elasticsearch import Elasticsearch
from settings import BONSAI_URL
import os, re, logging
import json

# Log transport details (optional):
logging.basicConfig(level=logging.INFO)

# Parse the auth and host from env:
# bonsai = os.environ['BONSAI_URL'] # Production
bonsai = BONSAI_URL  # Local
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
INDEX_NAME = "bot_data"

es = Elasticsearch(es_header)

body = {
			"query": {
				"more_like_this": {
					"fields": ["value"],
					"like": "Hi you, how are you?!",
					"min_term_freq": 1,
					"min_doc_freq": 1,
					"analyzer": "english"
				}
			},
			"size": 1
		}

res = es.search(index=INDEX_NAME, doc_type="question", body=body)
print(res)

#  Verify that Python can talk to Bonsai (optional):
#  es.ping()
