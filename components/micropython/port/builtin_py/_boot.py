from fpioa_manager import fm
from Maix import GPIO
import os,sys,time,gc,lcd,image,_thread
'''

 _boot.py -> _cmdExec.py -> (0) -> boot.py -------> main.py
     |              |                            /
     |              + ----> (1) -> _cmdCheck.py +
      \
       +-- _board.py (webAI)

'''
boot_py = '''
print('skip boot.py')
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
[__20210510__]
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
lcd.init()
#time.sleep(0.5)

lcd.clear(0xFFFF)


img = image.Image()
img.draw_string(80,100,"Initialize...",scale=2,x_spacing=4)
lcd.display(img)

fm.fpioa.set_function(7, fm.fpioa.GPIO7)
resetPin = GPIO(GPIO.GPIO7, GPIO.IN)
if resetPin.value()==0:
    lcd.clear(0xF000)
    try:
        f = open('/flash/main.py','w')
        f.write(main_py)
    finally:
        f.close()
    time.sleep(1)
    img.draw_string(90,100,"Reset OK",scale=2,x_spacing=4)
    lcd.display(img)
    time.sleep(2)
    lcd.clear(0xFFFF)
    import machine
    machine.reset()

#time.sleep(0.1)
#fm.unregister(7)
img = None
resetPin = None
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

#gc.enable()
from _board import webai