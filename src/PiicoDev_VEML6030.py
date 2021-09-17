# PiicoDev VEML6030 Ambient Light Sensor piico.dev/p3
# Written by Michael Ruppe at Core Electronics MAR 2021

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

# Registers
_veml6030Address = 0x10
_ALS_CONF = 0x00
_REG_ALS = 0x04

_DEFAULT_SETTINGS = b'\x00' # initialise gain:1x, integration 100ms, persistence 1, disable interrupt

class PiicoDev_VEML6030(object):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_veml6030Address):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr
        self.res = 0.0576 # lx/bit
        self.i2c.writeto_mem(self.addr, _ALS_CONF, _DEFAULT_SETTINGS)
        
    def read(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, _REG_ALS, 2)
        except:
            print(i2c_err_str.format(self.addr))
            return float('NaN')
        return int.from_bytes(data, 'little') * self.res
