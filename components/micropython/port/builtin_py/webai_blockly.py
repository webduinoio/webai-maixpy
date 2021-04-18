import gc
import time
import os
import sys
import lcd
from fpioa_manager import fm
from Maix import GPIO
from board import board_info
from machine import UART,Timer,PWM
import _thread
import time,lcd,image,sensor
import ustruct
from machine import I2C
from board import webai

def saveMsg(timer):
    global SYSTEM_THREAD_START_LIST
    while 1:
        if SYSTEM_SAVE_MSG_FLAG:
            print("lock thread")
            while not SYSTEM_ALLOCATE_LOCK.acquire():
                time.sleep(0.05)
            print("sleep 1")
            time.sleep(1)
            print("write1 cmd.txt")
            f=open('/flash/cmd.txt','w')
            print("write2 cmd.txt")
            f.write(timer.callback_arg())
            # f.write(cmd)
            print("write3 cmd.txt")
            f.close()
            print("write4 cmd.txt")
            os.sync()
            print("reset")
            SYSTEM_ALLOCATE_LOCK.release()
            import machine
            machine.reset()
        print("wait callback")
        time.sleep(0.1)



def MQTT_CALLBACK(uartObj):
    if SYSTEM_MQTT_CALLBACK_FLAG==True:
        SYSTEM_LOG_UART.stop()
        # from webai_api import downloadModel,takeMobileNetPic
        SUBSCRIBE_MSG = None
        startCallback=False
        global SYSTEM_WiFiCheckCount,SYSTEM_MQTT_TOPIC,SYSTEM_THREAD_START_LIST
        global SYSTEM_SAVE_MSG_FLAG
        global SYSTEM_MQTT_CONNECT
        try:
            while SYSTEM_LOG_UART.any():
                myLine = SYSTEM_LOG_UART.readline()
                # print("callback:",myLine)
                SUBSCRIBE_MSG = myLine.decode().strip()
                # if "mqttDisconnect" in myLine:
                #     SYSTEM_MQTT_CONNECT=False
                # if "subscribed" in myLine:
                #     SYSTEM_MQTT_CONNECT=True
                if "mqtt" in SUBSCRIBE_MSG[0:4]:
                    SUBSCRIBE_MSG = SUBSCRIBE_MSG.split(',', 2)
            if SUBSCRIBE_MSG != None and len(SUBSCRIBE_MSG) == 3:
                if SUBSCRIBE_MSG[1] == SYSTEM_ESP_DEVICE_ID+"/PING":
                    resetFlag=True
                    if SUBSCRIBE_MSG[2].find("_DEPLOY/") == 0:
                        startCallback=True
                        # pass
                        # resetFlag=False
                        # Mqtt.push("6e559b/PONG","OK")
                        
                        # print("DOWNLOAD")
                        # downloadModel('mqtt.main.py', 'yolo', SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:], True)
                        # print("reset")
                        #time.sleep(1)
                        # SYSTEM_TEST_MSG=SUBSCRIBE_MSG[2]
                        # SYSTEM_SAVE_MSG_FLAG=True
                    elif SUBSCRIBE_MSG[2].find("_RESET") == 0:
                        # Mqtt.push("6e559b/PONG","OK")
                        Mqtt.pushID("PONG", "OK")
                        print("reset")
                        import machine
                        machine.reset()
                    elif SUBSCRIBE_MSG[2].find("_TAKEPIC_YOLO/") == 0:
                        # Mqtt.push("6e559b/PONG","OK")
                        Mqtt.pushID("PONG", "OK")
                        print("_TAKEPIC_YOLO")
                        resetFlag=False
                    elif SUBSCRIBE_MSG[2].find("_TAKEPIC_MOBILENET/") == 0:
                        startCallback=True
                        # pass
                        # Mqtt.push("6e559b/PONG","OK")
                        # Mqtt.pushID("PONG", "OK")
                        # mqttJsonData = ujson.loads(
                        #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
                        # takeMobileNetPic(mqttJsonData['dsname'], mqttJsonData['count'], 1, mqttJsonData['url'], mqttJsonData['hashKey'])
                        # with open('/flash/cmd.txt','w') as f:
                        #     f.write(SUBSCRIBE_MSG[2])
                        # os.sync()
                        # import machine
                        # machine.reset()
                    elif SUBSCRIBE_MSG[2].find("_DOWNLOAD_MODEL/") == 0:
                        startCallback=True
                        # pass
                        # Mqtt.push("6e559b/PONG","OK")
                        # Mqtt.pushID("PONG", "OK")
                        # mqttJsonData = ujson.loads(
                        #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
                        # downloadModel(mqttJsonData['fileName'], mqttJsonData['modelType'], mqttJsonData['url'])
                        
                    elif SUBSCRIBE_MSG[2].find("_DOWNLOAD_FILE/") == 0:
                        startCallback=True
                        # pass
                        # Mqtt.push("6e559b/PONG","OK")
                        # Mqtt.pushID("PONG", "OK")
                        # mqttJsonData = ujson.loads(
                        #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
                        # downloadModel(mqttJsonData['fileName'], 'yolo', mqttJsonData['url'], True)
                        # print("reset")
                        #time.sleep(1)
                        # import machine
                        # os.sync()
                        # machine.reset()
                    else:
                        resetFlag=False
                        print("error command")
                    resetFlag=False
                    # _thread.start_new_thread(saveMsg, (SUBSCRIBE_MSG[2],))
                    # startCallback=True
                    if resetFlag:
                        print("stop thread")
                        for i in range(0,len(SYSTEM_THREAD_START_LIST)):
                            SYSTEM_THREAD_START_LIST[i]=0
                        bak = time.ticks()
                        print("check stop thread list")
                        while 1:
                            if 1 in SYSTEM_THREAD_STOP_LIST:
                                print("wait stop")
                                time.sleep(0.1)
                            else:
                                print("stop all thread")
                                break
                        print('total time ', time.ticks() - bak)
                        Mqtt.pushID("PONG", "OK")
                        print("write cmd.txt")
                        with open('/flash/cmd.txt','w') as f:
                            f.write(SUBSCRIBE_MSG[2])
                        os.sync()
                        print("reset")
                        import machine
                        machine.reset()
                    SYSTEM_WiFiCheckCount = 99
                    print("blockly:",SYSTEM_WiFiCheckCount)
                elif SYSTEM_THREAD_MQTT_FLAG == True:
                    if SYSTEM_MQTT_TOPIC.get(SUBSCRIBE_MSG[1]) != None:
                        print("user topic:",SUBSCRIBE_MSG[2])
                        SYSTEM_MQTT_TOPIC[SUBSCRIBE_MSG[1]] = SUBSCRIBE_MSG[2]
                    else:
                        print("error topic")
        except Exception as e:
            print(e)
            print("MQTT_CALLBACK read error")

        if startCallback:
            Mqtt.pushID("PONG", "saveCmd")
            SYSTEM_SAVE_MSG_FLAG=True
            # saveMqttMsg = Timer(Timer.TIMER2, Timer.CHANNEL0, mode=Timer.MODE_ONE_SHOT, period=500, unit=Timer.UNIT_MS, callback=saveMsg, arg=SUBSCRIBE_MSG[2], start=True, priority=1, div=0)
            Timer(Timer.TIMER2, Timer.CHANNEL0, mode=Timer.MODE_ONE_SHOT, period=500, unit=Timer.UNIT_MS, callback=saveMsg, arg=SUBSCRIBE_MSG[2], start=True, priority=1, div=0)
            # _thread.start_new_thread(saveMsg, (SUBSCRIBE_MSG[2],))
        else:
            SYSTEM_LOG_UART.start()
            while SYSTEM_LOG_UART.any():
                SYSTEM_LOG_UART.readline()


class Lcd:

    def __init__(self):
        import image
        self.image = image
        lcd.init()
        lcd.clear()
        #webai.img = webai.img
        print('Lcd_Blockly __init__')

    def __del__(self):
        del self
        print('Lcd_Blockly __del__')

    def clear(self):
        lcd.clear()
        #webai.img.clear()

    def draw_string(self, x, y, msg, strColor, bgColor):
        if not msg == '':
            lcd.draw_string(x, y, str(msg), strColor, bgColor)

    def displayImg(self, img=None):
        if type(img) == str:
            cwd = SYSTEM_DEFAULT_PATH
            if cwd == "flash":
                self.path = "/flash/"+img+'.jpg'
            else:
                self.path = "/sd/"+img+'.jpg'
            webai.img = self.image.Image(self.path)
            lcd.display(webai.img)
        else:
            lcd.display(img)

    def displayColor(self, color):
        lcd.clear(color)

    def selfObject(self):
        return lcd

    def width(self):
        return lcd.width()

    def height(self):
        return lcd.height()

    def drawCircle(self, x, y, radius, color=0xffffff, thickness=1, fill=False):
        webai.img.draw_circle(x, y, radius, color, thickness, fill)
        lcd.display(webai.img)

    def drawLine(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        webai.img.draw_line(x0, y0, x1, y1, color, thickness)
        lcd.display(webai.img)

    def drawRectangle(self, x, y, w, h, color=0xffffff, thickness=1, fill=False):
        webai.img.draw_rectangle(x, y, w, h, color, thickness, fill)
        lcd.display(webai.img)

    def drawArrow(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        webai.img.draw_arrow(x0, y0, x1, y1, color, thickness)
        lcd.display(webai.img)

    def drawCross(self, x, y, color=0xffffff, size=5, thickness=1):
        webai.img.draw_cross(x, y, color, size, thickness)
        lcd.display(webai.img)

    def drawString(self, x, y, text, color=(255,255,255), scale=2, x_spacing=20, mono_space=False):
        self.image.font_load(self.image.UTF8, 16, 16, 0x980000)
        webai.img.draw_string(x, y, text, scale=scale, color=color, x_spacing=x_spacing, mono_space=mono_space)
        self.image.font_free()
        lcd.display(webai.img)
            
class Camera:
    import sensor
    def __init__(self, flip=1, auto_gain=1, auto_whitebal=1, auto_exposure=1, brightness=3):
        #self.sensor=sensor
        try:
            showMessage("init camera")
            self.sensor.reset()
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.skip_frames(time=2000)
            self.setFlip(flip)
            self.sensor.set_auto_gain(auto_gain)
            self.sensor.set_auto_whitebal(auto_whitebal)
            self.sensor.set_auto_exposure(auto_exposure)
            self.sensor.set_brightness(brightness)
            print('Camera_Blockly __init__')
            showMessage("init camera OK")
        except Exception as e:
            print(e)
            showMessage("init camera ERROR")
    def setFlip(self, flip):
        global SYSTEM_CAMERA_FLIP
        SYSTEM_CAMERA_FLIP = flip
        self.sensor.set_vflip(SYSTEM_CAMERA_FLIP)

    def shutdown(self, enable):
        self.sensor.shutdown(enable)

    def snapshot(self):
        return self.sensor.snapshot()

    def stream(self):
        self.sensor.run(1)

    def save(self,fileName):
        cwd = SYSTEM_DEFAULT_PATH
        if cwd == "flash":
            self.path = "/flash/"+fileName+".jpg"
        else:
            self.path = "/sd/"+fileName+".jpg"
        self.sensor.snapshot().save(self.path)

    def selfObject(self):
        return self.sensor

    def __del__(self):
        del self
        print('Camera_Blockly __del__')


class Mic:
    import audio
    from Maix import I2S
    from fpioa_manager import fm
    # user setting
    #sample_rate   = 16000
    sample_rate = 48000

    # default seting
    sample_points = 2048
    wav_ch = 2

    fm.register(board_info.MIC_I2S_IN, fm.fpioa.I2S0_IN_D0, force=True)
    # 19 on Go Board and Bit(new version)
    fm.register(board_info.MIC_I2S_WS, fm.fpioa.I2S0_WS, force=True)
    fm.register(board_info.MIC_I2S_SCLK, fm.fpioa.I2S0_SCLK,force=True)  # 18 on Go Board and Bit(new version)

    rx = I2S(I2S.DEVICE_0)
    rx.channel_config(rx.CHANNEL_0, rx.RECEIVER, align_mode=I2S.STANDARD_MODE)
    rx.set_sample_rate(sample_rate)

    def start(self, folder="", fileName="recorder", record_time=5):
        if folder=="":
            cwd = SYSTEM_DEFAULT_PATH
            if cwd == "flash":
                folder = "flash"
                record_time = 1
            else:
                folder = "sd"
        self.recorder = self.audio.Audio(path="/"+folder+"/"+fileName+".wav", is_create=True, samplerate=self.sample_rate)
        self.queue = []
        print("start recorder")
        frame_cnt = record_time*self.sample_rate//self.sample_points

        for i in range(frame_cnt):
            tmp = self.rx.record(self.sample_points*self.wav_ch)
            if len(self.queue) > 0:
                ret = self.recorder.record(self.queue[0])
                self.queue.pop(0)
            self.rx.wait_record()
            self.queue.append(tmp)
            #lcdTmp.draw_string(int(311-len("please wait 10s ...")*6.9)//2,int(224//1.5),"please wait 10s ...",lcd.GREEN,lcd.BLACK)
            #lcd.draw_string(int(311-len("please wait 10s ...")*6.9)//2,int(224//1.5),"please wait 10s ...",lcd.GREEN,lcd.BLACK)
            print(str(i) + ":" + str(time.ticks()))

        self.recorder.finish()
        print("finish")


class Ir:
    PINUSE=[]
    PINIO=[]
    def io(PIN):
        PIN=fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN):
        PIN=fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)].value()
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO.value()
class Io:
    PWMPINUSE=[]
    PINUSE=[]
    PINIO=[]
    def io(PIN):
        PIN=fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,GPIO.PULL_UP)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN):
        PIN=fpioaMapGPIO[PIN]
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
            USER_PWM_LIST_COUNT=len(USER_PWM_LIST)
            if USER_PWM_LIST_COUNT<8:
                if USER_PWM_LIST_COUNT<4:
                    BLOCKLY_SYSTEM_TIMER=0
                else:
                    BLOCKLY_SYSTEM_TIMER=1
                PIN=fpioaMapGPIO[PIN]
                if PIN in __class__.PWMPINUSE:
                    #print("old",__class__.PWMPINUSE.index(PIN))
                    #print(__class__.PWMPINUSE)
                    USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(VALUE)
                else:
                    #print("new")
                    TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                    Io_Blockly_PWM = PWM(TIMER,freq=PWM_FREQ, duty=VALUE, pin=PIN[0])
                    __class__.PWMPINUSE.append(PIN)
                    USER_PWM_LIST.append(Io_Blockly_PWM)
                #print("USER_PWM_LIST_COUNT:"+str(USER_PWM_LIST_COUNT))
            else:
                raise Exception("Io_Blockly error")
        else:
            PIN=fpioaMapGPIO[PIN]
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

        
class Servo:
    PWMPINUSE=[]
    ANGLELIST=[]
    def angle(PIN,PWM_FREQ=50,VALUE=0):
        USER_PWM_LIST_COUNT=len(USER_PWM_LIST)
        if USER_PWM_LIST_COUNT<8:
            if USER_PWM_LIST_COUNT<4:
                BLOCKLY_SYSTEM_TIMER=0
            else:
                BLOCKLY_SYSTEM_TIMER=1
            PIN=fpioaMapGPIO[PIN]
            duty_cycle = (0.05 * PWM_FREQ) + (0.19 * PWM_FREQ * VALUE / 180)
            if PIN in __class__.PWMPINUSE:
                USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(duty_cycle)
                __class__.ANGLELIST[__class__.PWMPINUSE.index(PIN)]=VALUE
                # print("old")
            else:
                TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                Io_Blockly_PWM = PWM(TIMER,freq=PWM_FREQ, duty=duty_cycle, pin=PIN[0])
                __class__.PWMPINUSE.append(PIN)
                USER_PWM_LIST.append(Io_Blockly_PWM)
                __class__.ANGLELIST.append(VALUE)
                # print("new")
        else:
            raise Exception("Servo_Blockly error")
    def getAngle(PIN):
        PIN=fpioaMapGPIO[PIN]
        if PIN in __class__.PWMPINUSE:
            # print("true")
            return __class__.ANGLELIST[__class__.PWMPINUSE.index(PIN)]
        else:
            # print("false")
            return 110


 #  _______    _____    _____   ____    _  _     ______   ___    _____ 
 # |__   __|  / ____|  / ____| |___ \  | || |   |____  | |__ \  | ____|
 #    | |    | |      | (___     __) | | || |_      / /     ) | | |__  
 #    | |    | |       \___ \   |__ <  |__   _|    / /     / /  |___ \ 
 #    | |    | |____   ____) |  ___) |    | |     / /     / /_   ___) |
 #    |_|     \_____| |_____/  |____/     |_|    /_/     |____| |____/ 

_COMMAND_BIT = const(0x80)
_REGISTER_ENABLE = const(0x00)
_REGISTER_ATIME = const(0x01)
_REGISTER_AILT = const(0x04)
_REGISTER_AIHT = const(0x06)
_REGISTER_ID = const(0x12)
_REGISTER_APERS = const(0x0c)
_REGISTER_CONTROL = const(0x0f)
_REGISTER_SENSORID = const(0x12)
_REGISTER_STATUS = const(0x13)
_REGISTER_CDATA = const(0x14)
_REGISTER_RDATA = const(0x16)
_REGISTER_GDATA = const(0x18)
_REGISTER_BDATA = const(0x1a)
_ENABLE_AIEN = const(0x10)
_ENABLE_WEN = const(0x08)
_ENABLE_AEN = const(0x02)
_ENABLE_PON = const(0x01)
_GAINS = (1, 4, 16, 60)
_CYCLES = (0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)


class TCS34725:
   def __init__(self, i2c, address=0x29):
       self.i2c = i2c
       self.address = address
       self._active = False
       self.integration_time(2.4)
       sensor_id = self.sensor_id()
       if sensor_id not in (0x44, 0x10):
           #print(sensor_id)
           raise RuntimeError("wrong sensor id 0x{:x}".format(sensor_id))

   def _register8(self, register, value=None):
       register |= _COMMAND_BIT
       if value is None:
           return self.i2c.readfrom_mem(self.address, register, 1)[0]
       data = ustruct.pack('<B', value)
       self.i2c.writeto_mem(self.address, register, data)

   def _register16(self, register, value=None):
       register |= _COMMAND_BIT
       if value is None:
           data = self.i2c.readfrom_mem(self.address, register, 2)
           return ustruct.unpack('<H', data)[0]
       data = ustruct.pack('<H', value)
       self.i2c.writeto_mem(self.address, register, data)

   def active(self, value=None):
       if value is None:
           return self._active
       value = bool(value)
       if self._active == value:
           return
       self._active = value
       enable = self._register8(_REGISTER_ENABLE)
       if value:
           self._register8(_REGISTER_ENABLE, enable | _ENABLE_PON)
           time.sleep_ms(3)
           self._register8(_REGISTER_ENABLE,
               enable | _ENABLE_PON | _ENABLE_AEN)
       else:
           self._register8(_REGISTER_ENABLE,
               enable & ~(_ENABLE_PON | _ENABLE_AEN))

   def sensor_id(self):
       return self._register8(_REGISTER_SENSORID)

   def integration_time(self, value=None):
       if value is None:
           return self._integration_time
       value = min(614.4, max(2.4, value))
       cycles = int(value / 2.4)
       self._integration_time = cycles * 2.4
       return self._register8(_REGISTER_ATIME, 256 - cycles)

   def gain(self, value):
       if value is None:
           return _GAINS[self._register8(_REGISTER_CONTROL)]
       if value not in _GAINS:
           raise ValueError("gain must be 1, 4, 16 or 60")
       return self._register8(_REGISTER_CONTROL, _GAINS.index(value))

   def _valid(self):
       return bool(self._register8(_REGISTER_STATUS) & 0x01)

   def read(self, raw=False):
       was_active = self.active()
       self.active(True)
       while not self._valid():
           time.sleep_ms(int(self._integration_time + 0.9))
       data = tuple(self._register16(register) for register in (
           _REGISTER_RDATA,
           _REGISTER_GDATA,
           _REGISTER_BDATA,
           _REGISTER_CDATA,
       ))
       self.active(was_active)
       if raw:
           return data
       return self._temperature_and_lux(data)

   def _temperature_and_lux(self, data):
       r, g, b, c = data
       x = -0.14282 * r + 1.54924 * g + -0.95641 * b
       y = -0.32466 * r + 1.57837 * g + -0.73191 * b
       z = -0.68202 * r + 0.77073 * g +  0.56332 * b
       d = x + y + z
       n = (x / d - 0.3320) / (0.1858 - y / d)
       cct = 449.0 * n**3 + 3525.0 * n**2 + 6823.3 * n + 5520.33
       return cct, y

   def threshold(self, cycles=None, min_value=None, max_value=None):
       if cycles is None and min_value is None and max_value is None:
           min_value = self._register16(_REGISTER_AILT)
           max_value = self._register16(_REGISTER_AILT)
           if self._register8(_REGISTER_ENABLE) & _ENABLE_AIEN:
               cycles = _CYCLES[self._register8(_REGISTER_APERS) & 0x0f]
           else:
               cycles = -1
           return cycles, min_value, max_value
       if min_value is not None:
           self._register16(_REGISTER_AILT, min_value)
       if max_value is not None:
           self._register16(_REGISTER_AIHT, max_value)
       if cycles is not None:
           enable = self._register8(_REGISTER_ENABLE)
           if cycles == -1:
               self._register8(_REGISTER_ENABLE, enable & ~(_ENABLE_AIEN))
           else:
               self._register8(_REGISTER_ENABLE, enable | _ENABLE_AIEN)
               if cycles not in _CYCLES:
                   raise ValueError("invalid persistence cycles")
               self._register8(_REGISTER_APERS, _CYCLES.index(cycles))

   def interrupt(self, value=None):
       if value is None:
           return bool(self._register8(_REGISTER_STATUS) & _ENABLE_AIEN)
       if value:
           raise ValueError("interrupt can only be cleared")
       self.i2c.writeto(self.address, b'\xe6')



 #   ____    _         _                 _     _______                         _      _                 
 #  / __ \  | |       (_)               | |   |__   __|                       | |    (_)                
 # | |  | | | |__      _    ___    ___  | |_     | |     _ __    __ _    ___  | | __  _   _ __     __ _ 
 # | |  | | | '_ \    | |  / _ \  / __| | __|    | |    | '__|  / _` |  / __| | |/ / | | | '_ \   / _` |
 # | |__| | | |_) |   | | |  __/ | (__  | |_     | |    | |    | (_| | | (__  |   <  | | | | | | | (_| |
 #  \____/  |_.__/    | |  \___|  \___|  \__|    |_|    |_|     \__,_|  \___| |_|\_\ |_| |_| |_|  \__, |
 #                   _/ |                                                                          __/ |
 #                  |__/                                                                          |___/ 

class ObjectTracking():
    import KPU as kpu
    import sensor
    def showMessage(self,msg):
        print(msg)
        lcd.clear()
        lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)
        
    def __init__(self,flip=0,classes=[],model=None,threshold=0.1,nms_value=0.1,w=320,h=224):
        try:
            lcd.init()    
            showMessage("init camera")
            self.sensor.reset()
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((w, h))
            self.sensor.set_vflip(flip)
            self.sensor.set_auto_gain(1)
            self.sensor.set_auto_whitebal(1)
            self.sensor.set_auto_exposure(1)
            self.sensor.set_brightness(3)
            self.sensor.skip_frames(time = 2000)
            self.sensor.run(1)
        except Exception as e:
            print(e)
            showMessage("camera error")                        
            sys.exit()
            
        try:
            # modelPathStart=modelPath.find('(')
            # modelPathEnd=modelPath.rfind(')')
            # classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            cwd=SYSTEM_DEFAULT_PATH
            if cwd=="flash":
                model=0xD40000
            else:
                model="/sd/"+model+".kmodel"
            self.classes=classes
            showMessage("load model")
            self.task = self.kpu.load(model)
            self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
            self.kpu.init_yolo2(self.task, threshold, nms_value, 5, self.anchor)
            showMessage("init finish")
        except Exception as e:
            print(e)
            showMessage("load model error")
            sys.exit()
    def checkObjects(self):
        try:
            self.classesArr=[]
            img = self.sensor.snapshot()        
            code = self.kpu.run_yolo2(self.task, img)
            if code:
                for i in code:
                    img.draw_rectangle(i.rect())
                    lcd.display(img)
                    respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
                    self.classesArr.append(respList)
                    # print(self.classesArr)
                    # for i in code:
                    #     lcd.draw_string(i.x(), i.y(), self.classes[i.classid()], lcd.RED, lcd.WHITE)
                    #     lcd.draw_string(i.x(), i.y()+12, '%.3f'%i.value(), lcd.RED, lcd.WHITE)
                return True
            else:
                lcd.display(img)
                return False
        except Exception as e:
            print(e)

    def getObjects(self,obj):
        returnArr=[]
        for i in self.classesArr:
            if self.classes[i['classid']]==obj:
                returnArr.append(i)
        return returnArr

    def __del__(self):
        self.kpu.deinit(self.task)
        gc.collect()



 #  _____                                       _____   _                       _    __   _                  _     _                 
 # |_   _|                                     / ____| | |                     (_)  / _| (_)                | |   (_)                
 #   | |    _ __ ___     __ _    __ _    ___  | |      | |   __ _   ___   ___   _  | |_   _    ___    __ _  | |_   _    ___    _ __  
 #   | |   | '_ ` _ \   / _` |  / _` |  / _ \ | |      | |  / _` | / __| / __| | | |  _| | |  / __|  / _` | | __| | |  / _ \  | '_ \ 
 #  _| |_  | | | | | | | (_| | | (_| | |  __/ | |____  | | | (_| | \__ \ \__ \ | | | |   | | | (__  | (_| | | |_  | | | (_) | | | | |
 # |_____| |_| |_| |_|  \__,_|  \__, |  \___|  \_____| |_|  \__,_| |___/ |___/ |_| |_|   |_|  \___|  \__,_|  \__| |_|  \___/  |_| |_|
 #                               __/ |                                                                                               
 #                              |___/                                                                                                
class ImageClassification():
    import KPU as kpu
    import sensor
    def showMessage(self,msg):
        print(msg)
        lcd.clear()
        lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)
        
    def __init__(self,flip=0,classes=[],model=None,w=224,h=224):
        try:
            lcd.init()
            showMessage("init camera")
            self.sensor.reset()
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((w, h))
            self.sensor.set_vflip(flip)
            self.sensor.set_auto_gain(1)
            self.sensor.set_auto_whitebal(1)
            self.sensor.set_auto_exposure(1)
            self.sensor.set_brightness(3)
            self.sensor.skip_frames(time = 2000)
            self.sensor.run(1)
        except Exception as e:
            print(e)
            showMessage("camera error")
            sys.exit()
            
        try:
            # modelPathStart=modelPath.find('(')
            # modelPathEnd=modelPath.rfind(')')
            # classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            cwd=SYSTEM_DEFAULT_PATH
            if cwd=="flash":
                model=0xD40000
            else:
                model="/sd/"+model+".kmodel"
            self.classes=classes
            showMessage("load model")
            self.task = self.kpu.load(model)
            showMessage("init finish")
        except Exception as e:
            print(e)
            showMessage("load model error")
            sys.exit()
    def checkClass(self):
        try:
            self.classesArr=[]
            img = self.sensor.snapshot()
            fmap = self.kpu.forward(self.task, img)
            plist=fmap[:]
            pmax=max(plist)
            #print(pmax)
            max_index=plist.index(pmax)
            #lcd.display(img, oft=(0,0))
            lcd.display(img)
            #lcd.draw_string(0, 100, "%.2f:%s "%(pmax, labels[max_index].strip()))
            objname=self.classes[max_index].strip()
            print(objname)
            # lcd.draw_string(0, 100, "%s "%objname,lcd.RED, lcd.WHITE)
            # lcd.draw_string(0, 150, "%.2f"%pmax,lcd.RED, lcd.WHITE)
            respList={"x":0,"y":0,"w":0,"h":0,"value":float("%.2f"%pmax),"classid":max_index,"index":0,"objnum":0,"objname":objname}
            self.classesArr.append(respList)
            return True
        except Exception as e:
            print(e)
            self.classesArr=[]
            return False
        # try:
        #     self.classesArr=[]
        #     img = sensor.snapshot()
        #     code = self.kpu.run_yolo2(self.task, img)
        #     img=img.resize(224,224)
        #     if code:
        #         for i in code:
        #             lcd.display(img)
        #             respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
        #             self.classesArr.append(respList)
        #             # lcd.draw_string(0, 100, self.classes[i.classid()],lcd.RED, lcd.WHITE)
        #             # lcd.draw_string(0, 150, '%.3f'%i.value(),lcd.RED, lcd.WHITE)
        #         # print(self.classesArr)
        #         return True
        #     else:
        #         lcd.display(img)
        #         return False
        # except Exception as e:
        #     print(e)

    def getClass(self):
        #print(self.classesArr)
        if(len(self.classesArr)>0):
            self.classesArr.sort(key = lambda s: s['value'])
            #print(self.classesArr)
            return self.classesArr[len(self.classesArr)-1]
        else:
            return []
            
    def __del__(self):
        self.kpu.deinit(self.task)
        gc.collect()



 #  _   _          _                               _    
 # | \ | |        | |                             | |   
 # |  \| |   ___  | |_  __      __   ___    _ __  | | __
 # | . ` |  / _ \ | __| \ \ /\ / /  / _ \  | '__| | |/ /
 # | |\  | |  __/ | |_   \ V  V /  | (_) | | |    |   < 
 # |_| \_|  \___|  \__|   \_/\_/    \___/  |_|    |_|\_\
                                                      
class Network:
    def connect(SSID, PWD):
        import network
        import socket
        pin8285 = 20
        fm.register(pin8285, fm.fpioa.GPIO0, force=True)
        reset = GPIO(GPIO.GPIO0, GPIO.OUT)
        reset.value(0)
        time.sleep(0.01)
        reset.value(1)
        # time.sleep(0.5)
        fm.unregister(pin8285)
        myLine = ''
        while not "init finish" in myLine:
            while not SYSTEM_AT_UART.any():
                pass
            myLine = SYSTEM_AT_UART.readline()
        wlan = network.ESP8285(SYSTEM_AT_UART)
        err = 0
        while 1:
            try:
                wlan.connect(SSID, PWD)
            except Exception:
                err += 1
                print("Connect AP failed, now try again")
                if err > 3:
                    raise Exception("Conenct AP fail")
                continue
            break
        #time.sleep(1)
        # self.WiFiInfo = wlan.ifconfig()
        # del err, wlan
        # print(self.WiFiInfo)
        time.sleep(1)

    # def info(self):
    #     return self.WiFiInfo

    # def __del__(self):
    #     del self
    #     print("Network_Blockly __del__")


  # __  __    ____    _______   _______ 
 # |  \/  |  / __ \  |__   __| |__   __|
 # | \  / | | |  | |    | |       | |   
 # | |\/| | | |  | |    | |       | |   
 # | |  | | | |__| |    | |       | |   
 # |_|  |_|  \___\_\    |_|       |_|   

class Mqtt:
    # def __init__(self):
    #     pass
    def sub(topic):
        while not SYSTEM_MQTT_CONNECT:
            print("wait mqtt connect")
            showMessage("wait mqtt connect",clear=True)
            time.sleep(1)
        global SYSTEM_THREAD_MQTT_FLAG
        SYSTEM_THREAD_MQTT_FLAG=True
        print("subscribe topic ...")
        mqttSetSub = 'AT+MQTT="sub","{topic}"'.format(topic=topic)
        print(mqttSetSub)
        status=commCycle(mqttSetSub)
        if status=="OK":
            print("subscribe "+topic+" finish")
            showMessage("subscribe "+topic+" finish",clear=True)
        else:
            print("subscribe "+topic+" error")
            showMessage("subscribe "+topic+" finish",clear=True)
        del status
        time.sleep(0.5)

    def push(topic, msg):
        while not SYSTEM_MQTT_CONNECT:
            print("wait mqtt connect")
            showMessage("wait mqtt connect",clear=True)
            time.sleep(1)
        mqttSetPush = 'AT+MQTT="push","{topic}","{msg}"'.format(topic=topic, msg=msg)
        # print(mqttSetPush)
        commCycle(mqttSetPush)
        time.sleep(0.15)

    def subID(topic):
        while not SYSTEM_MQTT_CONNECT:
            print("wait mqtt connect")
            showMessage("wait mqtt connect",clear=True)
            time.sleep(1)
        global SYSTEM_THREAD_MQTT_FLAG
        SYSTEM_THREAD_MQTT_FLAG=True
        print("subscribeID topic ...")
        mqttSetSub = 'AT+MQTT="sub","{mqttUID}/{topic}"'.format(mqttUID=SYSTEM_ESP_DEVICE_ID, topic=topic)
        print(mqttSetSub)
        status=commCycle(mqttSetSub)
        if status=="OK":
            print("subscribe "+topic+" finish")
            showMessage("subscribe "+topic+" finish",clear=True)
        else:
            print("subscribe "+topic+" error")
            showMessage("subscribe "+topic+" finish",clear=True)
        del status
        time.sleep(0.5)

    def pushID(topic, msg):
        while not SYSTEM_MQTT_CONNECT:
            print("wait mqtt connect")
            showMessage("wait mqtt connect",clear=True)
            time.sleep(1)
        mqttSetPush = 'AT+MQTT="push","{mqttUID}/{topic}","{msg}"'.format(mqttUID=SYSTEM_ESP_DEVICE_ID, topic=topic, msg=msg)
        # print(mqttSetPush)
        commCycle(mqttSetPush)
        time.sleep(0.15)

    # def waitMsg(self):
    #     try:
    #         if SYSTEM_AT_UART.any():
    #             myLine = SYSTEM_AT_UART.readline()
    #             # print(myLine)
    #             subscribeMsg = myLine.decode().strip()
    #             if "mqtt" in subscribeMsg[0:4]:
    #                 subscribeMsg = subscribeMsg.split(',')
    #                 # print( [True,[None,subscribeMsg[1],None,subscribeMsg[2]]])
    #                 return [True, [None, subscribeMsg[1], None, subscribeMsg[2]]]
    #             else:
    #                 return [False, [None, None, None, None]]
    #         else:
    #             return [False, [None, None, None, None]]
    #     except Exception as e:
    #         print(e)
    #         return [False, [None, None, None, None]]

    # def __del__(self):
    #     del self
    #     print("Mqtt __del__")


# This controls one command exection cycle.
def commCycle(command, timeout=5000):
    SYSTEM_AT_UART.write(command + '\r\n')
    myLine = ''
    startTime = time.ticks_ms()
    ifdata = True
    try:
        while not "OK" in myLine:
            while not SYSTEM_AT_UART.any():
                endTime = time.ticks_ms()
                # print(endTime-startTime)
                if((endTime-startTime) >= timeout):
                    ifdata = False
                    break
            if(ifdata):
                myLine = SYSTEM_AT_UART.readline()
                print(myLine)
                if "ERROR" in myLine:
                    # print("ERROR")
                    # raise Exception('ERROR')
                    return "ERROR"
                elif "busy s" in myLine:
                    # print("busy sending")
                    # raise Exception('busy sending')
                    return "busy sending"
                elif "busy p" in myLine:
                    # print("busy processing")
                    # raise Exception('busy processing')
                    return "busy processing"
            else:
                print("timeout")
                # raise Exception('timeout')
                return "timeout"
                # break
        return "OK"
    except Exception as e:
        print(e)


def readUID(timeout=2000):
    myLine = ''
    respUID = ''
    startTime = time.ticks_ms()
    ifdata = True
    SYSTEM_AT_UART.write('AT+SYSUID' + '\r\n')
    try:
        while not "OK" in myLine:
            while not SYSTEM_AT_UART.any():
                endTime = time.ticks_ms()
                # print(end-start)
                if((endTime-startTime) >= timeout):
                    ifdata = False
                    break
            if(ifdata):
                myLine = SYSTEM_AT_UART.readline()
                print(myLine)
                if "unique id" in myLine:
                    myLine = myLine.strip().decode()
                    #print(myLine[10:])
                    respUID = myLine[10:]
                elif "ERROR" in myLine:
                    # print("ERROR")
                    # raise Exception('ERROR')
                    return "ERROR"
                elif "busy s" in myLine:
                    # print("busy sending")
                    # raise Exception('busy sending')
                    return "busy sending"
                elif "busy p" in myLine:
                    # print("busy processing")
                    # raise Exception('busy processing')
                    return "busy processing"
            else:
                print("timeout")
                # raise Exception('timeout')
                return "timeout"
                # break
        return respUID
    except Exception as e:
        print(e)
        return "ERROR"


def showMessage(msg, x=-1, y=0, center=True, clear=False):
    if msg=="":
        msg=" "
    if clear:
        lcd.clear()
    if center:
        lcd.draw_string(int(320-len(msg)*8)//2, 112, msg, lcd.WHITE)
    else:
        if x == -1:
            lcd.draw_string(int(320-len(msg)*8)//2, int(224/7*y), msg, lcd.WHITE)
        else:
            lcd.draw_string(x, int(224/7*y), msg, lcd.WHITE)

def printVal():
    print(globals())
    
print("load blockly finish")