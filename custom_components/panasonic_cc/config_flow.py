"""Config flow for the Panasonic Comfort Cloud platform."""
import asyncio
import logging
from typing import Any, Dict, Optional, Mapping

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from aio_panasonic_comfort_cloud import ApiClient
from . import DOMAIN as PANASONIC_DOMAIN
from .const import (
    CONF_FORCE_OUTSIDE_SENSOR,
    CONF_ENABLE_DAILY_ENERGY_SENSOR,
    DEFAULT_ENABLE_DAILY_ENERGY_SENSOR,
    CONF_USE_PANASONIC_PRESET_NAMES,
    DEFAULT_USE_PANASONIC_PRESET_NAMES,
    CONF_DEVICE_FETCH_INTERVAL,
    DEFAULT_DEVICE_FETCH_INTERVAL,
    CONF_ENERGY_FETCH_INTERVAL,
    DEFAULT_ENERGY_FETCH_INTERVAL,
    CONF_FORCE_ENABLE_NANOE,
    DEFAULT_FORCE_ENABLE_NANOE,
    CONF_REFRESH_TOKEN,
    PANASONIC_OAUTH_SCOPE)

_LOGGER = logging.getLogger(__name__)


class FlowHandler(config_entries.ConfigFlow, domain=PANASONIC_DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    _entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PanasonicOptionsFlowHandler(config_entry)

    async def _create_entry(
        self,
        username: str,
        password: str,
        refresh_token: str | None = None,
        user_input: Mapping[str, Any] | None = None,
    ):
        """Register new entry."""
        for entry in self._async_current_entries():
            if entry.domain == PANASONIC_DOMAIN:
                return self.async_abort(reason="already_configured")

        data = {
            CONF_USERNAME: username,
            CONF_PASSWORD: password,
            CONF_FORCE_OUTSIDE_SENSOR: False,
            CONF_FORCE_ENABLE_NANOE: user_input.get(CONF_FORCE_ENABLE_NANOE, DEFAULT_FORCE_ENABLE_NANOE) if user_input else DEFAULT_FORCE_ENABLE_NANOE,
            CONF_ENABLE_DAILY_ENERGY_SENSOR: user_input.get(CONF_ENABLE_DAILY_ENERGY_SENSOR, DEFAULT_ENABLE_DAILY_ENERGY_SENSOR) if user_input else DEFAULT_ENABLE_DAILY_ENERGY_SENSOR,
            CONF_USE_PANASONIC_PRESET_NAMES: user_input.get(CONF_USE_PANASONIC_PRESET_NAMES, DEFAULT_USE_PANASONIC_PRESET_NAMES) if user_input else DEFAULT_USE_PANASONIC_PRESET_NAMES,
            CONF_DEVICE_FETCH_INTERVAL: user_input.get(CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL) if user_input else DEFAULT_DEVICE_FETCH_INTERVAL,
            CONF_ENERGY_FETCH_INTERVAL: user_input.get(CONF_ENERGY_FETCH_INTERVAL, DEFAULT_ENERGY_FETCH_INTERVAL) if user_input else DEFAULT_ENERGY_FETCH_INTERVAL,
        }
        if refresh_token:
            data[CONF_REFRESH_TOKEN] = refresh_token
        return self.async_create_entry(title="", data=data)

    async def _create_device(
        self,
        username: str,
        password: str,
        refresh_token: str | None = None,
        user_input: Mapping[str, Any] | None = None,
    ):
        """Create device."""
        try:
            client = async_get_clientsession(self.hass)
            api = ApiClient(username, password, client)
            if refresh_token:
                await api._settings.is_ready()
                api._settings.set_token(refresh_token=refresh_token, scope=PANASONIC_OAUTH_SCOPE)
            await api.start_session()
            devices = api.get_devices()

            if not devices and not api.unknown_devices:
                _LOGGER.debug("No devices found")
                return self.async_abort(reason="no_devices")

        except asyncio.TimeoutError as te:
            _LOGGER.exception("TimeoutError", te)
            return self.async_abort(reason="device_timeout")
        except ClientError as ce:
            _LOGGER.exception("ClientError", ce)
            return self.async_abort(reason="device_fail")
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device", e)
            return self.async_abort(reason="device_fail")

        return await self._create_entry(username, password, refresh_token, user_input)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_REFRESH_TOKEN,
                        default="",
                    ): str,
                    vol.Optional(
                        CONF_ENABLE_DAILY_ENERGY_SENSOR,
                        default=DEFAULT_ENABLE_DAILY_ENERGY_SENSOR,
                    ): bool,
                    vol.Optional(
                        CONF_FORCE_ENABLE_NANOE,
                        default=False,
                    ): bool,
                    vol.Optional(
                        CONF_USE_PANASONIC_PRESET_NAMES,
                        default=DEFAULT_USE_PANASONIC_PRESET_NAMES,
                    ): bool,
                    vol.Optional(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=DEFAULT_DEVICE_FETCH_INTERVAL,
                    ): int,
                    vol.Optional(
                        CONF_ENERGY_FETCH_INTERVAL,
                        default=DEFAULT_ENERGY_FETCH_INTERVAL,
                    ): int,
                })
            )
        refresh_token = user_input.get(CONF_REFRESH_TOKEN) or None
        return await self._create_device(
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            refresh_token,
            user_input,
        )

    async def async_step_import(self, user_input):
        """Import a config entry."""
        username = user_input.get(CONF_USERNAME)
        if not username:
            return await self.async_step_user()
        return await self._create_device(
            username,
            user_input[CONF_PASSWORD],
            user_input.get(CONF_REFRESH_TOKEN) or None,
            user_input,
        )
    
    async def async_step_reconfigure(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle reauth on failure."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reconfigure_confirm()

    async def async_auth(self, user_input: Mapping[str, Any]) -> dict[str, str]:
        """Reusable Auth Helper."""
        client = async_get_clientsession(self.hass)
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        refresh_token = user_input.get(CONF_REFRESH_TOKEN) or None
        api = ApiClient(username, password, client)
        try:
            if refresh_token:
                await api._settings.is_ready()
                api._settings.set_token(refresh_token=refresh_token, scope=PANASONIC_OAUTH_SCOPE)
                await api.start_session()
            else:
                await api.reauthenticate()
            devices = api.get_devices()

            if not devices and not api.unknown_devices:
                return {"base": "no_devices"}
        except asyncio.TimeoutError as te:
            _LOGGER.exception("TimeoutError", te)
            return {"base": "device_timeout"}
        except ClientError as ce:
            _LOGGER.exception("ClientError", ce)
            return {"base": "device_fail"}
        except Exception as e:  # pylint: disable=broad-except
            err_msg = str(e)
            if "invalid_user_password" in err_msg:
                return {"base": "invalid_user_password"}
            _LOGGER.exception("Unexpected error creating device", e)
            return {"base": "device_fail"}


        return {}

    async def async_step_reconfigure_confirm(
        self, user_input: Mapping[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle users reauth credentials."""

        assert self._entry
        errors: dict[str, str] = {}

        if user_input and not (errors := await self.async_auth(user_input)):
            return self.async_update_reload_and_abort(
                self._entry,
                data=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_REFRESH_TOKEN,
                    default=self._entry.data.get(CONF_REFRESH_TOKEN, "") if self._entry else "",
                ): str,
                }),
            errors=errors,
        )



class PanasonicOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Panasonic options."""

    def __init__(self, config_entry):
        """Initialize Panasonic options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        """Manage Panasonic options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_DAILY_ENERGY_SENSOR,
                        default=self.config_entry.options.get(
                            CONF_ENABLE_DAILY_ENERGY_SENSOR, DEFAULT_ENABLE_DAILY_ENERGY_SENSOR
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FORCE_ENABLE_NANOE,
                        default=self.config_entry.options.get(
                            CONF_FORCE_ENABLE_NANOE, DEFAULT_FORCE_ENABLE_NANOE
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_USE_PANASONIC_PRESET_NAMES,
                        default=self.config_entry.options.get(
                            CONF_USE_PANASONIC_PRESET_NAMES, DEFAULT_USE_PANASONIC_PRESET_NAMES
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_ENERGY_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_ENERGY_FETCH_INTERVAL, DEFAULT_ENERGY_FETCH_INTERVAL
                        ),
                    ): int,
                }
            ),
        )
