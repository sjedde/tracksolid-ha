"""Device tracker platform for Tracksolid Pro."""
from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IMEIS, COORDINATOR, DOMAIN
from .coordinator import TracksolidCoordinator
from .entity import TracksolidEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TracksolidCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    imeis: list[str] = entry.data[CONF_IMEIS]
    async_add_entities(TracksolidTracker(coordinator, imei) for imei in imeis)


class TracksolidTracker(TracksolidEntity, TrackerEntity):
    """Represents a tracked vehicle/asset."""

    _attr_name = None  # Use device name as entity name

    def __init__(self, coordinator: TracksolidCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei)
        self._attr_unique_id = f"{imei}_tracker"

    @property
    def source_type(self) -> SourceType:
        data = self._device_data
        pos_type = str(data.get("posType", data.get("locType", "1")))
        if pos_type == "1":
            return SourceType.GPS
        return SourceType.GPS  # LBS / WiFi still reported as GPS in HA

    @property
    def latitude(self) -> float | None:
        data = self._device_data
        raw = data.get("lat") or data.get("latitude")
        try:
            return float(raw) if raw is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def longitude(self) -> float | None:
        data = self._device_data
        raw = data.get("lng") or data.get("longitude")
        try:
            return float(raw) if raw is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def location_accuracy(self) -> int:
        data = self._device_data
        # Use satellite count as a rough proxy: more sats = better accuracy
        sats = int(data.get("satellites", data.get("sat", 0)) or 0)
        if sats >= 8:
            return 5
        if sats >= 4:
            return 15
        return 50

    @property
    def extra_state_attributes(self) -> dict:
        data = self._device_data
        return {
            "imei": self._imei,
            "speed": data.get("speed"),
            "direction": data.get("direction"),
            "altitude": data.get("altitude"),
            "satellites": data.get("satellites", data.get("sat")),
            "gps_time": data.get("gpsTime"),
            "positioning_type": data.get("posType", data.get("locType")),
            "device_status": data.get("deviceStatus"),
            "acc_status": data.get("accStatus"),
        }
