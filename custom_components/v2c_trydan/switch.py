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

from .coordinator import V2CtrydanDataUpdateCoordinator
from .const import DOMAIN, CONF_PRECIO_LUZ

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    coordinator = V2CtrydanDataUpdateCoordinator(hass, ip_address)
    await coordinator.async_config_entry_first_refresh()

    # Obtén precio_luz_entity
    precio_luz_entity = hass.states.get(config_entry.options[CONF_PRECIO_LUZ]) if CONF_PRECIO_LUZ in config_entry.options else None

    switches = [
        V2CtrydanSwitch(coordinator, ip_address, key)
        for key in ["Paused", "Dynamic", "Locked"]
    ]

    switches.append(V2CCargaPVPCSwitch(precio_luz_entity))

    async_add_entities(switches)

class V2CtrydanSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, ip_address, data_key):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

    @property
    def name(self):
        return f"V2C trydan Switch {self._data_key}"

    @property
    def is_on(self):
        return bool(self.coordinator.data[self._data_key])

    async def async_turn_on(self, **kwargs):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/{self._data_key}=1"
                async with session.get(url) as response:
                    response.raise_for_status()
                    await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning on switch: {e}")

    async def async_turn_off(self, **kwargs):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._ip_address}/write/{self._data_key}=0"
                async with session.get(url) as response:
                    response.raise_for_status()
                    await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning off switch: {e}")

class V2CCargaPVPCSwitch(SwitchEntity):
    def __init__(self, precio_luz_entity):
        self._is_on = False
        self.precio_luz_entity = precio_luz_entity

    @property
    def unique_id(self):
        return f"v2c_carga_pvpc"

    @property
    def name(self):
        return "V2C trydan Switch v2c_carga_pvpc"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        if self.precio_luz_entity is not None:
            self._is_on = True
        else:
            self._is_on = False

    async def async_turn_off(self, **kwargs):
        self._is_on = False
