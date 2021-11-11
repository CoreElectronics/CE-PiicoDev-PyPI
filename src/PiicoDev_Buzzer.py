from PiicoDev_Unified import *
_baseAddr=0x08
_DevID=0x51
_regDevID=0x00
_regFirmVer=0x02
_regI2cAddr=0x04
_regTone=0x05
_regVolume=0x06
_regLED=0x07

class PiicoDev_Buzzer(object):        
    def tone(self, freq, dur=0):
        _f=int(freq);_d=int(dur)
        f = _f.to_bytes(2,'big')
        d = _d.to_bytes(2,'big')
        try: self.i2c.writeto_mem(self.addr, _regTone, f+d)
        except: print("couldn't write")
    
    def noTone(self):
        self.tone(0)
        
    def volume(self, vol):
        _v = int(vol); assert _v >=0 and _v <=2,"volume must be 0, 1 or 2"
        v = vol.to_bytes(1,'big')
        try:
            self.i2c.writeto_mem(self.addr, _regVolume, v)
            sleep_ms(5)
        except: print("couldn't write")

    def setI2Caddr(self, newAddr):
        x=int(newAddr)
        assert 8 <= x <= 0x77, 'address must be >=0x08 and <=0x77'
        self.i2c.writeto_mem(self.addr, _regI2cAddr, bytes([x]))
        self.addr = x
        sleep_ms(5)

    def readFirmware(self):
        v=self.i2c.readfrom_mem(self.addr, _regFirmVer, 2)
        return (v[1],v[0])

    def readID(self):
        return self.i2c.readfrom_mem(self.addr, _regDevID, 1)[0]

    def pwrLED(self, x):
        self.i2c.writeto_mem(self.addr, _regLED, bytes([x]))
        
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_baseAddr, volume=2):
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        a=addr
        if type(a) is list: # to accept DIP switch-positions eg [0,0,0,1]
            self.addr=_baseAddr+a[0]+2*a[1]+4*a[2]+8*a[3]
        else:
            self.addr = a # accept an integer
            
        self.volume(volume)
#         try:
#             if self.readID() != _DevID:
#                 print("* Incorrect device found at address {}".format(addr))
#             self.setBrightness(bright)
#             self.show()
#         except:
#             print("* Couldn't find a device - check switches and wiring")
#         
        