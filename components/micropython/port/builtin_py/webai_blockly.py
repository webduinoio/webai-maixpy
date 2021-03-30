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

def Blockly_Init():
    global USER_PWM_LIST
    USER_PWM_LIST = []
    global SYSTEM_K210_VERSION, SYSTEM_BTN_L, SYSTEM_BTN_R, SYSTEM_AT_UART, SYSTEM_ESP_VERSION, SYSTEM_ESP_DEVICE_ID, SYSTEM_DEFAULT_PATH, SYSTEM_MQTT_CALLBACK_FLAG, SYSTEM_THREAD_MQTT_FLAG, SYSTEM_THREAD_MQTT_MSG, SYSTEM_MQTT_TOPIC, SYSTEM_LOG_UART
    global SYSTEM_WLAN, SYSTEM_WiFiInfo,SYSTEM_WiFiCheckCount
    global fpioaMapGPIO
    global SYSTEM_THREAD_START_LIST,SYSTEM_THREAD_STOP_LIST
    SYSTEM_THREAD_START_LIST=[]
    SYSTEM_THREAD_STOP_LIST=[]


    global SYSTEM_SAVE_MSG_FLAG
    SYSTEM_SAVE_MSG_FLAG=False
    # SYSTEM_TEST_MSG=""
    global SYSTEM_ALLOCATE_LOCK
    SYSTEM_ALLOCATE_LOCK = _thread.allocate_lock()
    global SYSTEM_MQTT_CONNECT
    SYSTEM_MQTT_CONNECT=False

    fpioaMapGPIO={
'0':[board_info.P0,fm.fpioa.GPIOHS0,GPIO.GPIOHS0],
'1':[board_info.P1,fm.fpioa.GPIOHS1,GPIO.GPIOHS1],
'2':[board_info.P2,fm.fpioa.GPIOHS2,GPIO.GPIOHS2],
'3':[board_info.P3,fm.fpioa.GPIOHS3,GPIO.GPIOHS3],
'5':[board_info.P5,fm.fpioa.GPIOHS5,GPIO.GPIOHS5],
'6':[board_info.P6,fm.fpioa.GPIOHS6,GPIO.GPIOHS6],
'7':[board_info.P7,fm.fpioa.GPIOHS7,GPIO.GPIOHS7],
'8':[board_info.P8,fm.fpioa.GPIOHS8,GPIO.GPIOHS8],
'9':[board_info.P9,fm.fpioa.GPIOHS9,GPIO.GPIOHS9],
'10':[board_info.P10,fm.fpioa.GPIOHS10,GPIO.GPIOHS10],
'11':[board_info.P11,fm.fpioa.GPIOHS11,GPIO.GPIOHS11],
'12':[board_info.P12,fm.fpioa.GPIOHS12,GPIO.GPIOHS12],
'13':[board_info.P13,fm.fpioa.GPIOHS13,GPIO.GPIOHS13],
'14':[board_info.P14,fm.fpioa.GPIOHS14,GPIO.GPIOHS14],
'15':[board_info.P15,fm.fpioa.GPIOHS15,GPIO.GPIOHS15],
'16':[board_info.P16,fm.fpioa.GPIOHS16,GPIO.GPIOHS16],
'19':[board_info.P19,fm.fpioa.GPIO0,GPIO.GPIO0],
'20':[board_info.P20,fm.fpioa.GPIO1,GPIO.GPIO1]}
    SYSTEM_WLAN = None
    SYSTEM_WiFiInfo = None
    SYSTEM_WiFiCheckCount = 7
    SYSTEM_K210_VERSION = os.uname()
    pinA = 7  # A
    fm.fpioa.set_function(pinA, fm.fpioa.GPIO7)
    SYSTEM_BTN_L = GPIO(GPIO.GPIO7, GPIO.IN)
    pinB = 16  # B
    fm.fpioa.set_function(pinB, fm.fpioa.GPIO6)
    SYSTEM_BTN_R = GPIO(GPIO.GPIO6, GPIO.IN)
    del pinA, pinB
    fm.register(27, fm.fpioa.UART2_TX, force=True)
    fm.register(28, fm.fpioa.UART2_RX, force=True)
    SYSTEM_AT_UART = UART(UART.UART2, 115200, timeout=5000, read_buf_len=40960)
    startTime = time.ticks_ms()
    endTime = 0
    while SYSTEM_AT_UART.any():
        endTime = time.ticks_ms()
        if((endTime-startTime) >= 500):
            break
        print(SYSTEM_AT_UART.readline())
    SYSTEM_AT_UART.write('AT+GMR' + '\r\n')
    SYSTEM_ESP_VERSION = ""
    SYSTEM_ESP_DEVICE_ID = ""
    myLine = ''
    ifdata = True
    while not "OK" in myLine:
        while not SYSTEM_AT_UART.any():
            endTime = time.ticks_ms()
            # print(end-start)
            if((endTime-startTime) >= 2000):
                ifdata = False
                break
        if(ifdata):
            myLine = SYSTEM_AT_UART.readline()
            print(myLine)
            if "Bin version" in myLine:
                SYSTEM_ESP_VERSION = myLine
                SYSTEM_ESP_VERSION = SYSTEM_ESP_VERSION.decode()
                SYSTEM_ESP_VERSION = SYSTEM_ESP_VERSION[SYSTEM_ESP_VERSION.find(':')+1:]
                SYSTEM_ESP_VERSION = SYSTEM_ESP_VERSION.rstrip()
                # break
            if "deviceID" in myLine:
                SYSTEM_ESP_DEVICE_ID = myLine
                SYSTEM_ESP_DEVICE_ID = SYSTEM_ESP_DEVICE_ID.decode()
                SYSTEM_ESP_DEVICE_ID = SYSTEM_ESP_DEVICE_ID[SYSTEM_ESP_DEVICE_ID.find(':')+1:]
                SYSTEM_ESP_DEVICE_ID = SYSTEM_ESP_DEVICE_ID.rstrip()
                break
        else:
            print("timeout")
            break
    print("K210_VERSION:"+SYSTEM_K210_VERSION[5])
    print("ESP_VERSION:"+SYSTEM_ESP_VERSION)
    print("ESP_DEVICE_ID:"+SYSTEM_ESP_DEVICE_ID)

    # SYSTEM_AT_UART.deinit()
    # SYSTEM_AT_UART=None
    # fm.unregister(27)
    # fm.unregister(28)
    # del SYSTEM_AT_UART

    del myLine, startTime, ifdata, endTime

    SYSTEM_DEFAULT_PATH = os.getcwd()
    if "flash" in SYSTEM_DEFAULT_PATH:
        print("cwd:flash")
        SYSTEM_DEFAULT_PATH = "flash"
    else:
        print("cwd:sd")
        SYSTEM_DEFAULT_PATH = "sd"
    gc.collect()
    # from board import board_info

    # def MQTT_CALLBACK(uartObj):
    #     if SYSTEM_MQTT_CALLBACK_FLAG==True:
    #         SYSTEM_LOG_UART.stop()
    #         # from webai_api import downloadModel,takeMobileNetPic
    #         SUBSCRIBE_MSG = None
    #         global SYSTEM_WiFiCheckCount,SYSTEM_MQTT_TOPIC
    #         try:
    #             while SYSTEM_LOG_UART.any():
    #                 myLine = SYSTEM_LOG_UART.readline()
    #                 # print(myLine)
    #                 SUBSCRIBE_MSG = myLine.decode().strip()
    #                 if "mqtt" in SUBSCRIBE_MSG[0:4]:
    #                     SUBSCRIBE_MSG = SUBSCRIBE_MSG.split(',', 2)
    #             if SUBSCRIBE_MSG != None and len(SUBSCRIBE_MSG) == 3:
    #                 if SUBSCRIBE_MSG[1] == SYSTEM_ESP_DEVICE_ID+"/PING":
    #                     resetFlag=True
    #                     if SUBSCRIBE_MSG[2].find("_DEPLOY/") == 0:
    #                         pass
    #                         # Mqtt.push("6e559b/PONG","OK")
                            
    #                         # print("DOWNLOAD")
    #                         # downloadModel('mqtt.main.py', 'yolo', SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:], True)
    #                         # print("reset")
    #                         #time.sleep(1)
    #                     elif SUBSCRIBE_MSG[2].find("_RESET") == 0:
    #                         # Mqtt.push("6e559b/PONG","OK")
    #                         Mqtt.pushID("PONG", "OK")
    #                         print("reset")
    #                         import machine
    #                         machine.reset()
    #                     elif SUBSCRIBE_MSG[2].find("_TAKEPIC_YOLO/") == 0:
    #                         # Mqtt.push("6e559b/PONG","OK")
    #                         Mqtt.pushID("PONG", "OK")
    #                         print("_TAKEPIC_YOLO")
    #                         resetFlag=False
    #                     elif SUBSCRIBE_MSG[2].find("_TAKEPIC_MOBILENET/") == 0:
    #                         pass
    #                         # Mqtt.push("6e559b/PONG","OK")
    #                         # Mqtt.pushID("PONG", "OK")
    #                         # mqttJsonData = ujson.loads(
    #                         #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
    #                         # takeMobileNetPic(mqttJsonData['dsname'], mqttJsonData['count'], 1, mqttJsonData['url'], mqttJsonData['hashKey'])
    #                         # with open('/flash/cmd.txt','w') as f:
    #                         #     f.write(SUBSCRIBE_MSG[2])
    #                         # os.sync()
    #                         # import machine
    #                         # machine.reset()
    #                     elif SUBSCRIBE_MSG[2].find("_DOWNLOAD_MODEL/") == 0:
    #                         pass
    #                         # Mqtt.push("6e559b/PONG","OK")
    #                         # Mqtt.pushID("PONG", "OK")
    #                         # mqttJsonData = ujson.loads(
    #                         #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
    #                         # downloadModel(mqttJsonData['fileName'], mqttJsonData['modelType'], mqttJsonData['url'])
                            
    #                     elif SUBSCRIBE_MSG[2].find("_DOWNLOAD_FILE/") == 0:
    #                         pass
    #                         # Mqtt.push("6e559b/PONG","OK")
    #                         # Mqtt.pushID("PONG", "OK")
    #                         # mqttJsonData = ujson.loads(
    #                         #     SUBSCRIBE_MSG[2][SUBSCRIBE_MSG[2].find("/")+1:])
    #                         # downloadModel(mqttJsonData['fileName'], 'yolo', mqttJsonData['url'], True)
    #                         # print("reset")
    #                         #time.sleep(1)
    #                         # import machine
    #                         # os.sync()
    #                         # machine.reset()
    #                     else:
    #                         resetFlag=False
    #                         print("error command")
    #                     if resetFlag:
    #                         Mqtt.pushID("PONG", "OK")
    #                         print("write cmd.txt")
    #                         with open('/flash/cmd.txt','w') as f:
    #                             f.write(SUBSCRIBE_MSG[2])
    #                         os.sync()
    #                         print("reset")
    #                         import machine
    #                         machine.reset()
    #                     SYSTEM_WiFiCheckCount = -1
    #                     print("blockly:",SYSTEM_WiFiCheckCount)
    #                 elif SYSTEM_THREAD_MQTT_FLAG == True:
    #                     if SYSTEM_MQTT_TOPIC.get(SUBSCRIBE_MSG[1]) != None:
    #                         print("user topic:",SUBSCRIBE_MSG[2])
    #                         SYSTEM_MQTT_TOPIC[SUBSCRIBE_MSG[1]] = SUBSCRIBE_MSG[2]
    #                     else:
    #                         print("error topic")
    #         except Exception as e:
    #             print(e)
    #             print("MQTT_CALLBACK read error")
    #         SYSTEM_LOG_UART.start()

    #         while SYSTEM_LOG_UART.any():
    #             SYSTEM_LOG_UART.readline()
    # from webai_api import function
    SYSTEM_MQTT_CALLBACK_FLAG = True
    SYSTEM_THREAD_MQTT_FLAG = False
    SYSTEM_THREAD_MQTT_MSG = {}
    SYSTEM_MQTT_TOPIC = {}
    fm.register(18, fm.fpioa.UART3_RX, force=True)
    SYSTEM_LOG_UART = UART(UART.UART3, 115200, timeout=5000,read_buf_len=10240, callback=MQTT_CALLBACK)
    try:
        print("init SYSTEM_LOG_UART")
        while SYSTEM_LOG_UART.any():
            SYSTEM_LOG_UART.readline()
        print("init SYSTEM_LOG_UART end")
    except Exception as e:
        print(e)
        print("SYSTEM_LOG_UART error")


def saveMsg(timer):
# def saveMsg(cmd):
    global SYSTEM_THREAD_START_LIST
    while 1:
        if SYSTEM_SAVE_MSG_FLAG:
            # print("stop thread")

            # for i in range(0,len(SYSTEM_THREAD_START_LIST)):
            #     SYSTEM_THREAD_START_LIST[i]=0
            # bak = time.ticks()
            # print("check stop thread list",SYSTEM_THREAD_START_LIST)
            # while 1:
            #     if 1 in SYSTEM_THREAD_STOP_LIST:
            #         # print(SYSTEM_THREAD_STOP_LIST)
            #         print("wait stop",SYSTEM_THREAD_STOP_LIST)
            #         time.sleep(0.25)
            #     else:
            #         print("stop all thread")
            #         break
            # print('total time ', time.ticks() - bak)

            # print("sleep 2")
            # time.sleep(2)
            print("lock thread")
            while not SYSTEM_ALLOCATE_LOCK.acquire():
                time.sleep(0.05)
            print("sleep 1")
            time.sleep(1)
            print("write1 cmd.txt")
            # with open('/flash/cmd.txt','w') as f:
            #     print("write2 cmd.txt")
            #     f.write(webai_blockly.SYSTEM_TEST_MSG)
            #     print("write3 cmd.txt")
            # print("write4 cmd.txt")
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
                if "mqttDisconnect" in myLine:
                    SYSTEM_MQTT_CONNECT=False
                if "subscribed" in myLine:
                    SYSTEM_MQTT_CONNECT=True
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
        self.img = self.image.Image()
        print('Lcd_Blockly __init__')

    def __del__(self):
        del self
        print('Lcd_Blockly __del__')

    def clear(self):
        lcd.clear()
        self.img.clear()

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
            self.img = self.image.Image(self.path)
            lcd.display(self.img)
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
        self.img.draw_circle(x, y, radius, color, thickness, fill)
        lcd.display(self.img)

    def drawLine(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        self.img.draw_line(x0, y0, x1, y1, color, thickness)
        lcd.display(self.img)

    def drawRectangle(self, x, y, w, h, color=0xffffff, thickness=1, fill=False):
        self.img.draw_rectangle(x, y, w, h, color, thickness, fill)
        lcd.display(self.img)

    def drawArrow(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        self.img.draw_arrow(x0, y0, x1, y1, color, thickness)
        lcd.display(self.img)

    def drawCross(self, x, y, color=0xffffff, size=5, thickness=1):
        self.img.draw_cross(x, y, color, size, thickness)
        lcd.display(self.img)

    def drawString(self, x, y, text, color=(255,255,255), scale=2, x_spacing=20, mono_space=False):
        self.image.font_load(self.image.UTF8, 16, 16, 0x280000)
        self.img.draw_string(x, y, text, scale=scale, color=color, x_spacing=x_spacing, mono_space=mono_space)
        self.image.font_free()
        lcd.display(self.img)
            
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
            self.sensor.set_vflip(flip)
            self.sensor.set_auto_gain(auto_gain)
            self.sensor.set_auto_whitebal(auto_whitebal)
            self.sensor.set_auto_exposure(auto_exposure)
            self.sensor.set_brightness(brightness)
            print('Camera_Blockly __init__')
            showMessage("init camera OK")
        except Exception as e:
            print(e)
            showMessage("init camera ERROR")

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

    def start(self, folder="sd", fileName="recorder", record_time=5):
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


class Speaker:
    def __init__(self):
        from Maix import I2S
        from fpioa_manager import fm
        import audio
        fm.register(board_info.SPK_I2S_OUT, fm.fpioa.I2S2_OUT_D1, force=True)
        fm.register(board_info.SPK_I2S_WS, fm.fpioa.I2S2_WS, force=True)
        fm.register(board_info.SPK_I2S_SCLK, fm.fpioa.I2S2_SCLK, force=True)
        self.wav_dev = I2S(I2S.DEVICE_2)
        self.wav_dev.channel_config(self.wav_dev.CHANNEL_1, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT,cycles=I2S.SCLK_CYCLES_32, align_mode=I2S.RIGHT_JUSTIFYING_MODE)
        self.audio = audio
        self.volume = 5
        print("SPEAKER __init__")

    def __del__(self):
        del self
        print("SPEAKER __del__")

    def setVolume(self, volume):
        self.volume = volume

    def start(self, folder="sd", fileName=None, sample_rate=48000):
        if(fileName != None):
            cwd = SYSTEM_DEFAULT_PATH
            if cwd == "flash":
                folder = "flash"
            else:
                folder = "sd"
            self.wav_dev.set_sample_rate(sample_rate)
            player = self.audio.Audio(path="/"+folder+"/"+fileName+".wav")
            player.volume(self.volume)
            # read audio info
            #wav_info = player.play_process(wav_dev)
            #print("wav file head information: ", wav_info)
            player.play_process(self.wav_dev)
            print("start play")
            #commCycle("AT+SPEAKER=1")
            commCycle("AT+SPEAKER=1")

            while True:
               ret = player.play()
               if ret == None:
                   print("format error")
                   break
               elif ret == 0:
                   print("end")
                   break

            #commCycle("AT+SPEAKER=0")
            commCycle("AT+SPEAKER=0")
            player.finish()
            #print(time.time())
            print("play finish")
        else:
            print("fileName error")



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
                model=0x780000
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
                model=0x950000
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