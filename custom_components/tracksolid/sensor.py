"""Sensor platform for Tracksolid Pro."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
from homeassistant.util import dt as dt_util

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
        key="heartbeat",
        name="Last Heartbeat",
        data_key="hbTime",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:heart-pulse",
    ),
    TracksolidSensorDescription(
        key="heading",
        name="Heading",
        data_key="direction",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    TracksolidSensorDescription(
        key="status",
        name="Status",
        data_key="status",
        icon="mdi:motorbike",
    ),
    TracksolidSensorDescription(
        key="status_detail",
        name="Status Detail",
        data_key="statusStr",
        icon="mdi:information-outline",
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


def _parse_tracksolid_datetime(value: Any) -> datetime | None:
    """Parse a naive 'YYYY-MM-DD HH:MM:SS' string using the HA-configured timezone."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=dt_util.DEFAULT_TIME_ZONE
        )
    except ValueError:
        return None


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
        data = self._device_data
        if not data:
            return None

        value = data.get(self.entity_description.data_key)

        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return _parse_tracksolid_datetime(value)

        if value is None:
            # Speed is null when parked — treat as 0
            if self.entity_description.key == "speed":
                return 0
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value) if value else None
