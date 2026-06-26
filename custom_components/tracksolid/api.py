"""Tracksolid Pro API client."""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .const import (
    API_VERSION,
    METHOD_DEVICE_LIST,
    METHOD_DEVICE_LOCATION,
    METHOD_TOKEN_GET,
    METHOD_TOKEN_REFRESH,
    PLATFORM_APP_KEY,
    PLATFORM_APP_SECRET,
    REGION_URLS,
    TOKEN_REFRESH_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


class TracksolidAuthError(Exception):
    """Raised when authentication fails."""


class TracksolidApiError(Exception):
    """Raised when the API returns an error."""


class TracksolidApiClient:
    """Async client for the Tracksolid Pro Open API."""

    def __init__(
        self,
        username: str,
        password: str,
        region: str,
        session: aiohttp.ClientSession,
        app_key: str | None = None,
        app_secret: str | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._base_url = REGION_URLS[region]
        self._session = session
        self._app_key = app_key or PLATFORM_APP_KEY
        self._app_secret = app_secret or PLATFORM_APP_SECRET

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def async_ensure_token(self) -> None:
        """Ensure we have a valid access token, refreshing or obtaining one."""
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return
        if self._refresh_token:
            await self._async_refresh_token()
        else:
            await self._async_get_token()

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return all devices for the account."""
        await self.async_ensure_token()
        result = await self._async_request(
            METHOD_DEVICE_LIST,
            {"pageIndex": 1, "pageSize": 100},
        )
        return result.get("list", [])

    async def async_get_locations(self, imeis: list[str]) -> list[dict[str, Any]]:
        """Return the latest location for one or more IMEIs."""
        await self.async_ensure_token()
        result = await self._async_request(
            METHOD_DEVICE_LOCATION,
            {"imeis": ",".join(imeis)},
        )
        if isinstance(result, list):
            return result
        return result.get("list", result.get("data", []))

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def _async_get_token(self) -> None:
        """Obtain a new access token using username + password."""
        md5_password = hashlib.md5(self._password.encode()).hexdigest()
        data = await self._async_request(
            METHOD_TOKEN_GET,
            {
                "user_id": self._username,
                "user_pwd_md5": md5_password,
                "expires_in": 7200,
            },
            authenticated=False,
        )
        self._access_token = data["accessToken"]
        self._refresh_token = data.get("refreshToken")
        self._token_expires_at = time.monotonic() + TOKEN_REFRESH_THRESHOLD
        _LOGGER.debug("Obtained new Tracksolid access token")

    async def _async_refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        try:
            data = await self._async_request(
                METHOD_TOKEN_REFRESH,
                {"refreshToken": self._refresh_token},
                authenticated=False,
            )
            self._access_token = data["accessToken"]
            self._refresh_token = data.get("refreshToken", self._refresh_token)
            self._token_expires_at = time.monotonic() + TOKEN_REFRESH_THRESHOLD
            _LOGGER.debug("Refreshed Tracksolid access token")
        except TracksolidApiError:
            _LOGGER.warning("Token refresh failed, re-authenticating")
            self._refresh_token = None
            await self._async_get_token()

    # ------------------------------------------------------------------
    # Request building & signing
    # ------------------------------------------------------------------

    def _build_params(
        self, method: str, extra: dict[str, Any], authenticated: bool
    ) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        params: dict[str, Any] = {
            "app_key": self._app_key,
            "format": "json",
            "method": method,
            "sign_method": "md5",
            "timestamp": timestamp,
            "v": API_VERSION,
        }
        if authenticated and self._access_token:
            params["access_token"] = self._access_token
        params.update(extra)
        params["sign"] = self._sign(params)
        return params

    def _sign(self, params: dict[str, Any]) -> str:
        """Compute the MD5 signature.

        Format: md5( appSecret + key1value1key2value2... (alphabetical) + appSecret )
        Result is a 32-character uppercase hex string.
        """
        sorted_str = "".join(
            f"{k}{v}" for k, v in sorted(params.items()) if v is not None
        )
        raw = f"{self._app_secret}{sorted_str}{self._app_secret}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    async def _async_request(
        self,
        method: str,
        extra: dict[str, Any],
        authenticated: bool = True,
    ) -> dict[str, Any]:
        params = self._build_params(method, extra, authenticated)
        _LOGGER.debug("Tracksolid API request: %s", method)
        try:
            async with self._session.post(
                self._base_url, data=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise TracksolidApiError(f"HTTP error calling {method}: {err}") from err

        code = str(payload.get("code", ""))
        message = payload.get("message", "unknown")
        _LOGGER.debug("Tracksolid API response: code=%s message=%s", code, message)

        if code in ("1001", "1002", "1003"):
            raise TracksolidAuthError(
                f"Authentication failed (code {code}): {message}"
            )
        if code != "0":
            raise TracksolidApiError(f"API error {code}: {message}")

        return payload.get("result", payload.get("data", {}))
