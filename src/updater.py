import json
import time
import uuid
import logging
import sqlite3
import requests
import threading

from datetime import datetime

from src.util import add_hyphens_to_uuid
from src.guild import HypixelGuild


class DataUpdater:
    def __init__(self, key, db_path, guild_id):
        self.status_lock = threading.Lock()
        self._key = key
        self._db_path = db_path
        self._guild_id = guild_id
        self.step_handler = StepHandler()
        self.current_task_id = None

        # TODO: Check API Key and connection to database stuff
        # Open this connection somewhere else as to only allow logic to happen in this thread
        self.connection = sqlite3.connect(self._db_path)
        self.cursor = self.connection.cursor()

        # Check database stuff
        self._create_gexp_table()

    def _create_gexp_table(self):
        logging.debug("Creating Gexp Table")

        create_table_command = """
        CREATE TABLE IF NOT EXISTS expHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            timestamp INTEGER NOT NULL,
            date TEXT NOT NULL,
            uuid TEXT NOT NULL,
            amount INTEGER NOT NULL
        );
        """
        connection = sqlite3.connect(self._db_path)
        cursor = connection.cursor()
        cursor.execute(create_table_command)

        create_trigger_command_uuid = """
        CREATE TRIGGER IF NOT EXISTS format_uuid_trigger
        AFTER INSERT ON expHistory
        BEGIN
            UPDATE expHistory SET uuid =
                CASE
                    WHEN instr(uuid, '-') = 0 THEN
                        substr(uuid, 1, 8) || '-' ||
                        substr(uuid, 9, 4) || '-' ||
                        substr(uuid, 13, 4) || '-' ||
                        substr(uuid, 17, 4) || '-' ||
                        substr(uuid, 21)
                    ELSE
                        uuid
                END
            WHERE id = new.id;
        END;
        """
        cursor.execute(create_trigger_command_uuid)

        connection.commit()

    def _set_status(self, step, info):
        with self.status_lock:
            status = {"running": True}

    def _sync_member_gexp(self, member):
        try:
            _uuid = add_hyphens_to_uuid(member.uuid)
            # ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  ^
            # Note, the API will return uuid's without hyphens, the table
            # only stores hyphenated uuids, so if you search a table for an unhyphenated uuid, the result will be None,
            # and it will try to create a new entry in the table with the unhyphenated uuid, further complicating the
            # issue.
            xp_history = member.exp_history

            for date, amount in xp_history.items():
                self.cursor.execute("SELECT * FROM expHistory WHERE uuid=? AND date=?", (_uuid, date))
                result = self.cursor.fetchone()
                # Result Example:
                # (293237, 1686528186, '2023-06-11', '5328930e-d411-49cb-90ad-4e5c7b27dd86', 0)
                # If result does not exist, result will be None
                time_now = int(time.time())
                if result is None:
                    # Create Data
                    self.cursor.execute("INSERT INTO expHistory (timestamp, date, uuid, amount) VALUES (?, ?, ?, ?)", (
                        time_now, date, _uuid, amount))
                else:
                    # Ensure data is correct
                    recorded_amount = result[4]
                    if recorded_amount != amount:
                        # Fix un-synced data
                        self.cursor.execute("UPDATE expHistory SET timestamp=?, amount=? WHERE uuid=? AND date=?", (
                            time_now, amount, _uuid, date))

        except Exception as e:
            logging.fatal(f"Encountered fatal exception syncing exp history for {member}: {e}")
            return False
        return True

    def _run_update(self):
        self.current_task_id = uuid.uuid4()
        logging.debug(f"Starting database update task - '{self.current_task_id}.tid'")
        self.step_handler.task_id = self.current_task_id
        self.step_handler.start_step("initializing")
        # Init all the stuff I need (check db connection, test API key)
        self.step_handler.end_step()

        logging.debug(f"Fetching Data from Hypixel API... - '{self.current_task_id}.tid'")
        self.step_handler.start_step("fetch guild data")
        guild_data = self._fetch_guild_data()
        self.step_handler.end_step()

        logging.debug(f"Updating EXP History... - '{self.current_task_id}.tid'")
        self.step_handler.start_step("sync gexp")
        self._sync_gexp(guild_data)
        self.step_handler.end_step()

        self.step_handler.finish()

    def _fetch_guild_data(self):
        url = f'https://api.hypixel.net/guild?id={self._guild_id}'
        status_code = None
        response = {
            "success": False,
            "cause": "Internal Unknown Error",
            "task_id": self.current_task_id,
            "status_code": status_code
        }
        try:
            response = requests.get(url, headers={'API-Key': self._key})
            status_code = response.status_code
        except Exception as e:
            self.step_handler.end_step(
                errors=["Failed 'GET' request"],
                details={"status_code": status_code, "url": url}
            )
            raise e

        data = response.json()

        if status_code != 200:
            self.step_handler.end_step(
                errors=["Failed 'GET' request"],
                details={"status_code": status_code, "url": url, "cause": data.get("cause", "Unknown")}
            )
            raise Exception("Incorrect Status Code: ", status_code)

        api_success = data.get('success', False)
        self.step_handler.update_step_details({
            'api_success_response': api_success,
            'status_code': status_code
        })

        guild_json = data.get('guild', None)
        # Try casting first to catch errors?
        hypixel_guild = HypixelGuild(guild_json)
        return hypixel_guild

    def _sync_gexp(self, guild_data):
        members_synced = 0
        for member in guild_data.members.members:
            if self._sync_member_gexp(member):
                members_synced = members_synced + 1
            else:
                logging.error(f"Unknown error syncing member: '{member.uuid}'")
        self.step_handler.update_step_details(details={"members_updated": members_synced})
        self.connection.commit()


class StepHandler:
    def __init__(self):
        self.data = {}
        self.step_history = []
        self.current_step = {}
        self.task_id = None
        self._start_time = None

    def start_step(self, name):
        start_time = datetime.now().timestamp()
        self._start_time = start_time

        if self.current_step:
            self.step_history.append(self.current_step)

        self.current_step = {
            "start_time": start_time,
            "name": name,
            "end_time": None,
            "duration": None,
            "has_finished": False,
            "details": {}
        }

    def update_step_details(self, details: dict):
        if self.current_step:
            # Update the details of the current step
            self.current_step["details"].update(details)

    def end_step(self, errors: list = [], details: dict = None):
        end_time = datetime.now().timestamp()
        self.current_step["end_time"] = end_time
        self.current_step["duration"] = end_time - self.current_step["start_time"]
        self.current_step["has_finished"] = True
        if errors:
            self.current_step["errors"] = errors

        if details is not None:
            self.current_step["details"] = details

    def finish(self, details: dict = None):
        self.start_step("finished")
        now = datetime.now().timestamp()
        self.current_step = {
            "start_time": self._start_time,
            "end_time": now,
            "duration": self._start_time - now,
            "has_finished": True,
        }
        if details:
            self.current_step["details"] = details


    def json(self):
        self.data = {
            "task_id": str(self.task_id),
            "current_step": self.current_step,
            "step_history": self.step_history
        }
        return json.dumps(self.data, indent=2)
