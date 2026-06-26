"""Webhook handler for Tracksolid Pro push notifications."""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from homeassistant.components.webhook import Request
from homeassistant.core import HomeAssistant

from .const import (
    ALARM_TYPE_NAMES,
    ALARM_TYPE_VIBRATION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request
) -> web.Response:
    """Handle incoming push from Tracksolid."""
    try:
        data: dict[str, Any] = await request.json()
    except Exception:
        _LOGGER.warning("Tracksolid webhook: could not parse JSON body")
        return web.Response(status=400)

    _LOGGER.debug("Tracksolid push received: %s", data)

    msg_type = data.get("msgType", data.get("type", ""))

    if msg_type == "alarm" or "alarmType" in data:
        await _handle_alarm(hass, data)
    elif msg_type == "location" or "lat" in data:
        await _handle_location(hass, data)
    else:
        _LOGGER.debug("Tracksolid webhook: unhandled msgType=%s", msg_type)

    return web.Response(text="OK")


async def _handle_alarm(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Fire a HA event for an alarm push."""
    imei = str(data.get("imei", data.get("devImei", "")))
    alarm_type = int(data.get("alarmType", data.get("type", 0)))
    alarm_name = ALARM_TYPE_NAMES.get(alarm_type, f"alarm_{alarm_type}")

    event_data = {
        "imei": imei,
        "alarm_type": alarm_type,
        "alarm_name": alarm_name,
        "latitude": data.get("lat"),
        "longitude": data.get("lng"),
        "gps_time": data.get("gpsTime"),
        "raw": data,
    }

    hass.bus.async_fire(f"{DOMAIN}_alarm", event_data)

    if alarm_type == ALARM_TYPE_VIBRATION:
        _LOGGER.info("Tracksolid vibration alert for device %s", imei)
        hass.bus.async_fire(f"{DOMAIN}_vibration", event_data)

    # Update binary sensor state in coordinator if it exists
    _update_binary_sensor_state(hass, imei, alarm_type)


async def _handle_location(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Handle a location push by refreshing the coordinator."""
    from .const import COORDINATOR

    for entry_data in hass.data.get(DOMAIN, {}).values():
        coordinator = entry_data.get(COORDINATOR)
        if coordinator:
            await coordinator.async_request_refresh()
            break


def _update_binary_sensor_state(
    hass: HomeAssistant, imei: str, alarm_type: int
) -> None:
    """Store latest alarm state so binary sensors can pick it up."""
    store = hass.data.setdefault(DOMAIN, {}).setdefault("alarms", {})
    store[imei] = alarm_type
