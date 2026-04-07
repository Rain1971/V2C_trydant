import logging
import asyncio
from datetime import timedelta, datetime, timezone

import aiohttp
import re
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
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.const import EntityCategory
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_state_change_event,
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
    "BatteryPower": SensorDeviceClass.POWER,
    "Intensity": SensorDeviceClass.CURRENT,
    "MinIntensity": SensorDeviceClass.CURRENT,
    "MaxIntensity": SensorDeviceClass.CURRENT,
    "ContractedPower": SensorDeviceClass.POWER,
    "VoltageInstallation": SensorDeviceClass.VOLTAGE,
    # Text sensors configuration
    "ChargeState": SensorDeviceClass.ENUM,  # Fixed states
    "ChargeTime": None,  # Dynamic time format
    "FirmwareVersion": None,  # Dynamic version - diagnostic
    "ReadyState": None,  # Numeric state
    "Timer": None,  # Timer value
    "Dynamic": None,  # Boolean/numeric state
    "DynamicPowerMode": None,  # Mode indicator
    "Locked": None,  # Boolean state
    "Paused": None,  # Boolean state
    "PauseDynamic": None,  # Boolean state
    "SlaveError": None,  # Error indicator
    "IP": None,  # IP address - diagnostic
    "SignalStatus": None,  # WiFi signal status
    "SSID": None,  # WiFi network name - diagnostic
    "ID": None,  # Device ID - diagnostic
}

# Translation keys for sensor entities
TRANSLATION_KEY_MAP = {
    "ChargeEnergy": "chargeenergy",
    "ChargePower": "chargepower",
    "ChargeState": "chargestate",
    "ChargeTime": "chargetime",
    "ContractedPower": "contractedpower",
    "Dynamic": "dynamic",
    "DynamicPowerMode": "dynamicpowermode",
    "FVPower": "fvpower",
    "HousePower": "housepower",
    "BatteryPower": "batterypower",
    "Intensity": "intensity",
    "Locked": "locked",
    "MaxIntensity": "maxintensity",
    "MinIntensity": "minintensity",
    "Paused": "paused",
    "PauseDynamic": "pausedynamic",
    "SlaveError": "slaveerror",
    "Timer": "timer",
    "FirmwareVersion": "firmware_version",
    "ReadyState": "readystate",
    "VoltageInstallation": "voltageinstallation",
    "IP": "ip",
    "SignalStatus": "signalstatus",
    "SSID": "ssid",
    "ID": "id",
}

STATE_CLASS_MAP = {
    "ChargeEnergy": "total_increasing",
    "ChargePower": "measurement",
    "HousePower": "measurement",
    "FVPower": "measurement",
    "BatteryPower": "measurement",
    "Intensity": "measurement",
    "MinIntensity": "measurement",
    "MaxIntensity": "measurement",
    "ReadyState": "measurement",
    "ContractedPower": "measurement",
    "Timer": "measurement",
    "Dynamic": "measurement",
    "DynamicPowerMode": "measurement",
    "Locked": "measurement",
    "Paused": "measurement",
    "PauseDynamic": "measurement",
    "SlaveError": "measurement",
    "VoltageInstallation": "measurement",
    "SignalStatus": "measurement",
}

NATIVE_UNIT_MAP = {
    "ChargePower": "W",
    "ChargeEnergy": "kWh",
    "HousePower": "W",
    "FVPower": "W",
    "BatteryPower": "W",
    "Intensity": "A",
    "MinIntensity": "A",
    "MaxIntensity": "A",
    "ContractedPower": "W",
    "VoltageInstallation": "V",
    # Text sensors and state sensors must have None for units
    "ChargeTime": None,
    "FirmwareVersion": None,
    "ReadyState": None,
    "Timer": None,
    "Dynamic": None,
    "DynamicPowerMode": None,
    "Locked": None,
    "Paused": None,
    "PauseDynamic": None,
    "SlaveError": None,
    "IP": None,
    "SignalStatus": None,
    "SSID": None,
    "ID": None,
}

# Options for ENUM sensors
SENSOR_OPTIONS_MAP = {
    "ChargeState": [
        "Manguera no conectada",
        "Manguera conectada (NO CARGA)",
        "Manguera conectada (CARGANDO)",
    ]
}

# Entity categories for diagnostic sensors
ENTITY_CATEGORY_MAP = {
    "FirmwareVersion": EntityCategory.DIAGNOSTIC,  # Diagnostic information
    "ChargeTime": None,  # Main operational data
    "ChargeState": None,  # Main operational data
    "IP": EntityCategory.DIAGNOSTIC,  # Diagnostic information
    "SSID": EntityCategory.DIAGNOSTIC,  # Diagnostic information
    "ID": EntityCategory.DIAGNOSTIC,  # Diagnostic information
    "SignalStatus": EntityCategory.DIAGNOSTIC,  # Diagnostic information
}

UPDATE_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up V2C Trydan sensors from a config entry."""
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    kwh_per_100km = config_entry.options.get(CONF_KWH_PER_100KM, 15)

    # Get coordinator from domain data (already created in __init__.py)
    coordinator = hass.data[DOMAIN].get(config_entry.entry_id)
    if not coordinator:
        # Create coordinator as fallback
        _LOGGER.info("Creating coordinator as fallback for sensor platform")
        coordinator = V2CtrydanDataUpdateCoordinator(hass, ip_address)
        try:
            await coordinator.async_config_entry_first_refresh()
            hass.data[DOMAIN][config_entry.entry_id] = coordinator
        except Exception as e:
            _LOGGER.error(f"Failed to setup coordinator: {e}")
            return

    # Create sensors only if coordinator has data
    sensors = []
    if coordinator.data:
        sensors = [
            V2CtrydanSensor(
                coordinator, ip_address, key, kwh_per_100km, config_entry.entry_id
            )
            for key in coordinator.data.keys()
        ]
        sensors.append(ChargeKmSensor(coordinator, ip_address, kwh_per_100km))
        sensors.append(NumericalStatus(coordinator, ip_address))

        # Add PVPC price sensor if configured
        precio_luz_entity_id = config_entry.options.get(CONF_PRECIO_LUZ)
        if precio_luz_entity_id:
            precio_luz_entity = hass.states.get(precio_luz_entity_id)
            sensors.append(
                PrecioLuzEntity(
                    coordinator, precio_luz_entity, ip_address, config_entry
                )
            )
            if precio_luz_entity is not None:
                _LOGGER.debug("PrecioLuzEntity added to sensors list")
            else:
                # Create sensor anyway - it will work once the entity becomes available
                _LOGGER.warning(
                    f"PVPC entity '{precio_luz_entity_id}' not found yet, but creating sensor anyway"
                )

    else:
        _LOGGER.warning("No coordinator data available, sensors will not be created")

    async_add_entities(sensors, update_before_add=True)


class V2CtrydanSensor(CoordinatorEntity, SensorEntity):
    """Representation of a V2C Trydan sensor."""

    def __init__(
        self, coordinator, ip_address, data_key, kwh_per_100km, config_entry_id
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key
        self._kwh_per_100km = kwh_per_100km
        self._config_entry_id = config_entry_id
        self.imax_old = 0
        self.imin_old = 0
        self.i_old = 0
        self.carga_previo = 0
        self._last_reset = None
        self._attr_has_entity_name = True
        # Set translation key if available
        self._attr_translation_key = TRANSLATION_KEY_MAP.get(data_key)

    @property
    def unique_id(self):
        return f"{self._ip_address}_{self._data_key}"

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
    def state_class(self):
        """Return the state class of the sensor."""
        state_class_str = STATE_CLASS_MAP.get(self._data_key)
        if state_class_str == "total_increasing":
            return SensorStateClass.TOTAL_INCREASING
        elif state_class_str == "measurement":
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def options(self):
        """Return the list of available options for ENUM sensors."""
        return SENSOR_OPTIONS_MAP.get(self._data_key)

    @property
    def entity_category(self):
        """Return the entity category for diagnostic sensors."""
        return ENTITY_CATEGORY_MAP.get(self._data_key)

    async def update_min_intensity(self, value):
        # _LOGGER.debug(f"Entity MinIntensity value")
        if self.imin_old != value:
            # _LOGGER.debug(f"Entity MinIntensity changed from {self.imin_old} to {value}")
            if self.hass.states.get("number.v2c_min_intensity") is not None:
                # _LOGGER.debug(f"Entity MinIntensity update 1000")
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

        if self.coordinator.data is None:
            return

        if self._data_key == "MinIntensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_min_intensity(self.coordinator.data[self._data_key])
            )

        if self._data_key == "MaxIntensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_max_intensity(self.coordinator.data[self._data_key])
            )

        if self._data_key == "Intensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_intensity(self.coordinator.data[self._data_key])
            )

        self.async_on_remove(self.coordinator.async_add_listener(self.update_numbers))

    @callback
    def update_numbers(self):
        if self.coordinator.data is None:
            return

        if self._data_key == "MinIntensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_min_intensity(self.coordinator.data[self._data_key])
            )

        if self._data_key == "MaxIntensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_max_intensity(self.coordinator.data[self._data_key])
            )

        if self._data_key == "Intensity" and self._data_key in self.coordinator.data:
            self.hass.async_create_task(
                self.update_intensity(self.coordinator.data[self._data_key])
            )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        if self._data_key == "ChargeState":
            current = self.coordinator.data.get(self._data_key)
            if current is None:
                return None
            if current == 0:
                self.carga_previo = 0
                return "Manguera no conectada"
            elif current == 1:
                # if self.carga_previo == 2:
                #    self.hass.bus.async_fire("v2c_trydan.charging_complete")
                self.carga_previo = 1
                return "Manguera conectada (NO CARGA)"
            elif current == 2:
                self.carga_previo = 2
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
            return self.coordinator.data.get(self._data_key)
        elif self._data_key == "MaxIntensity":
            return self.coordinator.data.get(self._data_key)
        elif self._data_key == "Intensity":
            return self.coordinator.data.get(self._data_key)
        else:
            value = self.coordinator.data.get(self._data_key)
            if value is None:
                return None
            if self._data_key in [
                "HousePower",
                "ChargePower",
                "FVPower",
                "BatteryPower",
            ]:
                try:
                    return round(float(value))
                except (ValueError, TypeError):
                    return None
            else:
                return value

    @property
    def available(self):
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP.get(self._data_key)

    @property
    def native_unit_of_measurement(self):
        return NATIVE_UNIT_MAP.get(self._data_key)

    @property
    def last_reset(self):
        if self.state_class == "total":
            if self.state == 0:
                self._last_reset = datetime.now(timezone.utc)
            return self._last_reset
        return None


class ChargeKmSensor(CoordinatorEntity, SensorEntity):
    """Representation of a V2C Trydan charge km sensor."""

    def __init__(self, coordinator, ip_address, kwh_per_100km):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._kwh_per_100km = kwh_per_100km
        self._charging_paused = False
        self._attr_has_entity_name = True

    async def handle_paused_state_change(self, event):
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if new_state is not None and old_state is not None:
            if new_state.state == "on" and old_state.state == "off":
                # _LOGGER.debug("Charging paused")
                await self.async_set_km_to_charge(0)
                self._charging_paused = True
            if new_state.state == "off" and old_state.state == "on":
                # _LOGGER.debug("Charging unpaused")
                self._charging_paused = False

    async def handle_km_to_charge_state_change(self, event):
        entity_id = event.data.get("entity_id")

        if entity_id == "number.v2c_km_to_charge":
            old_state = event.data.get("old_state")
            new_state = event.data.get("new_state")
            # _LOGGER.debug(f"Entity {entity_id} changed from {old_state} to {new_state}")

    async def async_set_km_to_charge(self, value):
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.v2c_km_to_charge", "value": value},
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        async_track_time_interval(
            self.hass, self.check_and_pause_charging, timedelta(seconds=10)
        )
        async_track_state_change_event(
            self.hass,
            ["switch.v2c_trydan_switch_paused"],
            self.handle_paused_state_change,
        )
        self.hass.bus.async_listen(
            "state_changed", self.handle_km_to_charge_state_change
        )

    async def check_and_pause_charging(self, now):
        paused_switch = self.hass.states.get("switch.v2c_trydan_switch_paused")
        if paused_switch is not None and paused_switch.state == "on":
            return

        km_to_charge = self.hass.states.get("number.v2c_km_to_charge")
        if km_to_charge is not None:
            try:
                try:
                    km_to_charge_float = float(km_to_charge.state)
                except ValueError:
                    km_to_charge_float = -1.0

                if self.state >= km_to_charge_float and km_to_charge_float != 0:
                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        {"entity_id": "switch.v2c_trydan_switch_paused"},
                    )
                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        {"entity_id": "switch.v2c_trydan_switch_locked"},
                    )
                    await self.async_set_km_to_charge(0)
                    self.hass.bus.async_fire("v2c_trydan.charging_complete")
            except Exception as e:
                _LOGGER.error(
                    f"Error en carga de kilometros el valor esperado es: {km_to_charge.state} y el error {e}"
                )

    @property
    def unique_id(self):
        return f"{self._ip_address}_ChargeKm"

    @property
    def name(self):
        return "V2C trydan Sensor ChargeKm"

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
    def native_value(self):
        charge_energy = self.coordinator.data.get("ChargeEnergy", 0)
        charge_km = (charge_energy / (self._kwh_per_100km / 100)) * 0.92
        return round(charge_km, 2)

    @property
    def device_class(self):
        return SensorDeviceClass.DISTANCE

    @property
    def native_unit_of_measurement(self):
        return "km"

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT


class NumericalStatus(CoordinatorEntity, SensorEntity):
    """Representation of a V2C Trydan numerical status sensor."""

    def __init__(self, coordinator, ip_address):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._attr_has_entity_name = True

    @property
    def unique_id(self):
        return "NumericalStatus"

    @property
    def name(self):
        return "V2C trydan NumericalStatus"

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
    def native_value(self):
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
        return SensorStateClass.MEASUREMENT


class PrecioLuzEntity(CoordinatorEntity, SensorEntity):
    """Representation of a V2C Trydan price sensor."""

    def __init__(self, coordinator, precio_luz_entity, ip_address, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.v2c_precio_luz_entity = precio_luz_entity
        self.config_entry = config_entry
        self.ip_address = ip_address
        self._attr_extra_state_attributes = (
            {
                **precio_luz_entity.attributes,
                "ValidHours": "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23",
                "ValidHoursNextDay": "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23",
                "TotalHours": 24,
            }
            if precio_luz_entity is not None
            else {}
        )

        self._attr_has_entity_name = True

    @property
    def unique_id(self):
        return "v2c_precio_luz_entity"

    @property
    def name(self):
        return "v2c Precio Luz"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.ip_address)},
            name=f"V2C Trydan ({self.ip_address})",
            manufacturer="V2C",
            model="Trydan",
            configuration_url=f"http://{self.ip_address}",
        )

    @property
    def native_value(self):
        if self.v2c_precio_luz_entity is not None:
            try:
                return float(self.v2c_precio_luz_entity.state)
            except (ValueError, TypeError):
                return None
        else:
            return None

    @property
    def state_class(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.attributes.get(
                "state_class", "measurement"
            )
        else:
            return "measurement"

    @property
    def native_unit_of_measurement(self):
        if self.v2c_precio_luz_entity is not None:
            return self.v2c_precio_luz_entity.attributes.get(
                "unit_of_measurement", "€/kWh"
            )
        else:
            return "€/kWh"

    async def async_added_to_hass(self):
        """Register update callback when added to hass."""
        paused_switch_id = f"{self.ip_address}_Paused"
        v2c_carga_pvpc_switch_id = f"v2c_carga_pvpc"
        max_price_entity_id = "v2c_MaxPrice"

        async def find_entities():
            entity_registry_instance = entity_registry.async_get(self.hass)
            entities = {}
            for entity_id, entity_entry in entity_registry_instance.entities.items():
                if entity_entry.unique_id == paused_switch_id:
                    entities["paused_switch"] = self.hass.states.get(entity_id)
                if entity_entry.unique_id == v2c_carga_pvpc_switch_id:
                    entities["v2c_carga_pvpc_switch"] = self.hass.states.get(entity_id)
                if entity_entry.unique_id == max_price_entity_id:
                    entities["max_price_entity"] = self.hass.states.get(entity_id)
            return entities

        async def extract_price_attrs(precio_luz_entity, max_price, current_hour):
            valid_hours = []
            valid_hours_next_day = []
            total_hours = 0
            attributes = precio_luz_entity.attributes

            for i in range(24):
                price_attr = f"price_{i:02d}h"
                next_day_price_attr = f"price_next_day_{i:02d}h"

                if (
                    price_attr in attributes
                    and float(attributes[price_attr]) <= max_price
                ):
                    if i > current_hour:
                        valid_hours.append(i)
                        total_hours += 1

                if (
                    next_day_price_attr in attributes
                    and float(attributes[next_day_price_attr]) <= max_price
                ):
                    valid_hours_next_day.append(i)
                    total_hours += 1

            return valid_hours, valid_hours_next_day, total_hours

        async def pause_or_resume_charging(
            current_state, max_price, paused_switch, v2c_carga_pvpc_switch
        ):
            if v2c_carga_pvpc_switch.state == "on":
                try:
                    if float(current_state) <= max_price:
                        await self.hass.services.async_call(
                            "switch", "turn_off", {"entity_id": paused_switch.entity_id}
                        )
                    else:
                        await self.hass.services.async_call(
                            "switch", "turn_on", {"entity_id": paused_switch.entity_id}
                        )
                except (ValueError, TypeError):
                    _LOGGER.info(f"Current state is {current_state}")

        async def update_state(event_time):
            entities = await find_entities()
            paused_switch = entities.get("paused_switch")
            v2c_carga_pvpc_switch = entities.get("v2c_carga_pvpc_switch")
            max_price_entity = entities.get("max_price_entity")
            precio_luz_entity_id = self.config_entry.options.get(CONF_PRECIO_LUZ)

            if precio_luz_entity_id:
                await self.hass.services.async_call(
                    "homeassistant",
                    "update_entity",
                    {"entity_id": precio_luz_entity_id},
                )
                precio_luz_entity = self.hass.states.get(precio_luz_entity_id)
            else:
                precio_luz_entity = None

            if all(
                [
                    precio_luz_entity,
                    paused_switch,
                    v2c_carga_pvpc_switch,
                    max_price_entity,
                ]
            ):
                try:
                    max_price = float(max_price_entity.state)
                except (ValueError, TypeError):
                    max_price = 0.0
                current_hour = datetime.now().hour

                (
                    valid_hours,
                    valid_hours_next_day,
                    total_hours,
                ) = await extract_price_attrs(
                    precio_luz_entity, max_price, current_hour
                )

                self._attr_extra_state_attributes.update(
                    {
                        **precio_luz_entity.attributes,
                        "ValidHours": valid_hours,
                        "ValidHoursNextDay": valid_hours_next_day,
                        "TotalHours": total_hours,
                    }
                )

                await pause_or_resume_charging(
                    precio_luz_entity.state,
                    max_price,
                    paused_switch,
                    v2c_carga_pvpc_switch,
                )

                self.v2c_precio_luz_entity = precio_luz_entity

                self.async_write_ha_state()
            else:
                _LOGGER.debug("Hay entidades aun no creadas")

        await update_state(None)

        async_track_time_interval(self.hass, update_state, timedelta(seconds=30))
