import logging
from datetime import timedelta

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .coordinator import V2CTrydantDataUpdateCoordinator
from .const import DOMAIN, CONF_IP_ADDRESS

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

class V2CTrydantDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip_address):
        self.ip_address = ip_address

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=2))

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                data = await self._async_get_json(session, f"http://{self.ip_address}/RealTimeData")
                return data
        except Exception as e:
            raise UpdateFailed(f"Error fetching data from {self.ip_address}: {e}")

    async def _async_get_json(self, session, url):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    coordinator = V2CTrydantDataUpdateCoordinator(hass, ip_address)
    await coordinator.async_config_entry_first_refresh()

    switches = [
        V2CTrydantSwitch(coordinator, ip_address, key)
        for key in ["Paused", "Dynamic"]
    ]
    async_add_entities(switches)

class V2CTrydantSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, ip_address, data_key):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

    @property
    def name(self):
        return f"V2C Trydant Switch {self._data_key}"

    @property
    def is_on(self):
        return bool(self.coordinator.data[self._data_key])

    async def async_turn_on(self, **kwargs):
        async with aiohttp.ClientSession() as session:
            url = f"http://{self._ip_address}/write/{self._data_key}=1"
            async with session.get(url) as response:
                response.raise_for_status()
                await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        async with aiohttp.ClientSession() as session:
            url = f"http://{self._ip_address}/write/{self._data_key}=0"
            async with session.get(url) as response:
                response.raise_for_status()
                await self.coordinator.async_request_refresh()
