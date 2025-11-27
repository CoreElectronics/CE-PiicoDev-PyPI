# Class and methods for the MMC5603 3-axis magnetometer.
# Written by Michael Ruppe and Liam Howell at Core Electronics

# 2025 JAN 10 - Initial release


from PiicoDev_Unified import *
import math
import time

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'
range_compat_str = "Setting the range is not directly configurable, this has been left as a placeholder for compatability"
_I2C_ADDRESS = 0x30

# Registers
_REG_XOUT0 = 0x00  # Xout[19:12]
_REG_XOUT1 = 0x01  # Xout[11:4]
_REG_YOUT0 = 0x02  # Yout[19:12]
_REG_YOUT1 = 0x03  # Yout[11:4]
_REG_ZOUT0 = 0x04  # Zout[19:12]
_REG_ZOUT1 = 0x05  # Zout[11:4]
_REG_XOUT2 = 0x06  # Xout[3:0]
_REG_YOUT2 = 0x07  # Yout[3:0]
_REG_ZOUT2 = 0x08  # Zout[3:0]
_REG_TEMP = 0x09   # Temperature output
_REG_STATUS = 0x18 # Status register
_REG_ODR = 0x1A    # Output data rate
_REG_CTRL0 = 0x1B  # Internal control 0
_REG_CTRL1 = 0x1C  # Internal control 1
_REG_CTRL2 = 0x1D  # Internal control 2
_REG_PRODUCT_ID = 0x39  # Product ID

# Control bits
_BIT_TAKE_MEAS_M = 0x01
_BIT_TAKE_MEAS_T = 0x02
_BIT_DO_SET = 0x08
_BIT_DO_RESET = 0x10
_BIT_AUTO_SR = 0x04

def _readBit(x, n):
    return x & 1 << n != 0

def _setBit(x, n):
    return x | (1 << n)

def _clearBit(x, n):
    return x & ~(1 << n)

def _writeBit(x, n, b):
    if b == 0:
        return _clearBit(x, n)
    else:
        return _setBit(x, n)

class PiicoDev_MMC5603(object):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_I2C_ADDRESS, odr=255, sign_x=0, sign_y=0, sign_z=1, calibrationFile='calibration.cal', range=None, suppress_warnings=False):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr
        self.calibrationFile = calibrationFile
        self.suppress_warnings = suppress_warnings

        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
        if sign_x == 0:
            self.sign_x = -1
        else:
            self.sign_x = 1
        if sign_y == 0:
            self.sign_y = -1
        else:
            self.sign_y = 1
        if sign_z == 0:
            self.sign_z = -1
        else:
            self.sign_z = 1
        self.sensitivity = 0.1 # Changes depending on bit-mode, 20bit(0.0625)
        
        if range is not None:
            print(range_compat_str)

        self.odr = odr

        self.declination = 0
        self.data = {}
        self._dataValid = False

        # Perform initialization
        try:
            self.check_ID()
            self.reset()
            self.setOutputDataRate(self.odr)
            self.enable_continuous_mode()
            
        except Exception as e:
            print(i2c_err_str.format(self.addr))
            raise e

        if calibrationFile is not None:
            self.loadCalibration()
        sleep_ms(5)

    def reset(self):
        self.i2c.writeto_mem(self.addr, _REG_CTRL1, bytes([0x80]))
        sleep_ms(20)
        self.set_reset()

    def check_ID(self):
        id = self.i2c.readfrom_mem(self.addr, _REG_PRODUCT_ID, 1)[0]
        if id != 0x10:  # Expected product ID for MMC5603
            print(f"Warning: Unexpected product ID: {id}")

    def setOutputDataRate(self, odr):
        """Set the output data rate."""
        if not (1 <= odr <= 255):
            raise ValueError("ODR must be between 1 and 255.")
        self.i2c.writeto_mem(self.addr, _REG_ODR, bytes([odr]))

    def _convertAngleToPositive(self, angle):
        if angle >= 360.0:
            angle = angle - 360.0
        if angle < 0:
            angle = angle + 360.0
        return angle

    def setRange(self, range):
        if not self.suppress_warnings:
            print(range_compat_str)
        pass

    def enable_continuous_mode(self):
        self.i2c.writeto_mem(self.addr, _REG_CTRL0, bytes([0x80]))
        self.i2c.writeto_mem(self.addr, _REG_CTRL2, bytes([0x10]))

    def set_BW(self, BW= 0x03):
        self.i2c.writeto_mem(self.addr, _REG_CTRL1, bytes([BW]))  # BW = 11, default
        
    def readStatus(self):
        status = int.from_bytes(self.i2c.readfrom_mem(self.addr, 0x18, 1), 'big')
#         print(bin(status))
        return status
    
    def setDeclination(self, dec):
        self.declination = dec
    
    def _measurementStatus(self):
        status = self.i2c.readfrom_mem(self.addr, _REG_STATUS, 1)[0]
        if status & 0x02:  # Check Meas_m_done bit
            return True
        else:
            return False

    def dataValid(self):
        return self._dataValid

    def set_reset(self):
        """Perform SET and RESET operations to eliminate offset errors and residual magnetization."""
        # Perform SET operation
        self.i2c.writeto_mem(self.addr, _REG_CTRL0, bytes([_BIT_DO_SET]))
        sleep_ms(1)  # Wait for at least 1 ms

        # Perform RESET operation
        self.i2c.writeto_mem(self.addr, _REG_CTRL0, bytes([_BIT_DO_RESET]))
        sleep_ms(1)  # Wait for at least 1 ms

    def read(self, raw=False):
        """Read raw magnetic field data in microteslas (uT)."""
        self._dataValid = False
        NaN = {'x':float('NaN'),'y':float('NaN'),'z':float('NaN')}
        self.sample = NaN
        x=0
        y=0
        z=0
        # Read all data registers
        try:
            data = self.i2c.readfrom_mem(self.addr, _REG_XOUT0, 9)
            
            x = (data[0] << 8) | (data[1])
            y = (data[2] << 8) | (data[3])
            z = (data[4] << 8) | (data[5])
            self._dataValid = True
        except:
            if not self.suppress_warnings:
                print("Invalid read")

        x -= 1 << 15
        y -= 1 << 15
        z -= 1 << 15
        
        if (x >= 0x8000):
            x = -((65535 - x) + 1)
        x = (x - self.x_offset)
        if (y >= 0x8000):
            y = -((65535 - y) + 1)
        y = (y - self.y_offset)
        if (z >= 0x8000):
            z = -((65535 - z) + 1)
        z = (z - self.z_offset)
        if raw is False:
            x *= (self.sensitivity*self.sign_x)
            y *= (self.sensitivity*self.sign_y)
            z *= (self.sensitivity*self.sign_z)
        
        self.sample = {'x':x,'y':y,'z':z}
        return self.sample

    def readPolar(self):
        cartesian = self.read()
        angle = ( math.atan2(cartesian['x'],-cartesian['y']) /math.pi)*180.0 + self.declination
        angle = self._convertAngleToPositive(angle)
        magnitude = math.sqrt(cartesian['x']*cartesian['x'] + cartesian['y']*cartesian['y'] + cartesian['z']*cartesian['z'])
        return {'polar':angle, 'Gauss':magnitude*100, 'uT':magnitude}

    def readMagnitude(self):
        return self.readPolar()['uT']

    def readHeading(self):
        return self.readPolar()['polar']
    
    def setDeclination(self, dec):
        self.declination = dec

    def calibrate(self, enable_logging=False, disable_z=False):
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
        x_min = 65535
        x_max = -65535
        y_min = 65535
        y_max = -65535
        z_min = 65535
        z_max = -65535
        log = ''
        print('*** Calibrating.\n    Slowly rotate your sensor until the bar is full')
        print('[          ]', end='')
        range = 1000
        i = 0
        x=0;y=0;z=0;
        a=0.5 # EMA filter weight
        iterator = 0
        while i < range:
            i += 1
            iterator += 1
            sleep_ms(5)
            d = self.read(raw=True)
            x = a*d['x'] + (1-a)*x # EMA filter
            y = a*d['y'] + (1-a)*y
            z = a*d['z'] + (1-a)*z
            if x < x_min: x_min = x; i=0
            if x > x_max: x_max = x; i=0
            if y < y_min: y_min = y; i=0
            if y > y_max: y_max = y; i=0
            if disable_z:
                if z < z_min: z_min = z; i=0
                if z > z_max: z_max = z; i=0
            j = round(10*i/range);
            if iterator > 10:
                iterator = 0
                print( '\015[' + int(j)*'*' + int(10-j)*' ' + ']'+'     ' +(str(i)), end='') # print a progress bar
            if enable_logging:
                log = log + (str(d['x']) + ',' + str(d['y']) + ',' + str(d['z']) + '\n')
#         self.setOutputDataRate(self.odr) # set the output data rate back to the user selected rate
        self.x_offset = (x_max + x_min) / 2
        self.y_offset = (y_max + y_min) / 2
        self.z_offset = (z_max + z_min) / 2
        f = open(self.calibrationFile, "w")
        f.write('x_min:\n' + str(x_min) + '\nx_max:\n' + str(x_max) + '\ny_min:\n' + str(y_min) + '\ny_max:\n' + str(y_max) + '\nz_min\n' + str(z_min) + '\nz_max:\n' + str(z_max) + '\nx_offset:\n')
        f.write(str(self.x_offset) + '\ny_offset:\n' + str(self.y_offset) + '\nz_offset:\n' + str(self.z_offset))
        f.close()
        if enable_logging:
            flog = open("calibration.log", "w")
            flog.write(log)
            flog.close


    def loadCalibration(self):
        try:
            f = open(self.calibrationFile, "r")
            for i in range(13): f.readline()
            self.x_offset = float(f.readline())
            f.readline()
            self.y_offset = float(f.readline())
            f.readline()
            self.z_offset = float(f.readline())
            sleep_ms(5)
        except:
            if not self.suppress_warnings:
                print("No calibration file found. Run 'calibrate()' for best results.  Visit https://piico.dev/p15 for more info.")
            sleep_ms(1000)
