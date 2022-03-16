# Class to read data from the Core Electronics PiicoDev MS5637 Pressure Sensor
# Ported to MicroPython by Peter Johnston at Core Electronics MAY 2021
# Original repo https://github.com/TEConnectivity/piweathershield-python/tree/67fa820647fafa5a1a7a5a4828ee13d80a60a279

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

class PiicoDev_MS5637(object):
    # MS5637 device address
    _I2C_ADDRESS = 0x76

    # MS5637 device commands
    _SOFTRESET = 0x1E
    _MS5637_START_PRESSURE_ADC_CONVERSION = 0x40
    _MS5637_START_TEMPERATURE_ADC_CONVERSION = 0x50
    _MS5637_CONVERSION_OSR_MASK = 0x0F
    _ADC_READ = 0x00

    # MS5637 commands read eeprom
    _MS5637_PROM_ADDR_0 = 0xA0
    _MS5637_PROM_ADDR_1 = 0xA2
    _MS5637_PROM_ADDR_2 = 0xA4
    _MS5637_PROM_ADDR_3 = 0xA6
    _MS5637_PROM_ADDR_4 = 0xA8
    _MS5637_PROM_ADDR_5 = 0xAA
    _MS5637_PROM_ADDR_6 = 0xAC

    # MS5637 commands conversion time
    _MS5637_CONV_TIME_OSR_256 = 1 # 0.001
    _MS5637_CONV_TIME_OSR_512 = 2 # 0.002
    _MS5637_CONV_TIME_OSR_1024 = 3 # 0.003
    _MS5637_CONV_TIME_OSR_2048 = 5 # 0.005
    _MS5637_CONV_TIME_OSR_4096 = 9 # 0.009
    _MS5637_CONV_TIME_OSR_8192 = 17 # 0.017
    
    # MS5637 commands resolution 
    _RESOLUTION_OSR_256 = 0
    _RESOLUTION_OSR_512 = 1 
    _RESOLUTION_OSR_1024 = 2
    _RESOLUTION_OSR_2048 = 3
    _RESOLUTION_OSR_4096 = 4
    _RESOLUTION_OSR_8192 = 5
    
    # Coefficients indexes for temperature and pressure computation
    _MS5637_CRC_INDEX = 0
    _MS5637_PRESSURE_SENSITIVITY_INDEX = 1 
    _MS5637_PRESSURE_OFFSET_INDEX = 2
    _MS5637_TEMP_COEFF_OF_PRESSURE_SENSITIVITY_INDEX = 3
    _MS5637_TEMP_COEFF_OF_PRESSURE_OFFSET_INDEX = 4
    _MS5637_REFERENCE_TEMPERATURE_INDEX = 5
    _MS5637_TEMP_COEFF_OF_TEMPERATURE_INDEX = 6
    
    eeprom_coeff = [0,0,0,0,0,0,0,0]
    
    coeff_valid = False

    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr = _I2C_ADDRESS):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr
        #try:
        self.i2c.write8(self.addr, None, bytes([self._SOFTRESET]))
        sleep_ms(15)
        #except Exception:
        #    print('Device 0x{:02X} not found'.format(self.addr))

    # Set  ADC resolution.
    # res : ms5637_resolution_osr : Resolution requested
    # return temperature command, pressure command, temperature conversion time, pressure conversion time 
    def set_resolution(self,res) :
        time = [self._MS5637_CONV_TIME_OSR_256,
        self._MS5637_CONV_TIME_OSR_512,
        self._MS5637_CONV_TIME_OSR_1024,
        self._MS5637_CONV_TIME_OSR_2048,
        self._MS5637_CONV_TIME_OSR_4096,
        self._MS5637_CONV_TIME_OSR_8192]
        cmd_temp = res *2;
        cmd_temp |= self._MS5637_START_TEMPERATURE_ADC_CONVERSION;
        _time_temp = time[int((cmd_temp & self._MS5637_CONVERSION_OSR_MASK)/2)]
        
        cmd_pressure = res *2;
        cmd_pressure |= self._MS5637_START_PRESSURE_ADC_CONVERSION;
        _time_pressure = time[int((cmd_pressure & self._MS5637_CONVERSION_OSR_MASK)/2)]
        return cmd_temp,cmd_pressure, _time_temp, _time_pressure

    # Read eeprom coefficients
    # cmd : address of coefficient in EEPROM
    def read_eeprom_coeff (self, cmd) :
        data = self.i2c.readfrom_mem(self.addr, cmd, 2)
        return int.from_bytes(data, 'big')

    # Reads the ms5637 EEPROM coefficients to store them for computation.
    # Returns all coefficients read in the EEPROM 
    def read_eeprom(self) : 
        a = 0
        coeffs = [0,0,0,0,0,0,0,0]
        liste = [self._MS5637_PROM_ADDR_0,
        self._MS5637_PROM_ADDR_1,
        self._MS5637_PROM_ADDR_2,
        self._MS5637_PROM_ADDR_3,
        self._MS5637_PROM_ADDR_4,
        self._MS5637_PROM_ADDR_5,
        self._MS5637_PROM_ADDR_6,]
    
        for i in liste :
            coeffs[a] = self.read_eeprom_coeff(i)
            a = a+1
        self.coeff_valid = True
        return coeffs

    # Triggers conversion and read ADC value
    # Cmd : Command used for conversion (will determine Temperature vs Pressure and osr)
    # _time : ms
    # adc : ADC value
    def conversion_read_adc(self,cmd,_time) :
        self.i2c.write8(self.addr, None, bytes([cmd]))
        sleep_ms(_time)
        data = self.i2c.readfrom_mem(self.addr, self._ADC_READ, 3)
        adc = int.from_bytes(data, 'big')
        return adc
  
    # Read Temperature and Pressure, perform compensation
    # res: resolution [ # ]
    # returns Temperature [degC] and Pressure [hPa]
    def read_temperature_and_pressure(self,res=_RESOLUTION_OSR_8192) :
        if self.coeff_valid == False :
            self.eeprom_coeff = self.read_eeprom()
        (cmd_temp, cmd_pressure,_time_temp,_time_pressure) = self.set_resolution(res)
        try:
            adc_temperature = self.conversion_read_adc(cmd_temp,_time_temp)
            adc_pressure = self.conversion_read_adc(cmd_pressure,_time_pressure)
        except:
            print(i2c_err_str.format(self.addr))
            return float('NaN'), float('NaN')
        if ((type(adc_temperature) is not int) or (type(adc_pressure) is not int)):
            return float('NaN'), float('NaN')
         # Difference between actual and reference temperature = D2 - Tref
        dT = (adc_temperature) - (self.eeprom_coeff[self._MS5637_REFERENCE_TEMPERATURE_INDEX] * 0x100)
         # Actual temperature = 2000 + dT * TEMPSENS
        TEMP = 2000 + (dT * self.eeprom_coeff[self._MS5637_TEMP_COEFF_OF_TEMPERATURE_INDEX] >> 23);
         # Second order temperature compensation
        if TEMP < 2000 : 
            T2 = ( 3 * ( dT  * dT  ) ) >> 33
            OFF2 = 61 * (TEMP - 2000) * (TEMP - 2000) / 16 
            SENS2 = 29 * (TEMP - 2000) * (TEMP - 2000) / 16 
            if TEMP < -1500 :
                OFF2 += 17 * (TEMP + 1500) * (TEMP + 1500) 
                SENS2 += 9 * ((TEMP + 1500) * (TEMP + 1500))
        else :
            T2 = ( 5 * ( dT  * dT  ) ) >> 38
            OFF2 = 0 
            SENS2 = 0

        #  OFF = OFF_T1 + TCO * dT
        OFF = ( (self.eeprom_coeff[self._MS5637_PRESSURE_OFFSET_INDEX]) << 17 ) + ( ( (self.eeprom_coeff[self._MS5637_TEMP_COEFF_OF_PRESSURE_OFFSET_INDEX]) * dT ) >> 6 ) 
        OFF -= OFF2 ;

        # Sensitivity at actual temperature = SENS_T1 + TCS * dT
        SENS = ( self.eeprom_coeff[self._MS5637_PRESSURE_SENSITIVITY_INDEX] * 0x10000 ) + ( (self.eeprom_coeff[self._MS5637_TEMP_COEFF_OF_PRESSURE_SENSITIVITY_INDEX] * dT) >> 7 ) 
        SENS -= SENS2
        #  Temperature compensated pressure = D1 * SENS - OFF
        P = ( ( (int(adc_pressure * SENS)) >> 21 ) - int(OFF) ) >> 15 

        temperature = ( TEMP - T2 ) / 100.0
        pressure = P / 100.0

        return temperature, pressure
    
    # res: resolution [ # ]
    # Returns the pressure [hPa]
    def read_pressure(self,res=_RESOLUTION_OSR_8192) :
        temperature_and_pressure = self.read_temperature_and_pressure(res)
        return temperature_and_pressure[1]
    
    # Returns the altitude [m]
    def read_altitude(self,pressure_sea_level=1013.25):
        pressure = self.read_pressure()
        return 44330*(1-(float(pressure)/pressure_sea_level)**(1/5.255))

    def close(self):
        self.i2c.close()

    def __enter__(self):
        return self        

    def __exit__(self, type, value, traceback):
        self.close()