"""The v2c_trydan component."""
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_IP_ADDRESS, Platform
import logging
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "v2c_trydan"

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

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
    hass.data[DOMAIN]["ip_address"] = entry.data[CONF_IP_ADDRESS]
    ip_address = entry.data[CONF_IP_ADDRESS]

    async def set_min_intensity(call: ServiceCall):
        #_LOGGER.debug("min_intensity service called")
        min_intensity = call.data.get("min_intensity")
        try:
            min_intensity = int(min_intensity)
            if 6 <= min_intensity <= 32:
                #_LOGGER.debug(f"Valid min_intensity: {min_intensity}")
                await async_set_min_intensity(hass, ip_address, min_intensity)
            else:
                _LOGGER.error("min_intensity must be between 6 and 32")
        except ValueError:
            _LOGGER.error(f"Invalid min_intensity: {min_intensity}. Must be an integer.")

    async def async_set_dynamic_power_mode(call: ServiceCall):
        dynamic_power_mode = call.data.get("DynamicPowerMode")
        try:
            dynamic_power_mode = int(dynamic_power_mode)
            if 0 <= dynamic_power_mode <= 7:
                #_LOGGER.debug(f"Valid dynamic_power_mode: {dynamic_power_mode}")
                await async_set_dynamic_power_mode(hass, ip_address, dynamic_power_mode)
            else:
                _LOGGER.error("DynamicPowerMode must be between 0 and 7")
        except ValueError:
            _LOGGER.error(f"Invalid dynamic_power_mode: {dynamic_power_mode}. Must be an integer.")

    async def set_max_intensity(call):
        max_intensity = call.data["max_intensity"]
        try:
            max_intensity = int(max_intensity)
            if 6 <= max_intensity <= 32:
                #_LOGGER.debug(f"Valid max_intensity: {max_intensity}")
                await async_set_max_intensity(hass, ip_address, max_intensity)
            else:
                _LOGGER.error("max_intensity must be between 6 y 32")
        except ValueError:
            _LOGGER.error(f"Invalid max_intensity: {max_intensity}. Must be an integer.")

    async def set_intensity(call):
        intensity = call.data["intensity"]
        try:
            intensity = int(intensity)
            if 6 <= intensity <= 32:
                #_LOGGER.debug(f"Valid intensity: {intensity}")
                await async_set_intensity(hass, ip_address, intensity)
            else:
                _LOGGER.error("intensity must be between 6 y 32")
        except ValueError:
            _LOGGER.error(f"Invalid intensity: {intensity}. Must be an integer.")

    async def set_min_intensity_slider(call):
        min_intensity = call.data.get("v2c_min_intensity")
        #_LOGGER.debug(f"Received call to set_min_intensity_slider with {min_intensity}")
        if min_intensity is not None:
            try:
                min_intensity = int(min_intensity)
                if 6 <= min_intensity <= 32:
                    if entry:
                        ip_address = entry.data[CONF_IP_ADDRESS]
                        #_LOGGER.debug(f"Calling async_set_min_intensity with IP: {ip_address} and min_intensity: {min_intensity}")
                        await async_set_min_intensity(hass, ip_address, min_intensity)
                    else:
                        _LOGGER.error("Entry data not found for setting min_intensity_slider")
                else:
                    _LOGGER.error("v2c_min_intensity must be between 6 y 32")
            except ValueError:
                _LOGGER.error(f"Invalid v2c_min_intensity: {min_intensity}. Must be an integer.")
        else:
            _LOGGER.error("v2c_min_intensity not provided")

    async def set_dynamic_power_mode_slider(call):
        dynamic_power_mode = call.data.get("v2c_dynamic_power_mode")
        #_LOGGER.debug(f"Received call to set_dynamic_power_mode_slider with {dynamic_power_mode}")
        if dynamic_power_mode is not None:
            try:
                dynamic_power_mode = int(dynamic_power_mode)
                if 0 <= dynamic_power_mode <= 7:
                    if entry:
                        ip_address = entry.data[CONF_IP_ADDRESS]
                        #_LOGGER.debug(f"Calling async_set_dynamic_power_mode with IP: {ip_address} and dynamic_power_mode: {dynamic_power_mode}")
                        await async_set_dynamic_power_mode(hass, ip_address, dynamic_power_mode)
                    else:
                        _LOGGER.error("Entry data not found for setting dynamic_power_mode_slider")
                else:
                    _LOGGER.error("v2c_dynamic_power_mode must be between 0 y 7")
            except ValueError:
                _LOGGER.error(f"Invalid v2c_dynamic_power_mode: {dynamic_power_mode}. Must be an integer.")
        else:
            _LOGGER.error("v2c_dynamic_power_mode not provided")

    async def set_max_intensity_slider(call):
        max_intensity = call.data.get("v2c_max_intensity")
        #_LOGGER.debug(f"Received call to set_max_intensity_slider with {max_intensity}")
        if max_intensity is not None:
            try:
                max_intensity = int(max_intensity)
                if 6 <= max_intensity <= 32:
                    if entry:
                        ip_address = entry.data[CONF_IP_ADDRESS]
                        #_LOGGER.debug(f"Calling async_set_max_intensity with IP: {ip_address} and max_intensity: {max_intensity}")
                        await async_set_max_intensity(hass, ip_address, max_intensity)
                    else:
                        _LOGGER.error("Entry data not found for setting max_intensity_slider")
                else:
                    _LOGGER.error("v2c_max_intensity must be between 6 y 32")
            except ValueError:
                _LOGGER.error(f"Invalid v2c_max_intensity: {max_intensity}. Must be an integer.")
        else:
            _LOGGER.error("v2c_max_intensity not provided")

    hass.services.async_register(DOMAIN, "set_min_intensity", set_min_intensity)
    hass.services.async_register(DOMAIN, "set_max_intensity", set_max_intensity)
    hass.services.async_register(DOMAIN, "set_dynamic_power_mode", async_set_dynamic_power_mode)
    hass.services.async_register(DOMAIN, "set_intensity", set_intensity)
    hass.services.async_register(DOMAIN, "set_min_intensity_slider", set_min_intensity_slider)
    hass.services.async_register(DOMAIN, "set_max_intensity_slider", set_max_intensity_slider)
    hass.services.async_register(DOMAIN, "set_dynamic_power_mode_slider", set_dynamic_power_mode_slider)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_set_min_intensity(hass: HomeAssistant, ip_address: str, min_intensity: int):
    #_LOGGER.debug(f"Setting min intensity to {min_intensity} at IP {ip_address}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/MinIntensity={min_intensity}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                #_LOGGER.debug(f"Min intensity set successfully to {min_intensity} at IP {ip_address}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error communicating with API: {err}")

async def async_set_max_intensity(hass, ip_address: str, max_intensity):
    #_LOGGER.debug(f"Setting max intensity to {max_intensity} at IP {ip_address}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/MaxIntensity={max_intensity}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                #_LOGGER.debug(f"Max intensity set successfully to {max_intensity} at IP {ip_address}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error communicating with API: {err}")

async def async_set_dynamic_power_mode(hass: HomeAssistant, ip_address: str, dynamic_power_mode: int):
    #_LOGGER.debug(f"Setting dynamic power mode to {dynamic_power_mode} at IP {ip_address}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/DynamicPowerMode={dynamic_power_mode}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                #_LOGGER.debug(f"Dynamic power mode set successfully to {dynamic_power_mode} at IP {ip_address}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error communicating with API: {err}")

async def async_set_intensity(hass, ip_address: str, intensity):
    #_LOGGER.debug(f"Setting intensity to {intensity} at IP {ip_address}")
    async with aiohttp.ClientSession() as session:
        url = f"http://{ip_address}/write/Intensity={intensity}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                #_LOGGER.debug(f"Intensity set successfully to {intensity} at IP {ip_address}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error communicating with API: {err}")
