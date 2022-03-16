# A class to read data from the VEML6040 i2c light sensor
# Read RGB or HSV data
# Classify Hue given a dictionary of colour definitions

# No warranties express or implied, including any warranty of merchantability and warranty of fitness for a particular purpose.
# Written by Peter Johnston and Michael Ruppe at Core Electronics May 2021

from PiicoDev_Unified import *
from math import sqrt

# Registers
_veml6040Address = 0x10
_CONF = b'\x00'
_REG_RED = 0x08
_REG_GREEN = 0x09
_REG_BLUE = 0x0A
_REG_WHITE = 0x0B

_DEFAULT_SETTINGS = b'\x00' # initialise gain:1x, integration 40ms, Green Sensitivity 0.25168, Max. Detectable Lux 16496
                            # No Trig, Auto mode, enabled.
_SHUTDOWN = b'\x01'         # Disable colour sensor
_INTEGRATION_TIME = 40      # ms
_G_SENSITIVITY = 0.25168    # lux/step

_NaN=float('NaN')

def rgb2hsv(r, g, b):
    r = float(r/65535)
    g = float(g/65535)
    b = float(b/65535)
    high = max(r, g, b)
    low = min(r, g, b)
    h,s,v = high,high,high
    d = high - low
    s = 0 if high == 0 else d/high
    if high == low:
        h = 0.0
    else:
        h = {
            r: (g - b) / d+(6 if g < b else 0),
            g: (b - r) / d+2,
            b: (r - g) / d+4,
        }[high]
        h /= 6
    return {'hue':h*360,'sat':s, 'val':v}
    
class PiicoDev_VEML6040(object):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr = _veml6040Address):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr
        try:
            self.i2c.write8(self.addr, _CONF, _SHUTDOWN)
            self.i2c.write8(self.addr, _CONF, _DEFAULT_SETTINGS)
            sleep_ms(50)
        except Exception:
            print('Device 0x{:02X} not found'.format(self.addr))
            
    def classifyHue(self, hues={"red":0,"yellow":60,"green":120,"cyan":180,"blue":240,"magenta":300}, min_brightness=0):
        d=self.readHSV()
        if d['val'] > min_brightness:
            key, val = min(hues.items(), key=lambda x: min(360-abs(d['hue'] - x[1]),abs(d['hue'] - x[1]))) # nearest neighbour, but it wraps!
            return key
        else:
            return 'None'
    
    # Read colours from VEML6040
    # Returns raw red, green and blue readings, ambient light [Lux] and colour temperature [K]
    def readRGB(self):
        try:
            raw_data = self.i2c.readfrom_mem(self.addr, _REG_RED, 2)        # returns a bytes object   
            u16red = int.from_bytes(raw_data, 'little')
            
            raw_data = (self.i2c.readfrom_mem(self.addr, _REG_GREEN, 2))    # returns a bytes object
            u16grn = int.from_bytes(raw_data, 'little')
            
            raw_data = (self.i2c.readfrom_mem(self.addr, _REG_BLUE, 2))     # returns a bytes object
            u16blu = int.from_bytes(raw_data, 'little')
            
            raw_data = (self.i2c.readfrom_mem(self.addr, _REG_WHITE, 2))    # returns a bytes object
            data_white_int = int.from_bytes(raw_data, 'little')
        except:
            print(i2c_err_str.format(self.addr))
            return {"red":_NaN,"green":_NaN,"blue":_NaN,"white":_NaN,"als":_NaN,"cct":_NaN}
        
        # Generate the XYZ matrix based on https://www.vishay.com/docs/84331/designingveml6040.pdf
        colour_X = (-0.023249*u16red)+(0.291014*u16grn)+(-0.364880*u16blu)
        colour_Y = (-0.042799*u16red)+(0.272148*u16grn)+(-0.279591*u16blu)
        colour_Z = (-0.155901*u16red)+(0.251534*u16grn)+(-0.076240*u16blu)
        colour_total = colour_X+colour_Y+colour_Z
        if colour_total == 0:
            return {"red":_NaN,"green":_NaN,"blue":_NaN,"white":_NaN,"als":_NaN,"cct":_NaN}
        else:
            colour_x = colour_X / colour_total
            colour_y = colour_Y / colour_total
        
        # Use McCamy formula
        colour_n = (colour_x - 0.3320)/(0.1858 - colour_y)
        colour_CCT = 449.0*colour_n ** 3+3525.0*colour_n ** 2+6823.3*colour_n+5520.33
        
        # Calculate ambient light in Lux
        colour_ALS = u16grn*_G_SENSITIVITY
        return {"red":u16red,"green":u16grn,"blue":u16blu,"white":data_white_int,"als":colour_ALS,"cct":colour_CCT}
    
    def readHSV(self):
        d = self.readRGB()
        return rgb2hsv(d['red'],d['green'],d['blue'])
