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

# boot_py = '''

# '''
# SYSTEM_K210_VERSION=os.uname()
# from machine import UART
# from fpioa_manager import fm
# fm.register(27, fm.fpioa.UART2_TX, force=True)
# fm.register(28, fm.fpioa.UART2_RX, force=True)
# SYSTEM_AT_UART = UART(UART.UART2, 115200*1,timeout=1000, read_buf_len=4096)
# SYSTEM_AT_UART.write('AT+GMR' + '\r\n')
# myLine = ''
# SYSTEM_ESP_VERSION=""
# startTime=time.ticks_ms()
# ifdata=True
# while  not  "OK" in myLine:
#     while not SYSTEM_AT_UART.any():
#         endTime=time.ticks_ms()
#         # print(end-start)
#         if((endTime-startTime)>=5000):
#             ifdata=False
#             break
#     if(ifdata):
#         myLine = SYSTEM_AT_UART.readline()
#         # print(myLine)
#         if "Bin version" in myLine:
#             SYSTEM_ESP_VERSION=myLine
#             SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION.decode()
#             SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION[SYSTEM_ESP_VERSION.find(':')+1:]
#             SYSTEM_ESP_VERSION=SYSTEM_ESP_VERSION.rstrip()
#             break
#     else:
#         print("timeout")
#         break

# # while  not  "OK" in myLine:
# #     while not SYSTEM_AT_UART.any():
# #         pass
# #     myLine = SYSTEM_AT_UART.readline()
# #     if "Bin version" in myLine:
# #         SYSTEM_ESP_VERSION=myLine
# print("webAI:"+SYSTEM_K210_VERSION[5])
# print("esp8285:"+SYSTEM_ESP_VERSION)
# # del SYSTEM_K210_VERSION,SYSTEM_AT_UART,myLine,SYSTEM_ESP_VERSION,startTime,ifdata,endTime
# # version = {
# #   "versionK210": SYSTEM_K210_VERSION[5],
# #   "SYSTEM_ESP_VERSION": 
# # }
# # del SYSTEM_K210_VERSION,version




boot_py = '''
try:
    from machine import UART
    from fpioa_manager import fm
    from Maix import GPIO
    import gc,time

    fm.register(27, fm.fpioa.UART2_TX, force=True)
    fm.register(28, fm.fpioa.UART2_RX, force=True)
    SYSTEM_AT_UART = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)

    pin8285=20
    fm.register(pin8285, fm.fpioa.GPIO0)
    reset=GPIO(GPIO.GPIO0,GPIO.OUT)
    reset.value(0)
    time.sleep(0.2)
    reset.value(1)
    fm.unregister(pin8285)
    bak = time.ticks()
    myLine = ''
    while  not  "ready" in myLine:
        while not SYSTEM_AT_UART.any():
            pass
        myLine = SYSTEM_AT_UART.readline()
        print(myLine)
        
    # myLine = ''
    # while  not  "WIFI GOT IP" in myLine:
    #     while not SYSTEM_AT_UART.any():
    #         pass
    #     myLine = SYSTEM_AT_UART.readline()
    #     #print(myLine)

    # SYSTEM_AT_UART.write('AT+CIPSTA?\\r\\n'.format(enter="\\r\\n"))
    # myLine = ''
    # while  not  "OK" in myLine:
        # while not SYSTEM_AT_UART.any():
            # pass
        # myLine = SYSTEM_AT_UART.readline()
        # print(myLine)
    # time.sleep(1)
    # commCycle("AT+CIPSTA?")
    # print('total time ', (time.ticks() - bak) / 1000, ' s')

finally:
    gc.collect()
'''

boot_py = '''
try:
    print(globals())
    from board import board_info
    import time,network,ujson,lcd
    from machine import Timer
    from Maix import GPIO
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
    pinA=7#A
    fm.fpioa.set_function(pinA,fm.fpioa.GPIO7)
    gpioA=GPIO(GPIO.GPIO7,GPIO.IN)
    pinB=16#B
    fm.fpioa.set_function(pinB,fm.fpioa.GPIO6)
    gpioB=GPIO(GPIO.GPIO6,GPIO.IN)
    lcd.clear()
    K210_VERSION=os.uname()
    showMessage("k210 ver:"+K210_VERSION[5],x=-1,y=5,center=False,clear=False)
    del K210_VERSION
    showMessage("deviceID:"+SYSTEM_ESP_DEVICE_ID,x=-1,y=1,center=False,clear=False)
    showMessage("WiFi checking...",x=-1,y=4,center=False,clear=False)
    WIFI_SSID = "webduino.io"
    WIFI_PASW = "webduino"
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
    time.sleep(1)
    err = 0
    wifiStatus=""
    SYSTEM_WLAN = network.ESP8285(SYSTEM_AT_UART)
    #SYSTEM_WiFiInfo=["","","",WIFI_SSID,"","",""]
    SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
    print(SYSTEM_WiFiInfo)

    if setWiFiFlag:
        #SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
        if SYSTEM_WiFiInfo[0]=="0.0.0.0" or SYSTEM_WiFiInfo[3]!=WIFI_SSID:
            while 1:
                try:
                    SYSTEM_WLAN.connect(WIFI_SSID, WIFI_PASW)
                    SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
                    wifiStatus="OK"
                except Exception:
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

    print(SYSTEM_WiFiInfo)
    if wifiStatus=="OK":
        #SYSTEM_WiFiInfo=SYSTEM_WLAN.ifconfig()
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:OK ("+SYSTEM_WiFiInfo[6]+" dBm)",x=-1,y=4,center=False,clear=False)
    else:
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:not OK!!!",x=-1,y=4,center=False,clear=False)
    del wifiStatus,SYSTEM_WLAN
    gc.collect()
    tim.start()
    qrcodeMode=False
    #time.sleep(1)

    msg="press L Play                press R Scan"
    lcd.draw_string(0,224,msg,lcd.RED,lcd.BLACK)
    del msg
    while 1:
        if wifiCheckCount<0:
            break
        if gpioA.value()==0:
            break
        if gpioB.value()==0:
            qrcodeMode=True
            break
    del wifiCheckCount
    lcd.clear()
    tim.stop()
    tim.deinit()
    del tim
    #with open('/flash/wifi.json','w') as f:
        ##ujson.dump(, f)
        #obj = '{"ssid":"%s","pwd":"%s"}'%("webduino.io","webduino")
        ## jsDumps = ujson.dumps(obj)
        ## print(jsDumps)
        #f.write(obj)
        ##f.flush()
    #time.sleep(2)
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
        #sensor.set_vflip(1)
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
                        #with open('/flash/wifi.json','w') as f:
                            ##ujson.dump(, f)
                            #obj = '{"ssid":"%s","pwd":"%s"}'%(qrcodeData['ssid'],qrcodeData['password'])
                            ## jsDumps = ujson.dumps(obj)
                            ## print(jsDumps)
                            #f.write(obj)
                            ##f.flush()
                        #time.sleep(2)
                        showMessage("setting WiFi...",clear=True)
                        function.setWiFi(qrcodeData['ssid'],qrcodeData['password'])
                    elif qrcodeData['function']=="tackMobileNetPic":
                        showMessage("tack picture mode",clear=True)
                        function.tackMobileNetPic(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,gpioA,gpioB,qrcodeData['dsname'],qrcodeData['count'],False,qrcodeData['url'],qrcodeData['hashKey'])
                    elif qrcodeData['function']=="downloadModel":
                        showMessage("download model mode",clear=True)
                        function.downloadModel(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,gpioA,gpioB,qrcodeData['fileName'],qrcodeData['modelType'],qrcodeData['url'])
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
            if gpioA.value()==0:
                qrcodeMode=False
                break
        del img,res,qrcodeData

    showMessage("",clear=True)
    del pinA,pinB,gpioA,gpioB,qrcodeMode
    del timerCount,ujson,function,Timer,network
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
    #print(globals())
    sys.exit()
except Exception as e:
    print(e)
    if tim==None:
        tim.stop()
        tim.deinit()
        del tim
    gc.collect()
    #print(globals())
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
fm.register(27, fm.fpioa.UART2_TX, force=True)
fm.register(28, fm.fpioa.UART2_RX, force=True)
SYSTEM_AT_UART = UART(UART.UART2, 115200,timeout=5000, read_buf_len=40960)
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

# while  not  "OK" in myLine:
#     while not SYSTEM_AT_UART.any():
#         pass
#     myLine = SYSTEM_AT_UART.readline()
#     if "Bin version" in myLine:
#         SYSTEM_ESP_VERSION=myLine
print("K210_VERSION:"+SYSTEM_K210_VERSION[5])
print("ESP_VERSION:"+SYSTEM_ESP_VERSION)
print("ESP_DEVICE_ID:"+SYSTEM_ESP_DEVICE_ID)

# SYSTEM_AT_UART.deinit()
# SYSTEM_AT_UART=None
# fm.unregister(27)
# fm.unregister(28)
# del SYSTEM_AT_UART

del myLine,startTime,ifdata,endTime
# version = {
#   "versionK210": SYSTEM_K210_VERSION[5],
#   "SYSTEM_ESP_VERSION": 
# }
# del SYSTEM_K210_VERSION,version

SYSTEM_DEFAULT_PATH=os.getcwd()
if "flash" in SYSTEM_DEFAULT_PATH:
    print("cwd:flash")
    SYSTEM_DEFAULT_PATH="flash"
else:
    print("cwd:sd")
    SYSTEM_DEFAULT_PATH="sd"

#global val
#SYSTEM_ESP_DEVICE_ID
#SYSTEM_DEFAULT_PATH
gc.collect()
# from board import board_info
print("_boot init end")
for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for webAI tool)
del i