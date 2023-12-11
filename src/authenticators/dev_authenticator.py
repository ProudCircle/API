import random

from quart import jsonify, request
from functools import wraps
from .base_authenticator import BaseAuthenticator


class DevAuthenticator(BaseAuthenticator):
    def authenticate(self, request) -> bool:
        return random.choice([True, False])
    
    def get_level(self) -> int:
        return 0
    
    def require(self, level):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.authenticate(request):
                    return jsonify({"success": False, "cause": "Authentication failed"}), 401
                if self.get_level() < level:
                    return jsonify({"success": False, "cause": "Insufficient permissions"}), 403
                return await func(*args, **kwargs)
            return wrapper
        return decorator
