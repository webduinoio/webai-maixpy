import webai_blockly
from machine import Timer,PWM
from fpioa_manager import fm
from Maix import GPIO
import gc,time

# ██████╗ ██╗   ██╗███████╗███████╗███████╗██████╗ 
# ██╔══██╗██║   ██║╚══███╔╝╚══███╔╝██╔════╝██╔══██╗
# ██████╔╝██║   ██║  ███╔╝   ███╔╝ █████╗  ██████╔╝
# ██╔══██╗██║   ██║ ███╔╝   ███╔╝  ██╔══╝  ██╔══██╗
# ██████╔╝╚██████╔╝███████╗███████╗███████╗██║  ██║
# ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝

class Buzzer:
    def __init__(self):
        self.timer_bee = Timer(Timer.TIMER1, Timer.CHANNEL0, mode=Timer.MODE_PWM)
        self.pin_bee = PWM(self.timer_bee, freq=1000,duty=0,pin=24)
        print('inint..')

    def bee(self,tune,sec):
        self.pin_bee.duty(50)
        self.pin_bee.freq(tune)
        time.sleep(sec)
        self.pin_bee.duty(0)



# ██╗██████╗ 
# ██║██╔══██╗
# ██║██████╔╝
# ██║██╔══██╗
# ██║██║  ██║
# ╚═╝╚═╝  ╚═╝
           
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



#  █████             ███    ███████   
# ░░███            ███░   ███░░░░░███ 
#  ░███          ███░    ███     ░░███
#  ░███        ███░     ░███      ░███
#  ░███      ███░       ░███      ░███
#  ░███    ███░         ░░███     ███ 
#  █████ ███░            ░░░███████░  
# ░░░░░ ░░░                ░░░░░░░    

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

#   █████████                                         
#  ███░░░░░███                                        
# ░███    ░░░   ██████  ████████  █████ █████  ██████ 
# ░░█████████  ███░░███░░███░░███░░███ ░░███  ███░░███
#  ░░░░░░░░███░███████  ░███ ░░░  ░███  ░███ ░███ ░███
#  ███    ░███░███░░░   ░███      ░░███ ███  ░███ ░███
# ░░█████████ ░░██████  █████      ░░█████   ░░██████ 
#  ░░░░░░░░░   ░░░░░░  ░░░░░        ░░░░░     ░░░░░░  
                                                    
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



#    █████████           ████                        ███████    █████          ███                     █████   
#   ███░░░░░███         ░░███                      ███░░░░░███ ░░███          ░░░                     ░░███    
#  ███     ░░░   ██████  ░███   ██████  ████████  ███     ░░███ ░███████      █████  ██████   ██████  ███████  
# ░███          ███░░███ ░███  ███░░███░░███░░███░███      ░███ ░███░░███    ░░███  ███░░███ ███░░███░░░███░   
# ░███         ░███ ░███ ░███ ░███ ░███ ░███ ░░░ ░███      ░███ ░███ ░███     ░███ ░███████ ░███ ░░░   ░███    
# ░░███     ███░███ ░███ ░███ ░███ ░███ ░███     ░░███     ███  ░███ ░███     ░███ ░███░░░  ░███  ███  ░███ ███
#  ░░█████████ ░░██████  █████░░██████  █████     ░░░███████░   ████████      ░███ ░░██████ ░░██████   ░░█████ 
#   ░░░░░░░░░   ░░░░░░  ░░░░░  ░░░░░░  ░░░░░        ░░░░░░░    ░░░░░░░░       ░███  ░░░░░░   ░░░░░░     ░░░░░  
#                                                                         ███ ░███                             
#                                                                        ░░██████                              
#                                                                         ░░░░░░                               
class ColorObject:
    def findMax(img, threadshold, areaLimit=100, drawRectangle=True , drawPosition=False):
        blobs = img.find_blobs([threadshold])
        maxObject = None
        if blobs:
            for b in blobs:
                val = b[2]*b[3]
                if(val > areaLimit) :
                    maxObject = b
                    areaLimit = val
        if(maxObject != None) :
            if(drawPosition) :
                img.draw_string(10,10,str(maxObject[0:4]))
            if(drawRectangle) :
                img.draw_rectangle(maxObject[0:4])
        return maxObject

print("load webai_ext finish")