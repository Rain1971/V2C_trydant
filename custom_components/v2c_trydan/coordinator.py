import logging
from datetime import timedelta
import json
import re
import aiohttp
from aiohttp import ClientError, client_exceptions
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from tenacity import retry, stop_after_attempt, wait_fixed

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

        super().__init__(hass, logging.getLogger("null"), name="v2c_trydan", update_interval=timedelta(seconds=2))

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                data = await self._async_get_json(session, f"http://{self.ip_address}/RealTimeData")
                if self.error_reportado:  # Reinicia la variable y registra un mensaje de error cuando la comunicación es exitosa
                    self.error_reportado = False
                    _LOGGER.error(f"Error resuelto: Comunicación con {self.ip_address} restaurada")
                return data
        except Exception as e:
            if not self.error_reportado:  # Registra el error solo si no se ha registrado antes
                self.error_reportado = True
                _LOGGER.error(f"Error al obtener los datos de {self.ip_address}: {e}")
                raise UpdateFailed(f"Error al obtener los datos de {self.ip_address}: {e}")
            else:
                raise UpdateFailed("Error al comunicarse con la API")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def _async_get_json(self, session, url):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
                return json.loads(text)
        except client_exceptions.ClientConnectorError as err:
            self.error_reportado = True
            _LOGGER.error(f"Error al comunicarse con la API: {err}")
            raise UpdateFailed("Error al comunicarse con la API")
        except ClientError as err:
            if not self.error_reportado:  # Registra el error solo si no se ha registrado antes
                self.error_reportado = True
                _LOGGER.error(f"Error al comunicarse con la API: {err}")
                raise UpdateFailed("Error al comunicarse con la API")
            else:
                raise UpdateFailed("Error al comunicarse con la API")
        except Exception as e:
            if not self.error_reportado:  # Registra el error solo si no se ha registrado antes
                self.error_reportado = True
                _LOGGER.error(f"Error al parsear los datos JSON: {e}")
                raise UpdateFailed("Error al parsear los datos JSON")
            else:
                raise UpdateFailed("Error al parsear los datos JSON")