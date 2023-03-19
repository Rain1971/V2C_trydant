import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

class V2CTrydantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_IP_ADDRESS], data=user_input)
        
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA
        )