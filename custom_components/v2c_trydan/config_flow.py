import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import config_validation as cv
import aiohttp
import asyncio

from .const import DOMAIN, CONF_KWH_PER_100KM, CONF_PRECIO_LUZ

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS, description={"suggested_value": "IP trydan"}): str,
    }
)

class V2CtrydanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for V2C Trydan."""
    
    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self.ip_address = None
    
    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return V2CtrydanOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            ip_address = user_input[CONF_IP_ADDRESS]
            
            # Validate IP and connection
            try:
                if await self._test_connection(ip_address):
                    await self.async_set_unique_id(ip_address)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"V2C Trydan ({ip_address})", 
                        data=user_input
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )

    async def async_step_import(self, import_info):
        """Import entry from configuration.yaml."""
        return await self.async_step_user(import_info)

    async def _test_connection(self, ip_address: str) -> bool:
        """Test connection to the V2C Trydan device."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip_address}/RealTimeData",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

class V2CtrydanOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle V2C Trydan options flow."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        super().__init__(config_entry)
        self.current_kwh_per_100km = config_entry.options.get(CONF_KWH_PER_100KM, 20.8)
        self.current_precio_luz = config_entry.options.get(CONF_PRECIO_LUZ, "sensor.pvpc")

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_KWH_PER_100KM, description={"suggested_value": self.current_kwh_per_100km}
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_PRECIO_LUZ, description={"suggested_value": self.current_precio_luz}
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema
        )