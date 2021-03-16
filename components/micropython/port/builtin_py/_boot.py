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
    import webai_blockly
    from board import board_info
    import time,network,ujson,lcd
    from machine import Timer
    # from Maix import GPIO
    from fpioa_manager import fm
    from webai_blockly import showMessage
    print(globals())
    # webai_blockly.SYSTEM_WiFiCheckCount=7
    def timerCount(timer):
        if webai_blockly.SYSTEM_WiFiCheckCount<0:
            timer.stop()
        showMessage("play after "+str(webai_blockly.SYSTEM_WiFiCheckCount)+" seconds",x=-1,y=6,center=False,clear=False)
        webai_blockly.SYSTEM_WiFiCheckCount-=1
        print("timer:",webai_blockly.SYSTEM_WiFiCheckCount)
    tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=1, unit=Timer.UNIT_S, callback=timerCount, arg=timerCount, start=False, priority=1, div=0)
    # pinA=7#A
    # fm.fpioa.set_function(pinA,fm.fpioa.GPIO7)
    # webai_blockly.SYSTEM_BTN_L=GPIO(GPIO.GPIO7,GPIO.IN)
    # pinB=16#B
    # fm.fpioa.set_function(pinB,fm.fpioa.GPIO6)
    # webai_blockly.SYSTEM_BTN_R=GPIO(GPIO.GPIO6,GPIO.IN)
    lcd.init()
    lcd.clear()
    K210_VERSION=os.uname()
    showMessage("k210 ver:"+K210_VERSION[5]+" (lite)",x=-1,y=5,center=False,clear=False)
    del K210_VERSION
    showMessage("deviceID:"+webai_blockly.SYSTEM_ESP_DEVICE_ID,x=-1,y=1,center=False,clear=False)
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
    webai_blockly.SYSTEM_WLAN = network.ESP8285(webai_blockly.SYSTEM_AT_UART)
    # webai_blockly.SYSTEM_WiFiInfo=["","","",WIFI_SSID,"","",""]
    # webai_blockly.SYSTEM_WiFiInfo=webai_blockly.SYSTEM_WLAN.ifconfig()
    # print(webai_blockly.SYSTEM_WiFiInfo)
    # time.sleep(0.5)
    if setWiFiFlag:
        webai_blockly.SYSTEM_WiFiInfo=webai_blockly.SYSTEM_WLAN.ifconfig()
        # time.sleep(0.5)
        if webai_blockly.SYSTEM_WiFiInfo[0]=="0.0.0.0" or webai_blockly.SYSTEM_WiFiInfo[3]!=WIFI_SSID:
            while 1:
                try:
                    print("connect")
                    webai_blockly.SYSTEM_WLAN.connect(WIFI_SSID, WIFI_PASW, False)
                    # time.sleep(0.5)
                    print("info")
                    webai_blockly.SYSTEM_WiFiInfo=webai_blockly.SYSTEM_WLAN.ifconfig()
                    print(webai_blockly.SYSTEM_WiFiInfo)
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

    # print(webai_blockly.SYSTEM_WiFiInfo)
    if wifiStatus=="OK":
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:OK ("+webai_blockly.SYSTEM_WiFiInfo[6]+" dBm)",x=-1,y=4,center=False,clear=False)
    else:
        showMessage(" "*40,x=-1,y=4,center=False,clear=False)
        showMessage("WiFi status:not OK!!!",x=-1,y=4,center=False,clear=False)
    del wifiStatus
    gc.collect()
    tim.start()
    qrcodeMode=False
    msg="press L Play                press R Scan"
    lcd.draw_string(0,224,msg,lcd.RED,lcd.BLACK)
    del msg
    while 1:
        if webai_blockly.SYSTEM_WiFiCheckCount<0:
            break
        if webai_blockly.SYSTEM_BTN_L.value()==0:
            break
        if webai_blockly.SYSTEM_WiFiCheckCount>0 and webai_blockly.SYSTEM_BTN_R.value()==0 :
            qrcodeMode=True
            break
    tim.stop()
    tim.deinit()
    del tim
    # del webai_blockly.SYSTEM_WiFiCheckCount
    lcd.clear()
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
                        from webai_api import setWiFi
                        setWiFi(qrcodeData['ssid'],qrcodeData['password'])
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
            if webai_blockly.SYSTEM_BTN_L.value()==0:
                qrcodeMode=False
                break
        del img,res,qrcodeData

    showMessage("",clear=True)
    # del pinA,pinB,webai_blockly.SYSTEM_BTN_L,webai_blockly.SYSTEM_BTN_R,qrcodeMode
    del qrcodeMode,timerCount,ujson,Timer,network
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
except Exception as e:
    print(e)
    if 'tim' in locals():
        tim.stop()
        tim.deinit()
        del tim
finally:
    lcd.clear()
    gc.collect()
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
from webai_blockly import Blockly_Init
Blockly_Init()
print("_boot init end")
# for i in range(200):
#     time.sleep_ms(1) # wait for key interrupt(for webAI tool)
# del i