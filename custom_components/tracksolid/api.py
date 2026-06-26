"""Tracksolid Pro API client — uses the web app's own /v3/new/ backend."""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    ENDPOINT_GET_CURRENT_USER,
    ENDPOINT_GET_DEVICES,
    ENDPOINT_GET_GROUPS,
    ENDPOINT_GET_NODE_LIST,
    ENDPOINT_LOGIN,
    TOKEN_TTL,
)

_LOGGER = logging.getLogger(__name__)


class TracksolidAuthError(Exception):
    """Raised when authentication fails."""


class TracksolidApiError(Exception):
    """Raised when the API returns an unexpected error."""


class TracksolidApiClient:
    """Async client for the Tracksolid Pro web API.

    Authenticates with email + MD5(password) and receives a JWT Bearer token.
    No developer appKey or appSecret required.
    """

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._username = username
        self._password = password
        self._session = session

        self._token: str | None = None
        self._token_obtained_at: float = 0.0
        self._user_id: int | None = None
        self._base_url: str = API_BASE_URL

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_ensure_token(self) -> None:
        """Ensure we have a valid JWT token, re-authenticating if expired."""
        if self._token and time.monotonic() - self._token_obtained_at < TOKEN_TTL:
            return
        await self._async_login()

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return all devices with their current location data."""
        await self.async_ensure_token()

        # Get all organisation groups for this user
        groups = await self._async_get_groups()
        if not groups:
            _LOGGER.warning("No device groups found for account")
            return []

        devices: list[dict[str, Any]] = []
        for group in groups:
            org_id = group.get("id", "")
            batch = await self._async_get_devices_for_group(org_id)
            devices.extend(batch)

        # De-duplicate by IMEI in case device appears in multiple groups
        seen: set[str] = set()
        unique = []
        for d in devices:
            imei = str(d.get("imei", ""))
            if imei and imei not in seen:
                seen.add(imei)
                unique.append(d)

        return unique

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def _async_login(self) -> None:
        """Log in and store the JWT Bearer token."""
        md5_password = hashlib.md5(self._password.encode()).hexdigest()
        _LOGGER.debug("Logging in to Tracksolid Pro as %s", self._username)

        # Try MD5-hashed password first (as seen in the web app HAR).
        # Some accounts/regions may expect plaintext — fall back if denied.
        for password_attempt in (md5_password, self._password):
            payload = {
                "account": self._username,
                "password": password_attempt,
                "language": "en",
                "validCode": "",
                "nodeId": "",
            }
            try:
                data = await self._async_post(ENDPOINT_LOGIN, payload, authenticated=False)
                break  # success
            except TracksolidAuthError:
                if password_attempt is self._password:
                    raise  # both attempts failed
                _LOGGER.debug("MD5 password rejected, retrying with plaintext")

        token = data.get("token")
        if not token:
            raise TracksolidAuthError("Login succeeded but no token was returned")

        self._token = token
        self._token_obtained_at = time.monotonic()

        # Decode user ID from JWT payload (no signature validation needed)
        import base64, json as _json
        try:
            parts = token.split(".")
            padded = parts[1] + "=="
            jwt_payload = _json.loads(base64.b64decode(padded).decode())
            self._user_id = int(jwt_payload.get("accountId", 0))
        except Exception:
            _LOGGER.warning("Could not decode accountId from JWT")

        # If the server wants us to use a different node, switch to it
        target_node_id = data.get("targetNodeId")
        if target_node_id:
            await self._async_switch_node(target_node_id)

        _LOGGER.debug("Logged in, accountId=%s", self._user_id)

    async def _async_switch_node(self, target_node_id: Any) -> None:
        """Switch to the correct regional node if login response requests it."""
        try:
            nodes = await self._async_post(ENDPOINT_GET_NODE_LIST, {}, authenticated=True)
            if not isinstance(nodes, list):
                return
            for node in nodes:
                if str(node.get("id")) == str(target_node_id):
                    outer = node.get("nodeUrlOuter") or node.get("nodeUrl")
                    if outer:
                        _LOGGER.info("Switching to regional node: %s", outer)
                        self._base_url = outer.rstrip("/")
                        # Re-authenticate against the correct node
                        self._token = None
                        await self._async_login()
                    return
        except Exception as err:
            _LOGGER.debug("Node switch failed (non-fatal): %s", err)

    # ------------------------------------------------------------------
    # Device data
    # ------------------------------------------------------------------

    async def _async_get_groups(self) -> list[dict[str, Any]]:
        """Return all device groups for the logged-in user."""
        body = {
            "type": "NORMAL",
            "userId": self._user_id,
            "userType": 3,
            "keyword": "",
            "isNewMcType": "0",
        }
        result = await self._async_post(ENDPOINT_GET_GROUPS, body)
        if isinstance(result, list):
            return result
        return result.get("list", []) if isinstance(result, dict) else []

    async def _async_get_devices_for_group(
        self, org_id: str
    ) -> list[dict[str, Any]]:
        """Return all devices in a group, including current location data."""
        body = {
            "imei": "",
            "startRow": "0",
            "userType": 3,
            "userId": self._user_id,
            "orgId": org_id,
            "siftType": "",
            "sortType": "",
            "sortRule": "",
            "isNewMcType": "0",
            "videoEntry": "",
            "type": "NORMAL",
            "searchStatus": "ALL",
        }
        result = await self._async_post(ENDPOINT_GET_DEVICES, body)
        if isinstance(result, list):
            return result
        return result.get("list", []) if isinstance(result, dict) else []

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _async_post(
        self,
        endpoint: str,
        body: dict[str, Any],
        authenticated: bool = True,
    ) -> Any:
        url = f"{self._base_url}{endpoint}"
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.tracksolidpro.com",
            "Referer": "https://www.tracksolidpro.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        if authenticated and self._token:
            headers["Authorization"] = self._token

        _LOGGER.debug("POST %s", endpoint)
        try:
            async with self._session.post(
                url,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                _LOGGER.debug("Response HTTP %s from %s", resp.status, endpoint)
                if resp.status == 401:
                    raise TracksolidAuthError("Received 401 — token expired")
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except TracksolidAuthError:
            raise
        except aiohttp.ClientError as err:
            raise TracksolidApiError(f"HTTP error on {endpoint}: {err}") from err

        code = payload.get("code")
        msg = payload.get("msg", payload.get("message", ""))

        _LOGGER.debug("Response code=%s msg=%s payload=%s", code, msg, payload)

        # Both 0 and 10000 mean success in different parts of the API
        if code in (0, 10000, "0", "10000"):
            return payload.get("data", payload.get("result", {}))

        if code in (
            401, 1001, 1002, 1003, 20001,
            "401", "1001", "1002", "1003", "20001",
        ):
            raise TracksolidAuthError(f"Auth error {code}: {msg}")

        raise TracksolidApiError(f"API error {code}: {msg}")
