import logging
import asyncio
from datetime import timedelta, datetime

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.const import (
    CONF_NAME,
    STATE_UNKNOWN,
    CONF_IP_ADDRESS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_state_change,
    async_call_later,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, CONF_KWH_PER_100KM, CONF_PRECIO_LUZ
from .coordinator import V2CtrydanDataUpdateCoordinator
from .number import KmToChargeNumber

DEPENDENCIES = ["switch"]

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

UPDATE_INTERVAL = timedelta(minutes=1)

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
    sensors.append(NumericalStatus(coordinator))

    await asyncio.sleep(10)

    precio_luz_entity = hass.states.get(config_entry.options[CONF_PRECIO_LUZ]) if CONF_PRECIO_LUZ in config_entry.options else None

    async def async_update_precio_luz(now):
        nonlocal precio_luz_entity
        if precio_luz_entity is not None:
            precio_luz_entity = hass.states.get(CONF_PRECIO_LUZ)

    if all([precio_luz_entity]):
        precio_luz_entity_instance = PrecioLuzEntity(coordinator, precio_luz_entity, ip_address)
        sensors.append(precio_luz_entity_instance)
        _LOGGER.debug("PrecioLuzEntity instance added to sensors list")

    async_add_entities(sensors)

class V2CtrydanSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, ip_address, data_key, kwh_per_100km):
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key
        self._kwh_per_100km = kwh_per_100km
        self.imax_old = 0
        self.imin_old = 0
        self.i_old = 0

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

    @property
    def name(self):
        return f"V2C trydan Sensor {self._data_key}"

    async def update_min_intensity(self, value):
        #_LOGGER.debug(f"Entity MinIntensity value")
        if self.imin_old != value:
            #_LOGGER.debug(f"Entity MinIntensity changed from {self.imin_old} to {value}")
            if self.hass.states.get("number.v2c_min_intensity") is not None:
                #_LOGGER.debug(f"Entity MinIntensity update 1000")
                await self.hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": "number.v2c_min_intensity", "value": float(value)},
                )
                self.imin_old = value

    async def update_max_intensity(self, value):
        if self.imax_old != value:
            if self.hass.states.get("number.v2c_max_intensity") is not None:
                await self.hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": "number.v2c_max_intensity", "value": float(value)},
                )
                self.imax_old = value

    async def update_intensity(self, value):
        if self.i_old != value:
            if self.hass.states.get("number.intensity") is not None:
                await self.hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": "number.intensity", "value": float(value)},
                )
                self.i_old = value

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        if self._data_key == "MinIntensity":
            self.hass.async_create_task(self.update_min_intensity(self.coordinator.data[self._data_key]))

        if self._data_key == "MaxIntensity":
            self.hass.async_create_task(self.update_max_intensity(self.coordinator.data[self._data_key]))

        if self._data_key == "Intensity":
            self.hass.async_create_task(self.update_intensity(self.coordinator.data[self._data_key]))

        self.async_on_remove(self.coordinator.async_add_listener(self.update_numbers))

    @callback
    def update_numbers(self):
        if self._data_key == "MinIntensity":
            self.hass.async_create_task(self.update_min_intensity(self.coordinator.data[self._data_key]))

        if self._data_key == "MaxIntensity":
            self.hass.async_create_task(self.update_max_intensity(self.coordinator.data[self._data_key]))

        if self._data_key == "Intensity":
            self.hass.async_create_task(self.update_intensity(self.coordinator.data[self._data_key]))


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
        elif self._data_key == "MinIntensity":
            return self.coordinator.data[self._data_key]
        elif self._data_key == "MaxIntensity":
            return self.coordinator.data[self._data_key]
        elif self._data_key == "Intensity":
            return self.coordinator.data[self._data_key]
        else:
            value = self.coordinator.data[self._data_key]
            if self._data_key in ["HousePower", "ChargePower", "FVPower"]:
                return round(value)
            else:
                return value

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
        self._charging_paused = False

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        async_track_time_interval(self.hass, self.check_and_pause_charging, timedelta(seconds=10))

    async def handle_paused_state_change(self, entity_id, old_state, new_state):
        if new_state is not None and old_state is not None:
            if new_state.state == "on" and old_state.state == "off":
                #_LOGGER.debug("Charging paused")
                await self.async_set_km_to_charge(0)
                self._charging_paused = True
            if new_state.state == "off" and old_state.state == "on":
                #_LOGGER.debug("Charging unpaused")
                self._charging_paused = False

    async def handle_km_to_charge_state_change(self, event):
        entity_id = event.data.get("entity_id")
        
        if entity_id == "number.v2c_km_to_charge":
            old_state = event.data.get("old_state")
            new_state = event.data.get("new_state")
            #_LOGGER.debug(f"Entity {entity_id} changed from {old_state} to {new_state}")

    async def async_set_km_to_charge(self, value):
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.v2c_km_to_charge", "value": value},
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        async_track_time_interval(self.hass, self.check_and_pause_charging, timedelta(seconds=10))
        async_track_state_change(self.hass, ["switch.v2c_trydan_switch_paused"], self.handle_paused_state_change)
        self.hass.bus.async_listen("state_changed", self.handle_km_to_charge_state_change)


    async def check_and_pause_charging(self, now):
        paused_switch = self.hass.states.get("switch.v2c_trydan_switch_paused")
        if paused_switch is not None and paused_switch.state == "on":
            return

        km_to_charge = self.hass.states.get("number.v2c_km_to_charge")
        if km_to_charge is not None:
            km_to_charge = float(km_to_charge.state)
            if self.state >= km_to_charge and km_to_charge != 0:
                await self.hass.services.async_call("switch", "turn_on", {"entity_id": "switch.v2c_trydan_switch_paused"})
                await self.async_set_km_to_charge(0)
                self.hass.bus.async_fire("v2c_trydan.charging_complete")

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

class NumericalStatus(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def unique_id(self):
        return "NumericalStatus"

    @property
    def name(self):
        return "V2C trydan NumericalStatus"

    @property
    def state(self):
        Charge_State = self.coordinator.data.get("ChargeState", "0")      
        if Charge_State == "Manguera no conectada":
            return 0
        elif Charge_State == "Manguera conectada (NO CARGA)":
            return 1
        elif Charge_State == "Manguera conectada (CARGANDO)":
            return 2
        else:
            return Charge_State  
        return -1

    @property
    def state_class(self):
        return "measurement"

class PrecioLuzEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, precio_luz_entity, ip_address):
        super().__init__(coordinator)
        self.v2c_precio_luz_entity = precio_luz_entity
        self.ip_address = ip_address

    @property
    def unique_id(self):
        return f"v2c_precio_luz_entity"

    @property
    def name(self):
        return "v2c Precio Luz"

    @property
    def state(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.state
        else:
            return None

    @property
    def extra_state_attributes(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.attributes
        else:
            return None

    @property
    def state_class(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.attributes.get("state_class", "measurement")
        else:
            return "measurement"

    @property
    def native_unit_of_measurement(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.attributes.get("unit_of_measurement", "€/kWh")
        else:
            return "€/kWh"

    async def async_added_to_hass(self):
        """Register update callback when added to hass."""
        paused_switch_id = f"{self.ip_address}_Paused"
        v2c_carga_pvpc_switch_id = f"v2c_carga_pvpc"
        max_price_entity_id = "v2c_MaxPrice"

        async def update_state(event_time):
            precio_luz_entity = self.v2c_precio_luz_entity

            entity_registry_instance = entity_registry.async_get(self.hass)
            for entity_id, entity_entry in entity_registry_instance.entities.items():
                if entity_entry.unique_id == paused_switch_id:
                    paused_switch = self.hass.data["switch"].get_entity(entity_id)
                if entity_entry.unique_id == v2c_carga_pvpc_switch_id:
                    v2c_carga_pvpc_switch = self.hass.data["switch"].get_entity(entity_id)
                if entity_entry.unique_id == max_price_entity_id:
                    max_price_entity = self.hass.states.get(entity_id)
            
            if all([precio_luz_entity, paused_switch, v2c_carga_pvpc_switch, max_price_entity]):
                max_price = float(max_price_entity.state)
                if v2c_carga_pvpc_switch.is_on:
                    # Comprueba si el precio está entre max_price
                    if float(self.state) <= max_price:
                        self.hass.async_create_task(paused_switch.async_turn_off())
                    else:
                        self.hass.async_create_task(paused_switch.async_turn_on())
            else:
                _LOGGER.debug("Hay entidades aun no creadas")
                if precio_luz_entity is None:
                    _LOGGER.debug(f"1 V2C precio_luz_entity: {precio_luz_entity}")
                if paused_switch is None:
                    _LOGGER.debug(f"1 V2C paused_switch: {paused_switch}")
                if v2c_carga_pvpc_switch is None:
                    _LOGGER.debug(f"1 V2C v2c_carga_pvpc_switch: {v2c_carga_pvpc_switch}")
                if max_price_entity is None:
                    _LOGGER.debug(f"1 V2C max_price_entity: {max_price_entity}")

        await update_state(None)

        async_track_time_interval(self.hass, update_state, timedelta(seconds=60))