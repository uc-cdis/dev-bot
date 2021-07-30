import slack
import os
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter

from oncall_manager import OnCallManager

app = Flask(__name__)

signing_secret = os.environ["SIGNING_SECRET"]
slack_event_adapter = SlackEventAdapter(signing_secret.strip(), "/slack/events", app)

slack_token = os.environ["SLACK_API_TOKEN"]
client = slack.WebClient(
    token=slack_token.strip(), base_url="https://cdis.slack.com/api/"
)
BOT_ID = client.api_call("auth.test")["user_id"]


def list_all_commands():
    all_commands = commands_map.keys()
    return "here are all the commands available in dev-bot:\n {}".format(
        ",".join(all_commands)
    )


commands_map = {
    "help": {
        "args": "list all commands",
        "example": "@qa-bot help",
        "call": list_all_commands,
    },
    "read-oncall-log": {
        "args": "num_of_entries [asc|desc] (asc by default)",
        "example": "@dev-bot read-oncall-log 3 asc",
        "call": OnCallManager().read_oncall_log,
    },
    "add-oncall-log-entry": {
        "args": "issue_description",
        "example": "@dev-bot add-oncall-log-entry typo in manifest.json",
        "call": OnCallManager().add_oncall_log_entry,
    },
}


def process_command(command, args):
    # process args to handle whitespaces inside json blocks
    entered_json_block_at_index = None
    for i, a in enumerate(args):
        if "{" in a and "}" not in a:
            # print('Entered an incomplete JSON block. We have whitespaces in one of the json values')
            entered_json_block_at_index = i
            continue
        if entered_json_block_at_index:
            args[entered_json_block_at_index] += " " + args[i]


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    log.debug(f"event: {event}")
    log.debug(f"channel_id: {channel_id}")
    log.debug(f"user_id: {user_id}")
    log.debug(f"text: {text}")

    if BOT_ID != user_id:
        if "UP60ZEQJ0" in text:
            log.info("user {} just sent a msg: {}".format(user, the_msg))

            raw_command = text.replace("\xa0", " ")
            raw_command = raw_command.replace("“", '"').replace("”", '"')
            msg_parts_split = raw_command.split(" ")
            msg_parts = list(filter(None, msg_parts_split))
            # identify command
            if len(msg_parts) > 1:
                command = msg_parts[1]
                args = msg_parts[2:]
                bot_reply = process_command(command, args)
            else:
                bot_reply = """
Usage instructions: *@dev-bot <command>* \n
e.g., @dev-bot command
          _visit https://github.com/uc-cdis/dev-bot to learn more_
                """
            client.chat_postMessage(channel=channel_id, text=bot_reply)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
