"""Tracksolid Pro integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.webhook import (
    async_register as webhook_async_register,
    async_unregister as webhook_async_unregister,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TracksolidApiClient
from .const import (
    CONF_IMEIS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    WEBHOOK_ID,
)
from .coordinator import TracksolidCoordinator
from .webhook import async_handle_webhook

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.DEVICE_TRACKER, Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tracksolid Pro from a config entry."""
    session = async_get_clientsession(hass)

    client = TracksolidApiClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    imeis: list[str] = entry.data[CONF_IMEIS]
    scan_interval: int = int(
        entry.options.get(CONF_SCAN_INTERVAL)
        or entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    coordinator = TracksolidCoordinator(hass, client, imeis, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    # Register webhook for Tracksolid push notifications (vibration etc.)
    webhook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    webhook_async_register(
        hass,
        DOMAIN,
        "Tracksolid Push",
        webhook_id,
        async_handle_webhook,
    )
    _LOGGER.info("Tracksolid webhook registered at /api/webhook/%s", webhook_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    webhook_async_unregister(hass, webhook_id)

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
