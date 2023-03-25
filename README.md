# V2C trydan component for HOME ASSISTANT

Control system for V2C trydan

# Setup:

* Add this repository in HACS ( [https://github.com/Rain1971/V2C_trydan.git](https://github.com/Rain1971/V2C_trydan.git) )
* Add integration and put there your device IP
* Go to the integration on settings->devices and set Kwh x 100Km of your car by pressing configure
* You can also use a automation to check when device has chaged the Km set:
```
alias: CARGA COCHE COMPLETA
description: CARGA COMPLETA
trigger:
  - platform: event
    event_type: v2c_trydan.charging_complete
action:
  - service: notify.notify
    data:
      message: La carga del vehículo ha alcanzado el límite de kilómetros.
  - service: notify.pushover
    data:
      message: KM del coche CARGADOS
      title: CARGADOR!
      data:
        priority: 1
    enabled: true
mode: single
```
* Use [example.yaml](https://raw.githubusercontent.com/Rain1971/V2C_trydan/main/example.yaml) as lovelance example or copy this code:

```
type: vertical-stack
cards:
  - type: markdown
    content: <CENTER><H1>CARGADOR COCHE</H1></CENTER>
  - type: gauge
    entity: sensor.v2c_trydan_sensor_fvpower
    severity:
      green: 0
      yellow: 8000
      red: 9500
    needle: true
    min: 0
    max: 10000
    name: Producción FV
  - type: gauge
    entity: sensor.v2c_trydan_sensor_housepower
    name: Consumo hogar
    severity:
      green: -10000
      yellow: 0
      red: 0
    needle: true
    min: -10000
    max: 10000
  - type: gauge
    entity: sensor.v2c_trydan_sensor_chargepower
    name: Cargando en el coche
    needle: true
    min: 0
    max: 8000
    severity:
      green: 0
      yellow: 7200
      red: 7700
  - type: entities
    entities:
      - entity: sensor.v2c_trydan_sensor_chargestate
        name: Estado
        secondary_info: none
      - entity: switch.v2c_trydan_switch_dynamic
        name: Control dinámico
        secondary_info: last-changed
      - entity: switch.v2c_trydan_switch_paused
        name: En pausa
        icon: mdi:play
        secondary_info: last-changed
      - entity: switch.v2c_trydan_switch_locked
        name: Bloquedado
        icon: mdi:play
        secondary_info: last-changed
      - entity: sensor.v2c_trydan_sensor_intensity
        name: Intensidad de carga
        secondary_info: last-changed
      - entity: sensor.v2c_trydan_sensor_minintensity
        name: Mínimo dinámica
        secondary_info: last-changed
      - entity: sensor.v2c_trydan_sensor_maxintensity
        name: Máximo dinámica
        secondary_info: last-changed
      - entity: sensor.v2c_trydan_sensor_chargeenergy
        name: Energía cargada
        secondary_info: none
      - entity: sensor.v2c_trydan_sensor_chargekm
        name: Km Cargados
        secondary_info: none
      - entity: sensor.v2c_trydan_sensor_chargetime
        name: Tiempo de carga
      - entity: number.v2c_min_intensity
        name: Ajusta Imin dinámica
      - entity: number.v2c_max_intensity
        name: Ajusta Imax dinámica
      - entity: number.v2c_km_to_charge
        name: Km a Cargar
        secondary_info: last-changed
```
