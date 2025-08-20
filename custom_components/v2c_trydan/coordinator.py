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
    """Fix malformed JSON responses from V2C Trydan devices.
    
    Handles common issues:
    - Duplicated FirmwareVersion fields
    - Missing quotes on version numbers
    - Malformed structure
    """
    # Remove duplicate FirmwareVersion fields (keep the last one)
    firmware_pattern = r'"FirmwareVersion":"[^"]*",'
    matches = list(re.finditer(firmware_pattern, json_str))
    if len(matches) > 1:
        # Remove all but the last occurrence
        for match in matches[:-1]:
            json_str = json_str[:match.start()] + json_str[match.end():]
    
    # Fix version numbers without quotes
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
        """Get JSON data from API with retry logic.
        
        Handles firmware issues:
        - Incorrect Content-Type (text instead of application/json)
        - Malformed JSON with duplicate fields
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text()
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Log content-type issues for debugging
                    if 'application/json' not in content_type:
                        _LOGGER.debug(f"Device returned non-JSON content-type: {content_type}, parsing as JSON anyway")
                    
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        # Try to fix malformed JSON
                        _LOGGER.debug(f"JSON parsing failed, attempting to fix malformed response")
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