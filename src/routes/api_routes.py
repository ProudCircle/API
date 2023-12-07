import os
import aiosqlite
import logging as logger

from quart import Blueprint, jsonify
from ..rate_limiter import RateLimiter
from ..authenticators.dev_authenticator import DevAuthenticator

api_blueprint = Blueprint('api', __name__, url_prefix='/api')
authenticator = DevAuthenticator()
ratelimiter = RateLimiter({})


@api_blueprint.before_app_serving
async def before_serving():
    db_path = os.getenv("DB_PATH")
    logger.debug(f"Opening connection to database at {db_path}...")
    try:
        api_blueprint.db = await aiosqlite.connect(db_path)
        logger.debug("Connection established")
    except Exception as e:
        logger.critical("Could not establish connection with database", e)
        exit(12)


@api_blueprint.after_app_serving
async def after_serving():
    logger.debug("Closing database connection...")
    await api_blueprint.db.close()
    logger.debug("Database connection closed")


@api_blueprint.get('/')
@authenticator.require(0)
async def api():
    return jsonify({'success': True, 'details': 'Passed Authentication'})


@api_blueprint.get('/status')
async def hello():
    return jsonify({'success': True, 'status': 'debug'})


@api_blueprint.get('/test')
@ratelimiter.set(3)
async def doit():
    return {'test': 'test'}
