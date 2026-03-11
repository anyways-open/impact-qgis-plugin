import json
import webbrowser
from typing import Optional
from urllib import request, parse

from qgis.PyQt.QtCore import QTimer, pyqtSignal, QObject
from qgis.core import QgsMessageLog, Qgis

from .TokenStorage import TokenStorage
from ..settings import OIDC_AUTHORITY, OIDC_CLIENT_ID, OIDC_SCOPES, MESSAGE_CATEGORY


class DeviceFlowAuth(QObject):
    token_received = pyqtSignal(str)  # emits the access token
    login_failed = pyqtSignal(str)    # emits error message
    logged_out = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._storage = TokenStorage()
        self._poll_timer = None
        self._device_code = None
        self._token_endpoint = None
        self._device_authorization_endpoint = None
        self._userinfo_endpoint = None
        self._poll_interval = 5

    @property
    def is_logged_in(self) -> bool:
        tokens = self._storage.load()
        return bool(tokens["access_token"]) and (
            not self._storage.is_expired() or bool(tokens["refresh_token"])
        )

    def get_access_token(self) -> Optional[str]:
        tokens = self._storage.load()
        if not tokens["access_token"]:
            return None
        if not self._storage.is_expired():
            return tokens["access_token"]
        if tokens["refresh_token"]:
            if self._refresh_token(tokens["refresh_token"]):
                return self._storage.load()["access_token"]
        return None

    def _discover_endpoints(self):
        url = f"{OIDC_AUTHORITY}/.well-known/openid-configuration"
        try:
            resp = request.urlopen(request.Request(url), timeout=10)
            config = json.loads(resp.read().decode("utf-8"))
            self._token_endpoint = config["token_endpoint"]
            self._device_authorization_endpoint = config["device_authorization_endpoint"]
            self._userinfo_endpoint = config.get("userinfo_endpoint")
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"OIDC discovery failed: {e}", MESSAGE_CATEGORY, Qgis.Warning)
            return False

    def start_device_flow(self) -> Optional[dict]:
        if not self._discover_endpoints():
            self.login_failed.emit("Could not connect to identity server.")
            return None

        data = parse.urlencode({
            "client_id": OIDC_CLIENT_ID,
            "scope": OIDC_SCOPES,
        }).encode("utf-8")

        try:
            resp = request.urlopen(
                request.Request(self._device_authorization_endpoint, data=data),
                timeout=10,
            )
            flow = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            QgsMessageLog.logMessage(f"Device authorization failed: {e}", MESSAGE_CATEGORY, Qgis.Warning)
            self.login_failed.emit(f"Device authorization failed: {e}")
            return None

        self._device_code = flow["device_code"]
        self._poll_interval = flow.get("interval", 5)

        verification_uri = flow.get("verification_uri_complete") or flow.get("verification_uri", "")
        if verification_uri:
            webbrowser.open(verification_uri)

        self._start_polling()

        return {
            "user_code": flow.get("user_code", ""),
            "verification_uri": flow.get("verification_uri", ""),
            "verification_uri_complete": flow.get("verification_uri_complete", ""),
            "expires_in": flow.get("expires_in", 300),
        }

    def _start_polling(self):
        self._stop_polling()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_for_token)
        self._poll_timer.start(self._poll_interval * 1000)

    def _stop_polling(self):
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer.deleteLater()
            self._poll_timer = None

    def _poll_for_token(self):
        data = parse.urlencode({
            "client_id": OIDC_CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": self._device_code,
        }).encode("utf-8")

        try:
            resp = request.urlopen(
                request.Request(self._token_endpoint, data=data),
                timeout=10,
            )
            token_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            error_body = ""
            if hasattr(e, "read"):
                try:
                    error_body = json.loads(e.read().decode("utf-8"))
                except Exception:
                    self._stop_polling()
                    self.login_failed.emit(f"Token request failed: {e}")
                    return

            if isinstance(error_body, dict):
                error = error_body.get("error", "")
                if error == "authorization_pending":
                    return  # keep polling
                if error == "slow_down":
                    self._poll_interval += 5
                    self._stop_polling()
                    self._poll_timer = QTimer(self)
                    self._poll_timer.timeout.connect(self._poll_for_token)
                    self._poll_timer.start(self._poll_interval * 1000)
                    return
                if error == "expired_token":
                    self._stop_polling()
                    self.login_failed.emit("Login timed out. Please try again.")
                    return

            self._stop_polling()
            error_desc = ""
            if isinstance(error_body, dict):
                error_desc = error_body.get("error_description", str(e))
            else:
                error_desc = str(e)
            self.login_failed.emit(f"Login failed: {error_desc}")
            return

        self._stop_polling()
        self._storage.store(
            token_data["access_token"],
            token_data.get("refresh_token", ""),
            token_data.get("expires_in", 3600),
        )
        self.token_received.emit(token_data["access_token"])

    def try_restore_session(self) -> bool:
        """Try to restore a previous session from stored tokens.

        If the access token is expired, attempts a refresh.
        Clears stored tokens if the refresh token is rejected by the server.
        Returns True if a valid access token is available.
        """
        token = self.get_access_token()
        return token is not None

    def _refresh_token(self, refresh_token: str) -> bool:
        if self._token_endpoint is None:
            if not self._discover_endpoints():
                return False

        data = parse.urlencode({
            "client_id": OIDC_CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }).encode("utf-8")

        try:
            resp = request.urlopen(
                request.Request(self._token_endpoint, data=data),
                timeout=10,
            )
            token_data = json.loads(resp.read().decode("utf-8"))
            self._storage.store(
                token_data["access_token"],
                token_data.get("refresh_token", refresh_token),
                token_data.get("expires_in", 3600),
            )
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Token refresh failed: {e}", MESSAGE_CATEGORY, Qgis.Warning)
            # If the server explicitly rejected the refresh token, clear stale credentials.
            # Network errors (no 'code' attr) leave tokens in storage for later retry.
            if hasattr(e, 'code') and e.code in (400, 401, 403):
                self._storage.clear()
            return False

    def logout(self):
        self._stop_polling()
        self._storage.clear()
        self.logged_out.emit()

    def get_user_name(self) -> Optional[str]:
        token = self.get_access_token()
        if not token:
            return None
        try:
            # Fetch user info from the userinfo endpoint
            if self._token_endpoint is None:
                if not self._discover_endpoints():
                    return None
            # Derive userinfo endpoint from discovery
            if not hasattr(self, '_userinfo_endpoint') or self._userinfo_endpoint is None:
                return None
            req = request.Request(self._userinfo_endpoint)
            req.add_header("Authorization", f"Bearer {token}")
            resp = request.urlopen(req, timeout=10)
            userinfo = json.loads(resp.read().decode("utf-8"))
            return userinfo.get("name") or userinfo.get("preferred_username") or userinfo.get("email") or userinfo.get("sub")
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to get user name: {e}", MESSAGE_CATEGORY, Qgis.Warning)
            return None
