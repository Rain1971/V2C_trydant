import logging
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_get_json(session, url):
    async with async_timeout.timeout(30):
        async with session.get(url) as response:
            return await response.json()

class V2C_trydantData:
    def __init__(self, ip_address):
        self._ip_address = ip_address
        self.attributes = {}

    async def async_update(self):
        url = f"http://{self._ip_address}/RealTimeData"
        async with aiohttp.ClientSession() as session:
            try:
                data = await async_get_json(session, url)
                self.attributes = data
                _LOGGER.debug(f"Fetched data from {url}: {data}")
            except Exception as e:
                raise UpdateFailed(f"Error fetching data from {url}: {e}")

class V2C_trydantSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, attribute):
        super().__init__(coordinator)
        self._attribute = attribute

    @property
    def name(self):
        return f"V2C_trydant {self._attribute}"

    @property
    def state(self):
        return self.coordinator.data.attributes.get(self._attribute)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("Setting up V2C_trydant platform")
    ip_address = hass.data[DOMAIN][CONF_IP_ADDRESS]
    charger_data = V2C_trydantData(ip_address)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="V2C_trydant",
        update_method=charger_data.async_update,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([V2C_trydantSensor(coordinator, attr) for attr in charger_data.attributes.keys()])