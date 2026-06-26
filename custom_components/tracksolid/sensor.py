"""Sensor platform for Tracksolid Pro."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_IMEIS, COORDINATOR, DOMAIN
from .coordinator import TracksolidCoordinator
from .entity import TracksolidEntity


@dataclass(frozen=True)
class TracksolidSensorDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with a data key."""
    data_key: str = ""


SENSOR_TYPES: tuple[TracksolidSensorDescription, ...] = (
    TracksolidSensorDescription(
        key="speed",
        name="Speed",
        data_key="speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    TracksolidSensorDescription(
        key="satellites",
        name="Satellites",
        data_key="gpsNum",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:satellite-variant",
    ),
    TracksolidSensorDescription(
        key="gps_signal",
        name="GPS Signal",
        data_key="GPSSignal",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
    ),
    TracksolidSensorDescription(
        key="gps_time",
        name="Last GPS Fix",
        data_key="gpsTime",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
    TracksolidSensorDescription(
        key="status",
        name="Status",
        data_key="status",
        icon="mdi:motorbike",
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
        TracksolidSensor(coordinator, imei, desc)
        for imei in imeis
        for desc in SENSOR_TYPES
    )


class TracksolidSensor(TracksolidEntity, SensorEntity):
    """A sensor for a Tracksolid device."""

    entity_description: TracksolidSensorDescription

    def __init__(
        self,
        coordinator: TracksolidCoordinator,
        imei: str,
        description: TracksolidSensorDescription,
    ) -> None:
        super().__init__(coordinator, imei)
        self.entity_description = description
        self._attr_unique_id = f"{imei}_{description.key}"

    @property
    def native_value(self) -> Any:
        value = self._device_data.get(self.entity_description.data_key)
        if value is None:
            return None

        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            from homeassistant.util.dt import parse_datetime
            return parse_datetime(str(value))

        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value) if value else None
