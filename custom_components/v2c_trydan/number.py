from homeassistant.components.number import NumberEntity
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.helpers import config_validation as cv
import logging
import aiohttp

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    ip_address = config_entry.data.get("ip_address", "")
    
    async_add_entities([MaxIntensityNumber(hass, ip_address)])
    async_add_entities([MinIntensityNumber(hass, ip_address)])
    async_add_entities([DynamicPowerModeNumber(hass, ip_address)])
    async_add_entities([KmToChargeNumber(hass)])
    async_add_entities([IntensityNumber(hass, ip_address)])
    async_add_entities([MaxPrice(hass)])

class MaxIntensityNumber(NumberEntity):
    def __init__(self, hass, ip_address):
        self._hass = hass
        self._state = 32
        self._ip_address = ip_address

    @property
    def unique_id(self):
        return "v2c_max_intensity"

    @property
    def name(self):
        return "v2c_max_intensity"

    @property
    def icon(self):
        return "mdi:car"

    @property
    def native_unit_of_measurement(self):
        return "A"

    @property
    def native_value(self):
        return self._state

    @property
    def native_max_value(self):
        return 32

    @property
    def native_min_value(self):
        return 6

    async def async_set_native_value(self, value):
        if 6 <= value <= 32:
            await self._set_max_intensity(value)
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_max_intensity must be between 6 and 32")
            
    async def _set_max_intensity(self, max_intensity):
        if not self._ip_address:
            _LOGGER.error("IP address not available for MaxIntensityNumber")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/MaxIntensity={max_intensity}"
                async with session.get(url) as response:
                    response.raise_for_status()
                    _LOGGER.debug(f"Max intensity set successfully to {max_intensity}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error setting max intensity: {err}")

class MinIntensityNumber(NumberEntity):
    def __init__(self, hass, ip_address):
        self._hass = hass
        self._state = 6
        self._ip_address = ip_address

    @property
    def unique_id(self):
        return "v2c_min_intensity"

    @property
    def name(self):
        return "v2c_min_intensity"

    @property
    def icon(self):
        return "mdi:car"

    @property
    def native_unit_of_measurement(self):
        return "A"

    @property
    def native_value(self):
        return self._state

    @property
    def native_max_value(self):
        return 32

    @property
    def native_min_value(self):
        return 6

    async def async_set_native_value(self, value):
        if 6 <= value <= 32:
            # Llamar directamente a la API en lugar de usar el servicio
            await self._set_min_intensity(value)
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_min_intensity must be between 6 and 32")
            
    async def _set_min_intensity(self, min_intensity):
        if not self._ip_address:
            _LOGGER.error("IP address not available for MinIntensityNumber")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/MinIntensity={min_intensity}"
                async with session.get(url) as response:
                    response.raise_for_status()
                    _LOGGER.debug(f"Min intensity set successfully to {min_intensity}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error setting min intensity: {err}")

class DynamicPowerModeNumber(NumberEntity):
    def __init__(self, hass, ip_address):
        self._hass = hass
        self._state = 0
        self._ip_address = ip_address

    @property
    def unique_id(self):
        return "v2c_dynamic_power_mode"

    @property
    def name(self):
        return "v2c_dynamic_power_mode"

    @property
    def icon(self):
        return "mdi:car"

    @property
    def native_unit_of_measurement(self):
        return ""

    @property
    def native_value(self):
        return self._state

    @property
    def native_max_value(self):
        return 7

    @property
    def native_min_value(self):
        return 0

    async def async_set_native_value(self, value):
        if 0 <= value <= 7:
            # Llamar directamente a la API en lugar de usar el servicio
            await self._set_dynamic_power_mode(value)
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_dynamic_power_mode must be between 0 and 7")
            
    async def _set_dynamic_power_mode(self, dynamic_power_mode):
        if not self._ip_address:
            _LOGGER.error("IP address not available for DynamicPowerModeNumber")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/DynamicPowerMode={dynamic_power_mode}"
                async with session.get(url) as response:
                    response.raise_for_status()
                    _LOGGER.debug(f"Dynamic power mode set successfully to {dynamic_power_mode}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error setting dynamic power mode: {err}")

class KmToChargeNumber(NumberEntity):
    def __init__(self, hass):
        self._hass = hass
        self._state = 0

    @property
    def unique_id(self):
        return "v2c_km_to_charge"

    @property
    def name(self):
        return "v2c_km_to_charge"

    @property
    def icon(self):
        return "mdi:car"

    @property
    def native_unit_of_measurement(self):
        return "km"

    @property
    def native_value(self):
        return self._state

    @property
    def native_max_value(self):
        return 1000

    @property
    def native_min_value(self):
        return 0

    async def async_set_native_value(self, value):
        if 0 <= value <= 1000:
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_km_to_charge must be between 0 and 1000")

class IntensityNumber(NumberEntity):
    def __init__(self, hass, ip_address):
        self._hass = hass
        self._state = 6
        self._ip_address = ip_address

    @property
    def unique_id(self):
        return "v2c_intensity"

    @property
    def name(self):
        return "v2c_intensity"

    @property
    def icon(self):
        return "mdi:car"

    @property
    def native_unit_of_measurement(self):
        return "A"

    @property
    def native_value(self):
        return self._state

    @property
    def native_max_value(self):
        return 32

    @property
    def native_min_value(self):
        return 6

    async def async_set_native_value(self, value):
        if self.native_min_value <= value <= self.native_max_value:
            await self._set_intensity(value)
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_intensity must be between {} and {}".format(self.native_min_value, self.native_max_value))
            
    async def _set_intensity(self, intensity):
        if not self._ip_address:
            _LOGGER.error("IP address not available for IntensityNumber")
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/Intensity={intensity}"
                async with session.get(url) as response:
                    response.raise_for_status()
                    _LOGGER.debug(f"Intensity set successfully to {intensity}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error setting intensity: {err}")

class MaxPrice(NumberEntity):
    def __init__(self, hass):
        self._hass = hass
        self._state = 0

    @property
    def unique_id(self):
        return "v2c_MaxPrice"

    @property
    def name(self):
        return "v2c_MaxPrice"

    @property
    def icon(self):
        return "mdi:currency-eur"

    @property
    def native_value(self):
        return self._state

    @property
    def native_step(self) -> float | None:
        return 0.001

    @property
    def native_max_value(self):
        return 1.000

    @property
    def native_min_value(self):
        return 0.000

    async def async_set_native_value(self, value):
        if 0 <= value <= 1.0:
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_MaxPrice must be between 0 and 1")