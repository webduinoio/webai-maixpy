import os
import sys
import time
import gc
gc.enable()
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
print("[MaixPy] init end")  # for IDE
print("_boot init end")
# from machine import WDT
# def on_wdt(self):
#     print(self.context(), self)
#     self.feed()
# wdt1 = WDT(id=0, timeout=4000, callback=on_wdt, context={})
for i in range(200):
    time.sleep_ms(1)  # wait for key interrupt(for maixpy ide)
del i
from fpioa_manager import fm
from Maix import GPIO
import lcd
lcd.init()
fm.fpioa.set_function(7, fm.fpioa.GPIO7)
resetPin = GPIO(GPIO.GPIO7, GPIO.IN)
if resetPin.value()==0:
    lcd.clear(0x00F8)
    print("reset filesystem")
    f=None
    try:
        os.remove('/flash/boot.py')
    except Exception as e:
        print("reset boot.py error")
    try:
        os.remove('/flash/main.py')
    except Exception as e:
        print("reset main.py error")
    try:
        with open('/flash/cmd.txt','w') as f:
            f.write("")
    except Exception as e:
        print("reset cmd.txt error")
    try:
        with open('/flash/qrcode.cmd','w') as f:
            f.write("")
    except Exception as e:
        print("reset qrcode.cmd error")
    try:
        with open('/flash/wifi.json','w') as f:
            f.write('{"ssid":"%s","pwd":"%s"}'%("webduino.io","webduino"))
    except Exception as e:
        print("reset wifi.json error")
    del f
    lcd.clear(0xFFFF)
    import machine
    machine.reset()
fm.unregister(7)
del resetPin
gc.collect()

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
    # print("start boot.py,sleep 5")
    # time.sleep(5)
    from board import board_info
    import webai_blockly,os
    from webai_blockly import showMessage
    print(globals())

    import time,network,ujson,lcd
    from machine import Timer
    print(globals())
    def timerCount(timer):
        if webai_blockly.SYSTEM_WiFiCheckCount<0:
            timer.stop()
        showMessage("play after "+str(webai_blockly.SYSTEM_WiFiCheckCount)+" seconds",x=-1,y=6,center=False,clear=False)
        webai_blockly.SYSTEM_WiFiCheckCount-=1
        print("timer:",webai_blockly.SYSTEM_WiFiCheckCount)
    tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=1, unit=Timer.UNIT_S, callback=timerCount, arg=timerCount, start=False, priority=1, div=0)
    # lcd.init()
    lcd.clear()
    showMessage("ver:"+webai_blockly.SYSTEM_K210_VERSION[6],x=-1,y=5,center=False,clear=False)
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
        from webai_api import OTAWiFi
        OTAWiFi()
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
    clickTimeStart=0
    clickTimeEnd=0
    while 1:
        if webai_blockly.SYSTEM_WiFiCheckCount<0:
            break
        if webai_blockly.SYSTEM_BTN_L.value()==0:
            break
        if webai_blockly.SYSTEM_WiFiCheckCount>0 and webai_blockly.SYSTEM_BTN_R.value()==0 :
            # clickTimeStart = time.ticks_ms()
            # while webai_blockly.SYSTEM_BTN_R.value()==0:
            #     clickTimeEnd = time.ticks_ms()
            # print(clickTimeEnd-clickTimeStart)
            # if((clickTimeEnd-clickTimeStart) >= 10):
            qrcodeMode=True
            break
    tim.stop()
    tim.deinit()
    del tim,clickTimeStart,clickTimeEnd
    # del webai_blockly.SYSTEM_WiFiCheckCount
    lcd.clear()
    flip=True
    while qrcodeMode:
        import sensor
        import image
        # import lcd
        # lcd.init()
        lcd.clear()
        showMessage("init qrcode mode",clear=True)
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        # sensor.set_windowing((320,240))
        sensor.set_vflip(flip)
        sensor.set_hmirror(flip)
        sensor.run(1)
        sensor.skip_frames(30)
        lcd.register(0x36,0xC0)
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
                    if 'function' in qrcodeData:
                        #print(type(data['count']),data['count'])
                        if qrcodeData['function']=="wifi":
                            lcd.register(0x36,0x80)
                            showMessage("setting WiFi...",clear=True)
                            from webai_api import setWiFi
                            setWiFi(qrcodeData['ssid'],qrcodeData['password'])
                    elif qrcodeData['cmd']=="run":
                        lcd.register(0x36,0x80)
                        showMessage("run "+qrcodeData['args'],clear=True)
                        time.sleep(0.5)
                        with open("/flash/"+qrcodeData['args']+".py") as f:
                            exec(f.read())
                    elif qrcodeData['cmd']=="deploy":
                        lcd.register(0x36,0x80)
                        showMessage("deploy python",clear=True)
                        from webai_api import saveQRCode
                        saveQRCode(qrcodeData['url'])
                except Exception as e:
                    print(e)
                    print("format error")
            lcd.display(img)
            if webai_blockly.SYSTEM_BTN_L.value()==0:
                qrcodeMode=False
                break
            if webai_blockly.SYSTEM_BTN_R.value()==0:
                flip=not flip
                sensor.set_vflip(flip)
                sensor.set_hmirror(flip)
                if flip:
                    lcd.register(0x36,0xC0)
                else:
                    lcd.register(0x36,0x80)
                showMessage("",clear=True)
                time.sleep(0.5)
            # msg="press L Pass                press R Flip"
            # lcd.draw_string(0,223,msg,lcd.RED,lcd.BLACK)
        del img,res,qrcodeData
    lcd.register(0x36,0x80)
    showMessage("",clear=True)
    # del pinA,pinB,webai_blockly.SYSTEM_BTN_L,webai_blockly.SYSTEM_BTN_R,qrcodeMode
    del qrcodeMode,timerCount,ujson,Timer,network,flip
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
    lcd.register(0x36,0x80)
    lcd.clear()
    gc.collect()
    # from machine import WDT
    # def on_wdt(self):
    #     print(self.context(), self)
    #     self.feed()
    # wdt1 = WDT(id=1, timeout=4000, callback=on_wdt, context={})
'''

# boot_py = '''
# '''

# detect boot.py
main_py = '''
try:
    import gc, lcd, image, sys
    gc.collect()
    # lcd.init()
    lcd.clear()
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

# if "mqtt.main.py" in flash_ls:
#     cwd=os.getcwd()
#     code = ""
#     with open(cwd+"/mqtt.main.py") as f:
#         code = f.read()
#     with open(cwd+"/main.py", "w") as f:
#         f.write(code)
#     try:
#         os.remove(cwd+"/mqtt.main.py")
#     except Exception as e:
#         print(e)
#         print("del mqtt.main.py error")
#     os.sync()
    # import machine
    # machine.reset()
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
        code = f.read()
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
import webai_blockly


import image
from webai_blockly import Speaker
gc.collect()
# time.sleep(0.5)
img = image.Image('logo.jpg')
lcd.display(img)
del img
gc.collect()
time.sleep(0.5)

sp = Speaker()
sp.setVolume(20)
sp.start(fileName='logo', sample_rate=22050)
del sp
gc.collect()

# import webai_blockly,_thread
# print("_boot init end")
# for i in range(200):
#     time.sleep_ms(1) # wait for key interrupt(for webAI tool)
# del i
