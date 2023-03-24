import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN, CONF_KWH_PER_100KM

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS, description={"suggested_value": "IP Trydant"}): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_KWH_PER_100KM, description={"suggested_value": 20.8}): float,
    }
)

class V2CTrydantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    _instance = None

    def __init__(self):
        if V2CTrydantConfigFlow._instance is None:
            V2CTrydantConfigFlow._instance = self

    @classmethod
    def async_get_options_flow(cls, config_entry):
        if cls._instance is not None:
            return cls._instance._async_get_options_flow(config_entry)
        else:
            return V2CTrydantOptionsFlowHandler(config_entry=config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_IP_ADDRESS], data=user_input)
        
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA
        )

    async def async_step_import(self, import_info):
        """Import entry from configuration.yaml."""
        return await self.async_step_user(import_info)

    def _async_get_options_flow(self, config_entry):
        return V2CTrydantOptionsFlowHandler(config_entry=config_entry)



class V2CTrydantOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init", data_schema=OPTIONS_SCHEMA
        )