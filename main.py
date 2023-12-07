import os
import aiosqlite
import logging as logger  # Don't remember why I did this

from quart import Quart
from dotenv import load_dotenv

from src.config import Config
from src.updater import DataUpdater
from src.routes.api_routes import api_blueprint
from src.routes.website_routes import website_blueprint


app = Quart(__name__)


def main() -> None:
    # TODO: Ensure file structure exists before proceeding
    # TODO: Ensure dotenv vars are working correctly
    # TODO: Ensure config is okay
    logger.basicConfig(level=logger.DEBUG)
    load_dotenv()

    app.register_blueprint(api_blueprint)
    app.register_blueprint(website_blueprint)

    key = os.getenv("key")
    db_path = os.getenv("dbpath")
    guild_id = os.getenv("guildid")

    updater = DataUpdater(key, db_path, guild_id)
    updater._run_update()

    # app.run(debug=True, host='0.0.0.0', port=5000)


@app.before_serving
async def before_serving():
    db_path = os.getenv("DB_PATH")
    logger.debug(f"Opening connection to database at {db_path}...")
    try:
        app.db = await aiosqlite.connect(db_path)
        logger.debug("Connection established")
    except Exception as e:
        logger.critical("Could not establish connection with database", e)
        exit(12)


@app.after_serving
async def after_serving():
    logger.debug("Closing database connection...")
    await app.db.close()
    logger.debug("Database connection closed")


if __name__ == "__main__":
    main()

# Quart Example

# from dataclasses import dataclass
# from datetime import datetime

# from quart_schema import QuartSchema, validate_request, validate_response

# QuartSchema(app)

# @dataclass
# class TodoIn:
#     task: str
#     due: datetime | None

# @dataclass
# class Todoo(TodooIn):
#     id: int

# @app.post("/todos/")
# @validate_request(TodooIn)
# @validate_response(Todoo)
# async def create_todo(data: Todoo) -> Todoo:
#     return Todoo(id=1, task=data.task, due=data.due)

