from elasticsearch import Elasticsearch
from settings import BONSAI_URL
#from settings import YOUTUBE_KEY
import os, re, logging
import json
import requests

# Log transport details (optional):
logging.basicConfig(level=logging.INFO)

# Parse the auth and host from env:
#bonsai = os.environ['BONSAI_URL'] # Production
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
					"like": "What is the weather in Paris?",
					"min_term_freq": 1,
					"min_doc_freq": 1,
					"analyzer": "english"
				}
			},
			"size": 1
		}
res = es.search(index=INDEX_NAME, doc_type="question", body=body)
print(res)
parent_id = res["hits"]["hits"][0]["_parent"]
parent = es.get(index=INDEX_NAME, doc_type="answer", id=int(parent_id))
print(parent)
result = parent["_source"]["url_API"].format("UCJFp8uSYCjXOMnkUyb3CQ3Q", YOUTUBE_KEY)
response = requests.get(result)
video_urls = [item["id"]["videoId"] for item in response.json()["items"]]
print(video_urls)
#  Verify that Python can talk to Bonsai (optional):
#  es.ping()
