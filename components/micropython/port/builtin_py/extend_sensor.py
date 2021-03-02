from machine import Timer,PWM
from board import board_info,fpioaMapGPIO
from fpioa_manager import fm
from Maix import GPIO
import gc,time
timerUseCount=0
timerUseChannelCount=0
# fpioaMapGPIO={
# '0':[board_info.P0,fm.fpioa.GPIOHS0,GPIO.GPIOHS0],
# '1':[board_info.P1,fm.fpioa.GPIOHS1,GPIO.GPIOHS1],
# '2':[board_info.P2,fm.fpioa.GPIOHS2,GPIO.GPIOHS2],
# '3':[board_info.P3,fm.fpioa.GPIOHS3,GPIO.GPIOHS3],
# '5':[board_info.P5,fm.fpioa.GPIOHS5,GPIO.GPIOHS5],
# '6':[board_info.P6,fm.fpioa.GPIOHS6,GPIO.GPIOHS6],
# '7':[board_info.P7,fm.fpioa.GPIOHS7,GPIO.GPIOHS7],
# '8':[board_info.P8,fm.fpioa.GPIOHS8,GPIO.GPIOHS8],
# '9':[board_info.P9,fm.fpioa.GPIOHS9,GPIO.GPIOHS9],
# '10':[board_info.P10,fm.fpioa.GPIOHS10,GPIO.GPIOHS10],
# '11':[board_info.P11,fm.fpioa.GPIOHS11,GPIO.GPIOHS11],
# '12':[board_info.P12,fm.fpioa.GPIOHS12,GPIO.GPIOHS12],
# '13':[board_info.P13,fm.fpioa.GPIOHS13,GPIO.GPIOHS13],
# '14':[board_info.P14,fm.fpioa.GPIOHS14,GPIO.GPIOHS14],
# '15':[board_info.P15,fm.fpioa.GPIOHS15,GPIO.GPIOHS15],
# '16':[board_info.P16,fm.fpioa.GPIOHS16,GPIO.GPIOHS16],
# '19':[board_info.P19,fm.fpioa.GPIO0,GPIO.GPIO0],
# '20':[board_info.P20,fm.fpioa.GPIO1,GPIO.GPIO1]}

class DDM_Blockly:
    duty = 60
    def __init__(self,PWMPIN,PIN,INVERT=1):
        global timerUseCount,timerUseChannelCount
        if timerUseChannelCount<8:
            if timerUseChannelCount<4:
                timerUseCount=0
            else:
                timerUseCount=1
            self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
            self.INVERT=INVERT
            self.PWMPIN=fpioaMapGPIO[PWMPIN]
            self.PIN=fpioaMapGPIO[PIN]
            self.PWM = PWM(self.TIMER,freq=50, duty=60, pin=self.PWMPIN[0])
            fm.register(self.PIN[0], self.PIN[1],force=True)
            self.IO=GPIO(self.PIN[2],GPIO.OUT)
            self.IO.value(INVERT)
            print('DDM_Blockly __init__')
            timerUseChannelCount+=1
        else:
            raise Exception("DDM_Blockly error")

    def __del__(self):
        fm.unregister(self.PIN[0])
        del self
        print('DDM_Blockly __del__')
    def setup(self,value):
        self.duty = value
    # def run(self,value):
    #     self.PWM.duty(self.duty)
    def stop(self):
        self.PWM.duty(0)
    # def direction(self,value):
    #     self.IO.value(value)
    def positive(self):
        self.PWM.duty(self.duty)
        self.IO.value(1)
    def negative(self):
        self.PWM.duty(self.duty)
        self.IO.value(0)
    def invert(self):
        self.INVERT=not self.INVERT
        self.IO.value(self.INVERT)

class Led_Blockly:
    def __init__(self,DIGITAL=True,PINNONE=None,PIN=None):
        self.DIGITAL=DIGITAL
        if(DIGITAL):
            self.PIN=fpioaMapGPIO[PIN]
            fm.register(self.PIN[0], self.PIN[1],force=True)
            self.IO=GPIO(self.PIN[2],GPIO.OUT)
            self.IO.value(0)
            print('Led_Blockly __init__')
        else:
            global timerUseCount,timerUseChannelCount
            if timerUseChannelCount<8:
                if timerUseChannelCount<4:
                    timerUseCount=0
                else:
                    timerUseCount=1
                self.PWMPIN=fpioaMapGPIO[PIN]
                self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
                self.PWM = PWM(self.TIMER,freq=50, duty=0, pin=self.PWMPIN[0])
                timerUseChannelCount+=1
                print('Led_Blockly __init__')
            else:
                raise Exception("Led_Blockly error")

    def __del__(self):
        if(self.DIGITAL):
            fm.unregister(self.PIN[0])
        else:
            pass
        del self
        print('Led_Blockly __del__')
    def on(self,value=None):
        if(self.DIGITAL):
            self.IO.value(1)
        else:
            self.PWM.duty(value)
    def off(self):
        if(self.DIGITAL):
            self.IO.value(0)
        else:
            self.PWM.duty(0)
class Button_Blockly:
    def __init__(self,PIN=None,PINNONE=None):
        self.PIN=fpioaMapGPIO[PIN]
        fm.register(self.PIN[0], self.PIN[1],force=True)
        self.IO=GPIO(self.PIN[2],GPIO.IN,GPIO.PULL_UP)
        print('Button_Blockly __init__')
    def __del__(self):
        fm.unregister(self.PIN[0])
        del self
        print('Button_Blockly __del__')
    def value(self):
        return self.IO.value()
class Ir_Blockly:
    def __init__(self,PIN):
        self.PIN=fpioaMapGPIO[PIN]
        fm.register(self.PIN[0], self.PIN[1],force=True)
        self.IO=GPIO(self.PIN[2],GPIO.IN)
        print('Ir_Blockly __init__')
    def __del__(self):
        fm.unregister(self.PIN[0])
        del self
        print('Ir_Blockly __del__')
    def value(self):
        return self.IO.value()










class Io_Blockly:

    def __init__(self,PIN,MODE='input',PWMMODE=False,PWM_FREQ=50):
        self.PWMMODE=PWMMODE
        self.MODE=MODE
        if self.MODE=='input':
            if self.PWMMODE:
                raise Exception("PWMMODE or MODE error")
            else:
                self.PIN=fpioaMapGPIO[PIN]
                fm.register(self.PIN[0], self.PIN[1],force=True)
                self.IO=GPIO(self.PIN[2],GPIO.IN,GPIO.PULL_UP)
        else:
            if self.PWMMODE:
                global timerUseCount,timerUseChannelCount
                if timerUseChannelCount<8:
                    if timerUseChannelCount<4:
                        timerUseCount=0
                    else:
                        timerUseCount=1
                    self.PWMPIN=fpioaMapGPIO[PIN]
                    self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
                    self.PWM = PWM(self.TIMER,freq=PWM_FREQ, duty=0, pin=self.PWMPIN[0])
                    timerUseChannelCount+=1
                else:
                    raise Exception("Io_Blockly error")
            else:
                self.PIN=fpioaMapGPIO[PIN]
                fm.register(self.PIN[0], self.PIN[1],force=True)
                self.IO=GPIO(self.PIN[2],GPIO.OUT)
                self.IO.value(0)
        print('Io_Blockly __init__')

    def __del__(self):
        fm.unregister(self.PIN[0])
        del self
        print('Io_Blockly __del__')
        
    def write(self,value=0):
        if self.PWMMODE:
            self.PWM.duty(value*100)
        else:
            if type(value)==int:
                self.IO.value(value)
            else:
                self.IO.value(0)

    def read(self):
        return self.IO.value()
        
class Servo_Blockly:
    def __init__(self,PWMPIN,PWM_FREQ=50):
        global timerUseCount,timerUseChannelCount
        if timerUseChannelCount<8:
            if timerUseChannelCount<4:
                timerUseCount=0
            else:
                timerUseCount=1
            self.TIMER=Timer(timerUseCount,timerUseChannelCount%4, mode=Timer.MODE_PWM)
            self.PWMPIN=fpioaMapGPIO[PWMPIN]
            self.PWM_FREQ=PWM_FREQ
            self.PWM = PWM(self.TIMER,freq=self.PWM_FREQ, duty=0, pin=self.PWMPIN[0])
            print('Servo_Blockly __init__')
            timerUseChannelCount+=1
        else:
            raise Exception("Servo_Blockly error")

    def __del__(self):
        del self
        print('Servo_Blockly __del__')
        
    def angle_to_duty_cycle(self,angle=0):
        duty_cycle = (0.05 * self.PWM_FREQ) + (0.19 * self.PWM_FREQ * angle / 180)
        return duty_cycle
    
    def angle(self,angle=0):
        duty_cycle = (0.05 * self.PWM_FREQ) + (0.19 * self.PWM_FREQ * angle / 180)
        self.PWM.duty(duty_cycle)


print("load extend_sensor finish")