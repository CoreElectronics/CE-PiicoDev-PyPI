# A simple class to read data from the Core Electronics PiicoDev Potentiometer
# Peter Johnston and Michael Ruppe at Core Electronics
# 2022 APR 06 - Initial release
# 2022 OCT 12 - Stable release

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

_BASE_ADDRESS = 0x35
_DEVICE_ID_POT   = 379
_DEVICE_ID_SLIDE = 411

_REG_WHOAMI      = 0x01
_REG_FIRM_MAJ    = 0x02
_REG_FIRM_MIN    = 0x03
_REG_I2C_ADDRESS = 0x04
_REG_POT         = 0x05
_REG_LED         = 0x07

def _read_bit(x, n):
    return x & 1 << n != 0

def _set_bit(x, n):
    return x | (1 << n)

class PiicoDev_Potentiometer(object):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, address=_BASE_ADDRESS, id=None, minimum=0.0, maximum=100.0, suppress_warnings=False):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl, suppress_warnings=suppress_warnings)
        self._address = address
        self.minimum = minimum
        self.maximum = maximum
        if type(id) is list and not all(v == 0 for v in id): # preference using the ID argument. ignore id if all elements zero
            assert max(id) <= 1 and min(id) >= 0 and len(id) == 4, "id must be a list of 1/0, length=4"
            self._address=8+id[0]+2*id[1]+4*id[2]+8*id[3] # select address from pool
        else: self._address = address # accept an integer
        try:
            if self.whoami != _DEVICE_ID_POT and self.whoami != _DEVICE_ID_SLIDE:
                print("* Incorrect device found at address {}".format(address))   
        except:
            print("* Couldn't find a device - check switches and wiring")   

    def _read(self, register, length=1):
        try:
            return self.i2c.readfrom_mem(self.address, register, length)
        except:
            print(i2c_err_str.format(self.address))
            return None
    
    def _write(self, register, data):
        try:
            self.i2c.writeto_mem(self.address, register, data)
        except:
            print(i2c_err_str.format(self.address))
    
    def _read_int(self, register, length=1):
        data = self._read(register, length)
        if data is None:
            return None
        else:
            return int.from_bytes(data, 'big')
        
    def _write_int(self, register, integer, length=1):
        self._write(register, int.to_bytes(integer, length, 'big'))

    @property
    def raw(self):
        """Returns the raw ADC value"""
        raw_value = self._read_int(_REG_POT, 2)
        if raw_value is None:
            return(float('NaN'))
        else:
            return raw_value
        
    @property
    def value(self):
        """Returns a float between 0.0 and 100.0 (default) or a value from a user-defined scale"""
        raw_value = self.raw
        if raw_value is None:
            return(float('NaN'))
        else:
            return self._minimum + ((self._maximum - self._minimum) / 1023) * raw_value
    
    @property
    def minimum(self):
        """Returns the value that the pot returns at it's minimum *travel*"""
        return self._minimum
    
    @minimum.setter
    def minimum(self, x):
        """Sets the value that the pot returns at it's minimum *travel*"""
        self._minimum = x
    
    @property
    def maximum(self):
        """Returns the value that the pot returns at it's maximum *travel*"""
        return self._maximum
    
    @maximum.setter
    def maximum(self, x):
        """Sets the value that the pot returns at it's maximum *travel*"""
        self._maximum = x
    
    @property
    def address(self):
        """Returns the currently configured 7-bit I2C address"""
        return self._address

    @property
    def led(self):
        """Returns the state onboard "Power" LED. `True` / `False`"""
        return bool(self._read_int(_REG_LED))
    
    @led.setter
    def led(self, x):
        """control the state onboard "Power" LED. accepts `True` / `False`"""
        self._write_int(_set_bit(_REG_LED, 7), int(x)); return 0

    @property
    def whoami(self):
        """returns the device identifier"""
        return self._read_int(_REG_WHOAMI, 2)
    
    @property
    def firmware(self):
        """Returns the firmware version"""
        v=[0,0]
        v[1]=self._read_int(_REG_FIRM_MAJ)
        v[0]=self._read_int(_REG_FIRM_MIN)
        return (v[1],v[0])
    
    def setI2Caddr(self, newAddr):
        x=int(newAddr)
        assert 8 <= x <= 0x77, 'address must be >=0x08 and <=0x77'
        self._write_int(_REG_I2C_ADDRESS, x)
        self._address = x
        sleep_ms(5)
        return 0
