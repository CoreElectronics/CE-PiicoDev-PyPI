from PiicoDev_Unified import *
_baseAddr=0x08
_DevID=0x84
_regDevID=0x00
_regFirmVer=0x01
_regCtrl=0x03
_regClear=0x04
_regI2cAddr=0x05
_regBright=0x06
_regLedVals=0x07

def wheel(h, s=1, v=1):
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.) # assume int() truncates
    f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
    if i == 0: return [v, t, p]
    if i == 1: return [q, v, p]
    if i == 2: return [p, v, t]
    if i == 3: return [p, q, v]
    if i == 4: return [t, p, v]
    if i == 5: return [v, p, q]

class PiicoDev_RGB(object):
    def setPixel(self,n,c):
        self.led[n]=[round(c[0]),round(c[1]),round(c[2])]

    def show(self):
        buffer = bytes(self.led[0]) + bytes(self.led[1]) + bytes(self.led[2])
        self.i2c.writeto_mem(self.addr, _regLedVals, buffer)

    def setBrightness(self,x):
        self.bright= round(x) if 0 <= x <= 255 else 255
        self.i2c.writeto_mem(self.addr, _regBright, bytes([self.bright]))
        sleep_ms(1)

    def clear(self):
        self.i2c.writeto_mem(self.addr,_regClear,b'\x01')
        self.led=[[0,0,0],[0,0,0],[0,0,0]]
        sleep_ms(1)

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

    # Control the 'Power' LED. Defaults ON if anything else but False is passed in
    def pwrLED(self, state):
        assert state == True or state == False, 'argument must be True/1 or False/0'
        self.i2c.writeto_mem(self.addr,_regCtrl,bytes([state]))
        sleep_ms(1)
        
    def fill(self,c):
        for i in range(len(self.led)):
            self.led[i]=c
        self.show()
        
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_baseAddr, id=None, bright=50):
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        if type(id) is list: # preference using the ID argument
            assert max(id) <= 1 and min(id) >= 0 and len(id) is 4, "id must be a list of 1/0, length=4"
            self.addr=_baseAddr+id[0]+2*id[1]+4*id[2]+8*id[3]
        else:
            self.addr = addr # accept an integer
        self.led = [[0,0,0],[0,0,0],[0,0,0]]
        self.bright=bright
        try:
            self.setBrightness(bright)
            self.show()
        except Exception as e:
            print("* Couldn't find a device - check switches and wiring")
            raise e
        
        
