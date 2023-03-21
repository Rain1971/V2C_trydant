# V2C trydan component for HOME ASSISTANT

Control system for V2C trydan

# Setup:

* Add this repository in HACS
* Add integration and put there your device IP
* Use [example.yaml](https://raw.githubusercontent.com/Rain1971/V2C_trydant/main/example.yaml) as lovelance example or copy this code:

```
type: vertical-stack
cards:
  - type: markdown
    content: <CENTER><H1>CARGADOR COCHE</H1></CENTER>
  - type: gauge
    entity: sensor.v2c_trydant_sensor_fvpower
    severity:
      green: 0
      yellow: 8000
      red: 9500
    needle: true
    min: 0
    max: 10000
    name: Producción FV
  - type: gauge
    entity: sensor.v2c_trydant_sensor_housepower
    name: Consumo hogar
    severity:
      green: -10000
      yellow: 0
      red: 0
    needle: true
    min: -10000
    max: 10000
  - type: gauge
    entity: sensor.v2c_trydant_sensor_chargepower
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
      - entity: sensor.v2c_trydant_sensor_chargestate
        name: Estado
        secondary_info: none
      - entity: switch.v2c_trydant_switch_dynamic
        name: Control dinámico
        secondary_info: last-changed
      - entity: switch.v2c_trydant_switch_paused
        name: En pausa
        icon: mdi:play
        secondary_info: last-changed
      - entity: sensor.v2c_trydant_sensor_intensity
        name: Intensidad de carga
        secondary_info: last-changed
      - entity: sensor.v2c_trydant_sensor_minintensity
        name: Mínimo dinámica
        secondary_info: last-changed
      - entity: sensor.v2c_trydant_sensor_maxintensity
        name: Máximo dinámica
        secondary_info: last-changed
      - entity: sensor.v2c_trydant_sensor_chargeenergy
        name: Energía cargada
        secondary_info: none
      - entity: sensor.v2c_trydant_sensor_timer
        name: Tiempo de carga
```
