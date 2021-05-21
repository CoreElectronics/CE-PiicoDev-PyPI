# A simple class to read data from the VEML i2c light sensor

# This module has been tested with the following development boards:
#    • BBC Micro:bit
#    • Raspberry Pi Pico (RP2040)

# No warranties express or implied, including any warranty of merchantability and warranty of fitness for a particular purpose.
# Written by Michael Ruppe at Core Electronics MAR 2021
# Updated to work with unified PiicoDev i2c module.

from PiicoDev_Unified import *
i2c = PiicoDev_Unified_I2C()

# Registers
_veml6030Address = 0x10
_ALS_CONF = b'\x00'
_REG_ALS = b'\x04'

_DEFAULT_SETTINGS = b'\x00' # initialise gain:1x, integration 100ms, persistence 1, disable interrupt

class PiicoDev_VEML6030(object):    
    def __init__(self, addr=_veml6030Address, i2c=i2c):
        self.i2c = i2c
        self.addr = addr
        self.res = 0.0288 # lx/bit
        self.i2c.write8(self.addr, _ALS_CONF, _DEFAULT_SETTINGS)
        
    def read(self):
        data = self.i2c.read16(self.addr, _REG_ALS)
        return int.from_bytes(data, 'little') * self.res
          
