import logging

from homeassistant.const import CONF_IP_ADDRESS
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from . import services

DOMAIN = "V2C_trydant"
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

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data=config[DOMAIN]
        )
    )

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    hass.services.async_register(DOMAIN, "pause_charger", services.pause_charger)
    hass.services.async_register(DOMAIN, "resume_charger", services.resume_charger)
    hass.services.async_register(DOMAIN, "set_charge_intensity", services.set_charge_intensity)

    _LOGGER.info("V2C Trydant integration has been initialized.")
    return True