"""Config flow for Simplepush V2 integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
import voluptuous as vol

from . import async_validate_token
from .const import (
    CONF_API_TOKEN,
    CONF_DEFAULT_TOPIC,
    CONF_NAME,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SimplepushV2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Simplepush V2."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN].strip()
            raw_topic = user_input.get(CONF_DEFAULT_TOPIC, "").strip()
            default_topic = raw_topic.replace(" ", "_") if raw_topic else None
            name = user_input.get(CONF_NAME, "").strip() or DEFAULT_NAME

            # Check if this token is already configured
            await self.async_set_unique_id(api_token)
            self._abort_if_unique_id_configured()

            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                valid = await async_validate_token(session, api_token)
                if not valid:
                    errors["base"] = "invalid_auth"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_API_TOKEN: api_token,
                            CONF_DEFAULT_TOPIC: default_topic,
                        },
                    )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during Simplepush validation")
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): str,
                vol.Optional(CONF_DEFAULT_TOPIC): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_options_flow(
        cls, config_entry: config_entries.ConfigEntry
    ) -> config_entries.OptionsFlow:
        """Get options flow for this handler."""
        return SimplepushV2OptionsFlowHandler(config_entry)


class SimplepushV2OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Simplepush V2 options."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        """Initialize options flow."""
        self._custom_config_entry = config_entry

    @property
    def _entry(self) -> config_entries.ConfigEntry:
        """Get the current config entry."""
        if self._custom_config_entry is not None:
            return self._custom_config_entry
        return self.config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        current_token = self._entry.data.get(CONF_API_TOKEN, "")
        current_topic = self._entry.options.get(
            CONF_DEFAULT_TOPIC, self._entry.data.get(CONF_DEFAULT_TOPIC, "")
        ) or ""

        if user_input is not None:
            new_token = user_input.get(CONF_API_TOKEN, "").strip() or current_token
            raw_new_topic = user_input.get(CONF_DEFAULT_TOPIC, "").strip()
            new_topic = raw_new_topic.replace(" ", "_") if raw_new_topic else None

            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                valid = await async_validate_token(session, new_token)
                if not valid:
                    errors["base"] = "invalid_auth"
                else:
                    # Update config entry data if token changed
                    if new_token != current_token:
                        new_data = dict(self._entry.data)
                        new_data[CONF_API_TOKEN] = new_token
                        self.hass.config_entries.async_update_entry(
                            self._entry, data=new_data
                        )

                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_DEFAULT_TOPIC: new_topic,
                        },
                    )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Simplepush options flow")
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN, default=current_token): str,
                vol.Optional(CONF_DEFAULT_TOPIC, default=current_topic): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
