"""Config flow for Tracksolid Pro."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import TracksolidApiClient, TracksolidApiError, TracksolidAuthError
from .const import (
    CONF_APP_KEY,
    CONF_APP_SECRET,
    CONF_IMEIS,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORM_APP_KEY,
    PLATFORM_APP_SECRET,
    REGION_EU,
    REGION_HK_SG,
    REGION_LABELS,
    REGION_US,
)

_LOGGER = logging.getLogger(__name__)

REGION_OPTIONS = [
    {"value": REGION_EU, "label": REGION_LABELS[REGION_EU]},
    {"value": REGION_HK_SG, "label": REGION_LABELS[REGION_HK_SG]},
    {"value": REGION_US, "label": REGION_LABELS[REGION_US]},
]


async def _try_login(hass, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Authenticate and return the list of devices on the account."""
    session = async_get_clientsession(hass)
    client = TracksolidApiClient(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        region=data[CONF_REGION],
        session=session,
        app_key=data.get(CONF_APP_KEY) or None,
        app_secret=data.get(CONF_APP_SECRET) or None,
    )
    await client.async_ensure_token()
    return await client.async_get_devices()


class TracksolidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Tracksolid Pro config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._user_data: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Step 1 — login
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                devices = await _try_login(self.hass, user_input)
            except TracksolidAuthError as err:
                _LOGGER.warning("Tracksolid auth failed: %s", err)
                errors["base"] = "invalid_auth"
            except TracksolidApiError as err:
                _LOGGER.warning("Tracksolid connect failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Tracksolid login")
                errors["base"] = "unknown"
            else:
                self._user_data = user_input
                self._devices = devices
                return await self.async_step_devices()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME,
                    description={"suggested_value": self._user_data.get(CONF_USERNAME, "")},
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL)),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_REGION,
                    default=self._user_data.get(CONF_REGION, DEFAULT_REGION),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=REGION_OPTIONS,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_APP_KEY,
                    description={"suggested_value": self._user_data.get(CONF_APP_KEY, PLATFORM_APP_KEY)},
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_APP_SECRET,
                    description={"suggested_value": self._user_data.get(CONF_APP_SECRET, PLATFORM_APP_SECRET)},
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2 — select devices
    # ------------------------------------------------------------------

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        device_options = {
            str(d.get("imei", d.get("devImei", ""))): (
                f"{d.get('deviceName', d.get('name', 'Unknown'))} "
                f"({d.get('imei', d.get('devImei', ''))})"
            )
            for d in self._devices
            if d.get("imei") or d.get("devImei")
        }

        if not device_options:
            errors["base"] = "no_devices"

        if user_input is not None and not errors:
            selected_imeis: list[str] = user_input[CONF_IMEIS]
            if not selected_imeis:
                errors[CONF_IMEIS] = "no_devices_selected"
            else:
                return self.async_create_entry(
                    title="Tracksolid Pro",
                    data={
                        **self._user_data,
                        CONF_IMEIS: selected_imeis,
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_IMEIS): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": imei, "label": label}
                            for imei, label in device_options.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10, max=300, step=5, mode=NumberSelectorMode.SLIDER
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="devices", data_schema=schema, errors=errors
        )
