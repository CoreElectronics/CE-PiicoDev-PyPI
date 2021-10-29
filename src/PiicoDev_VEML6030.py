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
        self.gain=1
        self.res = 0.0576 # [lx/bit]
        self.i2c.writeto_mem(self.addr, _ALS_CONF, _DEFAULT_SETTINGS)
        sleep_ms(4)
        
    def read(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, _REG_ALS, 2)
        except:
            print(i2c_err_str.format(self.addr))
            return float('NaN')
        return int.from_bytes(data, 'little') * self.res
    
    def setGain(self,g):
        if g not in [0.125,0.25,1,2]:
            raise ValueError ('Invalid gain. Accepted values: 0.125, 0.25, 1, 2')
        self.gain=g
        if g == 0.125:
            conf = b'\x00\x10'
            self.res = 0.4608
        if g == 0.25:
            conf = b'\x00\x18'
            self.res = 0.2304
        if g == 1:
            conf = b'\x00\x00'
            self.res = 0.0576
        if g == 2:
            conf = b'\x00\x08'
            self.res = 0.0288
        self.setBits(_ALS_CONF, conf, 'b\x18\x00')
        sleep_ms(4)
        return
    
    def setBits(self, address, byte, mask): # ToDo: generalise for 8 or 16bit registers. Make more elegant.
        old = self.i2c.readfrom_mem(self.addr, address, 2)
        old_byte = int.from_bytes(self.i2c.readfrom_mem(self.addr, address, 2),'little')
        temp_byte = old_byte
        int_byte = int.from_bytes(byte,"little")
        int_mask = int.from_bytes(mask,"big")
        for n in range(16): # Cycle through each bit
            bit_mask = (int_mask >> n) & 1
            if bit_mask == 1:
                if ((int_byte >> n) & 1) == 1:
                    temp_byte = temp_byte | 1 << n
                else:
                    temp_byte = temp_byte & ~(1 << n)
        new_byte = temp_byte
        print(new_byte)
        self.i2c.writeto_mem(self.addr, address, new_byte.to_bytes(2,'little'))
          
