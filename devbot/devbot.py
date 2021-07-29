import slack
import os
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter


app = Flask(__name__)

signing_secret = os.environ["SIGNING_SECRET"]
slack_event_adapter = SlackEventAdapter(signing_secret.strip(), "/slack/events", app)

slack_token = os.environ["SLACK_API_TOKEN"]
client = slack.WebClient(
    token=slack_token.strip(), base_url="https://cdis.slack.com/api/"
)
BOT_ID = client.api_call("auth.test")["user_id"]


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    print(f"event: {event}")
    print(f"channel_id: {channel_id}")
    print(f"user_id: {user_id}")
    print(f"text: {text}")

    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id, text=text)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
