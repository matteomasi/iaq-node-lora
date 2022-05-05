"""
LoPy LoRaWAN NODE configuration options

---
IoT PLATFORM - PyCom LOPY4 LoRaWAN Node
Indoor Air Quality (IAQ) Sensor
Sensirion sensors: SGP30, SPS30, SCD30 
---

(c) Matteo M. 2022

"""
import pycom
from network import LoRa


# Measurement interval
MEAS_INTERVAL = 120                 # DEFAULT INTERVAL (seconds)

# If nvram has a value for measurement interval set it, else take the default value
try:
    M_INT = pycom.nvs_get('MEAS_INTERVAL')
    if (M_INT >= 30) and (M_INT <= 1200): # Check that the value is in the correct range (from 30 s to 20 min)
        MEAS_INTERVAL = M_INT

except Exception:
    pycom.nvs_set('MEAS_INTERVAL',MEAS_INTERVAL)


# Watchdog timer (MUST be > MEAS_INTERVAL)
WATCHDOG = MEAS_INTERVAL + 30       # seconds

# Jitter to avoid LoRa collision between devices (must be different for each node)
JITTER = 0                          # ms

# LoRa frequency settings  for EU868
LORA_FREQUENCY = 868100000          # Node frequency
LORA_NODE_DR = 5                    # Data rate 


# Node settings - OTAA authentication params
# DEV EUI
lora = LoRa()
A = lora.mac()
# APP EUI
B = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
# APP KEY
C = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ])


# Debugging mode
DEBUG_MODE = True

"""
LORA AVAILABLE SETTINGS:

Frequencies: 
868.1 - SF7BW125 to SF12BW125
868.3 - SF7BW125 to SF12BW125 and SF7BW250
868.5 - SF7BW125 to SF12BW125
867.1 - SF7BW125 to SF12BW125
867.3 - SF7BW125 to SF12BW125
867.5 - SF7BW125 to SF12BW125
867.7 - SF7BW125 to SF12BW125
867.9 - SF7BW125 to SF12BW125

Data rates:
DR  SF      BW (kHz)    bit/s   Max. payload (bytes)
0   SF12    125         250     51
1   SF11    125         440     51
2   SF10    125         980     51
3   SF9     125         1,760   115
4   SF8     125         3,125   242
5   SF7     125         5,470   242
6   SF7     250         11,000  242    

"""