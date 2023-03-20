import logging
from datetime import timedelta

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, CONF_IP_ADDRESS
from .coordinator import V2CTrydantDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

class V2CTrydantDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip_address):
        self.ip_address = ip_address

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                data = await self._async_get_json(session, f"http://{self.ip_address}/RealTimeData")
                return data
        except Exception as e:
            raise UpdateFailed(f"Error fetching data from {self.ip_address}: {e}")

    async def _async_get_json(self, session, url):
        try:
            async with async_timeout.timeout(10):  # Ajusta el valor de timeout según sea necesario
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    coordinator = V2CTrydantDataUpdateCoordinator(hass, ip_address)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        V2CTrydantSensor(coordinator, ip_address, key)
        for key in coordinator.data.keys()
    ]
    async_add_entities(sensors)

class V2CTrydantSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, ip_address, data_key):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

    @property
    def name(self):
        return f"V2C Trydant Sensor {self._data_key}"

    @property
    def state(self):
        return self.coordinator.data[self._data_key]
