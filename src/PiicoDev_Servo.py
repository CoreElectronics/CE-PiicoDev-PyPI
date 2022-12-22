try: from ustruct import pack, unpack
except: from struct import pack, unpack
from PiicoDev_Unified import *
compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

def remap(old_val, old_min, old_max, new_min, new_max):
    """Remap one range of values to another range and saturate for out-of-bounds"""
    x = (new_max - new_min)*(old_val - old_min) / (old_max - old_min) + new_min
    return min(new_max,max(x,new_min))

class PCA9685:
    """
    A Class to drive the PCA9685 PWM driver
    """
    def __init__(self, i2c, address=0x44):
        self.i2c = i2c
        self.address = address
        self.reset()
        self.frequency=50 # Hz

    def _write(self, address, value):
        self.i2c.writeto_mem(self.address, address, bytearray([value]))

    def _read(self, address):
        return self.i2c.readfrom_mem(self.address, address, 1)[0]

    def reset(self):
        self._write(0x00, 0x00)
    
    @property
    def frequency(self):
        return self._frequency        
    @frequency.setter
    def frequency(self,f):
        """Set the pulse frequency"""
        prescale = int(25000000.0 / 4096.0 / f + 0.5)
        old_mode = self._read(0x00) # Mode 1
        self._write(0x00, (old_mode & 0x7F) | 0x10) # Disable oscillator
        self._write(0xfe, prescale) # Apply prescale
        self._write(0x00, old_mode) # Start oscillator
        sleep_ms(1)
        self._write(0x00, old_mode | 0xa1) # Mode 1, autoincrement on
        self._frequency = 1/((prescale-0.5)*4096/25e6)
        
    def pwm(self, index, on=None, off=None):
        if on is None or off is None:
            data = self.i2c.readfrom_mem(self.address, 0x06 + 4 * index, 4)
            return unpack('<HH', data)
        data = pack('<HH', on, off)
        self.i2c.writeto_mem(self.address, 0x06 + 4 * index,  data)

    def duty(self, index, value=None, invert=False):
        if value is None: # get the duty cycle
            pwm = self.pwm(index)
            if pwm == (0, 4096):
                value = 0
            elif pwm == (4096, 0):
                value = 4095
            value = pwm[1]
            if invert:
                value = 4095 - value
            return value
        if not 0 <= value <= 4095:
            raise ValueError("Out of range")
        if invert:
            value = 4095 - value
        if value == 0:
            self.pwm(index, 0, 4095)
        elif value == 4095:
            self.pwm(index, 4095, 0)
        else:
            self.pwm(index, 0, value)
            
_I2C_ADDRESS = 0x44
class PiicoDev_Servo_Driver(PCA9685):
    """
    A child class that wraps PCA9685 with PiicoDev initialisation logic
    """    
    def __init__(self, bus=None, freq=None, sda=None, scl=None, address=_I2C_ADDRESS, asw=None):
        try:
            if compat_ind >= 1: pass
            else: print(compat_str)
        except: print(compat_str)
        if type(asw) is list and len(asw) is 2 and all(element in [0,1] for element in asw):
            addr = _I2C_ADDRESS + asw[0] + 2*asw[1]
        else:   
            addr = address # default address used if asw not provided OR invalid
        i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        PCA9685.__init__(self, i2c, address=addr)

class PiicoDev_Servo:
    def __init__(self, controller, channel, freq=50, min_us=600, max_us=2400, degrees=180, midpoint_us=None, range_us=None):
        self.period = 1_000_000/freq # microseconds
        print('period us',self.period)
        if midpoint_us is not None and range_us is not None: # option to define the servo timing with a midpoint and a range
            min_us = midpoint_us - range_us/2
            max_us = midpoint_us + range_us/2
        self.min_duty = self._us2duty(min_us) 
        self.max_duty = self._us2duty(max_us)
        print('min duty',self.min_duty)
        print('max duty',self.max_duty)
        self._degrees = degrees
        self.freq = freq
        self.controller = controller
        self.channel = {4:0,3:1,2:2,1:3}[channel] # map {silk label:PCA9685 channel}
        
    def _us2duty(self, value):
        return int(4095 * value / self.period + 0.5)
    
    @property
    def angle(self):
        return self._angle
    @angle.setter
    def angle(self, x):
        duty = self.min_duty + (self.max_duty - self.min_duty) * x / self._degrees
        duty = min(self.max_duty, max(self.min_duty, int(duty)))
        self.controller.duty(self.channel, duty)
        self._angle = min(self._degrees,max(x,0)) # saturate the property
        
    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self,x):
        self._speed = x
        duty = int(remap(x, -1, 1, self.min_duty, self.max_duty)+0.5)
        self.controller.duty(self.channel, duty)

    def release(self):
        self.controller.duty(self.channel, 0)
        