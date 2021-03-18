import webai_blockly
from machine import Timer,PWM
from board import board_info,fpioaMapGPIO
from fpioa_manager import fm
from Maix import GPIO
import gc,time
class DDM:
    PWMPINUSE=[]
    PINUSE=[]
    PINIO=[]
    DUTY=60
    def setup(PWMPIN,PIN,PWM_FREQ=50,VALUE=1):
        USER_PWM_LIST_COUNT=len(webai_blockly.USER_PWM_LIST)
        if USER_PWM_LIST_COUNT<8:
            if USER_PWM_LIST_COUNT<4:
                BLOCKLY_SYSTEM_TIMER=0
            else:
                BLOCKLY_SYSTEM_TIMER=1
            PWMPIN=webai_blockly.fpioaMapGPIO[PWMPIN]
            PIN=webai_blockly.fpioaMapGPIO[PIN]
            if PWMPIN in __class__.PWMPINUSE:
                webai_blockly.USER_PWM_LIST[__class__.PWMPINUSE.index(PWMPIN)].duty(__class__.DUTY)
                __class__.PINIO[__class__.PINUSE.index(PIN)].value(VALUE)
            else:
                TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                DDM_PWM = PWM(TIMER,freq=PWM_FREQ, duty=__class__.DUTY, pin=PWMPIN[0])
                __class__.PWMPINUSE.append(PWMPIN)
                webai_blockly.USER_PWM_LIST.append(DDM_PWM)
                fm.register(PIN[0], PIN[1],force=True)
                IO=GPIO(PIN[2],GPIO.OUT)
                IO.value(VALUE)
                __class__.PINUSE.append(PIN)
                __class__.PINIO.append(IO)
        else:
            raise Exception("DDM error")

    def run(PWMPIN,PIN,PWM_FREQ=50,VALUE=60):
        USER_PWM_LIST_COUNT=len(webai_blockly.USER_PWM_LIST)
        if USER_PWM_LIST_COUNT<8:
            if USER_PWM_LIST_COUNT<4:
                BLOCKLY_SYSTEM_TIMER=0
            else:
                BLOCKLY_SYSTEM_TIMER=1
            PWMPIN=webai_blockly.fpioaMapGPIO[PWMPIN]
            PIN=webai_blockly.fpioaMapGPIO[PIN]
            if PWMPIN in __class__.PWMPINUSE:
                webai_blockly.USER_PWM_LIST[__class__.PWMPINUSE.index(PWMPIN)].duty(VALUE)
            else:
                TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                DDM_PWM = PWM(TIMER,freq=PWM_FREQ, duty=VALUE, pin=PWMPIN[0])
                __class__.PWMPINUSE.append(PWMPIN)
                webai_blockly.USER_PWM_LIST.append(DDM_PWM)
                fm.register(PIN[0], PIN[1],force=True)
                IO=GPIO(PIN[2],GPIO.OUT)
                IO.value(VALUE)
                __class__.PINUSE.append(PIN)
                __class__.PINIO.append(IO)
            __class__.DUTY=VALUE
        else:
            raise Exception("DDM error")
    # duty = 60
    # def __init__(self,PWMPIN,PIN,INVERT=1):
    #     global timerUseCount,timerUseChannelCount
    #     if timerUseChannelCount<8:
    #         if timerUseChannelCount<4:
    #             timerUseCount=0
    #         else:
    #             timerUseCount=1
    #         self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
    #         self.INVERT=INVERT
    #         self.PWMPIN=webai_blockly.fpioaMapGPIO[PWMPIN]
    #         self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #         self.PWM = PWM(self.TIMER,freq=50, duty=60, pin=self.PWMPIN[0])
    #         fm.register(self.PIN[0], self.PIN[1],force=True)
    #         self.IO=GPIO(self.PIN[2],GPIO.OUT)
    #         self.IO.value(INVERT)
    #         print('DDM __init__')
    #         timerUseChannelCount+=1
    #     else:
    #         raise Exception("DDM error")

    # def __del__(self):
    #     fm.unregister(self.PIN[0])
    #     del self
    #     print('DDM __del__')
    # def setup(self,value):
    #     self.duty = value
    # # def run(self,value):
    # #     self.PWM.duty(self.duty)
    # def stop(self):
    #     self.PWM.duty(0)
    # # def direction(self,value):
    # #     self.IO.value(value)
    # def positive(self):
    #     self.PWM.duty(self.duty)
    #     self.IO.value(1)
    # def negative(self):
    #     self.PWM.duty(self.duty)
    #     self.IO.value(0)
    # def invert(self):
    #     self.INVERT=not self.INVERT
    #     self.IO.value(self.INVERT)

class Led:
    PWMPINUSE=[]
    PINUSE=[]
    PINIO=[]
    def write(PINNONE=None,PIN=None,PWMMODE=False,PWM_FREQ=50,VALUE=0):
        if PWMMODE:
            USER_PWM_LIST_COUNT=len(webai_blockly.USER_PWM_LIST)
            if USER_PWM_LIST_COUNT<8:
                if USER_PWM_LIST_COUNT<4:
                    BLOCKLY_SYSTEM_TIMER=0
                else:
                    BLOCKLY_SYSTEM_TIMER=1
                PIN=webai_blockly.fpioaMapGPIO[PIN]
                if PIN in __class__.PWMPINUSE:
                    webai_blockly.USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(VALUE)
                else:
                    TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                    Led_PWM = PWM(TIMER,freq=PWM_FREQ, duty=VALUE, pin=PIN[0])
                    __class__.PWMPINUSE.append(PIN)
                    webai_blockly.USER_PWM_LIST.append(Led_PWM)
            else:
                raise Exception("Led error")
        else:
            PIN=webai_blockly.fpioaMapGPIO[PIN]
            if PIN in __class__.PINUSE:
                __class__.PINIO[__class__.PINUSE.index(PIN)].value(VALUE)
            else:
                fm.register(PIN[0], PIN[1],force=True)
                IO=GPIO(PIN[2],GPIO.OUT)
                IO.value(VALUE)
                __class__.PINUSE.append(PIN)
                __class__.PINIO.append(IO)
    # def __init__(self,DIGITAL=True,PINNONE=None,PIN=None):
    #     self.DIGITAL=DIGITAL
    #     if(DIGITAL):
    #         self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #         fm.register(self.PIN[0], self.PIN[1],force=True)
    #         self.IO=GPIO(self.PIN[2],GPIO.OUT)
    #         self.IO.value(0)
    #         print('Led __init__')
    #     else:
    #         global timerUseCount,timerUseChannelCount
    #         if timerUseChannelCount<8:
    #             if timerUseChannelCount<4:
    #                 timerUseCount=0
    #             else:
    #                 timerUseCount=1
    #             self.PWMPIN=webai_blockly.fpioaMapGPIO[PIN]
    #             self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
    #             self.PWM = PWM(self.TIMER,freq=50, duty=0, pin=self.PWMPIN[0])
    #             timerUseChannelCount+=1
    #             print('Led __init__')
    #         else:
    #             raise Exception("Led error")

    # def __del__(self):
    #     if(self.DIGITAL):
    #         fm.unregister(self.PIN[0])
    #     else:
    #         pass
    #     del self
    #     print('Led __del__')
    # def on(self,value=None):
    #     if(self.DIGITAL):
    #         self.IO.value(1)
    #     else:
    #         self.PWM.duty(value)
    # def off(self):
    #     if(self.DIGITAL):
    #         self.IO.value(0)
    #     else:
    #         self.PWM.duty(0)
class Button:
    PINUSE=[]
    PINIO=[]
    def io(PIN=None,PINNONE=None):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN=None,PINNONE=None):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)].value()
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO.value()
    # def __init__(self,PIN=None,PINNONE=None):
    #     self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #     fm.register(self.PIN[0], self.PIN[1],force=True)
    #     self.IO=GPIO(self.PIN[2],GPIO.IN,GPIO.PULL_UP)
    #     print('Button __init__')
    # def __del__(self):
    #     fm.unregister(self.PIN[0])
    #     del self
    #     print('Button __del__')
    # def value(self):
    #     return self.IO.value()
    # def selfObject(self):
    #     return self.IO
class Ir:
    PINUSE=[]
    PINIO=[]
    def io(PIN):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)].value()
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO.value()
    # def __init__(self,PIN):
    #     self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #     fm.register(self.PIN[0], self.PIN[1],force=True)
    #     self.IO=GPIO(self.PIN[2],GPIO.IN)
    #     print('Ir __init__')
    # def __del__(self):
    #     fm.unregister(self.PIN[0])
    #     del self
    #     print('Ir __del__')
    # def value(self):
    #     return self.IO.value()
    # def selfObject(self):
    #     return self.IO






class Io:
    PWMPINUSE=[]
    PINUSE=[]
    PINIO=[]
    def io(PIN):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)].value()
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO.value()
    def write(PIN,PWMMODE=False,PWM_FREQ=50,VALUE=0):
        if PWMMODE:
            USER_PWM_LIST_COUNT=len(webai_blockly.USER_PWM_LIST)
            if USER_PWM_LIST_COUNT<8:
                if USER_PWM_LIST_COUNT<4:
                    BLOCKLY_SYSTEM_TIMER=0
                else:
                    BLOCKLY_SYSTEM_TIMER=1
                PIN=webai_blockly.fpioaMapGPIO[PIN]
                if PIN in __class__.PWMPINUSE:
                    #print("old",__class__.PWMPINUSE.index(PIN))
                    #print(__class__.PWMPINUSE)
                    webai_blockly.USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(VALUE)
                else:
                    #print("new")
                    TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                    Io_PWM = PWM(TIMER,freq=PWM_FREQ, duty=VALUE, pin=PIN[0])
                    __class__.PWMPINUSE.append(PIN)
                    webai_blockly.USER_PWM_LIST.append(Io_PWM)
                #print("USER_PWM_LIST_COUNT:"+str(USER_PWM_LIST_COUNT))
            else:
                raise Exception("Io error")
        else:
            PIN=webai_blockly.fpioaMapGPIO[PIN]
            if PIN in __class__.PINUSE:
                #print("old")
                __class__.PINIO[__class__.PINUSE.index(PIN)].value(VALUE)
            else:
                #print("new")
                fm.register(PIN[0], PIN[1],force=True)
                IO=GPIO(PIN[2],GPIO.OUT)
                IO.value(VALUE)
                __class__.PINUSE.append(PIN)
                __class__.PINIO.append(IO)

    # def __init__(self,PIN,MODE='input',PWMMODE=False,PWM_FREQ=50):
    #     self.PWMMODE=PWMMODE
    #     self.MODE=MODE
    #     if self.MODE=='input':
    #         if self.PWMMODE:
    #             raise Exception("PWMMODE or MODE error")
    #         else:
    #             self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #             fm.register(self.PIN[0], self.PIN[1],force=True)
    #             self.IO=GPIO(self.PIN[2],GPIO.IN,GPIO.PULL_UP)
    #     else:
    #         if self.PWMMODE:
    #             global timerUseCount,timerUseChannelCount
    #             if timerUseChannelCount<8:
    #                 if timerUseChannelCount<4:
    #                     timerUseCount=0
    #                 else:
    #                     timerUseCount=1
    #                 self.PWMPIN=webai_blockly.fpioaMapGPIO[PIN]
    #                 self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
    #                 self.PWM = PWM(self.TIMER,freq=PWM_FREQ, duty=0, pin=self.PWMPIN[0])
    #                 timerUseChannelCount+=1
    #             else:
    #                 raise Exception("Io error")
    #         else:
    #             self.PIN=webai_blockly.fpioaMapGPIO[PIN]
    #             fm.register(self.PIN[0], self.PIN[1],force=True)
    #             self.IO=GPIO(self.PIN[2],GPIO.OUT)
    #             self.IO.value(0)
    #     print('Io __init__')

    # def __del__(self):
    #     fm.unregister(self.PIN[0])
    #     del self
    #     print('Io __del__')
        
    # def write(self,value=0):
    #     if self.PWMMODE:
    #         self.PWM.duty(value*100)
    #     else:
    #         if type(value)==int:
    #             self.IO.value(value)
    #         else:
    #             self.IO.value(0)

    # def read(self):
    #     return self.IO.value()
        
class Servo:
    PWMPINUSE=[]
    ANGLELIST=[]
    def angle(PIN,PWM_FREQ=50,VALUE=0):
        USER_PWM_LIST_COUNT=len(webai_blockly.USER_PWM_LIST)
        if USER_PWM_LIST_COUNT<8:
            if USER_PWM_LIST_COUNT<4:
                BLOCKLY_SYSTEM_TIMER=0
            else:
                BLOCKLY_SYSTEM_TIMER=1
            PIN=webai_blockly.fpioaMapGPIO[PIN]
            duty_cycle = (0.05 * PWM_FREQ) + (0.19 * PWM_FREQ * VALUE / 180)
            if PIN in __class__.PWMPINUSE:
                webai_blockly.USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(duty_cycle)
                __class__.ANGLELIST[__class__.PWMPINUSE.index(PIN)]=VALUE
                # print("old")
            else:
                TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                Io_PWM = PWM(TIMER,freq=PWM_FREQ, duty=duty_cycle, pin=PIN[0])
                __class__.PWMPINUSE.append(PIN)
                webai_blockly.USER_PWM_LIST.append(Io_PWM)
                __class__.ANGLELIST.append(VALUE)
                # print("new")
        else:
            raise Exception("Servo error")
    def getAngle(PIN):
        PIN=webai_blockly.fpioaMapGPIO[PIN]
        if PIN in __class__.PWMPINUSE:
            # print("true")
            return __class__.ANGLELIST[__class__.PWMPINUSE.index(PIN)]
        else:
            # print("false")
            return 110
    # def __init__(self,PWMPIN,PWM_FREQ=50):
    #     global timerUseCount,timerUseChannelCount
    #     if timerUseChannelCount<8:
    #         if timerUseChannelCount<4:
    #             timerUseCount=0
    #         else:
    #             timerUseCount=1
    #         self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
    #         self.PWMPIN=webai_blockly.fpioaMapGPIO[PWMPIN]
    #         self.PWM_FREQ=PWM_FREQ
    #         self.PWM = PWM(self.TIMER,freq=self.PWM_FREQ, duty=0, pin=self.PWMPIN[0])
    #         print('Servo __init__')
    #         timerUseChannelCount+=1
    #     else:
    #         raise Exception("Servo error")

    # def __del__(self):
    #     del self
    #     print('Servo __del__')
        
    # def angle_to_duty_cycle(self,angle=0):
    #     duty_cycle = (0.05 * self.PWM_FREQ) + (0.19 * self.PWM_FREQ * angle / 180)
    #     return duty_cycle
    
    # def angle(self,angle=0):
    #     duty_cycle = (0.05 * self.PWM_FREQ) + (0.19 * self.PWM_FREQ * angle / 180)
    #     self.PWM.duty(duty_cycle)


print("load gigo_blockly finish")