import logging
import aiohttp
import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import V2CtrydanDataUpdateCoordinator
from .const import DOMAIN, CONF_PRECIO_LUZ

_LOGGER = logging.getLogger(__name__)

# Translation keys for switch entities
SWITCH_TRANSLATION_KEY_MAP = {
    "Dynamic": "dynamic",
    "Paused": "paused",
    "Locked": "locked",
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    ip_address = config_entry.data[CONF_IP_ADDRESS]

    # Get coordinator from domain data (already created in __init__.py)
    coordinator = hass.data[DOMAIN].get(config_entry.entry_id)
    if not coordinator:
        # Create coordinator as fallback
        _LOGGER.info("Creating coordinator as fallback for switch platform")
        coordinator = V2CtrydanDataUpdateCoordinator(hass, ip_address)
        try:
            await coordinator.async_config_entry_first_refresh()
            hass.data[DOMAIN][config_entry.entry_id] = coordinator
        except Exception as e:
            _LOGGER.error(f"Failed to setup coordinator: {e}")
            return

    switches = [
        V2CtrydanSwitch(coordinator, ip_address, key)
        for key in ["Paused", "Dynamic", "Locked"]
    ]
    _LOGGER.info(
        f"Created {len(switches)} basic switches: {[s.__class__.__name__ for s in switches]}"
    )

    # Only add PVPC switch if precio_luz entity is configured
    if CONF_PRECIO_LUZ in config_entry.options:
        precio_luz_entity_id = config_entry.options[CONF_PRECIO_LUZ]
        _LOGGER.info(f"PVPC entity configured: {precio_luz_entity_id}")

        # Check if entity exists and log all available PVPC entities for debugging
        all_pvpc_entities = [
            state.entity_id
            for state in hass.states.async_all()
            if "pvpc" in state.entity_id.lower()
        ]
        _LOGGER.info(f"Available PVPC entities: {all_pvpc_entities}")

        precio_luz_entity = hass.states.get(precio_luz_entity_id)
        switches.append(
            V2CCargaPVPCSwitch(precio_luz_entity, precio_luz_entity_id, ip_address)
        )
        if precio_luz_entity is not None:
            _LOGGER.info(f"Added PVPC switch, total switches: {len(switches)}")
        else:
            # Create switch anyway - it will work once the entity becomes available
            _LOGGER.warning(
                f"PVPC entity '{precio_luz_entity_id}' not found yet, but creating switch anyway"
            )
            _LOGGER.info(
                f"Added PVPC switch (will activate when entity available), total switches: {len(switches)}"
            )
    else:
        _LOGGER.info("PVPC entity not configured in options")

    _LOGGER.info(f"Setting up {len(switches)} switches total")
    async_add_entities(switches)


class V2CtrydanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a V2C Trydan switch."""

    def __init__(self, coordinator, ip_address, data_key):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._ip_address = ip_address
        self._data_key = data_key
        self._attr_has_entity_name = True
        # Set translation key if available
        self._attr_translation_key = SWITCH_TRANSLATION_KEY_MAP.get(data_key)

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
    def is_on(self):
        """Return true if switch is on."""
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get(self._data_key, False))

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        session = async_get_clientsession(self.hass)
        url = f"http://{self._ip_address}/write/{self._data_key}=1"
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                await self.coordinator.async_request_refresh()
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error turning on switch {self._data_key}: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        session = async_get_clientsession(self.hass)
        url = f"http://{self._ip_address}/write/{self._data_key}=0"
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                await self.coordinator.async_request_refresh()
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error turning off switch {self._data_key}: {e}")
            raise


class V2CCargaPVPCSwitch(SwitchEntity):
    def __init__(self, precio_luz_entity, precio_luz_entity_id, ip_address):
        self._is_on = False
        self.precio_luz_entity = precio_luz_entity
        self._ip_address = ip_address
        self._precio_luz_entity_id = precio_luz_entity_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "carga_pvpc"
        _LOGGER.info(
            f"Initialized V2CCargaPVPCSwitch with entity: {self._precio_luz_entity_id}"
        )

    @property
    def unique_id(self):
        return f"v2c_carga_pvpc"

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
    def name(self):
        return "V2C trydan Switch v2c_carga_pvpc"

    @property
    def is_on(self):
        return self._is_on

    @property
    def available(self):
        """Return if entity is available."""
        # Try to refresh PVPC entity if not available
        if self.precio_luz_entity is None:
            self.precio_luz_entity = self.hass.states.get(self._precio_luz_entity_id)

        # Entity is available if we have PVPC entity or if it exists in hass.states
        return (
            self.precio_luz_entity is not None
            or self.hass.states.get(self._precio_luz_entity_id) is not None
        )

    async def async_turn_on(self, **kwargs):
        # Try to get entity dynamically if not available during init
        if self.precio_luz_entity is None:
            self.precio_luz_entity = self.hass.states.get(self._precio_luz_entity_id)

        if (
            self.precio_luz_entity is not None
            or self.hass.states.get(self._precio_luz_entity_id) is not None
        ):
            self._is_on = True
            _LOGGER.info(
                f"V2C PVPC switch turned ON - monitoring {self._precio_luz_entity_id}"
            )
        else:
            self._is_on = False
            _LOGGER.warning(
                f"Cannot turn on PVPC switch - entity {self._precio_luz_entity_id} not found"
            )

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        _LOGGER.info(f"V2C PVPC switch turned OFF")

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        await super().async_added_to_hass()

        # Check if PVPC entity is available after being added to hass
        if self.precio_luz_entity is None:
            self.precio_luz_entity = self.hass.states.get(self._precio_luz_entity_id)
            if self.precio_luz_entity is not None:
                _LOGGER.info(
                    f"PVPC entity {self._precio_luz_entity_id} found after being added to hass"
                )
                # Update the entity state to reflect availability
                self.async_write_ha_state()
