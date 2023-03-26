# CAR CHARGER V2C trydan component for HOME ASSISTANT

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/Rain1971/V2C_trydant.svg)](https://GitHub.com//Rain1971/V2C_trydant/releases/)

This integration exposes the information and functions made available by [V2C trydan](https://v2charge.com/trydan/) directly via http interface in Home Assistant.

# Prerequisites

This integration supports network connection to V2C trydan directly, so that take note of the V2C trydan static IP address previously. 

For a later configuration, you need to know the electrical consumption data of your car expressed in Kwh per 100 km

# Setup:

* Add this repository in HACS ( [https://github.com/Rain1971/V2C_trydant.git](https://github.com/Rain1971/V2C_trydant.git) )
* Add integration and put there your device IP
* Go to the integration on settings->devices and set Kwh x 100Km of your car by pressing configure

# Entities:

The following entities are created:  

| Name                               | Type    | R/W  | Units   | Description                                    |
| :--------------------------------- | :------ | :--- | :------ | :--------------------------------------------- |
| v2c_trydan_sensor_chargeenergy     | Sensor | R   | N kWh    | Current charging session energy in kWh.        
| v2c_trydan_sensor_chargekm         | Sensor | R/W | N km     | Current charging session energy in Km.
| v2c_trydan_sensor_chargepower      | Sensor | R   | N W      | Current charging power in Watts.
| v2c_trydan_sensor_chargestate      | Sensor | R   | S `values`  | Charge Point. States: `Manguera no conectada`, `Manguera conectada (NO CARGA)`,`Manguera conectada (CARGANDO)`
| v2c_trydan_sensor_chargetime       | Sensor | R   | N s      | Current charging session time. 
| v2c_trydan_sensor_contractedpower  | Sensor | R   | N W      | House Contracted Power in Watts. Default `-1`
| vc2_trydan_sensor_dynamic          | Sensor | R   | N `values`  | Dynamic Intensity Modulation state: `0`-Disabled, `1`-Enabled
| vc2_trydan_sensor_dynamicpowermode | Sensor | R   | N `values`  | Dynamic Mode: 0 Timed Power enabled; `1`-Timed Power Disabled, `2`-Timed Power Disabled and Exclusive Mode setted, `3`-Timed Power Disabled and Min Power Mode setted, `4`-Timed Power Disabled and Grid+FV mode setted, `5`-Timed Power Disabled and Stop Mode setted
| vc2_trydan_sensor_fvpower          | Sensor | R   | N W      | Photovoltaic power generation in Watts.
| vc2_trydan_sensor_housepower       | Sensor | R   | N W      | House power consumption in Watts.
| v2c_trydan_sensor_intensity        | Sensor | R/W | N A      | Intensity offered by Charge Point in Amps, **if Dynamic Charge is disabled**. 
| v2c_trydan_sensor_locked           | Sensor | R   | N `values`  | Disabling state of Charge Point: `0`-Enabled, `1`-Disabled 
| v2c_trydan_sensor_maxintensity     | Sensor | R/W | N A      | Intensity offered maximun limit in Amps, **if Dynamic Charge is enabled**. (max default 32A)
| v2c_trydan_sensor_minintensity     | Sensor | R/W | N A      | Intensity offered minimun limit in Amps, **if Dynamic Charge is enabled**. (max default 6A)
| v2c_trydan_sensor_paused           | Sensor | R   | N `values`  | Pause state of current charging session: `0`-Enabled, `1`-Disabled                
| v2c_trydan_sensor_pausedynamic     | Sensor | R   | N `values`  | Dynamic Control Modulation Pause State: `0`-Modulating, `1`-No Modulating
| v2c_trydan_sensor_slaveerror       | Sensor | R   | N `values`  | Slave communication state: `0`-No error, `1`-error message, `2`-Communication error
| v2c_trydan_sensor_timer            | Sensor | R   | N `values`  | Charge Point Timer state: `1`-Timer ON, `0`-Timer OFF
| vc2_trydan_switch_dynamic          | Switch | R/W | `on` `off`  | Toggle to dynamic charge. Default `off`                       
| v2c_trydan_switch_paused           | Switch | R/W | `on` `off`  | Toggle to pause charge. Default `off`                        
| v2c_trydan_switch_locked           | Switch | R/W | `on` `off`  | Toggle to block the charger. Default `off`

# Examples:
* You can also use a automation to check when device has changed the Km set:
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
* Use [example.yaml](https://raw.githubusercontent.com/Rain1971/V2C_trydant/main/example.yaml) as lovelace example or copy this code:

```
type: vertical-stack
cards:
  - type: markdown
    content: <CENTER><H1>CARGADOR COCHE</H1></CENTER>
  - type: horizontal-stack
    cards:
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
      - entity: number.v2c_km_to_charge
        name: Km a Cargar
        secondary_info: last-changed
        icon: mdi:car-arrow-right
  - type: conditional
    conditions:
      - entity: switch.v2c_trydan_switch_dynamic
        state: 'on'
    card:
      type: entities
      entities:
        - entity: number.v2c_min_intensity
          name: Ajusta Imin dinámica
          icon: mdi:current-ac
        - entity: number.v2c_max_intensity
          name: Ajusta Imax dinámica
          icon: mdi:current-ac
  - type: conditional
    conditions:
      - entity: switch.v2c_trydan_switch_dynamic
        state: 'off'
    card:
      type: entities
      entities:
        - entity: number.v2c_intensity
          name: Ajusta ICarga
          icon: mdi:current-ac
```
