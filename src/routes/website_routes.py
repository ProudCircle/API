from quart import Blueprint

website_blueprint = Blueprint('web', __name__)

@website_blueprint.get('/')
async def index():
    return "Welcome to my web server!"
