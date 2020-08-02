from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from . import DOMAIN, CONF_BUCKET, CONF_REGION, CONF_ACCESS_KEY_ID, CONF_SECRET_ACCESS_KEY, DEFAULT_REGION, SUPPORTED_REGIONS


@config_entries.HANDLERS.register(DOMAIN)
class S3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_BUCKET])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_BUCKET], data=user_input
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(
                    SUPPORTED_REGIONS
                ),
                vol.Required(CONF_ACCESS_KEY_ID): str,
                vol.Required(CONF_SECRET_ACCESS_KEY): str,
                vol.Required(CONF_BUCKET): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema
        )
