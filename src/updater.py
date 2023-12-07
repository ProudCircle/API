import uuid
import sqlite3
import requests
import threading

from datetime import datetime


class DataUpdater:
    def __init__(self, key, db_path, guild_id):
        self.status_lock = threading.lock()
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
            "start_time": start_time,
            "task_id": task_id
            }
        )

        # TODO: Check API Key and connection to database stuff
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()

        try:
            # Key/Guild Test
            key = self._key
            guild_id = self._guild_id
            url = f'https://api.hypixel.net?guild/id={guild_id}'
            response = requests.get(url, headers={'API-Key': key})
            status_code = response.status_code
            print(f"status code: {status_code}")
        except Exception as e:
            print("Issue")
            raise(e)
        print("Done")
