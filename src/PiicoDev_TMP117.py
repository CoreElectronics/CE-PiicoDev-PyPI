# Class to read temperature from the PiicoDev TMP117 i2c temperature sensor
# https://github.com/CoreElectronics/CE-PiicoDev-TMP117-MicroPython-Module
# Written by Michael Ruppe at Core Electronics MAR 2021

from PiicoDev_Unified import *

# Register definitions
REG_TEMPC = 0x00
compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

class PiicoDev_TMP117(object):    
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr = 0x48):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr

    def readTempC(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, REG_TEMPC, 2)
        except:
            print(i2c_err_str.format(self.addr))
            return float('NaN')
        
        tempDataRaw = int.from_bytes(data, 'big')
        # handle negatives
        if tempDataRaw >= 0x8000:
            return -256.0 + (tempDataRaw - 0x8000) * 7.8125e-3 # One LSB equals 7.812 mdegC
        else:
            return tempDataRaw * 7.8125e-3 # One LSB equals 7.812 mdegC
    
    def readTempF(self):
        return (self.readTempC() * 9/5) + 32
        
    def readTempK(self):
        return self.readTempC() + 273.15
