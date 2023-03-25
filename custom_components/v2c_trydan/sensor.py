import logging
from datetime import timedelta, datetime

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, CONF_KWH_PER_100KM
from .coordinator import V2CtrydanDataUpdateCoordinator
from .number import KmToChargeNumber

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

DEVICE_CLASS_MAP = {
    "ChargePower": SensorDeviceClass.POWER,
    "ChargeEnergy": SensorDeviceClass.ENERGY,
    "HousePower": SensorDeviceClass.POWER,
    "FVPower": SensorDeviceClass.POWER,
    "Intensity": SensorDeviceClass.CURRENT,
    "MinIntensity": SensorDeviceClass.CURRENT,
    "MaxIntensity": SensorDeviceClass.CURRENT
}

STATE_CLASS_MAP = {
    "ChargeEnergy": "total"
}

NATIVE_UNIT_MAP = {
    "ChargePower": "W",
    "ChargeEnergy": "kWh",
    "HousePower": "W",
    "FVPower": "W",
    "Intensity": "A",
    "MinIntensity": "A",
    "MaxIntensity": "A"
}

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    kwh_per_100km = config_entry.options.get(CONF_KWH_PER_100KM, 15)
    coordinator = V2CtrydanDataUpdateCoordinator(hass, ip_address)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        V2CtrydanSensor(coordinator, ip_address, key, kwh_per_100km)
        for key in coordinator.data.keys()
    ]
    sensors.append(ChargeKmSensor(coordinator, ip_address, kwh_per_100km))
    async_add_entities(sensors)

class V2CtrydanSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, ip_address, data_key, kwh_per_100km):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key
        self._kwh_per_100km = kwh_per_100km

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

    @property
    def name(self):
        return f"V2C trydan Sensor {self._data_key}"

    @property
    def state(self):
        if self._data_key == "ChargeState":
            current = self.coordinator.data[self._data_key]
            if current == 0:
                return "Manguera no conectada"
            elif current == 1:
                return "Manguera conectada (NO CARGA)"
            elif current == 2:
                return "Manguera conectada (CARGANDO)"
            else:
                return current
        elif self._data_key == "ChargeTime":
            charge_time_seconds = self.coordinator.data.get("ChargeTime", 0)
            hours = charge_time_seconds // 3600
            minutes = (charge_time_seconds % 3600) // 60
            seconds = charge_time_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return self.coordinator.data[self._data_key]

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP.get(self._data_key, "")

    @property
    def native_unit_of_measurement(self):
        return NATIVE_UNIT_MAP.get(self._data_key, "")

    @property
    def last_reset(self):
        if self.state_class == "total":
            return datetime.fromisoformat('2011-11-04')
        return None

    @property
    def state_class(self):
        return STATE_CLASS_MAP.get(self._data_key, "measurement")

class ChargeKmSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, ip_address, kwh_per_100km):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._kwh_per_100km = kwh_per_100km

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        async_track_time_interval(self.hass, self.check_and_pause_charging, timedelta(seconds=10))

    async def check_and_pause_charging(self, now):
        _LOGGER.debug("Checking if it's necessary to pause charging")
        km_to_charge = self.hass.states.get("number.v2c_km_to_charge")
        if km_to_charge is not None:
            km_to_charge = float(km_to_charge.state)
            if self.state >= km_to_charge and km_to_charge != 0:
                _LOGGER.debug("Pausing charging and resetting km to charge")
                await self.hass.services.async_call("switch", "turn_on", {"entity_id": "switch.v2c_trydan_switch_paused"})
                self.hass.states.async_set("number.v2c_km_to_charge", 0)

    @property
    def unique_id(self):
        return f"{self._ip_address}_ChargeKm"

    @property
    def name(self):
        return "V2C trydan Sensor ChargeKm"

    @property
    def state(self):
        charge_energy = self.coordinator.data.get("ChargeEnergy", 0)
        charge_km = charge_energy / ((self._kwh_per_100km / 100) * 0.8)
        return round(charge_km, 2)

    @property
    def device_class(self):
        return SensorDeviceClass.DISTANCE

    @property
    def native_unit_of_measurement(self):
        return "km"

    @property
    def state_class(self):
        return "measurement"