from math import floor
from functools import wraps
from quart import jsonify, request


class RateLimiter:
    def __init__(self, config) -> None:
        self.config = config
        self.cache = {}

    def has_requests_remaining(self, request, limit: int):
        # Limit by ip addresses
        amount_sent = self.cache.get(request.remote_addr)
        if amount_sent:
            if amount_sent >= floor(limit):
                self.cache[request.remote_addr] = self.cache[request.remote_addr] + 0.0001
                return False
            self.cache[request.remote_addr] = self.cache[request.remote_addr] + 1
            return True
            
        self.cache[request.remote_addr] = 1
        return True

    def set(self, limit):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.has_requests_remaining(request, limit):
                    return jsonify({"success": False, "cause": "Rate Limit Exceeded", "requests": floor(self.cache.get(request.remote_addr, 0))})
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    