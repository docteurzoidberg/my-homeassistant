"""Config flow to configure Cozytouch."""
import logging

import voluptuous as vol
from cozytouchpy.exception import AuthentificationFailed, CozytouchException
from homeassistant import config_entries, core
from homeassistant.const import CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from homeassistant.core import callback

from . import async_connect
from .const import (
    CONF_COZYTOUCH_ACTUATOR,
    DEFAULT_COZYTOUCH_ACTUATOR,
    DEFAULT_TIMEOUT,
    DOMAIN,
    SENSOR_TYPES,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
        vol.Optional(
            CONF_COZYTOUCH_ACTUATOR, default=DEFAULT_COZYTOUCH_ACTUATOR
        ): vol.In(SENSOR_TYPES),
    }
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    return await async_connect(hass, data)


class CozytouchFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Cozytouch config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get option flow."""
        return CozytouchOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except AuthentificationFailed as e:
                errors = {"base": "login_inccorect"}
                _LOGGER.error("Error: %s", e)
            except CozytouchException as e:
                errors = {"base": "parsing"}
                _LOGGER.error("Error: %s", e)

            if "base" not in errors:
                return self.async_create_entry(title="Cozytouch", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CozytouchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle option."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._actuator = self.config_entry.options.get(
            CONF_COZYTOUCH_ACTUATOR, DEFAULT_COZYTOUCH_ACTUATOR
        )

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        OPTIONS_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_COZYTOUCH_ACTUATOR, default=self._actuator): vol.In(
                    SENSOR_TYPES
                )
            }
        )

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="user", data_schema=OPTIONS_SCHEMA)
