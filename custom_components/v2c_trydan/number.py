from homeassistant.components.number import NumberEntity
from homeassistant.const import DEVICE_DEFAULT_NAME, CONF_IP_ADDRESS
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging
import aiohttp
import asyncio

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    _LOGGER.info(f"Setting up number entities with IP address: {ip_address}")
    
    async_add_entities([MaxIntensityNumber(hass, ip_address)])
    async_add_entities([MinIntensityNumber(hass, ip_address)])
    async_add_entities([KmToChargeNumber(hass)])
    async_add_entities([IntensityNumber(hass, ip_address)])
    async_add_entities([MaxPrice(hass)])

class MaxIntensityNumber(NumberEntity):
    """Representation of max intensity number entity."""
    
    def __init__(self, hass, ip_address):
        """Initialize the number entity."""
        self._hass = hass
        self._state = 32
        self._ip_address = ip_address
        self._attr_has_entity_name = True
        self._attr_translation_key = "max_intensity"

    @property
    def unique_id(self):
        return "v2c_max_intensity"

        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._ip_address)},
            name=f"V2C Trydan ({self._ip_address})",
            manufacturer="V2C",
            model="Trydan",
            configuration_url=f"http://{self._ip_address}",
        )

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
        # Convert to integer for the device
        int_value = int(value)
        if 6 <= int_value <= 32:
            await self._set_max_intensity(int_value)
            self._state = int_value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_max_intensity must be between 6 and 32")
            
    async def _set_max_intensity(self, max_intensity):
        """Set max intensity on the device."""
        if not self._ip_address:
            _LOGGER.error("IP address not available for MaxIntensityNumber")
            return
            
        session = async_get_clientsession(self._hass)
        url = f"http://{self._ip_address}/write/MaxIntensity={max_intensity}"
        try:
            timeout = aiohttp.ClientTimeout(total=5, connect=2)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                response_text = await response.text()
                
                # Check if device returned an error
                if response_text.strip().upper() == "ERROR":
                    _LOGGER.error(f"Device returned ERROR when setting max intensity to {max_intensity}")
                    raise ValueError(f"Device rejected max intensity value {max_intensity}")
        except asyncio.TimeoutError as err:
            _LOGGER.error(f"Timeout setting max intensity: {err}")
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP error setting max intensity: {err}")
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error setting max intensity: {err}")
            raise

class MinIntensityNumber(NumberEntity):
    """Representation of min intensity number entity."""
    
    def __init__(self, hass, ip_address):
        """Initialize the number entity."""
        self._hass = hass
        self._state = 6
        self._ip_address = ip_address
        self._attr_has_entity_name = True
        self._attr_translation_key = "min_intensity"

    @property
    def unique_id(self):
        return "v2c_min_intensity"

        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._ip_address)},
            name=f"V2C Trydan ({self._ip_address})",
            manufacturer="V2C",
            model="Trydan",
            configuration_url=f"http://{self._ip_address}",
        )

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
        # Convert to integer for the device
        int_value = int(value)
        if 6 <= int_value <= 32:
            await self._set_min_intensity(int_value)
            self._state = int_value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_min_intensity must be between 6 and 32")
            
    async def _set_min_intensity(self, min_intensity):
        """Set min intensity on the device."""
        if not self._ip_address:
            _LOGGER.error("IP address not available for MinIntensityNumber")
            return
            
        session = async_get_clientsession(self._hass)
        url = f"http://{self._ip_address}/write/MinIntensity={min_intensity}"
        try:
            timeout = aiohttp.ClientTimeout(total=5, connect=2)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                response_text = await response.text()
                
                # Check if device returned an error
                if response_text.strip().upper() == "ERROR":
                    _LOGGER.error(f"Device returned ERROR when setting min intensity to {min_intensity}")
                    raise ValueError(f"Device rejected min intensity value {min_intensity}")
        except asyncio.TimeoutError as err:
            _LOGGER.error(f"Timeout setting min intensity: {err}")
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP error setting min intensity: {err}")
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error setting min intensity: {err}")
            raise


class KmToChargeNumber(NumberEntity):
    """Representation of km to charge number entity."""
    
    def __init__(self, hass):
        """Initialize the number entity."""
        self._hass = hass
        self._state = 0
        self._attr_has_entity_name = True
        self._attr_translation_key = "km_to_charge"

    @property
    def unique_id(self):
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
    """Representation of intensity number entity."""
    
    def __init__(self, hass, ip_address):
        """Initialize the number entity."""
        self._hass = hass
        self._state = 6
        self._ip_address = ip_address
        self._attr_has_entity_name = True
        self._attr_translation_key = "intensity"

    @property
    def unique_id(self):
        return "v2c_intensity"

        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._ip_address)},
            name=f"V2C Trydan ({self._ip_address})",
            manufacturer="V2C",
            model="Trydan",
            configuration_url=f"http://{self._ip_address}",
        )

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
        # Convert to integer for the device
        int_value = int(value)
        if self.native_min_value <= int_value <= self.native_max_value:
            await self._set_intensity(int_value)
            self._state = int_value
            self.async_write_ha_state()
        else:
            _LOGGER.error("v2c_intensity must be between {} and {}".format(self.native_min_value, self.native_max_value))
            
    async def _set_intensity(self, intensity):
        """Set intensity on the device."""
        if not self._ip_address:
            _LOGGER.error("IP address not available for IntensityNumber")
            return
            
        session = async_get_clientsession(self._hass)
        url = f"http://{self._ip_address}/write/Intensity={intensity}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                _LOGGER.debug(f"Intensity set successfully to {intensity}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error setting intensity: {err}")
            raise

class MaxPrice(NumberEntity):
    """Representation of max price number entity."""
    
    def __init__(self, hass):
        """Initialize the number entity."""
        self._hass = hass
        self._state = 0
        self._attr_has_entity_name = True
        self._attr_translation_key = "max_price"

    @property
    def unique_id(self):
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