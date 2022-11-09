# A simple class to read data from a Core Electronics PiicoDev switch
# Peter Johnston at Core Electronics
# 2022 APR 06 - Initial release

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

_BASE_ADDRESS = 0x42
_DEVICE_ID    = 409

_REG_WHOAMI                = 0x01
_REG_FIRM_MAJ              = 0x02
_REG_FIRM_MIN              = 0x03
_REG_I2C_ADDRESS           = 0x04
_REG_LED                   = 0x05
_REG_IS_PRESSED            = 0x11
_REG_WAS_PRESSED           = 0x12
_REG_DOUBLE_PRESS_DETECTED = 0x13
_REG_PRESS_COUNT           = 0x14
_REG_DOUBLE_PRESS_DURATION = 0x21
_REG_EMA_PARAMETER         = 0x22
_REG_EMA_PERIOD            = 0x23

def _read_bit(x, n):
    return x & 1 << n != 0

def _set_bit(x, n):
    return x | (1 << n)

class PiicoDev_Switch(object):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, address=_BASE_ADDRESS, id=None, double_press_duration=300, ema_parameter=63, ema_period=20, suppress_warnings=False):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl, suppress_warnings=suppress_warnings)
        self._address = address
        if type(id) is list and not all(v == 0 for v in id): # preference using the ID argument. ignore id if all elements zero
            assert max(id) <= 1 and min(id) >= 0 and len(id) == 4, "id must be a list of 1/0, length=4"
            self._address=8+id[0]+2*id[1]+4*id[2]+8*id[3] # select address from pool
        else: self._address = address # accept an integer
        try:
            if self.whoami != _DEVICE_ID:
                print("* Incorrect device found at address {}".format(address))   
        except:
            print("* Couldn't find a device - check switches and wiring")
        self.double_press_duration = double_press_duration
        self.ema_parameter = ema_parameter
        self.ema_period = ema_period

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
    def press_count(self):
        """Returns the number of times the button has been pressed since the last time the button was read"""
        count_value = self._read_int(_REG_PRESS_COUNT, 2)
        if count_value is None:
            return(float('NaN'))
        else:
            return count_value

    @property    
    def is_pressed(self):
        """Returns the current state of the button.  `True` for pressed and `False` for not pressed"""
        if self._read_int(_REG_IS_PRESSED, 1) == 1:
            return False
        else:
            return True
        
    @property    
    def was_pressed(self):
        """Returns the current state of the button.  `True` for pressed and `False` for not pressed"""
        if self._read_int(_REG_WAS_PRESSED, 1) == 0:
            return False
        else:
            return True
        
    @property
    def was_double_pressed(self):
        if self._read_int(_REG_DOUBLE_PRESS_DETECTED, 1) == 1:
            return True
        else:
            return False

    @property
    def double_press_duration(self):
        """Returns the period of time between each press to register as a double-press"""
        return self._read_int(_REG_DOUBLE_PRESS_DURATION, 2)
    
    @double_press_duration.setter
    def double_press_duration(self, value):
        """Sets the period of time between each press to register as a double-press"""
        self._write_int(_set_bit(_REG_DOUBLE_PRESS_DURATION, 7), value, 2)
        
    @property
    def ema_parameter(self):
        """Returns the EMA parameter"""
        return self._read_int(_REG_EMA_PARAMETER)
    
    @ema_parameter.setter
    def ema_parameter(self, value):
        """Sets the EMA parameter"""
        self._write_int(_set_bit(_REG_EMA_PARAMETER, 7), value)
        
    @property
    def ema_period(self):
        """Returns the EMA period"""
        return self._read_int(_REG_EMA_PERIOD)
    
    @ema_period.setter
    def ema_period(self, value):
        """Sets the EMA period"""
        self._write_int(_set_bit(_REG_EMA_PERIOD, 7), value)

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

    def setI2Caddr(self, new_addr):
        x=int(new_addr)
        assert 8 <= x <= 0x77, 'address must be >=0x08 and <=0x77'
        self._write_int(_set_bit(_REG_I2C_ADDRESS, 7), x)
        self._address = x
        sleep_ms(5)
        return 0
 