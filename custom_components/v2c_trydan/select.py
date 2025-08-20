from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging
import aiohttp
import asyncio
import json
import re

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

def _parse_response_json(text: str, content_type: str = '') -> dict:
    """Parse JSON response, handling V2C firmware issues.
    
    Handles:
    - Incorrect Content-Type (text instead of application/json)
    - Duplicate FirmwareVersion fields
    """
    # Log content-type issues for debugging
    if content_type and 'application/json' not in content_type.lower():
        _LOGGER.debug(f"Device returned non-JSON content-type: {content_type}, parsing as JSON anyway")
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        _LOGGER.debug("JSON parsing failed, attempting to fix malformed response")
        
        # Remove duplicate FirmwareVersion fields (keep the last one)
        firmware_pattern = r'"FirmwareVersion":"[^"]*",'
        matches = list(re.finditer(firmware_pattern, text))
        if len(matches) > 1:
            # Remove all but the last occurrence
            for match in matches[:-1]:
                text = text[:match.start()] + text[match.end():]
        
        # Try to parse again
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Failed to parse malformed JSON: {e}")
            raise

# Dynamic Power Mode options with translation keys
DYNAMIC_POWER_MODE_OPTIONS = [
    "enable_timed_power",                    # 0
    "disable_timed_power",                   # 1
    "disable_timed_power_exclusive",         # 2
    "disable_timed_power_min",               # 3
    "disable_timed_power_grid_fv",           # 4
    "disable_timed_power_stop",              # 5
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    
    async_add_entities([DynamicPowerModeSelect(hass, ip_address)])

class DynamicPowerModeSelect(SelectEntity):
    """Representation of Dynamic Power Mode selector entity."""
    
    def __init__(self, hass, ip_address):
        """Initialize the select entity."""
        self._hass = hass
        self._ip_address = ip_address
        self._current_option = None
        self._attr_has_entity_name = True
        self._attr_options = DYNAMIC_POWER_MODE_OPTIONS
        self._attr_translation_key = "dynamic_power_mode"

    @property
    def unique_id(self):
        return "v2c_dynamic_power_mode_select"

        
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
        return "mdi:cog"

    @property
    def current_option(self):
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self._attr_options:
            _LOGGER.error(f"Invalid option: {option}")
            return
            
        # Get the numeric value for this option
        mode_value = self._attr_options.index(option)
        
        await self._set_dynamic_power_mode(mode_value)
        self._current_option = option
        self.async_write_ha_state()

    async def _set_dynamic_power_mode(self, mode_value: int):
        """Set dynamic power mode on the device."""
        if not self._ip_address:
            _LOGGER.error("IP address not available for DynamicPowerModeSelect")
            return
            
        session = async_get_clientsession(self._hass)
        url = f"http://{self._ip_address}/write/DynamicPowerMode={mode_value}"
        try:
            timeout = aiohttp.ClientTimeout(total=5, connect=2)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                response_text = await response.text()
                
                # Check if device returned an error
                if response_text.strip().upper() == "ERROR":
                    _LOGGER.error(f"Device returned ERROR when setting dynamic power mode to {mode_value}")
                    raise ValueError(f"Device rejected dynamic power mode value {mode_value}")
        except asyncio.TimeoutError as err:
            _LOGGER.error(f"Timeout setting dynamic power mode: {err}")
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP error setting dynamic power mode: {err}")
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error setting dynamic power mode: {err}")
            raise

    async def async_update(self):
        """Fetch the current state from the device."""
        if not self._ip_address:
            return
            
        session = async_get_clientsession(self._hass)
        url = f"http://{self._ip_address}/RealTimeData"
        try:
            timeout = aiohttp.ClientTimeout(total=5, connect=2)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                
                # Handle firmware response issues
                text = await response.text()
                content_type = response.headers.get('content-type', '')
                data = _parse_response_json(text, content_type)
                
                # Get the DynamicPowerMode value from the response
                dynamic_power_mode = data.get("DynamicPowerMode")
                if dynamic_power_mode is not None and 0 <= dynamic_power_mode <= 5:
                    self._current_option = self._attr_options[dynamic_power_mode]
                else:
                    _LOGGER.warning(f"Invalid DynamicPowerMode value: {dynamic_power_mode}")
                    
        except (asyncio.TimeoutError, aiohttp.ClientError, ValueError) as err:
            _LOGGER.error(f"Error fetching dynamic power mode: {err}")
        except Exception as err:
            _LOGGER.error(f"Unexpected error fetching dynamic power mode: {err}")