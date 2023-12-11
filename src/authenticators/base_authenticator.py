from functools import wraps
from abc import ABC, abstractmethod


class BaseAuthenticator(ABC):
    @abstractmethod
    def authenticate(self, request) -> bool:
        pass

    @abstractmethod
    def get_level(self) -> int:
        pass
