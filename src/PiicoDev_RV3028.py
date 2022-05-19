# A basic class to use the Makerverse RV3028 Supercap Real Time Clock on the Raspberry Pi Pico
# Written by Brenton Schulz, Peter Johnston and Michael Ruppe at Core Electronics
# 2022 May 18  Add alarm functions - MR
# 2022 May 4th Use class attributes instead of setters/getters
# 2021 NOV 5th Initial feature set complete
#     - Set / get date and time
#     - Set / get UNIX time (independent of main calendar clock)
#     - Enable event interrupt on EVI pin
#     - Get event timestamp
#     - Configure trickle charger for onboard supercap
#     - Configure frequency of CLK output pin

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'
_dayNames=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
_I2C_ADDRESS = 0x52
_SEC = 0x00
_MIN = 0x01
_HOUR = 0x02
_DAY = 0x04
_MONTH = 0x05
_YEAR = 0x06
_ALMIN = 0x07
_STATUS = 0x0E
_CTRL1 = 0x0F
_CTRL2 = 0x10
_CIM = 0x12
_ECTRL = 0x13
_SECTS = 0x15
_DAYTS = 0x18
_UNIX = 0x1B
_REG_ID = 0x28
_EE_CLKOUT = 0x35
_EE_BACKUP = 0x37

def _setBit(x, n):
    return x | (1 << n)

def _clearBit(x, n):
    return x & ~(1 << n)

def _writeBit(x, n, b):
    if b == 0:
        return _clearBit(x, n)
    else:
        return _setBit(x, n)
    
def _readBit(x, n):
    return x & 1 << n != 0
    
def _writeCrumb(x, n, c):
    x = _writeBit(x, n, _readBit(c, 0))
    return _writeBit(x, n+1, _readBit(c, 1))

def _writeTribit(x,n,c):
    x = _writeBit(x, n, _readBit(c, 0))
    x = _writeBit(x, n+1, _readBit(c, 1))
    return _writeBit(x, n+2, _readBit(c, 2)) 

def _bcdDecode(val):
    return (val>>4)*10 + (val&0x0F)

def _bcdEncode(val):
    return ((val//10) << 4) | (val % 10)

class PiicoDev_RV3028(object):    
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_I2C_ADDRESS):
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
            part = int(self.i2c.readfrom_mem(self.addr, _REG_ID, 1)[0])
        except Exception as e:
            print(i2c_err_str.format(self.addr))
            raise e
        
        self._weekday = 0 # integer 0 to 6
        self.alarmHours=0
        self.alarm_ampm='am' # for defining alam AM/PM. Ignored if system time is 24-hr
        self.alarmMinutes=0
        self.alarmWeekdayDate=0
        self.setBatterySwitchover()
        self.configTrickleCharger()
        self.setTrickleCharger()
        self.getDateTime()
        
    @property
    def weekday(self):
        """Get the weekday and return as integer 0 to 6"""
        return self._weekday
    @weekday.setter
    def weekday(self, day):
        """Set the weekday. Accepts an integer 0 to 6"""
        if 0 <= day <= 6: self._weekday = day
        else: print('Warning: Weekday must be integer 0 to 6')
    
    @property
    def weekdayName(self):
        """Get the weekday and return as a string."""
        return _dayNames[self._weekday]
    @weekdayName.setter
    def weekdayName(self, day):
        """Set the weekday. Accepts a string, checks string is a day name, and stores as integer 0 to 6"""
        if day in _dayNames: self._weekday = _dayNames.index(day)
        else: print('Warning: weekdayName must be "Monday", "Tuesday", ... "Saturday" or "Sunday"')

    def _read(self, reg, N):
        try:
            tmp = int.from_bytes(self.i2c.readfrom_mem(self.addr, reg, N), 'little')
        except:
            print("Error reading from RV3028")
            return float('NaN')
        return tmp
        
    def _write(self, reg, data):
        try:
            self.i2c.writeto_mem(self.addr, reg, data)
        except:
            print("Error writing to RV3028")
            return float('NaN')
        
    def getUnixTime(self):
        return self._read(_UNIX, 4)
    
    def setUnixTime(self, time):
        self._write(_UNIX, time.to_bytes(4, 'little'))
        
    def setBatterySwitchover(self, state = True):
        tmp = self._read(_EE_BACKUP, 1)
        if state is True:
            tmp = _writeCrumb(tmp, 2, 0b01)
        elif state is False:
            tmp = _writeCrumb(tmp, 2, 0b00)
        else:
            print("Parameter State must be True or False")
            return
        self._write(_EE_BACKUP, tmp.to_bytes(1, 'little'))
                    
    def setTrickleCharger(self, state = True):
        tmp = self._read(_EE_BACKUP, 1)
        if state is True:
            tmp = _writeBit(tmp, 5, 1)
        elif state is False:
            tmp = _writeBit(tmp, 5, 0)
        else:
            print("Parameter State must be True or False")
            return
        self._write(_EE_BACKUP, tmp.to_bytes(1,'little'))
        
    def configTrickleCharger(self, R = '3k'):
        tmp = self._read(_EE_BACKUP, 1)
        tmp = _setBit(tmp, 7)
        if R == '3k':
            tmp = _writeCrumb(tmp, 0, 0b00)
        elif R == '5k':
            tmp = _writeCrumb(tmp, 0, 0b01)
        elif R == '9k':
            tmp = _writeCrumb(tmp, 0, 0b10)
        elif R == '15k':
            tmp = _writeCrumb(tmp, 0, 0b11)
        else:
            print("R parameter must be '3k', '5k', '9k', or '15k'")
            return
        self._write(_EE_BACKUP, tmp.to_bytes(1, 'little'))
        
    def configClockOutput(self, clk):
        tmp = self._read(_EE_CLKOUT, 1)
        if clk == 32768:
            tmp = _writeTribit(tmp, 0, 0)
        elif clk == 8192:
            tmp = _writeTribit(tmp, 0, 1)
        elif clk == 1024:
            tmp = _writeTribit(tmp, 0, 2)
        elif clk == 64:
            tmp = _writeTribit(tmp, 0, 3)
        elif clk == 32:
            tmp = _writeTribit(tmp, 0, 4)
        elif clk == 1:
            tmp = _writeTribit(tmp, 0, 5)
        elif clk == 0:
            tmp = _writeTribit(tmp, 0, 7)
        else:
            print("clk parameter must be 32678, 8192, 1024, 64,32, 1, or 0. Values are in units of Hz.")
            return
        self._write(_EE_CLKOUT, tmp.to_bytes(1, 'little'))
        
    def resetEventInterrupt(self, edge = 'falling'):
        # Clear EVF, _STATUS bit 1
        tmp = self._read(_STATUS, 1)
        tmp = _clearBit(tmp, 1)
        self._write(_STATUS, bytes([tmp]))
        
        # TSS = 0, _ECTRL bit 0 (External event as time stamp source)
        # TSOW = 0, _ECTRL bit 1 (First recorded event timestamp kept)
        # EHL = 0, _ECTRL bit 6 (Falling edge default - PCB has pullup on EVI)
        # TSR = 1, _ECTRL bit 2 (reset event timestamp)
        tmp = self._read(_ECTRL, 1)
        tmp = _clearBit(tmp, 0)
        if edge == 'falling':
            tmp = _clearBit(tmp, 6)
        else:
            tmp = _setBit(tmp, 6)
        tmp = _clearBit(tmp, 1)
        tmp = _setBit(tmp, 2)
        self._write(_ECTRL, bytes([tmp]))
        
        # EIE = 1, _CTRL2 bit 2
        # TSE = 1, _CTRL2 bit 7
        tmp = self._read(_CTRL2, 1)
        tmp = _setBit(tmp, 2)
        tmp = _setBit(tmp, 7)
        self._write(_CTRL2, bytes([tmp]))

        tmp = self._write(_ECTRL, bytes([0]))
        
    def getEventInterrupt(self):
        tmp = self._read(_STATUS, 1)
        if _readBit(tmp,1) == 1:
            return True
        else:
            return False
    
    def getDateTime(self, eventTimestamp = False):
        if eventTimestamp is False:
            tmp = self._read(_SEC, 7)
            date = tmp.to_bytes(7, 'little')
            self.day = _bcdDecode(date[4])
            self.month = _bcdDecode(date[5])
            self.year = _bcdDecode(date[6])
        else:
            tmp = self._read(_SECTS, 6)
            date = tmp.to_bytes(6, 'little')
            self.day = _bcdDecode(date[3])
            self.month = _bcdDecode(date[4])
            self.year = _bcdDecode(date[5])
        
        hrFormat = _readBit(self._read(_CTRL2,1), 1)
        t = tmp.to_bytes(7, 'little')
        self.minute = _bcdDecode(t[1])
        self.second = _bcdDecode(t[0])
        self.hour = _bcdDecode(t[2])
        self._weekday = t[3]
        self.ampm = '24'
        if hrFormat == 1:
            if _readBit(t[2], 5) == 0:
                self.ampm = 'AM'
            else:
                hrByte = _clearBit(t[2], 5)
                self.hour = _bcdDecode(hrByte)
                self.ampm = 'PM'

    def setDateTime(self):
        year_2_digits = self.year
        if year_2_digits > 100:
                year_2_digits -= 2000
        
        tmp = self._read(_CTRL2, 1)
        if self.ampm == '24':
            tmp = _writeBit(tmp, 1, 0)
            hrs = _bcdEncode(self.hour)
        elif self.ampm != '24':
            tmp = _writeBit(tmp, 1, 1)
            hrs = _bcdEncode(self.hour)
            if self.ampm == 'AM':
                hrs = _clearBit(hrs, 5)
            elif self.ampm == 'PM':
                hrs = _setBit(hrs, 5)
        self._write(_CTRL2, tmp.to_bytes(1,'little'))
        self._write(_SEC, bytes([_bcdEncode(self.second), _bcdEncode(self.minute), hrs, self._weekday, _bcdEncode(self.day), _bcdEncode(self.month), _bcdEncode(year_2_digits)]))
    
    def alarmSetup(self, minutes=False, hours=False, weekday=False, date=False, interrupt=True):
        """Push alarm settings to the RTC, enable alarm interrupt output as required. Arguments specify which time parameters to compare."""
        AE_M=1;AE_H=1;AE_WD=1; # Alarm enable bits (active low)
        if weekday and date:
            print("Warning: Cannot enable alarm for weeday AND date. Aborting...")
            return
        WADA=False
        if weekday is not False:
            WADA=False # set the alarm source selection bit (weekday or date)
            self.alarmWeekdayDate = int(weekday)
            AE_WD=0
        if date is not False:
            WADA=True
            self.alarmWeekdayDate = int(date)
            AE_WD=0
        tmp = self._read(_CTRL1, 1) #read/write WADA bit to control register
        tmp = _writeBit(tmp, 5, WADA)
        self._write(_CTRL1, tmp.to_bytes(1,'little'))
        
        # handle 24/AM/PM hours
        if hours is not False:
            self.alarmHours = int(hours)
            AE_H = 0
        h = _bcdEncode(self.alarmHours)
        if self.ampm != '24':
            ampm = (self.alarm_ampm == 'PM')
            h = _writeBit(h, 5, ampm)
    
        if minutes is not False:
            self.alarmMinutes = int(minutes)
            AE_M = 0
        
        m = (AE_M << 7) | _bcdEncode(self.alarmMinutes)       # set the Alarm Minutes register 0x07: AE_M[7], Minutes[6:0]
        h = (AE_H << 7) | h                                   # set the Alarm Hours register   0x08: AE_H[7], Hours[6:0] - 24-hr time only
        d = (AE_WD << 7) | _bcdEncode(self.alarmWeekdayDate)  # set the Alarm Weekday/Date register 0x09: AE_WD[7], day/date [5:0]
        self._write(_ALMIN, bytes([m,h,d])) # write the alarm registers
        
        # Alarm signal on INT pin
        tmp = self._read(_CTRL2, 1)
        tmp = _writeBit(tmp, 3, interrupt)
        self._write(_CTRL2, tmp.to_bytes(1,'little'))
        
    def alarmDisable(self):
        """Disable alarm, interrupt and clear the Alarm Flag if necessary"""
        self.alarmSetup(minutes=False, hours=False, weekday=False, date=False, interrupt=False)
        self.checkAlarm()
        
    def checkAlarm(self):
        """Return the Alarm Flag status, and reset if triggered"""
        tmp = self._read(_STATUS, 1)
        if _readBit(tmp, 2):
            tmp = _writeBit(tmp, 2, 0) # reset the AF alarm flag
            self._write(_STATUS, tmp.to_bytes(1,'little'))
            return True
        else: return False

    def timestamp(self, eventTimestamp = False):
        self.getDateTime(eventTimestamp = eventTimestamp)
        timestamp = "{:02d}".format(self.year+2000) + "-" + "{:02d}".format(self.month) + "-" + "{:02d}".format(self.day) + " " + "{:02d}".format(self.hour) + ":" + "{:02d}".format(self.minute) + ":" + "{:02d}".format(self.second)
        if self.ampm != '24':
            timestamp += " " + self.ampm
        return timestamp
    
    def clearAllInterrupts(self):
        self._write(_STATUS, bytes([0]))

