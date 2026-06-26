"""Sensor platform for Tracksolid Pro."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IMEIS, COORDINATOR, DOMAIN
from .coordinator import TracksolidCoordinator
from .entity import TracksolidEntity


@dataclass(frozen=True)
class TracksolidSensorEntityDescription(SensorEntityDescription):
    """Describes a Tracksolid sensor."""

    data_key: str = ""
    data_key_alt: str = ""


SENSOR_TYPES: tuple[TracksolidSensorEntityDescription, ...] = (
    TracksolidSensorEntityDescription(
        key="speed",
        name="Speed",
        data_key="speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    TracksolidSensorEntityDescription(
        key="battery",
        name="Battery",
        data_key="battery",
        data_key_alt="batteryLevel",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TracksolidSensorEntityDescription(
        key="satellites",
        name="Satellites",
        data_key="satellites",
        data_key_alt="sat",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:satellite-variant",
    ),
    TracksolidSensorEntityDescription(
        key="signal",
        name="Signal",
        data_key="gsm",
        data_key_alt="gsmSignal",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
    ),
    TracksolidSensorEntityDescription(
        key="last_update",
        name="Last Update",
        data_key="gpsTime",
        data_key_alt="lastTime",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
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
        TracksolidSensor(coordinator, imei, description)
        for imei in imeis
        for description in SENSOR_TYPES
    )


class TracksolidSensor(TracksolidEntity, SensorEntity):
    """A sensor reading from a Tracksolid device."""

    entity_description: TracksolidSensorEntityDescription

    def __init__(
        self,
        coordinator: TracksolidCoordinator,
        imei: str,
        description: TracksolidSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, imei)
        self.entity_description = description
        self._attr_unique_id = f"{imei}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self._device_data
        value = data.get(self.entity_description.data_key)
        if value is None and self.entity_description.data_key_alt:
            value = data.get(self.entity_description.data_key_alt)
        if value is None:
            return None

        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            from homeassistant.util.dt import parse_datetime
            return parse_datetime(str(value))

        try:
            return float(value)
        except (ValueError, TypeError):
            return value
