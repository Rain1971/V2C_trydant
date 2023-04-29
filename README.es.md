# CAR CHARGER V2C trydan component for HOME ASSISTANT

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/Rain1971/V2C_trydant.svg)](https://GitHub.com//Rain1971/V2C_trydant/releases/)
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/Rain1971/V2C_trydant/blob/main/README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](https://github.com/Rain1971/V2C_trydant/blob/main/README.es.md)

Esta integración expone la información y funciones disponibles en [V2C trydan](https://v2charge.com/trydan/) directamente a través de la interfaz http en Home Assistant.

# Prerequisitos:

Esta integración soporta la conexión de red a V2C trydan directamente, por lo que toma nota de la dirección IP estática de V2C trydan previamente.

Para una configuración posterior, necesitarás conocer los datos de consumo eléctrico de tu coche expresados en Kwh por 100 km

Si quieres usar la función de control de carga basada en el precio, debes instalar las siguientes integraciones para lovelace, desde HACS:
- [PVPC Hourly Pricing Card](https://github.com/danimart1991/pvpc-hourly-pricing-card) 
- [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row)

# Instalación:

* Añade este repositorio en HACS ( [https://github.com/Rain1971/V2C_trydant.git](https://github.com/Rain1971/V2C_trydant.git) )
![Charts](./images/install1.png)
![Charts](./images/install2.png)
* Reinicia Home Assistant
* Ve a Configuración -> Integraciones -> Añadir Integración
![Charts](./images/install3.png)
![Charts](./images/install4.png)
* Añade la integración y pon la IP de tu dispositivo
* Ve a la integración de V2C. Ahota hay 28 entidades. Pulsa en ajustes y configura:
   - Kwh x 100Km de tu coche (por defecto: 22)
   - Sensor.pvpc  ->( añade esto solo si quieres controlar la carga de tu coche en función del precio de la electricidad. Ver PVPC Hourly Pricing Card )
   ![Charts](./images/install5.png)
* Pulsa 'Enviar' y se creará una nueva entidad: sensor.v2c_precio_luz. Ahora hay 29 entidades.
* Reinicia Home Assistant
# Entities:

Se crean las siguientes entidades:

| Name                               | Type    | R/W  | Units        | Description                                    |
| :--------------------------------- | :------ | :--- | :----------- | :--------------------------------------------- |
| v2c_trydan_sensor_chargeenergy     | Sensor | R   | N kWh      | Current charging session energy in kWh.        
| v2c_trydan_sensor_chargekm  v2c_km_to_charge        | Sensor Number   | R \ W | N km     | Current charging session energy in Km.
| v2c_trydan_sensor_chargepower      | Sensor | R   | N W        | Current charging power in Watts.
| v2c_trydan_sensor_chargestate      | Sensor | R   | S `values`    | Charge Point. Spanish string States: `Manguera no conectada`, `Manguera conectada (NO CARGA)`,`Manguera conectada (CARGANDO)`
| v2c_trydan_numericalstatus         | Sensor | R   | N `values`    | Charge Point. Numerical Status: `0`-Hose Not connected, `1`-Hose Connected (BUT NOT CHARGING),`2`-Hose Connected (CHARGING)
| v2c_trydan_sensor_chargetime       | Sensor | R   | N s        | Current charging session time. 
| v2c_trydan_sensor_contractedpower  | Sensor | R   | N W        | House Contracted Power in Watts. Default `-1`
| vc2_trydan_sensor_dynamic          | Sensor | R   | N `values`    | Dynamic Intensity Modulation state: `0`-Disabled, `1`-Enabled
| vc2_trydan_sensor_dynamicpowermode | Sensor | R   | N `values`    | Dynamic Mode: 0 Timed Power enabled; `1`-Timed Power Disabled, `2`-Timed Power Disabled and Exclusive Mode setted, `3`-Timed Power Disabled and Min Power Mode setted, `4`-Timed Power Disabled and Grid+FV mode setted, `5`-Timed Power Disabled and Stop Mode setted
| vc2_trydan_sensor_fvpower          | Sensor | R   | N W        | Photovoltaic power generation in Watts.
| vc2_trydan_sensor_housepower       | Sensor | R   | N W        | House power consumption in Watts.
| v2c_trydan_sensor_intensity \   v2c_intensity      | Sensor Number | R \ W | N A        | Intensity offered by Charge Point in Amps, **if Dynamic Charge is disabled**. 
| v2c_trydan_sensor_locked           | Sensor | R   | N `values`    | Disabling state of Charge Point: `0`-Enabled, `1`-Disabled 
| v2c_trydan_sensor_maxintensity  v2c_max_intensity   | Sensor Number   | R \ W | N A        | Intensity offered maximun limit in Amps, **if Dynamic Charge is enabled**. (max default 32A)
| v2c_trydan_sensor_minintensity  v2c_min_intensity     | Sensor Number | R \ W | N A        | Intensity offered minimun limit in Amps, **if Dynamic Charge is enabled**. (max default 6A)
| v2c_trydan_sensor_paused           | Sensor | R   | N `values`    | Pause state of current charging session: `0`-Enabled, `1`-Disabled                
| v2c_trydan_sensor_pausedynamic     | Sensor | R   | N `values`    | Dynamic Control Modulation Pause State: `0`-Modulating, `1`-No Modulating
| v2c_trydan_sensor_slaveerror       | Sensor | R   | N `values`    | Slave communication state: `0`-No error, `1`-error message, `2`-Communication error
| v2c_trydan_sensor_timer            | Sensor | R   | N `values`    | Charge Point Timer state: `1`-Timer ON, `0`-Timer OFF
| v2c_precio_luz                     | Sensor | R   | state `attributes` | Data retrieved from api.esios.ree.es by REE. The `state` contains the current price and also these attributes: `state_class`, `measurement`, `tariff`, `period`, `available_power`, `next_period`, `hours_to_next_period`, `next_better_price`, `hours_to_better_price`,  `num_better_prices_ahead`, `price_position`, `price_ratio`, `max_price`, `max_price_at`, `min_price`, `min_price_at`, `next_best_at`, `price_00h` to `price_23h`, `unit_of_measurement`, `attribution`, `icon`, `friendly_name`, `ValidHours` (show at what times it will charge with that maximum price) and `TotalHours` (contains the total number of charging hours). These last two values are updated every 30 seconds and only if number.v2c_maxprice > 0 
| vc2_trydan_switch_dynamic          | Switch | R/W | `on` `off`    | Toggle to dynamic charge. Default `off`                       
| v2c_trydan_switch_paused           | Switch | R/W | `on` `off`    | Toggle to pause charge. Default `off`                        
| v2c_trydan_switch_locked           | Switch | R/W | `on` `off`    | Toggle to block the charger. Default `off`
| v2c_trydan_switch_v2c_carga_pvpc   | Switch | R/W | `on` `off`    | Toggle whether or not you want to charge while limiting by PVPC price . Default `off`


# Eventos:

Los siguientes eventos son creados:

| Event                              | Description                                   |
| :--------------------------------- |:--------------------------------------------- |
| v2c_trydan.charging_complete       | Event triggered when the energy corresponding to the selected kilometers has been charged. 

# Ejemplos:

* Puedes también usar una automatización para comprobar cuando el dispositivo ha cambiado el Km establecido:
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
* Usa [example.yaml](https://raw.githubusercontent.com/Rain1971/V2C_trydant/main/example.yaml) como ejemplo para crear tu propio sensor de carga o simplemente copia y pega el siguiente código en tu configuración de Home Assistant:

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

O USANDO control pvpc ( Necesitas tener configurado el sensor de pvpc ):
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
      - entity: sensor.v2c_precio_luz
      - entity: switch.v2c_trydan_switch_v2c_carga_pvpc
        name: Carga por Precio
      - entity: number.v2c_maxprice
        name: Precio MAX para cargar
      - type: custom:multiple-entity-row
        entity: sensor.v2c_precio_luz
        name: HORAS A LAS QUE CARGARÁ
        icon: mdi:hours-24
        show_state: false
        secondary_info:
          attribute: ValidHours
      - type: custom:multiple-entity-row
        entity: sensor.v2c_precio_luz
        name: TOTAL HORAS
        icon: mdi:sigma
        show_state: false
        secondary_info:
          attribute: TotalHours
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
