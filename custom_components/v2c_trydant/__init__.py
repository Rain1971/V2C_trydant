"""The v2c_trydant component."""
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_IP_ADDRESS
import logging
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "v2c_trydant"

PLATFORMS = ["sensor", "switch", "number"]

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
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_setup(entry, platform)

    hass.data[DOMAIN]["ip_address"] = entry.data[CONF_IP_ADDRESS]
    ip_address = entry.data[CONF_IP_ADDRESS]

    async def set_min_intensity(call: ServiceCall):
        min_intensity = call.data.get("min_intensity")
        if 6 <= int(min_intensity) <= 32:
            await async_set_min_intensity(hass, ip_address, min_intensity)
        else:
            _LOGGER.error("min_intensity must be between 6 and 32")

    async def set_max_intensity(call):
        max_intensity = call.data["max_intensity"]
        if 6 <= int(max_intensity) <= 32:
            await async_set_max_intensity(hass, ip_address, max_intensity)
        else:
            _LOGGER.error("max_intensity must be between 6 and 32")

    async def set_min_intensity_slider(call):
        min_intensity = call.data.get("v2c_min_intensity")
        if min_intensity is not None:
            if 6 <= int(min_intensity) <= 32:
                if entry:
                    ip_address = entry.data[CONF_IP_ADDRESS]
                    await async_set_min_intensity(hass, ip_address, min_intensity)
                else:
                    _LOGGER.error(f"Entity ID not found: {entity_id}")
            else:
                _LOGGER.error("v2c_min_intensity must be between 6 and 32")
        else:
            _LOGGER.error("v2c_max_intensity not provided")

    async def set_max_intensity_slider(call):
        max_intensity = call.data.get("v2c_max_intensity")
        if max_intensity is not None:
            if 6 <= int(max_intensity) <= 32:
                if entry:
                    ip_address = entry.data[CONF_IP_ADDRESS]
                    await async_set_max_intensity(hass, ip_address, max_intensity)
                else:
                    _LOGGER.error(f"Entity ID not found: {entity_id}")
            else:
                _LOGGER.error("v2c_max_intensity must be between 6 and 32")
        else:
            _LOGGER.error("v2c_max_intensity not provided")

    hass.services.async_register(DOMAIN, "set_min_intensity", set_min_intensity)
    hass.services.async_register(DOMAIN, "set_max_intensity", set_max_intensity)
    hass.services.async_register(DOMAIN, "set_min_intensity_slider", set_min_intensity_slider)
    hass.services.async_register(DOMAIN, "set_max_intensity_slider", set_max_intensity_slider)


    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_set_min_intensity(hass: HomeAssistant, ip_address: str, min_intensity: int):
    _LOGGER.debug(f"Setting min intensity to {min_intensity}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/MinIntensity={min_intensity}"
        async with session.get(url) as response:
            response.raise_for_status()

async def async_set_max_intensity(hass, ip_address: str, max_intensity):
    _LOGGER.debug(f"Setting max intensity to {max_intensity}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/MaxIntensity={max_intensity}"
        async with session.get(url) as response:
            response.raise_for_status()

