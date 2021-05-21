# A simple class to read temperature from the TMP117 i2c temperature sensor
# Currently only supports reading temperature in C, F, K. Does not support
# alarms.

# This module has been tested with the following development boards:
#    • BBC Micro:bit
#    • Raspberry Pi Pico (RP2040)

# No warranties express or implied, including any warranty of merchantability and warranty of fitness for a particular purpose.
# Written by Michael Ruppe at Core Electronics MAR 2021
# Updated to work with unified PiicoDev i2c module.

from PiicoDev_Unified import *
i2c = PiicoDev_Unified_I2C()


# Register definitions
REG_TEMPC = b'\x00'

class PiicoDev_TMP117(object):    
    def __init__(self, addr = 0x48, i2c = i2c):
        self.i2c = i2c
        self.addr = addr
        
    
    def readTempC(self):
        data = self.i2c.read16(self.addr, REG_TEMPC)
        
#         self.i2c.UnifiedWrite(self.addr, REG_TEMPC)
#         data = self.i2c.UnifiedRead(self.addr, 2) # returns a bytes object
        tempDataRaw = int.from_bytes(data, 'big')
        # handle negatives (MicroPython int.from_bytes does not support signed conversion (yet)
        if tempDataRaw >= 0x8000:
            return -256.0 + (tempDataRaw - 0x8000) * 7.8125e-3 # One LSB equals 7.812 mdegC
        else:
            return tempDataRaw * 7.8125e-3 # One LSB equals 7.812 mdegC
    
    def readTempF(self):
        return (self.readTempC() * 9/5) + 32
        
    def readTempK(self):
        return self.readTempC() + 273.15
