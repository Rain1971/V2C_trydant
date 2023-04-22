from homeassistant.components.number import NumberEntity
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.helpers import config_validation as cv
import logging
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):

    async_add_entities([MaxIntensityNumber(hass)])
    async_add_entities([MinIntensityNumber(hass)])
    async_add_entities([KmToChargeNumber(hass)])
    async_add_entities([IntensityNumber(hass)])
    async_add_entities([MaxPrice(hass)])

class MaxIntensityNumber(NumberEntity):
    def __init__(self, hass):
        self._hass = hass
        self._state = 32

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
            await self._hass.services.async_call(DOMAIN, "set_max_intensity_slider", {"v2c_max_intensity": value})
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_max_intensity must be between 6 and 32")

class MinIntensityNumber(NumberEntity):
    def __init__(self, hass):
        self._hass = hass
        self._state = 6

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
            await self._hass.services.async_call(DOMAIN, "set_min_intensity_slider", {"v2c_min_intensity": value})
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_min_intensity must be between 6 and 32")

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
    def __init__(self, hass):
        self._hass = hass
        self._state = 6

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
            await self._hass.services.async_call(DOMAIN, "set_intensity", {"intensity": value})
            self._state = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_intensity must be between {} and {}".format(self.native_min_value, self.native_max_value))

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