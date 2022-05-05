# iaq-node-lora

Indoor air quality (IAQ) node built on Pycom LoPy4 hardware.

The measurement node is designed to be always on. The data is sent over LoRaWAN network.  

## Hardware

- Pycom LoPy4 (Espressif ESP32-based and MicroPython enabled development board)
- Sensirion SCD30. NDIR CO₂ gas sensor.
- Sensirion SPS30. Particulate matter (PM) sensor measuring PM1.0, PM2.5, PM4 and PM10.
- Sensirion SGP30. Multi-gas (VOC and CO₂eq) sensor.
