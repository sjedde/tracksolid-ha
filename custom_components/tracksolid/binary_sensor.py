"""Binary sensor platform for Tracksolid Pro."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IMEIS, COORDINATOR, DOMAIN, STATUS_MOVING
from .coordinator import TracksolidCoordinator
from .entity import TracksolidEntity


@dataclass(frozen=True)
class TracksolidBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with a data key."""
    data_key: str = ""
    true_value: Any = None


BINARY_SENSOR_TYPES: tuple[TracksolidBinarySensorDescription, ...] = (
    TracksolidBinarySensorDescription(
        key="vibration",
        name="Vibration",
        device_class=BinarySensorDeviceClass.VIBRATION,
        icon="mdi:vibrate",
        data_key="_alarm_vibration",
    ),
    TracksolidBinarySensorDescription(
        key="ignition",
        name="Ignition",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
        data_key="acc",
        true_value="1",
    ),
    TracksolidBinarySensorDescription(
        key="moving",
        name="Moving",
        device_class=BinarySensorDeviceClass.MOTION,
        icon="mdi:motorbike",
        data_key="status",
        true_value=STATUS_MOVING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TracksolidCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    imeis: list[str] = entry.data[CONF_IMEIS]
    async_add_entities(
        TracksolidBinarySensor(coordinator, imei, desc)
        for imei in imeis
        for desc in BINARY_SENSOR_TYPES
    )


class TracksolidBinarySensor(TracksolidEntity, BinarySensorEntity):
    """Binary sensor for a Tracksolid device."""

    entity_description: TracksolidBinarySensorDescription

    def __init__(
        self,
        coordinator: TracksolidCoordinator,
        imei: str,
        description: TracksolidBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, imei)
        self.entity_description = description
        self._attr_unique_id = f"{imei}_{description.key}"
        self._vibration_active = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.key == "vibration":
            self.async_on_remove(
                self.hass.bus.async_listen(
                    f"{DOMAIN}_vibration", self._handle_vibration_event
                )
            )

    def _handle_vibration_event(self, event) -> None:
        if str(event.data.get("imei")) == self._imei:
            self._vibration_active = True
            self.async_write_ha_state()
            # Auto-clear after 60 seconds
            self.hass.loop.call_later(60, self._clear_vibration)

    def _clear_vibration(self) -> None:
        self._vibration_active = False
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.key == "vibration":
            return self._vibration_active

        data = self._device_data
        if not data:
            return None

        value = data.get(self.entity_description.data_key)
        if value is None:
            return None

        if self.entity_description.true_value is not None:
            return str(value) == str(self.entity_description.true_value)

        return bool(value)
