from googleapiclient import discovery
from google.oauth2.service_account import Credentials

import json
import os
import re
import logging
import datetime
from datetime import datetime

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)


class OnCallManager:
    def __init__(self):
        """
        Interacts with APIs to speed up routine tasks
        """
        self.log_sheet_id = os.environ["SPREADSHEET_ID"]
        self.log_sheet_cells_range = os.environ["SHEET_CELLS_RANGE"]
        self.log_svc_account = os.environ["DEV_SERVICE_ACCOUNT"]
        self.log_sheet_api_scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    def add_oncall_log_entry(self, oncall_engineer_name, issue_description):
        bot_response = ""

        dateTimeObj = datetime.now()
        today_timestamp = f"{dateTimeObj.month}/{dateTimeObj.day}/{dateTimeObj.year}"

        creds = None
        # TODO: Refactor this to a google facade module
        if os.path.exists("/var/www/devbot/token.json"):
            creds = Credentials.from_service_account_file(
                "/var/www/devbot/token.json", scopes=self.log_sheet_api_scopes
            )
            delegated_credentials = creds.with_subject(self.log_svc_account)
            client = discovery.build("sheets", "v4", credentials=delegated_credentials)
        else:
            print("there is no auth token! Abort...")
            sys.exit(1)

        # Call the Sheets API
        sheet = client.spreadsheets()
        reading = (
            sheet.values()
            .get(spreadsheetId=self.log_sheet_id, range=self.log_sheet_cells_range)
            .execute()
        )
        values = reading.get("values", [])

        next_row_with_empty_issue_description = 0
        if logging.DEBUG:
            if not values:
                print("No data found.")
            else:
                for row in values:
                    # Column D is the one where the issue description should be
                    # print(len(row[3]))
                    if len(row[3]) == 0:
                        print("found empty row. Adding issue description here...")
                    else:
                        print(f"debugging: Row data: {row}")

        # Date | Dev | Slack Msg | Issue | Fix | Improvement Ideas / Ticket
        values.append(
            [today_timestamp, oncall_engineer_name, "", issue_description, "", ""]
        )
        cell_update_body = {"values": values}
        writing = (
            client.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.log_sheet_id,
                range=self.log_sheet_cells_range,
                valueInputOption="USER_ENTERED",
                body=cell_update_body,
            )
            .execute()
        )

        return bot_response


if __name__ == "__main__":
    result = OnCallManager().add_oncall_log_entry(
        "Joe Bloggs", "TESTING TESTING, THIS IS A TEST!!!"
    )
    print(result)
