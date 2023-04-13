import logging
from datetime import timedelta

import aiohttp

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

class V2CtrydanDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip_address):
        self.ip_address = ip_address
        self.error_reported = False

        super().__init__(hass, logging.getLogger("null"), name="v2c_trydan", update_interval=timedelta(seconds=2))

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                data = await self._async_get_json(session, f"http://{self.ip_address}/RealTimeData")
                if self.error_reported:  # Restablece la variable y registra un mensaje de error cuando la comunicación es exitosa
                    self.error_reported = False
                    _LOGGER.error(f"Error resolved: Communication with {self.ip_address} restored")
                return data
        except Exception as e:
            if not self.error_reported:  # Registra el error solo si no se ha registrado antes
                self.error_reported = True
                raise UpdateFailed(f"Error fetching data from {self.ip_address}: {e}")
            else:
                raise UpdateFailed("Error communicating with API")

    async def _async_get_json(self, session, url):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except aiohttp.ClientError as err:
            if not self.error_reported:  # Registra el error solo si no se ha registrado antes
                self.error_reported = True
                _LOGGER.error(f"Error communicating with API: {err}")
                raise UpdateFailed("Error communicating with API")
            else:
                raise UpdateFailed("Error communicating with API")
        except Exception as e:
            if not self.error_reported:  # Registra el error solo si no se ha registrado antes
                self.error_reported = True
                _LOGGER.error(f"Error parsing JSON data: {e}")
                raise UpdateFailed("Error parsing JSON data")
            else:
                raise UpdateFailed("Error parsing JSON data")