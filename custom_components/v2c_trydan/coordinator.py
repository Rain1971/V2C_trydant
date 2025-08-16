import logging
from datetime import timedelta
import json
import re
import aiohttp
from aiohttp import ClientError, client_exceptions, ClientSession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

_LOGGER = logging.getLogger(__name__)

def arreglar_json_invalido(json_str: str) -> dict:
    cadena = json_str.replace("1.6.13", "\"1.6.13\"")
    json_str_arreglado = cadena.replace("\"ReadyState\":", ",\"ReadyState\":")
    try:
        return json.loads(json_str_arreglado)
    except json.JSONDecodeError as e:
        _LOGGER.error(f"Error al parsear JSON: {str(e)}\nJSON: {json_str_arreglado}")
        raise UpdateFailed(f"Error al parsear los datos JSON: {str(e)}")

class V2CtrydanDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip_address):
        self.ip_address = ip_address
        self.error_reportado = False
        self._session = None
        self._consecutive_errors = 0
        self.MAX_CONSECUTIVE_ERRORS = 5

        super().__init__(
            hass, 
            _LOGGER, 
            name="v2c_trydan", 
            update_interval=timedelta(seconds=5),
            always_update=False
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            if self._session is None:
                self._session = async_get_clientsession(self.hass)
            
            data = await self._async_get_json(self._session, f"http://{self.ip_address}/RealTimeData")
            
            # Reset error tracking on successful update
            if self.error_reportado or self._consecutive_errors > 0:
                self.error_reportado = False
                self._consecutive_errors = 0
                _LOGGER.info(f"Connection to {self.ip_address} restored")
            
            return data
            
        except RetryError as e:
            self._consecutive_errors += 1
            if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                if not self.error_reportado:
                    self.error_reportado = True
                    _LOGGER.error(
                        f"Persistent connection issues with {self.ip_address} after {self._consecutive_errors} attempts. "
                        "Consider checking device connectivity."
                    )
            raise UpdateFailed(f"Failed to connect to {self.ip_address} after multiple retries: {e}")
            
        except Exception as e:
            self._consecutive_errors += 1
            if not self.error_reportado:
                self.error_reportado = True
                _LOGGER.error(f"Unexpected error communicating with {self.ip_address}: {e}")
            raise UpdateFailed(f"Error fetching data from {self.ip_address}: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _async_get_json(self, session, url):
        """Get JSON data from API with retry logic."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        # Try to fix malformed JSON
                        return arreglar_json_invalido(text)
                else:
                    response.raise_for_status()
                    
        except client_exceptions.ClientConnectorError as err:
            _LOGGER.debug(f"Connection error to {self.ip_address}: {err}")
            raise
        except client_exceptions.ServerTimeoutError as err:
            _LOGGER.debug(f"Timeout error to {self.ip_address}: {err}")
            raise
        except ClientError as err:
            _LOGGER.debug(f"HTTP client error to {self.ip_address}: {err}")
            raise
        except json.JSONDecodeError as e:
            _LOGGER.error(f"JSON parsing error from {self.ip_address}: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error fetching data from {self.ip_address}: {e}")
            raise