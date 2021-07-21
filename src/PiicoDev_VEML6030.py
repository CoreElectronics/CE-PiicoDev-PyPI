# PiicoDev VEML6030 Ambient Light Sensor piico.dev/p3
# Written by Michael Ruppe at Core Electronics MAR 2021

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
          
