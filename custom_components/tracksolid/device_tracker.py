"""Device tracker platform for Tracksolid Pro."""
from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IMEIS, COORDINATOR, DOMAIN, STATUS_MOVING
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
    """Represents a tracked vehicle on the HA map."""

    _attr_name = None  # Entity name = device name

    def __init__(self, coordinator: TracksolidCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei)
        self._attr_unique_id = f"{imei}_tracker"

    @property
    def source_type(self) -> SourceType:
        pos = self._device_data.get("positionType", "GPS")
        return SourceType.GPS if str(pos).upper() == "GPS" else SourceType.GPS

    @property
    def latitude(self) -> float | None:
        try:
            return float(self._device_data["lat"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        try:
            return float(self._device_data["lng"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def location_accuracy(self) -> int:
        # GPSSignal: 1–4 bars; gpsNum: satellite count
        try:
            sats = int(self._device_data.get("gpsNum", 0) or 0)
        except (ValueError, TypeError):
            sats = 0
        if sats >= 8:
            return 5
        if sats >= 4:
            return 15
        return 50

    @property
    def extra_state_attributes(self) -> dict:
        d = self._device_data
        return {
            "imei": self._imei,
            "speed": d.get("speed"),
            "direction": d.get("direction"),
            "status": d.get("status"),
            "gps_time": d.get("gpsTime"),
            "heartbeat_time": d.get("hbTime"),
            "satellites": d.get("gpsNum"),
            "gps_signal": d.get("GPSSignal"),
            "position_type": d.get("positionType"),
            "ignition": d.get("acc") == "1",
            "device_type": d.get("mcTypeAlias", d.get("mcType")),
        }
