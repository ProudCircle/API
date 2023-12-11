import uuid
import logging
import sqlite3
import requests
import threading

from datetime import datetime

from src.guild import HypixelGuild


class DataUpdater:
    def __init__(self, key, db_path, guild_id):
        self.status_lock = threading.Lock()
        self._key = key
        self._db_path = db_path
        self._guild_id = guild_id

    def _set_status(self, step, info):
        with self.status_lock:
            status = {"running": True}

    def _run_update(self):
        print("Starting Update")
        start_time = datetime.now().timestamp()
        task_id = uuid.uuid4()
        self._set_status('Startup', {
            "running": True,
            "step": "startup",
            "session_start_time": start_time,
            "task_id": task_id
            }
        )

        # TODO: Check API Key and connection to database stuff
        # Open this connection somewhere else as to only allow logic to happen in this thread
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()

        logging.debug("Fetching Data from Hypixel API...")
        fetch_start_time = datetime.now().timestamp()
        self._set_status('Fetching Data', {
            "running": True,
            "step": "fetching data",
            "session_start_time": start_time,
            "task_start_time": fetch_start_time,
            "task_id": task_id
        })

        try:
            # Key/Guild Test
            key = self._key
            guild_id = self._guild_id
            url = f'https://api.hypixel.net/guild?id={guild_id}'
            response = requests.get(url, headers={'API-Key': key})
            status_code = response.status_code
            if status_code != 200:
                raise Exception('Invalid response code: ' + response.__str__())
            data = response.json()
            api_success = data.get('success', False)
            guild_json = data.get('guild', None)
            if guild_json is None:
                raise Exception('Successful GET request returned invalid data')
                # Invalid API Key?

            hypixel_guild = HypixelGuild(guild_json)
        except Exception as e:
            print("Issue")
            raise e
        print("Done")
