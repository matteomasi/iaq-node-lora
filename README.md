# iaq-node-lora

Indoor Air Quality (IAQ) node built on Pycom LoPy4 hardware, running [MicroPython](https://micropython.org/).

The node is designed to be always on. The data is sent to a gateway over the LoRaWAN network.
The code was tested by connecting the node to a private LoRa network (self-deployed with RAK-Wireless RAK7258 and RAK7268 gateways).  

## Hardware

- Pycom LoPy4 (Espressif ESP32-based and MicroPython enabled development board)
- Sensirion SCD30. NDIR CO₂ gas sensor.
- Sensirion SPS30. Particulate matter (PM) sensor measuring PM1.0, PM2.5, PM4 and PM10.
- Sensirion SGP30. Multi-gas (VOC and CO₂eq) sensor. The Adafruit SGP30 Air Quality Sensor Breakout was used in this project.

## I₂C addresses

| Device | Address |
| - | - |
| SCD30 | 0x61 |
| SPS30 | 0x69 |
| SGP30 | 0x58 |

## Usage

- Rename config_sample.py to config.py.
- Configure the LoRaWAN gateway by registering the device with its EUI.
- Edit settings in config.py.
- Upload the project to the LoPy4 board.

## LoRa payload format (uplink)

The payload is sent over LoRa with the format specified below:

| Position | Parameter | Format | Bytes | Scale |
| - | - | - | - | - |
| 1 | Temperature | int16 | 2 | 100 |
| 2 | Humidity | int16 | 2 | 100 |
| 3 | CO₂ | float | 4 | 1 |
| 4 | tVOC | float | 4 | 1 |
| 5 | eCO₂ | float | 4 | 1 |
| 6 | PM1 | int16 | 2 | 10 |
| 7 | PM2.5 | int16 | 2 | 10 |
| 8 | PM4.0 | int16 | 2 | 10 |
| 9 | PM10 | int16 | 2 | 10 |

## Messages received through LoRa (downlink)

The node is able to process the following incoming commands:

| Index | Description | Format | Data |
| - | - | - | - |
| 0x11 | Reboot | | |
| 0x12 | Set measurement interval | \<int16\> | Interval (seconds) |
| 0x13 | Set SGP30 baselines | \<int16\>\<int16\> | eCO2, tVOC |
