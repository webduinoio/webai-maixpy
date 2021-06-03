from fpioa_manager import fm
from Maix import GPIO,utils
import os,sys,time,gc,lcd,image,_thread

gc.enable()
'''

 _boot.py -> _board.py (webAI)

'''
boot_py = '''
try:
    from webai import *
    from machine import Timer
    import time, ujson

    cmdData = webai.cfg.get("cmd")
    print("[boot.py] cmdData:",cmdData)
    SYSTEM_WiFiCheckCount = 5

    cfgData = webai.cfg.load()
    WIFI_SSID = "webduino.io"
    WIFI_PASW = "webduino"
    if 'wifi' in cfgData:
        WIFI_SSID = cfgData['wifi']['ssid']
        WIFI_PASW = cfgData['wifi']['pwd']    

    if cmdData == None:
        print("[boot.py] normal boot...")
        def timerCount(timer):
            global SYSTEM_WiFiCheckCount
            if SYSTEM_WiFiCheckCount<=0:
                webai.clear()
                timer.stop()
            webai.showMessage("play after "+str(SYSTEM_WiFiCheckCount)+" seconds",x=-1,y=6,center=False,clear=False)
            SYSTEM_WiFiCheckCount-=1
            print("[boot.py] timer:",SYSTEM_WiFiCheckCount)

        tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=1, unit=Timer.UNIT_S, callback=timerCount, arg=timerCount, start=False, priority=1, div=0)
        gc.collect()
        lcd.clear()
        webai.img = image.Image()
        webai.draw_string(47,28,"DeviceID: "+webai.deviceID,scale=2,x_spacing=4)
        webai.show(img=webai.img)
        webai.img = None
        gc.collect()
        webai.showMessage("ver:"+os.uname()[6],x=-1,y=5,center=False,clear=False)
        webai.showMessage("WiFi checking...",x=-1,y=4,center=False,clear=False)
        setWiFiFlag=True
        webai.showMessage("ssid: "+WIFI_SSID,x=-1,y=2.5,center=False,clear=False)
        err = 0
        wifiStatus=""
        ifconfig = None
        if setWiFiFlag:
            ifconfig = webai.esp8285.wlan.ifconfig()
            if ifconfig[0]=="0.0.0.0" or ifconfig[3]!=WIFI_SSID:
                while 1:
                    try:
                        webai.esp8285.wlan.connect(WIFI_SSID, WIFI_PASW)
                        ifconfig=webai.esp8285.wlan.ifconfig()
                        webai.esp8285.updateState()
                        wifiStatus="OK"
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
                webai.esp8285.wifiConnect = True
                wifiStatus="OK"
        del err,WIFI_SSID,WIFI_PASW,setWiFiFlag
        if wifiStatus=="OK":
            webai.mqtt.sub('PING',webai.cmdProcess.sub,includeID=True)
            webai.esp8285.ota()
            webai.showMessage(" "*40,x=-1,y=4,center=False,clear=False)
            webai.showMessage("WiFi status:OK ("+ifconfig[6]+" dBm)",x=-1,y=4,center=False,clear=False)
        else:
            webai.showMessage(" "*40,x=-1,y=4,center=False,clear=False)
            webai.showMessage("WiFi status:not OK!!!",x=-1,y=4,center=False,clear=False)
        del wifiStatus
        qrcodeMode=False
        tim.start()
        lcd.draw_string(0,224,"press L Play                press R Scan",lcd.RED,lcd.BLACK)
        while 1:
            if SYSTEM_WiFiCheckCount<0:
                break
            if webai.btnL.btn.value()==0:
                print("run main.py")
                break
            if SYSTEM_WiFiCheckCount>0 and webai.btnR.btn.value()==0:
                tim.stop()
                img = image.Image()
                img.draw_string(80,100,"init Camera...",scale=2,x_spacing=4)
                lcd.display(img)
                img = None
                gc.collect()
                webai.initCamera(True)
                QRCodeRunner.scan()
        webai.lcd.clear()
        if not webai.img == None:
            webai.img.clear()
        tim.stop()
        tim.deinit()
        del tim
        try:
            if webai.adc()==1023:
                print("init cmdSerial...")
                webai.speaker.play(filename='logo.wav',sample_rate=48000)
                webai.cmdSerial.init()
                _thread.start_new_thread(webai.cmdSerial.run,())
        except Exception as e:
            print("webai.adc() error:",e)                

    else:
        print("[boot] run command...")
        #time.sleep(1)

        # check usb or mqtt mode
        cmdData = webai.cfg.get('cmd')
        if cmdData[:8]=='_DEPLOY/':
            info = ujson.loads(cmdData[8:])
            if 'url' in info:
                if info['url'] != 'local':
                    webai.connect(WIFI_SSID,WIFI_PASW)
                    webai.esp8285.wifiConnect = True
                    webai.mqtt.sub('PING',webai.cmdProcess.sub,includeID=True) 
        
        webai.cmdProcess.load()
        webai.lcd.clear()

except Exception as e:
    print("boot exception:",e)
    sys.print_exception(e)

'''

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
    loading.draw_string(int(lcd.width()//2 - len(info) * 5)-10, (lcd.height())//2-20, info, color=(255, 255, 255), scale=2, mono_space=0)
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
[__20210516__]
'''
#time.sleep(0.5)
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


for i in range(200):
    time.sleep_ms(10)  # wait for key interrupt(for maixpy ide)
del i

print("<<<< [Start] >>>>")
time.sleep_ms(100) # wait for stop command
lcd.init()
#time.sleep(0.5)

lcd.clear(0xFFFF)


img = image.Image()
img.draw_string(80,100,"Initialize...",scale=2,x_spacing=4)
lcd.display(img)

try:
    os.stat('main.py')[6]
except:
    try:
        f = open('/flash/main.py','w')
        f.write(main_py)
    finally:
        f.close()

fm.fpioa.set_function(7, fm.fpioa.GPIO7)
resetPin = GPIO(GPIO.GPIO7, GPIO.IN)
if resetPin.value()==0:
    lcd.clear(0x07E0)
    # cfg reset flag
    utils.flash_write(0x4000,bytearray([0,0]))
    try:
        f1 = open('/flash/main.py','w')
        f1.write(main_py)
        f1.close()
    finally:
        os.sync()
    time.sleep(1)
    img.clear()
    img.draw_string(110,100,"Reset OK",scale=2,x_spacing=4)
    lcd.display(img)
    time.sleep(2)
    lcd.clear(0xFFFF)
    import machine
    machine.reset()

#time.sleep(0.1)
#fm.unregister(7)
img = None
resetPin = None
main_py = None
gc.collect()

# check IDE mode
ide_mode_conf = "/flash/ide_mode.conf"
ide = True

try:
    f = open(ide_mode_conf,'r')
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

print(banner)
banner = None

exec(boot_py)
print('[boot.py] end')