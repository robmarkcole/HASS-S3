from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, FlowResult
from typing import Any
import voluptuous as vol
from . import (
    DOMAIN,
    CONF_REGION,
    CONF_ACCESS_KEY_ID,
    CONF_SECRET_ACCESS_KEY,
    CONF_ENDPOINT_URL,
    DEFAULT_REGION,
    SUPPORTED_REGIONS,
)

OPTIONS_SCHEMA_CREATE = vol.Schema(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): str,
        vol.Required(CONF_SECRET_ACCESS_KEY): str,
        vol.Optional(CONF_ENDPOINT_URL): str,
    }
)

OPTIONS_SCHEMA_UPDATE = vol.Schema(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_SECRET_ACCESS_KEY): str,
        vol.Optional(CONF_ENDPOINT_URL): str,
    }
)


class S3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ACCESS_KEY_ID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_ACCESS_KEY_ID], data=user_input
            )

        return self.async_show_form(step_id="user", data_schema=OPTIONS_SCHEMA_CREATE)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            if CONF_ACCESS_KEY_ID in self.config_entry.data:
                user_input[CONF_ACCESS_KEY_ID] = self.config_entry.data[
                    CONF_ACCESS_KEY_ID
                ]

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )

            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA_UPDATE, self.config_entry.data
            ),
        )
