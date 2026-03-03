import time

from qgis.core import QgsSettings


_PREFIX = "anyways.eu/impact/auth/"


class TokenStorage:
    def __init__(self):
        self._settings = QgsSettings()

    def store(self, access_token: str, refresh_token: str, expires_in: int):
        self._settings.setValue(f"{_PREFIX}access_token", access_token)
        self._settings.setValue(f"{_PREFIX}refresh_token", refresh_token)
        self._settings.setValue(f"{_PREFIX}expires_at", int(time.time()) + expires_in)

    def load(self) -> dict:
        return {
            "access_token": self._settings.value(f"{_PREFIX}access_token", ""),
            "refresh_token": self._settings.value(f"{_PREFIX}refresh_token", ""),
            "expires_at": int(self._settings.value(f"{_PREFIX}expires_at", 0)),
        }

    def is_expired(self) -> bool:
        expires_at = int(self._settings.value(f"{_PREFIX}expires_at", 0))
        return time.time() >= (expires_at - 30)

    def clear(self):
        self._settings.remove(f"{_PREFIX}access_token")
        self._settings.remove(f"{_PREFIX}refresh_token")
        self._settings.remove(f"{_PREFIX}expires_at")
