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
    """Polls Tracksolid for the latest device locations."""

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
        self._imeis = imeis

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest location data for all tracked IMEIs."""
        try:
            locations = await self._client.async_get_locations(self._imeis)
        except TracksolidAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except TracksolidApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

        # Index by IMEI for easy lookup
        return {str(loc.get("imei", loc.get("devImei", ""))): loc for loc in locations}
