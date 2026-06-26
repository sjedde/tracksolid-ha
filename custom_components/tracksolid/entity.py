"""Base entity for Tracksolid Pro."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TracksolidCoordinator


class TracksolidEntity(CoordinatorEntity[TracksolidCoordinator]):
    """Base class for all Tracksolid entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TracksolidCoordinator, imei: str) -> None:
        super().__init__(coordinator)
        self._imei = imei

    @property
    def _device_data(self) -> dict:
        return self.coordinator.data.get(self._imei, {})

    @property
    def device_info(self) -> DeviceInfo:
        data = self._device_data
        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=data.get("deviceName", data.get("name", f"Tracksolid {self._imei}")),
            manufacturer="Jimi IoT",
            model=data.get("deviceType", data.get("model", "GPS Tracker")),
            serial_number=self._imei,
        )
