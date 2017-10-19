import os
import sys
from datetime import datetime
from elasticsearch import Elasticsearch
import re, logging
import json
import requests
from flask import Flask, request
import random
import string

# Log transport details (optional):
logging.basicConfig(level=logging.INFO)

# Parse the auth and host from env:
bonsai = os.environ['BONSAI_URL'] # Production

auth = re.search('https://(.*)@', bonsai).group(1).split(':')
host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')

# Connect to cluster over SSL using auth for best security:
es_header = [{
	'host': host,
	'port': 443,
	'use_ssl': True,
	'http_auth': (auth[0], auth[1])
}]

# Instantiate the new Elasticsearch connection:
ES = Elasticsearch(es_header)
INDEX_NAME = "bot_data"

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Verification endpoint", 200


@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    try:
        if data["object"] == "page":
            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    if messaging_event.get("message"):
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"]["text"]
                        parent = find_question(message_text)
                        answer = ES.get(index=INDEX_NAME, doc_type="answer", id=parent)
                        message_to_send = answer_management(answer, message_text)
                        log(message_to_send)
                        send_message(sender_id, message_to_send)
        return "ok", 200
    except:
        return "ok", 200 # Messenger always expect a 200


def find_question(message):
    body = {
        "query": {
            "more_like_this": {
                "fields": ["value"],
                "like": message,
                "min_term_freq": 1,
                "min_doc_freq": 1,
                "analyzer": "english"
            }
        },
        "size": 1
    }
    response = ES.search(index=INDEX_NAME, doc_type="question", body=body)
    if response["hits"]["total"] == 0:
        return 11  # Fall back answer
    else:
        return int(response["hits"]["hits"][0]["_parent"])


def answer_management(answer, user_query):
    if answer["_id"] == "8":
        youtube_query = answer["_source"]["url_API"].format("UCJFp8uSYCjXOMnkUyb3CQ3Q", os.environ['YOUTUBE_API_KEY'])
        response = requests.get(youtube_query)
        video = random.choice([item["id"]["videoId"] for item in response.json()["items"]])
        messages = [answer["_source"]["value"], answer["_source"]["url"].format(video)]
    elif answer["_id"] == "10":
        if " in " not in user_query:
            messages = ["I didn't quite get the city. Ask me something like: What is the weather in Hong Kong?"]
        else:
            translator = str.maketrans('', '', string.punctuation)
            city = user_query.split(" in ")[1].translate(translator).replace(" ", "%20")
            log(answer["_source"]["url_API"].format(city))
            response = requests.get(answer["_source"]["url_API"].format(city))
            log(response.json())
            forecast = response.json()["query"]["results"]["channel"]["item"]["forecast"][0]
            log(forecast)
            messages = [answer["_source"]["value"].format(city,forecast["date"],
                        (forecast["high"] - 32)/1.8, (int(forecast["low"]) - 32)/1.8, forecast["text"])]
    else:
        messages = [answer["_source"]["value"]]
    return messages


def send_message(recipient_id, messages):
    for message in messages:
        log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message))

        params = {
            "access_token": os.environ["PAGE_ACCESS_TOKEN"]
        }
        headers = {
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message
            }
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            log(r.status_code)
            log(r.text)


def log(msg, *args, **kwargs):
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = str(msg).format(*args, **kwargs)
        print("{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)