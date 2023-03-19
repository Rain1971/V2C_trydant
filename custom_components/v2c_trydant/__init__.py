import logging

from homeassistant.const import CONF_IP_ADDRESS
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "v2c_trydant"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass, config):
    hass.data[DOMAIN] = {
        CONF_IP_ADDRESS: config[DOMAIN].get(CONF_IP_ADDRESS),
    }

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    async def pause_charger(call):
        """Pause the V2C_trydant charger."""
        # ...

    async def resume_charger(call):
        """Resume the V2C_trydant charger."""
        # ...

    async def set_charge_intensity(call):
        """Set the charge intensity of the V2C_trydant charger."""
        # ...

    hass.services.async_register(DOMAIN, "pause_charger", pause_charger)
    hass.services.async_register(DOMAIN, "resume_charger", resume_charger)
    hass.services.async_register(DOMAIN, "set_charge_intensity", set_charge_intensity)

    _LOGGER.info("V2C_trydant integration has been initialized.")
    return True