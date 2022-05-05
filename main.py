"""
LoPy LoRaWAN NODE - MAIN CODE

---
IoT PLATFORM - PyCom LOPY4 LoRaWAN Node
Indoor Air Quality (IAQ) Sensor
Sensirion sensors: SGP30, SPS30, SCD30 
---

(c) Matteo M. 2022

"""
import config
from node import Node

if __name__ == '__main__':
    # Initialize Node object
    n = Node()
    # Start node operation
    n.start()

    if config.DEBUG_MODE:
        # Enable REPL terminal - for debugging
        n._log('You may now press ENTER to enter the REPL')
        input()

