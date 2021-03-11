import os, sys, time,gc
sys.path.append('')
sys.path.append('.')

# chdir to "/sd" or "/flash"
devices = os.listdir("/")
if "sd" in devices:
    os.chdir("/sd")
    sys.path.append('/sd')
else:
    os.chdir("/flash")
sys.path.append('/flash')
del devices
print("[MaixPy] init end") # for IDE
for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for maixpy ide)
del i

# check IDE mode
ide_mode_conf = "/flash/ide_mode.conf"
ide = True
# ide = False

try:
    f = open(ide_mode_conf)
    f.close()
    del f
except Exception:
    ide = False

if ide:
    os.remove(ide_mode_conf)
    from machine import UART
    import lcd
    lcd.init(color=lcd.PINK)
    repl = UART.repl_uart()
    repl.init(1500000, 8, None, 1, read_buf_len=2048, ide=True, from_ide=False)
    sys.exit()
del ide, ide_mode_conf

boot_py = '''
try:
    print(globals())
    from board import board_info
    import time,network,ujson,lcd
    from machine import Timer
    # from Maix import GPIO
    from fpioa_manager import fm
    from board_sensor import showMessage
    print(globals())
    wifiCheckCount=7
    def timerCount(timer):
        global wifiCheckCount
        showMessage("play after "+str(wifiCheckCount)+" seconds",x=-1,y=6,center=False,clear=False)
        wifiCheckCount-=1
        print(wifiCheckCount)
    tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=1, unit=Timer.UNIT_S, callback=timerCount, arg=timerCount, start=False, priority=1, div=0)
    # pinA=7#A
    # fm.fpioa.set_function(pinA,fm.fpioa.GPIO7)
    # SYSTEM_BTN_L=GPIO(GPIO.GPIO7,GPIO.IN)
    # pinB=16#B
    # fm.fpioa.set_function(pinB,fm.fpioa.GPIO6)
    # SYSTEM_BTN_R=GPIO(GPIO.GPIO6,GPIO.IN)
    lcd.init()
    lcd.clear()
    K210_VERSION=os.uname()
    showMessage("k210 ver:"+K210_VERSION[5],x=-1,y=5,center=False,clear=False)
    del K210_VERSION
    showMessage("deviceID:"+SYSTEM_ESP_DEVICE_ID,x=-1,y=1,center=False,clear=False)
    showMessage("WiFi checking...",x=-1,y=4,center=False,clear=False)
    WIFI_SSID = ""
    WIFI_PASW = ""
    setWiFiFlag=False
    try:
        with open('/flash/wifi.json','r') as f:
            jsDumps = ujson.load(f)
            print(jsDumps)
            WIFI_SSID=jsDumps['ssid']
            WIFI_PASW=jsDumps['pwd']
            setWiFiFlag=True
            del jsDumps
        del f
    except Exception as e:
        print(e)
        print("not setting wifi")

    showMessage("ssid: "+WIFI_SSID,x=-1,y=2.5,center=False,clear=False)
    # time.sleep(1)
    err = 0
    wifiStatus=""
    SYSTEM_WLAN = network.ESP8285(SYSTEM_AT_UART)
    # SYSTEM_WiFiInfo=["","","",WIFI_SSID,"","",""]
    # SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
    # print(SYSTEM_WiFiInfo)
    # time.sleep(0.5)
    if setWiFiFlag:
        SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
        # time.sleep(0.5)
        if SYSTEM_WiFiInfo[0]=="0.0.0.0" or SYSTEM_WiFiInfo[3]!=WIFI_SSID:
            while 1:
                try:
                    print("connect")
                    SYSTEM_WLAN.connect(WIFI_SSID, WIFI_PASW, False)
                    # time.sleep(0.5)
                    print("info")
                    SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
                    print(SYSTEM_WiFiInfo)
                    wifiStatus="OK"
                    print("end")
                except Exception as e:
                    print(e)
                    err += 1
                    print("Connect AP failed, now try again")
                    wifiStatus="ERROR"
                    if err > 1:
                        print("Conenct AP fail")
                        break
                    continue
                break
        else:
            wifiStatus="OK"
    del err,WIFI_SSID,WIFI_PASW,setWiFiFlag

    # print(SYSTEM_WiFiInfo)
    if wifiStatus=="OK":
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:OK ("+SYSTEM_WiFiInfo[6]+" dBm)",x=-1,y=4,center=False,clear=False)
    else:
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:not OK!!!",x=-1,y=4,center=False,clear=False)
    del wifiStatus,SYSTEM_WLAN
    gc.collect()
    tim.start()
    qrcodeMode=False
    msg="press L Play                press R Scan"
    lcd.draw_string(0,224,msg,lcd.RED,lcd.BLACK)
    del msg
    while 1:
        if wifiCheckCount<0:
            break
        if SYSTEM_BTN_L.value()==0:
            break
        if SYSTEM_BTN_R.value()==0:
            qrcodeMode=True
            break
    del wifiCheckCount
    lcd.clear()
    tim.stop()
    tim.deinit()
    del tim
    from qrcode_exec import function
    while qrcodeMode:
        import sensor
        import image
        import lcd
        lcd.init()
        showMessage("init qrcode mode",clear=True)
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.run(1)
        sensor.skip_frames(30)
        while True:
            #clock.tick()
            img = sensor.snapshot()
            res = img.find_qrcodes()
            #fps =clock.fps()
            if len(res) > 0:
                #img.draw_string(2,2, res[0].payload(), color=(0,128,0), scale=2)
                #print(res)
                #print(res[0].payload())
                try:
                    qrcodeData=ujson.loads(res[0].payload())
                    print(qrcodeData)
                    #print(type(data['count']),data['count'])
                    if qrcodeData['function']=="wifi":
                        showMessage("setting WiFi...",clear=True)
                        function.setWiFi(qrcodeData['ssid'],qrcodeData['password'])
                    elif qrcodeData['function']=="tackMobileNetPic":
                        showMessage("tack picture mode",clear=True)
                        function.tackMobileNetPic(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,SYSTEM_BTN_L,SYSTEM_BTN_R,qrcodeData['dsname'],qrcodeData['count'],False,qrcodeData['url'],qrcodeData['hashKey'])
                    elif qrcodeData['function']=="downloadModel":
                        showMessage("download model mode",clear=True)
                        function.downloadModel(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,SYSTEM_BTN_L,SYSTEM_BTN_R,qrcodeData['fileName'],qrcodeData['modelType'],qrcodeData['url'])
                #except KeyboardInterrupt as e:
                    #lcd.clear()
                    #print(e)
                    #print("KeyboardInterrupt exit")
                    #sys.exit()
                except Exception as e:
                    print(e)
                    print("format error")

                #print(res[0].corners())
                #print(res[0].rect())

            lcd.display(img)
            if SYSTEM_BTN_L.value()==0:
                qrcodeMode=False
                break
        del img,res,qrcodeData

    showMessage("",clear=True)
    # del pinA,pinB,SYSTEM_BTN_L,SYSTEM_BTN_R,qrcodeMode
    del qrcodeMode,timerCount,ujson,function,Timer,network
    print("end")
    print(globals())
    gc.collect()
    print(globals())
except KeyboardInterrupt as e:
    print(e)
    print("KeyboardInterrupt exit")
    if 'tim' in locals():
        tim.stop()
        tim.deinit()
        del tim
    gc.collect()
    sys.exit()
except Exception as e:
    print(e)
    if tim==None:
        tim.stop()
        tim.deinit()
        del tim
    gc.collect()
    sys.exit()
'''

# boot_py = '''
# '''

# detect boot.py
main_py = '''
try:
    import gc, lcd, image, sys
    gc.collect()
    lcd.init()
    lcd.draw_string(0,0,'test',lcd.WHITE,lcd.BLACK)
    loading = image.Image(size=(lcd.width(), lcd.height()))
    # loading.draw_rectangle((0, 0, lcd.width(), lcd.height()), fill=True, color=(255, 0, 0))
    info = "Webduino WebAI"
    loading.draw_string(int(lcd.width()//2 - len(info) * 5), (lcd.height())//2, info, color=(255, 255, 255), scale=2, mono_space=0)
    # v = sys.implementation.version
    # vers = 'V{}.{}.{} : webduino.io'.format(v[0],v[1],v[2])
    # loading.draw_string(int(lcd.width()//2 - len(info) * 6), (lcd.height())//3 + 20, vers, color=(255, 255, 255), scale=1, mono_space=1)
    lcd.display(loading)
    # del loading, v, info, vers
    del loading,info
    gc.collect()
finally:
    gc.collect()
'''

# main_py = '''
# try:
#     import lcd,gc
#     lcd.init()
#     lcd.draw_string(0,100,'  webAI:'+'{SYSTEM_K210_VERSION}',lcd.WHITE,lcd.BLACK)
#     lcd.draw_string(0,200,'esp8285:'+'{SYSTEM_ESP_VERSION}',lcd.WHITE,lcd.BLACK)
#     gc.collect()
# finally:
#     gc.collect()
# '''.format(SYSTEM_K210_VERSION=SYSTEM_K210_VERSION[5],SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION)

flash_ls = os.listdir()
# f = open("boot.py", "wb")
# f.write(boot_py)
# f.close()
# del f
if not "boot.py" in flash_ls:
    f = open("boot.py", "wb")
    f.write(boot_py)
    f.close()
    del f
del boot_py
# f = open("main.py", "wb")
# f.write(main_py)
# f.close()
if not "main.py" in flash_ls:
    f = open("main.py", "wb")
    f.write(main_py)
    f.close()
    del f
del main_py

flash_ls = os.listdir("/flash")
try:
    sd_ls = os.listdir("/sd")
except Exception:
    sd_ls = []
if "cover.boot.py" in sd_ls:
    code0 = ""
    if "boot.py" in flash_ls:
        with open("/flash/boot.py") as f:
            code0 = f.read()
    with open("/sd/cover.boot.py") as f:
        code=f.read()
    if code0 != code:
        with open("/flash/boot.py", "w") as f:
            f.write(code)
        import machine
        machine.reset()

if "cover.main.py" in sd_ls:
    code0 = ""
    if "main.py" in flash_ls:
        with open("/flash/main.py") as f:
            code0 = f.read()
    with open("/sd/cover.main.py") as f:
        code = f.read()
    if code0 != code:
        with open("/flash/main.py", "w") as f:
            f.write(code)
        import machine
        machine.reset()

try:
    del flash_ls
    del sd_ls
    del code0
    del code
except Exception:
    pass

banner = '''
 __  __              _____  __   __  _____   __     __
|  \/  |     /\     |_   _| \ \ / / |  __ \  \ \   / /
| \  / |    /  \      | |    \ V /  | |__) |  \ \_/ /
| |\/| |   / /\ \     | |     > <   |  ___/    \   /
| |  | |  / ____ \   _| |_   / . \  | |         | |
|_|  |_| /_/    \_\ |_____| /_/ \_\ |_|         |_|

Official Site : https://www.sipeed.com
Wiki          : https://maixpy.sipeed.com

              _         _       _             
             | |       | |     (_)            
__      _____| |__   __| |_   _ _ _ __   ___  
\ \ /\ / / _ \ '_ \ / _` | | | | | '_ \ / _ \ 
 \ V  V /  __/ |_) | (_| | |_| | | | | | (_) |
  \_/\_/ \___|_.__/ \__,_|\__,_|_|_| |_|\___/ 
                                              
Official Site : https://webduino.io
'''
print(banner)
del banner
SYSTEM_K210_VERSION=os.uname()
from machine import UART
from fpioa_manager import fm
from Maix import GPIO
pinA=7#A
fm.fpioa.set_function(pinA,fm.fpioa.GPIO7)
SYSTEM_BTN_L=GPIO(GPIO.GPIO7,GPIO.IN)
pinB=16#B
fm.fpioa.set_function(pinB,fm.fpioa.GPIO6)
SYSTEM_BTN_R=GPIO(GPIO.GPIO6,GPIO.IN)
del pinA,pinB
fm.register(27, fm.fpioa.UART2_TX, force=True)
fm.register(28, fm.fpioa.UART2_RX, force=True)
SYSTEM_AT_UART = UART(UART.UART2, 115200,timeout=5000, read_buf_len=40960)
while SYSTEM_AT_UART.any():
    endTime=time.ticks_ms()
    if((endTime-startTime)>=500):
        break
    print(SYSTEM_AT_UART.readline())
SYSTEM_AT_UART.write('AT+GMR' + '\r\n')
SYSTEM_ESP_VERSION=""
SYSTEM_ESP_DEVICE_ID=""
startTime=time.ticks_ms()
myLine = ''
ifdata=True
while  not  "OK" in myLine:
    while not SYSTEM_AT_UART.any():
        endTime=time.ticks_ms()
        # print(end-start)
        if((endTime-startTime)>=2000):
            ifdata=False
            break
    if(ifdata):
        myLine = SYSTEM_AT_UART.readline()
        # print(myLine)
        if "Bin version" in myLine:
            SYSTEM_ESP_VERSION=myLine
            SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION.decode()
            SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION[SYSTEM_ESP_VERSION.find(':')+1:]
            SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION.rstrip()
            # break
        if "deviceID" in myLine:
            SYSTEM_ESP_DEVICE_ID=myLine
            SYSTEM_ESP_DEVICE_ID=SYSTEM_ESP_DEVICE_ID.decode()
            SYSTEM_ESP_DEVICE_ID=SYSTEM_ESP_DEVICE_ID[SYSTEM_ESP_DEVICE_ID.find(':')+1:]
            SYSTEM_ESP_DEVICE_ID=SYSTEM_ESP_DEVICE_ID.rstrip()
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

del myLine,startTime,ifdata,endTime

SYSTEM_DEFAULT_PATH=os.getcwd()
if "flash" in SYSTEM_DEFAULT_PATH:
    print("cwd:flash")
    SYSTEM_DEFAULT_PATH="flash"
else:
    print("cwd:sd")
    SYSTEM_DEFAULT_PATH="sd"
gc.collect()
# from board import board_info

def MQTT_CALLBACK(uartObj):
    SYSTEM_LOG_UART.stop()
    from qrcode_exec import function
    SUBSCRIBE_MSG=None
    try:
        while SYSTEM_LOG_UART.any():
            myLine = SYSTEM_LOG_UART.readline()
            # print(myLine)
            SUBSCRIBE_MSG=myLine.decode().strip()
            if "mqtt" in SUBSCRIBE_MSG[0:4]:
                SUBSCRIBE_MSG=SUBSCRIBE_MSG.split(',',2)

        if SUBSCRIBE_MSG!=None and len(SUBSCRIBE_MSG)==3:
            if SUBSCRIBE_MSG[1]==SYSTEM_ESP_DEVICE_ID+"/PING" and (len(SUBSCRIBE_MSG[2])>=6 and SUBSCRIBE_MSG[2][0:6]=="DEPLOY"):
                function.downloadModel(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,SYSTEM_BTN_L,SYSTEM_BTN_R,'main.py','yolo',SUBSCRIBE_MSG[2][7:],True)
                print("reset")
                #time.sleep(1)
                import machine
                machine.reset()
            if SYSTEM_THREAD_MQTT_FLAG==True:
                if SYSTEM_MQTT_TOPIC.get(SUBSCRIBE_MSG[1])!=None:
                    SYSTEM_MQTT_TOPIC[SUBSCRIBE_MSG[1]]=SUBSCRIBE_MSG[2]
                else:
                    print("error topic")

                # for i in SYSTEM_MQTT_TOPIC:
                #     if SUBSCRIBE_MSG[1]==i:
                #         SYSTEM_THREAD_MQTT_MSG[i]=SUBSCRIBE_MSG[2]
    except Exception as e:
        print(e)
        print("MQTT_CALLBACK read error")
    SYSTEM_LOG_UART.start()

    while SYSTEM_LOG_UART.any():
        SYSTEM_LOG_UART.readline()
# from qrcode_exec import function
SYSTEM_THREAD_MQTT_FLAG=False
SYSTEM_THREAD_MQTT_MSG={}
SYSTEM_MQTT_TOPIC={}
fm.register(18, fm.fpioa.UART3_RX, force=True)
SYSTEM_LOG_UART = UART(UART.UART3, 115200*1,timeout=1000, read_buf_len=4096,callback=MQTT_CALLBACK)
try:
    print("init SYSTEM_LOG_UART")
    while SYSTEM_LOG_UART.any():
        SYSTEM_LOG_UART.readline()
    print("init SYSTEM_LOG_UART end")
except Exception as e:
    print(e)
    print("SYSTEM_LOG_UART error")
print("_boot init end")
for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for webAI tool)
del i