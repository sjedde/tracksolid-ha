"""DataUpdateCoordinator for Tracksolid Pro."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TracksolidApiClient, TracksolidApiError, TracksolidAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TracksolidCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls Tracksolid Pro for the latest device locations and status."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TracksolidApiClient,
        imeis: list[str],
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self._imeis = set(imeis)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest device data, indexed by IMEI."""
        try:
            devices = await self._client.async_get_devices()
        except TracksolidAuthError as err:
            # Force re-auth on next call
            self._client._token = None
            raise UpdateFailed(f"Authentication error: {err}") from err
        except TracksolidApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

        result: dict[str, Any] = {}
        for device in devices:
            imei = str(device.get("imei", ""))
            if not imei:
                continue
            # Only track IMEIs the user selected during setup
            if imei in self._imeis:
                result[imei] = device

        return result
