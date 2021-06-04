from webai import webai
from Maix import GPIO
from board import board_info
from fpioa_manager import fm
import image,gc,sys,time,_thread,os,ustruct
from machine import UART,Timer,PWM

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

USER_PWM_LIST = []

SYSTEM_BTN_L = webai.btnL.btn
SYSTEM_BTN_R = webai.btnR.btn
SYSTEM_MQTT_TOPIC = webai.esp8285.subQueue
SYSTEM_ALLOCATE_LOCK = _thread.allocate_lock()

class Mqtt:
    def push(topic,msg):
        webai.mqtt.pub(topic,msg)

    def sub(topic):
        webai.mqtt.sub(topic,Mqtt.procMsg)
        
    def procMsg(topic,msg):
        webai.esp8285.subQueue[topic] = msg


class Lcd:
    def __init__(self):
        print("webai lcd init")
        webai.img = image.Image()
        gc.collect()

    def clear(self):
        webai.lcd.clear()
        if not webai.img == None:
          webai.img.clear()

    def width(self):
        return webai.lcd.width()

    def height(self):
        return webai.lcd.height()

    def drawCircle(self, x, y, radius, color=0xffffff, thickness=1, fill=False):
        webai.img.draw_circle(x, y, radius, color, thickness, fill)
        webai.lcd.display(webai.img)

    def drawLine(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        webai.img.draw_line(x0, y0, x1, y1, color, thickness)
        webai.lcd.display(webai.img)

    def drawRectangle(self, x, y, w, h, color=0xffffff, thickness=1, fill=False):
        webai.img.draw_rectangle(x, y, w, h, color, thickness, fill)
        webai.lcd.display(webai.img)

    def drawArrow(self, x0, y0, x1, y1, color=0xffffff, thickness=1):
        webai.img.draw_arrow(x0, y0, x1, y1, color, thickness)
        webai.lcd.display(webai.img)

    def drawCross(self, x, y, color=0xffffff, size=5, thickness=1):
        webai.img.draw_cross(x, y, color, size, thickness)
        webai.lcd.display(webai.img)


    def drawString(self, x, y, text, color=(255,255,255), scale=2, x_spacing=20, mono_space=False,img=None,display=True):
        if not img==None:
            webai.img = img
        webai.draw_string(x, y, text, img=webai.img, color=color, scale=scale,mono_space=mono_space,lcd_show=display,x_spacing=x_spacing)

    def draw_string(self, x, y, msg, strColor, bgColor):
        if not msg == '':
            webai.lcd.draw_string(x, y, str(msg), strColor, bgColor)

    def displayImg(self,img=None):
        webai.img = None
        gc.collect()
        if type(img) is str:
            if(img[:4]=='http'):
                try:
                    print("download:",img)
                    webai.cloud.download(img,filename='_cache_.jpg',resize=320)
                    img = '_cache_.jpg'
                except Exception as ee:
                    print("displayImg err:",ee)
            elif(len(img.lower())<4 or img.lower()[-4:] != '.jpg'):
                img = img + ".jpg"
            webai.img = webai.res.loadImg(img)
        else:
            webai.img = img
        webai.lcd.display(webai.img)

class Camera:
    def setFlip(self,flip):
        webai.camera.initCamera(flip)
        webai.camera.set_vflip(flip)

    def snapshot(self):
        return webai.snapshot()

    def save(self,name):
        webai.snapshot()
        if not '.jpg' in name:
            name = name + '.jpg'
        webai.img.save(name)

class Speaker:

    def start(self,fileName='logo', sample_rate=11025):
        webai.speaker.play(filename=fileName,sample_rate=sample_rate)

    def setVolume(self,vol):
        webai.speaker.setVolume(vol)


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

        



class ObjectTracking():
    import KPU as kpu
    import sensor
        
    def __init__(self,flip=0,classes=[],model=None,threshold=0.1,nms_value=0.1,w=320,h=224):
        try:
            webai.camera.reset()
            webai.camera.set_pixformat(self.sensor.RGB565)
            webai.camera.set_framesize(self.sensor.QVGA)
            webai.camera.set_windowing((w, h))
            webai.camera.set_vflip(flip)
            #webai.camera.set_auto_gain(1)
            #webai.camera.set_auto_whitebal(1)
            #webai.camera.set_auto_exposure(1)
            #webai.camera.set_brightness(3)
            webai.camera.skip_frames(time = 2000)
            webai.camera.run(1)
        except Exception as e:
            print(e)
            sys.exit()
            
        try:
            # modelPathStart=modelPath.find('(')
            # modelPathEnd=modelPath.rfind(')')
            # classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            if model == 'monster':
                self.task = self.kpu.load(webai.res.monster())
            else:
                cwd="flash"
                if cwd=="flash":
                    model=0xB90000
                else:
                    model="/sd/"+model+".kmodel"
                self.task = self.kpu.load(model)
            self.classes=classes
            self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
            self.kpu.init_yolo2(self.task, threshold, nms_value, 5, self.anchor)
        except Exception as e:
            print('>>>',e)
            sys.exit()
    def checkObjects(self):
        try:
            self.classesArr=[]
            webai.img = self.sensor.snapshot()        
            code = self.kpu.run_yolo2(self.task, webai.img)
            if code:
                for i in code:
                    webai.img.draw_rectangle(i.rect())
                    webai.lcd.display(webai.img)
                    respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
                    self.classesArr.append(respList)
                    # print(self.classesArr)
                    # for i in code:
                    #     lcd.draw_string(i.x(), i.y(), self.classes[i.classid()], lcd.RED, lcd.WHITE)
                    #     lcd.draw_string(i.x(), i.y()+12, '%.3f'%i.value(), lcd.RED, lcd.WHITE)
                return True
            else:
                webai.lcd.display(webai.img)
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
        
    def __init__(self,flip=0,classes=[],model=None,w=224,h=224):
        try:
            self.sensor.reset()
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((w, h))
            self.sensor.set_vflip(flip)
            #self.sensor.set_auto_gain(1)
            #self.sensor.set_auto_whitebal(1)
            #self.sensor.set_auto_exposure(1)
            #self.sensor.set_brightness(3)
            self.sensor.skip_frames(time = 200)
            self.sensor.run(1)
        except Exception as e:
            print(e)
            sys.exit()
            
        try:
            cwd="flash"
            if cwd=="flash":
                model=0xD40000
            else:
                model="/sd/"+model+".kmodel"
            self.classes=classes
            self.task = self.kpu.load(model)
        except Exception as e:
            print(e)
            sys.exit()
    def checkClass(self):
        try:
            self.classesArr=[]
            webai.img = self.sensor.snapshot()
            fmap = self.kpu.forward(self.task, webai.img)
            plist=fmap[:]
            pmax=max(plist)
            #print(pmax)
            max_index=plist.index(pmax)
            #lcd.display(img, oft=(0,0))
            webai.lcd.display(webai.img)
            #lcd.draw_string(0, 100, "%.2f:%s "%(pmax, labels[max_index].strip()))
            objname=self.classes[max_index].strip()
            #print(objname)
            # lcd.draw_string(0, 100, "%s "%objname,lcd.RED, lcd.WHITE)
            # lcd.draw_string(0, 150, "%.2f"%pmax,lcd.RED, lcd.WHITE)
            respList={"x":0,"y":0,"w":0,"h":0,"value":float("%.2f"%pmax),"classid":max_index,"index":0,"objnum":0,"objname":objname}
            self.classesArr.append(respList)
            time.sleep(0.01)
            return True
        except Exception as e:
            print(e)
            self.classesArr=[]
            return False

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

