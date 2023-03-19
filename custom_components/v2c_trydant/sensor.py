import asyncio
import logging
import aiohttp
import async_timeout
from typing import Callable, Any
import datetime

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

async def async_get_json(session, url):
    async with async_timeout.timeout(30):
        async with session.get(url) as response:
            return await response.json(content_type=None)

async def async_setup_platform(hass: HomeAssistant, config: dict, async_add_entities: Callable[[list], Any], discovery_info=None):
    #ip_address = config.get(CONF_IP_ADDRESS)
    ip_address = "10.48.130.141"

    async def async_update_data():
        _LOGGER.debug(f"Fetching data from {ip_address}")
        async with aiohttp.ClientSession() as session:
            try:
                data = await async_get_json(session, f"http://{ip_address}/RealTimeData")
                _LOGGER.debug(f"Received data: {data}")
                return data
            except Exception as e:
                raise UpdateFailed(f"Error fetching data from {ip_address}: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="V2C_trydant_sensor",
        update_method=async_update_data,
        update_interval=datetime.timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([V2C_trydantSensor(coordinator, attr) for attr in coordinator.data.keys()], True)

class V2C_trydantSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, attribute):
        super().__init__(coordinator)
        self._attribute = attribute
        self._attr_name = f"V2C_trydant_{attribute}"
        self._attr_unique_id = f"v2c_trydant_{attribute}"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self.coordinator.data.get(self._attribute)