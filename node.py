"""
LoPy LoRaWAN NODE CLASS

---
IoT PLATFORM - PyCom LOPY4 LoRaWAN Node
Indoor Air Quality (IAQ) Sensor
Sensirion sensors: SGP30, SPS30, SCD30 
---

(c) Matteo M. 2022

"""
from network import LoRa
import machine
from machine import Timer
from machine import WDT
from machine import I2C
import pycom
import adafruit_sgp30
import scd30
import sps30
import socket
import struct
import ustruct
import ubinascii
import time
import utime
import math
import config



class Node: 
    """
    Main class for node operation
    """

    def __init__(self):
        """
        Contructor / initialization
        """
        
        # Internal variables
        self._timer = None
        self._wdt = None

        # Main variables
        self.lora = None
        self.sock = None
        self.lpp = None

        # SGP30 baselines
        self.tVOC_b_rx = None
        self.eCO2_b_rx = None

        self.baseline_manual = False

        # Readout fail (from sensors) flag
        self.fail_count = 0


    def start(self):
        """
        Main operations
        """
        # Initialize watchdog
        self._wdt = WDT(timeout=config.MEAS_INTERVAL*1000 + config.WATCHDOG*1000)

        # Initialize I2C
        self.i2c = I2C(0, I2C.MASTER)
        self.i2c.init(I2C.MASTER, baudrate=10000)
        time.sleep_ms(200)

        # Initialize sensors
        # SGP30
        self.sgp30 = adafruit_sgp30.Adafruit_SGP30(self.i2c)
        
        # SCD30
        time.sleep_ms(200)
        self.scd30 = scd30.SCD30(self.i2c)
        time.sleep_ms(100)
        self.scd30.set_measurement_interval(2)
        time.sleep_ms(100)
        self.scd30.start_continous_measurement()
        
        
        # SPS30
        time.sleep_ms(200)
        self.sps30 = sps30.SPS30(self.i2c)
        time.sleep_ms(200)
        self.sps30.start_measurement()



        # Add some jitter to avoid LoRa collisions between sensors on startup
        self._log('Waiting ' + str(config.JITTER) + 'ms ...')
        time.sleep_ms(config.JITTER)
    
        # Initialize LoRaWAN
        self.lora_connect()

        # Set a timer for measurements at a defined time interval 
        self._timer = Timer.Alarm(self.send_receive, config.MEAS_INTERVAL, periodic=True)


    def lora_connect(self):
        """
        Connection to LoRaWAN 
        """
       
        # Initialize LoRaWAN connection
        self.lora = LoRa(mode=LoRa.LORAWAN, adr=False, public=True, region=LoRa.EU868, device_class=LoRa.CLASS_C, tx_retries=1)
        
 
        # join a network using OTAA
        self.lora.join(
            activation=LoRa.OTAA, 
            auth=(config.A, config.B, config.C), 
            timeout=0, 
            dr=config.LORA_NODE_DR
        )

        # wait until the module has joined the network
        while not self.lora.has_joined():
            time.sleep(2.5)
            self._log('Not joined to LoRaWAN yet...')


        # create a LoRa socket
        self.sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # set the LoRaWAN data rate
        self.sock.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)

        # set confirmed message True
        self.sock.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

        # make the socket non-blocking
        self.sock.setblocking(False)

        time.sleep(5.0)
        
        # Set LoRa callback
        self.lora.callback(trigger=(LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT | LoRa.TX_FAILED_EVENT), handler=self._lora_cb)
        
        self._log('Connected to LoRaWAN')

        # Feed the watchdog
        self._wdt.feed()


    def send_receive(self,alarm):
        """
        Send measurements and receive messages through LoRaWAN
        """        
        
        # Check if sensors are working
        if len(self.i2c.scan()) < 3:
            self.fail_count += 1
        else:
            self.fail_count = 0     # Reset flag if everything is ok
    
        time.sleep_ms(200)
    
        if self.fail_count > 3:
            machine.reset() # Reboot if the sensors are still not working
        
        
        ###############
        # SGP30
        ###############
        
        # When baseline is received, set it at every cycle
        if self.baseline_manual: 
            self.sgp30.set_iaq_baseline(self.tVOC_b_rx,self.eCO2_b_rx) # Set the baselines on the sensor

        # Take measurements
        tVOC = float(self.sgp30.tvoc)
        eCO2 = float(self.sgp30.co2eq)
        
        tVOC_b = int(self.sgp30.baseline_tvoc)
        eCO2_b = int(self.sgp30.baseline_co2eq)


        ###############
        # SCD30
        ###############
        time.sleep_ms(200)
        scd_meas = self.scd30.read_measurement()
        CO2 = 9999
        T = 9999
        H = 9999

        if not math.isnan(scd_meas[0]):
            CO2 = scd_meas[0]
        if not math.isnan(scd_meas[1]):
            T = scd_meas[1]
        if not math.isnan(scd_meas[2]):
            H = scd_meas[2]


        ###############
        # SPS30
        ###############
        time.sleep_ms(200)

        PM1 = 9999
        PM2 = 9999
        PM4 = 9999
        PM10 = 9999

        if self.sps30.read_measured_values() != self.sps30.MEASURED_VALUES_ERROR:
            PM1 = self.sps30.measurement[0]
            PM2 = self.sps30.measurement[1]
            PM4 = self.sps30.measurement[2]
            PM10 = self.sps30.measurement[3]

        # Create measurement array
        m = [
                int(T*100), 
                int(H*100),
                float(CO2),
                float(tVOC),
                float(eCO2),
                int(PM1*10),
                int(PM2*10),
                int(PM4*10),
                int(PM10*10)
            ]
        
        # Pack payload
        pkt = bytes()
        for meas in m:
            fmrt = 'f'      # Default format: 32 bit float
            if isinstance(meas, int):
                fmrt = 'h'  # 16 bit signed integer
            # Concatenate bytes in the payload
            pkt += ustruct.pack(fmrt, meas)
        
        # Include baselines as unsigned integers (H)
        pkt += struct.pack('HH',tVOC_b,eCO2_b) 


        # Send payload
        self._log('Sending payload, size: ' + str(len(pkt)))
        self.sock.send(pkt)


        # Open receiving windows
        # Multiple messages may be received
        # CLASS-C LoRa can handle continuous listening on rx
        time.sleep(1.0)
        rx_status = True
        while rx_status:
            rx, port = self.sock.recvfrom(256)
            if rx:
                self._log('Received: {}, on port: {}'.format(rx, port))
                self.rx_handle(rx)   # Handle the received messages
                time.sleep(0.2)
            else:
                rx_status = False

        # Feed the watchdog
        self._wdt.feed()

        # Print LoRa statistics - for debugging
        self._log(self.lora.stats())


    def rx_handle(self,rx):
        """
        Handle the messages received through LoRaWAN
        """
        bytes_ = rx

        # Check which command has been received
        if (len(bytes_) > 1):  # The data received should be at least 2 bytes
            cmd = ustruct.unpack('H',bytes_[0:2])[0]
        else:
            cmd = 0x0000

        # 0x11 REBOOT
        if cmd == 0x0011:
            self._log('Received reboot command from LoRa')
            self._log('Rebooting ...')
            time.sleep(1.0)
            machine.reset() # reboot board
        
        # 0x12 SET MEASUREMENT INTERVAL
        if cmd == 0x0012:
            meas_int = ustruct.unpack('H',bytes_[2:4])[0]
            if (meas_int >= 30) and (meas_int <= 1800): # Check that the value is in the correct range
                pycom.nvs_set('MEAS_INTERVAL',meas_int) # Save to nvram
                self._log('The received measurement interval has been set. T =' + str(meas_int))
                time.sleep(1.0)
                machine.reset() # reboot board

        # 0x13 SET SGP30 BASELINE
        if cmd == 0x0013:
            self.tVOC_b_rx = ustruct.unpack('H',bytes_[2:4])[0]
            self.eCO2_b_rx = ustruct.unpack('H',bytes_[4:6])[0]
            self._log('SGP30 baseline values has been received: ' + str(self.tVOC_b_rx) +','+str(self.eCO2_b_rx))
            self.baseline_manual = True     # If baseline are received, switch mode to manual (e.g, always set the manual baseline)


    def _lora_cb(self, lora):
        """
        LoRa radio events callback handler.
        """
        events = lora.events()
        
        if events & LoRa.RX_PACKET_EVENT:
            self._log('LoRa RX ok')
        
        if events & LoRa.TX_PACKET_EVENT:
            self._log('LoRa TX ok')
        
        if events & LoRa.TX_FAILED_EVENT:
            self._log('LoRa TX failed')
            machine.reset() # REBOOT


    def _log(self, message, *args):
        """
        Outputs a log message to terminal
        """
        if config.DEBUG_MODE:
            print('[{:>10.3f}] {}'.format(
                utime.ticks_ms() / 1000,
                str(message).format(*args)
                ))