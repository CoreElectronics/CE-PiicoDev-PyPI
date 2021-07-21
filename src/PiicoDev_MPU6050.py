# Class to read data from the Core Electronics PiicoDev Motion Sensor MPU-6050
# Ported to MicroPython by Peter Johnston and Michael Ruppeat Core Electronics APR 2021
# Original repo https://github.com/nickcoutsos/MPU-6050-Python

from PiicoDev_Unified import *
from math import sqrt
i2c = PiicoDev_Unified_I2C()

# Address
_MPU6050_ADDRESS = 0x68

class PiicoDev_MPU6050(object):

    # Global Variables
    GRAVITIY_MS2 = 9.80665

    # Scale Modifiers
    ACC_SCLR_2G = 16384.0
    ACC_SCLR_4G = 8192.0
    ACC_SCLR_8G = 4096.0
    ACC_SCLR_16G = 2048.0

    GYR_SCLR_250DEG = 131.0
    GYR_SCLR_500DEG = 65.5
    GYR_SCLR_1000DEG = 32.8
    GYR_SCLR_2000DEG = 16.4

    # Pre-defined ranges
    ACC_RNG_2G = 0x00
    ACC_RNG_4G = 0x08
    ACC_RNG_8G = 0x10
    ACC_RNG_16G = 0x18

    GYR_RNG_250DEG = 0x00
    GYR_RNG_500DEG = 0x08
    GYR_RNG_1000DEG = 0x10
    GYR_RNG_2000DEG = 0x18

    # MPU-6050 Registers
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C

    SELF_TEST_X = 0x0D
    SELF_TEST_Y = 0x0E
    SELF_TEST_Z = 0x0F
    SELF_TEST_A = 0x10

    ACCEL_XOUT0 = 0x3B
    ACCEL_XOUT1 = 0x3C
    ACCEL_YOUT0 = 0x3D
    ACCEL_YOUT1 = 0x3E
    ACCEL_ZOUT0 = 0x3F
    ACCEL_ZOUT1 = 0x40

    TEMP_OUT0 = 0x41
    TEMP_OUT1 = 0x42

    GYRO_XOUT0 = 0x43
    GYRO_XOUT1 = 0x44
    GYRO_YOUT0 = 0x45
    GYRO_YOUT1 = 0x46
    GYRO_ZOUT0 = 0x47
    GYRO_ZOUT1 = 0x48

    ACCEL_CONFIG = 0x1C
    GYRO_CONFIG = 0x1B

    def __init__(self, addr=_MPU6050_ADDRESS, i2c_=i2c):
        self.i2c = i2c_
        self.addr = addr
        try:
            # Wake up the MPU-6050 since it starts in sleep mode
            self.i2c.write8(self.addr, bytes([self.PWR_MGMT_1]), bytes([0x00]))
            print('Device 0x{:02X} found'.format(self.addr))
        except Exception:
            print('Device 0x{:02X} not found'.format(self.addr))

    # I2C communication method to read two I2C registers and combine them into a signed integer
    def read_i2c_word(self, register_high):
        # Read the data from the registers
        rawData = self.i2c.readfrom_mem(self.addr, register_high, 2)
        value = (int.from_bytes(rawData, 'big'))
        if (value >= 0x8000):
            return -((65535 - value) + 1)
        else:
            return value

    # Reads the temperature from the onboard temperature sensor of the MPU-6050.
    # Returns the temperature [degC].
    def read_temperature(self):
        raw_temp = self.read_i2c_word(self.TEMP_OUT0)
        actual_temp = (raw_temp / 340) + 36.53
        return actual_temp

    # Sets the range of the accelerometer
    # accel_range : the range to set the accelerometer to. Using a pre-defined range is advised.
    def set_accel_range(self, accel_range):
        self.i2c.write8(self.addr, bytes([self.ACCEL_CONFIG]), bytes([0x00]))
        self.i2c.write8(self.addr, bytes([self.ACCEL_CONFIG]), bytes([accel_range]))

    # Gets the range the accelerometer is set to.
    # raw=True: Returns raw value from the ACCEL_CONFIG register
    # raw=False: Return integer: -1, 2, 4, 8 or 16. When it returns -1 something went wrong.
    def get_accel_range(self, raw = False):
        # Get the raw value
        raw_data = self.i2c.read16(self.addr, bytes([self.ACCEL_CONFIG]))
        if raw is True:
            return raw_data[0]
        elif raw is False:
            if raw_data[0] == self.ACC_RNG_2G:
                return 2
            elif raw_data[0] == self.ACC_RNG_4G:
                return 4
            elif raw_data[0] == self.ACC_RNG_8G:
                return 8
            elif raw_data[0] == self.ACC_RNG_16G:
                return 16
            else:
                return -1

    # Reads and returns the X, Y and Z values from the accelerometer.
    # Returns dictionary data in g or m/s^2 (g=False)
    def read_accel_data(self, g = False):
        x = self.read_i2c_word(self.ACCEL_XOUT0)
        y = self.read_i2c_word(self.ACCEL_YOUT0)
        z = self.read_i2c_word(self.ACCEL_ZOUT0)

        scaler = None
        accel_range = self.get_accel_range(True)

        if accel_range == self.ACC_RNG_2G:
            scaler = self.ACC_SCLR_2G
        elif accel_range == self.ACC_RNG_4G:
            scaler = self.ACC_SCLR_4G
        elif accel_range == self.ACC_RNG_8G:
            scaler = self.ACC_SCLR_8G
        elif accel_range == self.ACC_RNG_16G:
            scaler = self.ACC_SCLR_16G
        else:
            print("Unkown range - scaler set to self.ACC_SCLR_2G")
            scaler = self.ACC_SCLR_2G

        x = x / scaler
        y = y / scaler
        z = z / scaler

        if g is True:
            return {'x': x, 'y': y, 'z': z}
        elif g is False:
            x = x * self.GRAVITIY_MS2
            y = y * self.GRAVITIY_MS2
            z = z * self.GRAVITIY_MS2
            return {'x': x, 'y': y, 'z': z}

    def read_accel_abs(self, g=False):
        d=self.read_accel_data(g)
        return sqrt(d['x']**2+d['y']**2+d['z']**2)

    def set_gyro_range(self, gyro_range):
        self.i2c.write8(self.addr, bytes([self.GYRO_CONFIG]), bytes([0x00]))
        self.i2c.write8(self.addr, bytes([self.GYRO_CONFIG]), bytes([gyro_range]))

    # Gets the range the gyroscope is set to.
    # raw=True: return raw value from GYRO_CONFIG register
    # raw=False: return range in deg/s
    def get_gyro_range(self, raw = False):
        # Get the raw value
        raw_data = self.i2c.read16(self.addr, bytes([self.GYRO_CONFIG]))

        if raw is True:
            return raw_data[0]
        elif raw is False:
            if raw_data[0] == self.GYR_RNG_250DEG:
                return 250
            elif raw_data[0] == self.GYR_RNG_500DEG:
                return 500
            elif raw_data[0] == self.GYR_RNG_1000DEG:
                return 1000
            elif raw_data[0] == self.GYR_RNG_2000DEG:
                return 2000
            else:
                return -1

    # Gets and returns the X, Y and Z values from the gyroscope.
    # Returns the read values in a dictionary.
    def read_gyro_data(self):
        # Read the raw data from the MPU-6050
        x = self.read_i2c_word(self.GYRO_XOUT0)
        y = self.read_i2c_word(self.GYRO_YOUT0)
        z = self.read_i2c_word(self.GYRO_ZOUT0)

        scaler = None
        gyro_range = self.get_gyro_range(True)

        if gyro_range == self.GYR_RNG_250DEG:
            scaler = self.GYR_SCLR_250DEG
        elif gyro_range == self.GYR_RNG_500DEG:
            scaler = self.GYR_SCLR_500DEG
        elif gyro_range == self.GYR_RNG_1000DEG:
            scaler = self.GYR_SCLR_1000DEG
        elif gyro_range == self.GYR_RNG_2000DEG:
            scaler = self.GYR_SCLR_2000DEG
        else:
            print("Unkown range - scaler set to self.GYR_SCLR_250DEG")
            scaler = self.GYR_SCLR_250DEG

        x = x / scaler
        y = y / scaler
        z = z / scaler

        return {'x': x, 'y': y, 'z': z}
