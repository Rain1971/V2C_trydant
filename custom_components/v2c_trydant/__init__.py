"""The v2c_trydant component."""
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant

DOMAIN = "v2c_trydant"

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for entry_config in config[DOMAIN]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=entry_config
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)