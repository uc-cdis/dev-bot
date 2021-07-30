import slack
import os
import logging
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

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)


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

    if entered_json_block_at_index:
        args = args[: entered_json_block_at_index + 1]
        log.debug("args: {}".format(args))

    # execute command
    if command in commands_map.keys():
        log.info("args: " + str(args))
        if len(args) >= 1 and args[0] == "help":
            return f"""instructions for {command}: \n
args:  {commands_map[command]['args']}
example:  {commands_map[command]['example']}
      """
            return help_txt
        else:
            try:
                return commands_map[command]["call"](*args)
            except TypeError as te:
                return str(te)
            except Exception as e:
                log.error(e)
                traceback.print_exc()
                return "something went wrong. Contact the QA team"
    else:
        return "command not recognized. :thisisfine:"


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
        if "<@U029984C71C>" in text:
            log.info(f"user {user_id} just sent a msg: {text}")

            raw_command = text.replace("\xa0", " ")
            log.debug(f"raw_command: {raw_command}")
            raw_command = raw_command.replace("“", '"').replace("”", '"')
            log.debug(f"raw_command: {raw_command}")
            msg_parts_split = raw_command.split(" ")
            log.debug(f"msg_parts_split: {msg_parts_split}")
            msg_parts = list(filter(None, msg_parts_split))
            log.debug(f"msg_parts: {msg_parts}")
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
