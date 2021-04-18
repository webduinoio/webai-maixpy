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
print('skip boot.py')
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
__20210416__
'''
print(banner)
del banner
