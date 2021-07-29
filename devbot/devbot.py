import slack
import os
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter


app = Flask(__name__)

signing_secret = os.environ["SIGNING_SECRET"]
slack_event_adapter = SlackEventAdapter(signing_secret.strip(), "/slack/events", app)

slack_token = os.environ["SLACK_API_TOKEN"]
client = slack.WebClient(token=slack_token.strip())


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = payload.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    client.chat_postMessage(channel=channel_id, text=text)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
