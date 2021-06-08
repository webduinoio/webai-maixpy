import KPU as kpu
import machine , ubinascii , os , time , gc , sensor
from modules import ws2812
#from microWebCli import MicroWebCli

from board import board_info
from machine import UART
from fpioa_manager import fm
from Maix import config,utils,GPIO
from microWebCli import MicroWebCli
import sensor,lcd,machine,time,network,ujson
import gc,uos,json,os,image,_thread,ubinascii
from webai import *


_thread.stack_size(16*1024)

class visionService:
    class Field:
        def __init__(self,boundary,key,value):
            visionService.Field.boundary = boundary
            self.boundary = b'------%s\r\n' % boundary
            self.key = b'Content-Disposition: form-data; name="%s"\r\n' % key
            self.CRLF = b'\r\n'
            self.value = b'%s\r\n' % value
        def data(self):
            return b''.join([self.boundary,self.key,self.CRLF,self.value])
        def length(self):
            return len(self.data())

    class Filename:
        def __init__(self,boundary,filename):
            visionService.Field.boundary = boundary
            self.filename = filename
            self.boundary = b'------%s\r\n' % boundary
            self.name = b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % ('image', filename[filename.find("/",1)+1:])
            self.CNT = b'Content-Type: image/jpeg\r\n'
            self.CRLF = b'\r\n'
            self.DATA = None # file bytearray
        def destroy(self):
            self.DATA = None
            time.sleep(0.001)
            gc.collect()
        def data(self):
            self.DATA = webai.imgCache.load(self.filename)
            print("Filename data:",self.filename,':',len(self.DATA))
            return b''.join([self.boundary,self.name,self.CNT,self.CRLF,self.DATA,self.CRLF])
        def length(self):
            return webai.imgCache.files[self.filename]['size']+len(b''.join([self.boundary,self.name,self.CNT,self.CRLF,self.CRLF]))

    def __init__(self,url,hashkey):
        self.url = url+'?hashkey='+hashkey
        self.boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')

    def countFilesSize(self,files):
        self.fileSize = 0
        for i in files:
            self.fileSize = self.fileSize + visionService.Filename(self.boundary,i).length()
        return self.fileSize        

    def fileUpload(self,dsname,shared,files,cb=None):
        self.fileSize = self.countFilesSize(files)
        boundary = self.boundary
        shared_field = visionService.Field(boundary,'shared',shared)
        dsname_field = visionService.Field(boundary,'dsname',dsname)
        bodyEnd = b''.join([b'\r\n------%s--' % boundary, b'\r\n'])
        bodyLen = shared_field.length()+dsname_field.length()+len(bodyEnd)+self.fileSize
        try:
            wCli = MicroWebCli(self.url, 'POST')
            wCli.OpenRequest(None, 'multipart/form-data; boundary=----%s' % boundary, str(bodyLen))
            print("uploading...total size:",bodyLen)
            wCli._write(shared_field.data())
            wCli._write(dsname_field.data())
            cntUpload = 0
            cntLen = len(files)
            for i in files:
                cntUpload = cntUpload + 1
                print("uploading...file:",i)
                _file = visionService.Filename(boundary,i)
                wCli._write(_file.data())
                _file.destroy()
                if not cb == None:
                    cb(cntUpload,cntLen)
            wCli._write(bodyEnd)
            print("write done.")
            return wCli.GetResponse().IsSuccess()
        finally:
            wCli.Close()

class MiniHttp:
    def readline(self):
        # return self.raw.readline() # mpy
        data = b""
        while True:
            tmp = self.raw.recv(1)
            data += tmp
            if tmp == b'\n':
                break
        return data

    def write(self, data):
        # return self.raw.write(data) # mpy
        self.raw.send(bytes(data))

    def read(self, len):
        return self.raw.read(len) # mpy
        # return self.raw.recv(len)

    def __init__(self):
        self.raw = None

    def connect(self, url, timeout=2):
        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""

        if proto == "http:":
            port = 80
        elif proto == "https:":
            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        import socket
        ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        ai = ai[0]
        if self.raw is not None:
            self.raw.close()
        raw = socket.socket(ai[0], ai[1], ai[2])
        raw.settimeout(timeout)

        raw.connect(ai[-1])
        if proto == "https:":
            import ussl as ssl
            raw = ssl.wrap_socket(raw, server_hostname=host)
        self.raw = raw
        self.host = bytes(host, "utf-8")
        self.path = bytes(path, "utf-8")

    def exit(self):
        if self.raw != None:
            self.raw.close()
            self.raw = None

    def request(self, method, headers={}, data=None):
        try:
            self.headers = headers
            self.write(b"%s /%s HTTP/1.1\r\n" % (method, self.path))
            if not "Host" in headers:
                self.write(b"Host: %s\r\n" % self.host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                self.write(k)
                self.write(b": ")
                self.write(headers[k])
                self.write(b"\r\n")
            if data:
                self.write(b"Content-Length: %d\r\n" % len(data))
            self.write(b"\r\n")
            if data:
                self.write(data)
            l = self.readline()
            # print(l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ""
            response = {}
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = self.readline()
                if not l or l == b"\r\n":
                    break
                if l.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in l:
                        raise ValueError("Unsupported " + l)
                # elif l.startswith(b"Location:") and not 200 <= status <= 299:
                    # raise NotImplementedError("Redirects not yet supported")
                try:
                    tmp = l.split(b': ')
                    response[tmp[0]] = tmp[1][:-2]
                except Exception as e:
                    print(e)
        except OSError:
            self.exit()
            raise
        return (status, reason, response)

class mcar:
    ready = False
    def init():
        if(mcar.ready == True):
            return
        from Maix import GPIO
        from fpioa_manager import fm
        from machine import Timer,PWM
        mcar.ready = True
        fm.register(0, fm.fpioa.GPIO2)#p13
        fm.register(1, fm.fpioa.GPIO3)#p14
        mcar.leftDirection=GPIO(GPIO.GPIO3,GPIO.OUT)
        mcar.rightDirection=GPIO(GPIO.GPIO2,GPIO.OUT)
        leftTimer = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
        rightTimer = Timer(Timer.TIMER0, Timer.CHANNEL1, mode=Timer.MODE_PWM)
        mcar.rightWheel = PWM(rightTimer, freq=500000, duty=0, pin=8)#p6
        mcar.leftWheel = PWM(leftTimer, freq=500000, duty=0, pin=10)#p8
        mcar.ws2812 = ws2812(led_pin=22, led_num=8)

    def stop():
        mcar.move(0,0)

    def forward(power=100):
        mcar.move(power,power)

    def backward(power=100):
        mcar.move(-1*power,-1*power)

    def left(power=45):
        mcar.move(-1*power,power)

    def right(power=45):
        mcar.move(power,-1*power)

    def move(left=45,right=45):
        mcar.motor_left(left)
        mcar.motor_right(right)

    def motor_left(val=0):
        mcar.init()
        if(val>=0):
            mcar.leftDirection.value(0)
            mcar.leftWheel.duty(val)
        else:
            mcar.leftDirection.value(1)
            mcar.leftWheel.duty(100+val)

    def motor_right(val=0):
        mcar.init()
        if(val>=0):
            mcar.rightDirection.value(0)
            mcar.rightWheel.duty(val)
        else:
            mcar.rightDirection.value(1)
            mcar.rightWheel.duty(100+val)

    def led_on(num=0, color=(0xff, 0xff, 0xff)):
        mcar.ws2812.set_led(num, color)
        mcar.ws2812.display()

    def led_off():
        for i in range(8):
            mcar.ws2812.set_led(i)
        mcar.ws2812.display()
class ColorObject:
    def findMax(img, threadshold, areaLimit=100, drawRectangle=True , drawPosition=False):
        blobs = img.find_blobs([threadshold])
        maxObject = False
        if blobs:
            for b in blobs:
                val = b[2]*b[3]
                if(val > areaLimit) :
                    maxObject = b
                    areaLimit = val
        if(maxObject != False) :
            if(drawPosition) :
                img.draw_string(10,10,str(maxObject[0:4]))
            if(drawRectangle) :
                img.draw_rectangle(maxObject[0:4])
        return maxObject

# ███████╗ █████╗  ██████╗███████╗██████╗ ███████╗████████╗███████╗ ██████╗████████╗
# ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
# █████╗  ███████║██║     █████╗  ██║  ██║█████╗     ██║   █████╗  ██║        ██║   
# ██╔══╝  ██╔══██║██║     ██╔══╝  ██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   
# ██║     ██║  ██║╚██████╗███████╗██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   
# ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   

class FaceDetect:
    def init(address=0xD40000):
        FaceDetect.task = kpu.load(webai.res.face())
        anchor = (0.1606, 0.3562, 0.4712, 0.9568, 0.9877, 1.9108, 1.8761, 3.5310, 3.4423, 5.6823)
        kpu.init_yolo2( FaceDetect.task , 0.5, 0.3, 5, anchor)

    def findMax(img,areaLimit=100,confidenceLimit=0.65,drawRectangle=True):
        code = kpu.run_yolo2(FaceDetect.task, img)
        maxFaceArea = False
        nowArea = 0
        if code:
            for item in code:
                confidence = float(item.value())
                if(confidence<confidenceLimit):
                    continue
                itemROL = item.rect()
                nowArea = itemROL[2]*itemROL[3]
                if(nowArea < areaLimit):
                    continue
                classID = int(item.classid()) # 0: noMask , 1:Mask
                info = {
                    "x":itemROL[0] , "y":itemROL[1],
                    "w":itemROL[2] , "h":itemROL[3],
                    "mask": classID==1
                }
                maxFaceArea = info
                if drawRectangle:
                    img.draw_rectangle(itemROL, (255, 255, 255), tickness=5)
        return maxFaceArea


#  ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
# ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
# ██║     ██║   ██║██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
# ██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
# ╚██████╗╚██████╔╝██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
#  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                                                             
class CodeScanner :
    def findQRCode(img,loop=True):
        px = 0
        py = -15
        lt_x = 20
        lt_y = 20
        payload = ""
        while loop:
            webai.camera.set_hmirror(True)
            webai.img = webai.camera.snapshot()
            payload = CodeScanner.scanQRCode(webai.img)
            webai.camera.set_hmirror(False)
            webai.img = webai.camera.snapshot()
            if payload=='':
                payload = CodeScanner.scanQRCode(webai.img)
            if not payload=='':
                break
            #左上
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,98+lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,48+lt_x+px,48+lt_y+py,0xFFFF,2)
            #右上
            webai.img.draw_line(222-lt_x+px,8+lt_y+py,272-lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,8+lt_y+py,272-lt_x+px,48+lt_y+py,0xFFFF,2)
            #左下
            webai.img.draw_line(48+lt_x+px,232-lt_y+py,98+lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,192-lt_y+py,48+lt_x+px,232-lt_y+py,0xFFFF,2)
            #右下
            webai.img.draw_line(222-lt_x+px,232-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,192-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_string(90,208,"Scan QRCode",scale=2,x_spacing=2)
            webai.show(img=webai.img)
        webai.img = None
        gc.collect()
        return payload

    def scanQRCode(img):
        payload = ""
        for code in img.find_qrcodes():
            payload = code.payload()
            break
        return payload

    def scanBarCode(img):
        payload = ""
        for code in img.find_barcodes():
            payload = code.payload()
            break
        return payload

    def findBarCode(img):
        px = 0
        py = -15
        lt_x = 0
        lt_y = 60
        payload = ""
        while True:
            webai.camera.set_hmirror(True)
            webai.img = webai.camera.snapshot()
            payload = CodeScanner.scanBarCode(webai.img)
            webai.camera.set_hmirror(False)
            webai.img = webai.camera.snapshot()
            if payload=='':
                payload = CodeScanner.scanBarCode(webai.img)
            if not payload=='':
                break
            #左上
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,78+lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,48+lt_x+px,48+lt_y+py,0xFFFF,2)
            #右上
            webai.img.draw_line(242-lt_x+px,8+lt_y+py,272-lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,8+lt_y+py,272-lt_x+px,48+lt_y+py,0xFFFF,2)
            #左下
            webai.img.draw_line(48+lt_x+px,232-lt_y+py,78+lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,192-lt_y+py,48+lt_x+px,232-lt_y+py,0xFFFF,2)
            #右下
            webai.img.draw_line(242-lt_x+px,232-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,192-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_string(80,208,"Scan BarCode",scale=2,x_spacing=2)
            webai.show(img=webai.img)
        webai.img = None
        gc.collect()
        return payload
class cmdSerial:

    def init():
        from machine import UART
        #webai.initCamera(1)
        cmdSerial.repl = UART.repl_uart()
        cmdSerial.repl.init(115200, 8, None, 1, read_buf_len=20*1024, ide=False, from_ide=False)
        while cmdSerial.repl.any():
            cmdSerial.repl.read(1)
        cmdSerial.print(10,10,"Ready to go....",True)

    def print(x,y,text,clear,debug = True):
        debug = False
        if not debug:
            return
        if clear:
            webai.lcd.clear()
        webai.lcd.draw_string(x,y,text,lcd.WHITE)

    def readLine():
        while not cmdSerial.repl.any():
            time.sleep(0.01)
        recv = cmdSerial.repl.readline()
        return recv.decode("utf-8").rstrip()

    def run():
        while True:
            try:
                cmdSerial.print(10,10,"-- wait cmd --",True)
                cmd = cmdSerial.readLine()
                #webai.lcd.clear()
                cmdSerial.print(10,10,"CMD:"+cmd+"       ",False)
                func = getattr(cmdSerial,cmd)
                cmdSerial.print(10,30,"func::"+str(func),False)
                func(cmdSerial.repl)
                func = None

            except Exception as ee:
                webai.lcd.clear(lcd.RED)
                time.sleep(0.1)
                webai.lcd.clear(lcd.BLACK)
                cmdSerial.print(10,80,"CMD:"+cmd,False)
                errmsg = str(ee)
                cmdSerial.print(30,100,errmsg,False)
                if len(errmsg)>36:
                    cmdSerial.print(30,120,errmsg[36:],False)


    def execREPL(repl):
        info = cmdSerial.readLine()
        cmdSerial.print(10,30,"size: "+info,True)
        readLen = int(info)
        cmdSerial.print(10,110,"exec...",False)
        data = repl.read(int(readLen))
        data = data.decode("utf-8").rstrip()
        try:
            exec(data)
        except Exception as e:
            print("exec(...) err:",e)
        print("_REPL_OK_")
        cmdSerial.print(10,130,"OK",False)
        data = None
        time.sleep(0.01)
        gc.collect()
        while cmdSerial.repl.any():
            cmdSerial.repl.read(1)

    def mem(repl):
        from Maix import utils
        import KPU as kpu
        info = "mem_free:"+str(gc.mem_free()/1024)+"KB"
        print(info)
        kpu.memtest()

    def deviceID(repl):
        print(webai.deviceID)

    def deployPy(repl):
        filename = cmdSerial.readLine()
        codeLen = cmdSerial.readLine()
        codeText = repl.read(int(codeLen))
        webai.fs.save(filename,codeText)
        print('OK')

    def clear(repl):
        while cmdSerial.repl.any():
            cmdSerial.repl.read(1)
        print("cmd_clear OK")

    def setWiFi(repl):
        ssid = cmdSerial.readLine()
        pwd = cmdSerial.readLine()
        webai.cfg.put('wifi',{'ssid':ssid,'pwd':pwd})
        print("OK")
        time.sleep(0.1)
        machine.reset()

    def restart(repl):
        import machine
        print("OK")
        time.sleep(0.1)
        machine.reset()

    def snapshot(repl):
        #webai.initCamera(1)
        img = webai.snapshot()
        jpg = img.compress(80)
        jpg = jpg.to_bytes()
        cmdSerial.print(10,30,"snapshot write bytes:"+str(len(jpg)), False)
        # send jpg size
        print(str(len(jpg)))
        # send jpg bytearray
        repl.write(jpg)
        cmdSerial.print(10,50,"snapshot write OK", False)
        img = None
        jpg = None
        time.sleep(0.01)
        gc.collect()

    def flashRead(repl):
        info = cmdSerial.readLine()
        cmdSerial.print(10,30,"address,size: "+info,True)
        info = info.split(',')
        addr = int(info[0])
        readLen = int(info[1])
        data = utils.flash_read(addr,readLen)
        cmdSerial.print(10,70,"flash_read OK",False)
        print(str(len(data)))
        repl.write(data)
        cmdSerial.print(10,110,"send bytearray...OK",False)
        data = None
        time.sleep(0.01)
        gc.collect()

    def flashWrite(repl):
        info = cmdSerial.readLine()
        cmdSerial.print(10,30,"write address,size: "+info,True)
        info = info.split(',')
        addr = int(info[0])
        readLen = int(info[1])
        cmdSerial.print(10,110,"write to flash...",False)
        data = repl.read(int(readLen))
        utils.flash_write(addr,data)
        cmdSerial.print(10,110,"write to flash...OK",False)
        data = None
        time.sleep(0.01)
        gc.collect()
        print('OK')

class _res_:

    def init():
        __class__.addr = 0x700000
        __class__.data = {"0.asr":[0,5256],"1.asr":[5256,5256],"1.font":[10512,2097152],"2.asr":[2107664,5256],"2.monster":[2112920,1633704],"3.asr":[3746624,5256],"3.face":[3751880,1601704],"4.asr":[5353584,5256],"5.asr":[5358840,5256],"6.asr":[5364096,5256],"7.asr":[5369352,5256],"8.asr":[5374608,5256],"bg.jpg":[5379864,25516],"blue.jpg":[5405380,58132],"board.jpg":[5463512,53420],"face.py":[5516932,1245],"faceMask.py":[5518177,1212],"green.jpg":[5519389,50776],"logo.jpg":[5570165,39598],"m01.jpg":[5609763,34824],"m02.jpg":[5644587,29248],"mleft.jpg":[5673835,33802],"monsters.py":[5707637,1296],"mooncar.jpg":[5708933,53385],"mqttCar.py":[5762318,2356],"mright.jpg":[5764674,33773],"mrun.jpg":[5798447,31887],"red.jpg":[5830334,44478],"voice.py":[5874812,2197],"wifi_err.jpg":[5877009,50604],"wifi_ok.jpg":[5927613,46427],"yellow.jpg":[5974040,57615],"yoloCar.py":[6031655,4086]}
    
    def loadImg(name,newImg=False):
        if not newImg:
            webai.img = None
        gc.collect()
        if not name in __class__.data:
            return image.Image(name)
        info = __class__.data[name]
        jpeg_buff = utils.flash_read(__class__.addr+info[0],info[1])
        if not newImg:
            webai.img = image.Image(jpeg_buff, from_bytes = True)
        else:
            img = image.Image(jpeg_buff, from_bytes = True)
        jpeg_buff = None
        gc.collect()
        if not newImg:
            return webai.img
        else:
            return img
        
    def loadPy(name):
        name += '.py'
        if not name in __class__.data:
            cwd = os.getcwd()
            f = open(cwd+'/'+name)
            pythonCode = f.read()
            f.close()
            del f
        else:
            info = __class__.data[name]
            pythonCode = utils.flash_read(__class__.addr+info[0],info[1])
        return pythonCode

    def loadAsr(num):
        info = __class__.data[str(num)+'.asr']
        return utils.flash_read(__class__.addr+info[0], info[1])

    def font():
        return __class__.addr+__class__.data['1.font'][0]
    
    def monster():
        return __class__.addr+__class__.data['2.monster'][0]

    def face():
        return __class__.addr+__class__.data['3.face'][0]

# 0x900000 ~ 0x97FFFF  512KB 存放快取圖片，減少檔案系統使用
class imgCache:
    def init():
        if not hasattr(__class__,'initialize'):
            if webai.cfg.get('cache') == None:
                webai.cfg.put('cache',{'files':{},'meta':{'idx':0,'addr':0x900000}})
            imgCache.cache = webai.cfg.get('cache')
            imgCache.meta = imgCache.cache['meta']
            imgCache.files = imgCache.cache['files']
            __class__.initialize = True

    def save(filename,img,quality=80):
        imgCache.init()
        idx = imgCache.meta['idx']
        fileExists = filename in imgCache.files

        if fileExists:
            return False
        else:
            idx = idx + 1
        jpg = img.compress(quality)
        jpg = jpg.to_bytes()
        size = len(jpg)
        imgCache.meta['idx'] = idx
        imgCache.meta['filename'] = filename
        info = {
            'idx': idx,
            'addr': imgCache.meta['addr'],
            'size':size
        }
        imgCache.files[filename] = info
        #write data
        utils.flash_write(imgCache.meta['addr'],jpg)
        if not fileExists:
            imgCache.meta['addr'] = imgCache.meta['addr'] + size
        #print("save>>>>",imgCache.cache['meta'])
        webai.cfg.put('cache',imgCache.cache)
        jpg = None
        img = None
        gc.collect()
        return True

    def load(filename):
        imgCache.init()
        idx = imgCache.meta['idx']
        fileExists = filename in imgCache.files
        if not fileExists:
            return None
        size = imgCache.files[filename]['size']
        addr = imgCache.files[filename]['addr']
        jpeg_buff = utils.flash_read(addr,size)
        return jpeg_buff

    def loadImg(filename):
        imgCache.init()
        webai.img = None
        gc.collect()
        idx = imgCache.meta['idx']
        fileExists = filename in imgCache.files
        if not fileExists:
            return None
        size = imgCache.files[filename]['size']
        addr = imgCache.files[filename]['addr']
        jpeg_buff = utils.flash_read(addr,size)
        img = image.Image(jpeg_buff, from_bytes = True)
        jpeg_buff = None
        gc.collect()
        return img

    def clear():
        webai.cfg.put('cache',{'files':{},'meta':{'idx':0,'addr':0x900000}})


class cfg:

    def init():
        cfg.flag = 0x4000
        cfg.length = 0x4002
        # maxium size: 4096 - 4 bytes
        cfg.data = 0x4004       # 16388
        cfg.blobData = 0x10000  # 65536~
        id = utils.flash_read(cfg.flag,2)
        # check flag '119 97' = 'w a'
        if id[0] != 119 or id[1] != 97: 
            utils.flash_write(cfg.flag,bytearray([119,97]))
            cfg.save({})
        else:
            dataLen = utils.flash_read(cfg.length,2)
            cfg.size = dataLen[0]*0x100 + dataLen[1]

    def clear():
        cfg.save({})

    def reset():
        cfg.save({})

    def load():
        jsonData = utils.flash_read(cfg.data,cfg.size)
        try:
            cfg.size = len(jsonData)
            return ujson.loads(jsonData)
        except:
            raise Exception("parse error:"+ str(jsonData))

    def save(obj):
        """
        :param name: obj
        :param type: json
        """
        jsonData = ujson.dumps(obj)
        cfg.size = len(jsonData.encode())
        #write size
        hi = cfg.size // 256
        lo = cfg.size % 256
        utils.flash_write(cfg.length,bytearray([hi,lo]))
        #write data
        utils.flash_write(cfg.data,jsonData.encode())
        print("save",cfg.size,"bytes")

    def get(key):
        obj = cfg.load()
        if(not key in obj):
            val = None
        else:
            val = obj[key]
        obj = None
        del obj
        return val

    def put(key,value):
        obj = cfg.load()
        obj[key] = value
        cfg.save(obj)
        obj = None
        del obj

    def remove(key):
        obj = cfg.load()
        if(not key in obj):
            val = None
        else:
            val = obj[key]
            del obj[key]
            cfg.save(obj)
        ob = None
        del obj
        return val

    def saveImg(img,quality=80):
        jpg = img.compress(quality)
        cfg.saveBlob(jpg.to_bytes())
        print("img size:",len(jpg.to_bytes()))
        jpg = None
        gc.collect()

    def loadImg():
        jpeg_buff = cfg.loadBlob()
        #jpeg_buff = b'\xFF'   # jpeg buffer
        img = image.Image(jpeg_buff, from_bytes = True)
        jpeg_buff = None
        return img

    def saveBlob(barray):
        cfg.saveBlobAddr(cfg.blobData, barray)

    def loadBlob():
        cfg.loadBlobAddr(cfg.blobData)

    def saveBlobAddr(addr, barray):
        blobLength = len(barray)
        hi = blobLength // 256
        lo = blobLength % 256
        utils.flash_write(addr,bytearray([hi,lo]))
        #write data
        utils.flash_write(addr+2,barray)

    def loadBlobAddr(addr):
        blobLen = utils.flash_read(addr,2)
        blobLen = blobLen[0]*0x100 + blobLen[1]
        return utils.flash_read(addr+2,blobLen)

class cloud:
    container = 'user'
    def download(self, url, filename=None, address=None, redirect=True, resize=320, img=True, showProgress=False, enableLog=True):
        def progress(percent):
            webai.img = image.Image()
            percent = int(percent)
            webai.img.draw_rectangle(10,100,300,40,color=(64,128,64),thickness=2)
            webai.img.draw_rectangle(10,100,percent*3,40,color=(64,128,64),thickness=2,fill=True)
            webai.img.draw_string(130,150,str(percent)+"%",scale=2,x_spacing=2,mono_space=True)
            if(percent < 100):
                webai.img.draw_string(30,50,"Downloading...",scale=2,x_spacing=4,mono_space=False)
            else:
                webai.img.draw_string(30,50,"OK!",scale=2,x_spacing=4,mono_space=False)
            webai.show(img=webai.img)
            webai.img = None
            gc.collect()
        
        if redirect:
            server = "http://share.webduino.io/storage/"
            #server = "http://192.168.0.48:3000/storage/"
            if img:
                url = server + "redirect/img_resize/" + str(resize) + "/?url=" + url
            else:
                url = server + "redirect?url=" + url
        webai.log(enableLog, "redirect url:%s"%url)
        http = MiniHttp()
        block_size = 10240*2
        start = time.ticks()
        start_pos = 0
        file_pos, filesize, errCount = 0, 0, 0
        if not filename==None:
            saveFile = open(filename,'wb')
        else:
            start_pos = address if type(address) is int else int(address,16)
        while True:
            try:
                if http.raw is None:
                    http.connect(url)
                    webai.log(enableLog, "http connect.")
                else:
                    if filesize == 0:
                        res = http.request(b"HEAD", {b'Connection': b'keep-alive'})
                        #print("res>>>",res)
                        if res[0] == 200:
                            filesize = int(res[2][b'Content-Length'], 10)
                            webai.log(enableLog, "")
                            webai.log(enableLog, "filesize: %s"%filesize)
                    else:
                        errCount=0
                        file_end = file_pos + block_size
                        if file_end > filesize:
                            file_end = filesize
                        headers = {
                                b'Connection': b'keep-alive',
                                b'Range': b'bytes=%d-%d' % (file_pos, file_end)
                        }
                        res = http.request(b"GET", headers)
                        cntLength = res[2][b'Content-Length']
                        data = http.read(int(cntLength, 10))
                        dataLen = len(data)
                        spendSec = int((time.ticks() - start)/1000)
                        speed = 0
                        try:
                            speed = int(file_pos/1024/spendSec*100)/100
                        except:
                            pass
                        percent = int((file_pos / filesize)*1000)//10
                        if showProgress:
                            #webai.draw_string(80,110,"Run..."+str(percent)+"%",scale=2,x_spacing=6)
                            # webai.progress(percent)
                            progress(percent)
                            webai.img = None
                            gc.collect()
                        if len(data) == (file_end - file_pos):
                            webai.log(enableLog, "writing: %s ~ %s %s %% %s KB"%(hex(start_pos+file_pos), hex(start_pos+file_end), percent, speed))
                            if not address==None:
                                utils.flash_write(start_pos+file_pos,data)
                            if not filename==None:
                                saveFile.write(data)
                            if file_end == filesize:
                                webai.log(enableLog, "100%% , total time: %s seconds"%spendSec)
                                break
                            else:
                                file_pos = file_end
            except Exception as e:
                errCount+=1
                webai.log(enableLog, "errorCount: %s"%(errCount), e)
                time.sleep(0.5)
                if errCount>4:
                    raise e
            finally:
                data = None
        http.exit()
        http = None 
        gc.collect()
        if showProgress:
            webai.draw_string(110,100,"下載完成  ",scale=2)
            webai.img = None
            gc.collect()
        if not filename == None:
            saveFile.close()

    def uploadPic(self,url,hashkey,dsname,files,cb=None):
        vs = visionService(url,hashkey)
        return vs.fileUpload(dsname,'false',files,cb)

    def putBytearray(self,_bytearray,desFile,retry=3):
        while True:
            try:
                self._putBytearray(_bytearray,desFile,retry)
                return "http://share.webduino.io/storage/_download/"+self.container+"/"+desFile
                break
            except Exception as ee:
                retry = retry - 1
                if(retry==0):
                    break
                print("retry...",retry,ee)
                webai.resetESP8285()

    def putFile(self,srcFile,desFile,retry=3):
        while True:
            try:
                self._putFile(srcFile,desFile,retry)
                break
            except:
                retry = retry - 1
                if(retry==0):
                    break
                print("retry...",retry)
                webai.resetESP8285()

    def putImg(self,img,desFile,retry=3):
        url = None
        while True:
            try:
                filename = '_tmp_.jpg'
                print("save...",filename)
                img.save(filename)
                print("save done.")
                url = self._putFile(filename,desFile,retry)
                os.remove(filename)
                break
            except:
                retry = retry - 1
                if(retry==0):
                    raise Exception("upload "+desFile+" fail")
                    break
                print("retry...",retry)
                webai.resetESP8285()
        return url

    def _putBytearray(self,_bytearray,desFile,retry):
        startTime = time.ticks_ms()
        url = "http://share.webduino.io/_upload/"+self.container+"/"
        print("open post...bytearray")
        wCli = MicroWebCli(url, 'POST')
        print("open post...done")
        print("fileSize:",len(_bytearray))
        boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')
        bodyStart = \
        '------%s\r\n'%boundary+\
        'Content-Disposition: form-data; name="file"; filename="'+desFile+'"\r\n'+\
        'Content-Type: application/octet-stream\r\n\r\n'
        bodyEnd =  '\r\n------%s--' % boundary
        bodyLen = len(bodyStart) + len(_bytearray) + len(bodyEnd)
        wCli.OpenRequest(contentType='multipart/form-data; boundary=----%s' % boundary,contentLength=bodyLen)
        wCli._write(bodyStart)
        wCli._write(_bytearray)
        wCli._write(bodyEnd)
        wCli.Close()
        print("upload completed , spend time:",(time.ticks_ms()-startTime)/1000,"sec" )

    def getImg(self,uploadFile):
        return self._getImg(uploadFile)

    def _getImg(self,uploadFile):
        saveFile = '_tmp_.jpg'
        url = "http://share.webduino.io/storage/_download/"+self.container+"/"+uploadFile
        print('loadImg:',url)
        if(len(uploadFile)>8 and
            ( uploadFile[:7]=='http://' or uploadFile[:7]=='https:/')):
            url = uploadFile
        wCli = MicroWebCli(url)
        try:
            f = open(saveFile,"wb")
            wCli.OpenRequest()
            buf  = bytearray(10240)
            resp = wCli.GetResponse()
            fileLen = resp.GetContentLength()
            if resp.IsSuccess() :
              readLen = 0
              bufLen = len(buf)
              while not resp.IsClosed() :
                if(fileLen-readLen >= bufLen):
                  x = resp.ReadContentInto(buf)
                else:
                  x = resp.ReadContentInto(buf,fileLen-readLen)
                readLen += x
                print("download:",readLen,'/',fileLen)
                if x < len(buf) :
                  buf = buf[:x]
                  f.write(buf)
                  break
                f.write(buf)
            else:
                print("download failure")
        finally:
            f.close()
            wCli.Close()
        img = webai.res.loadImg(saveFile)
        os.remove(saveFile)
        return img

    def getFile(self,url,saveFile):
        print('url:',url)
        wCli = MicroWebCli(url)
        try:
            f = open(saveFile,"wb")
            wCli.OpenRequest()
            buf  = bytearray(10240)
            resp = wCli.GetResponse()
            if resp.IsSuccess() :
              readLen = 0
              bufLen = len(buf)
              resp._socket.settimeout(1)
              fileLen = resp._socket.readline()
              fileLen = '0x'+fileLen[:-2].decode()
              fileLen = int(fileLen)
              resp._socket.readline()
              print("cntLen:",fileLen)
              readLen = 0
              bufLen = len(buf)
              while not resp.IsClosed() :
                if(fileLen-readLen >= bufLen):
                  x = resp.ReadContentInto(buf)
                else:
                  x = resp.ReadContentInto(buf,fileLen-readLen)
                readLen += x
                print("download:",readLen,'/',fileLen)
                if x < len(buf) :
                  buf = buf[:x]
                  f.write(buf)
                  break
                f.write(buf)
            else:
                print("download failure")
        finally:
            f.close()
            wCli.Close()

    def _putFile(self,srcFile,desFile,retry):
        startTime = time.ticks_ms()
        url = "http://share.webduino.io/_upload/"+self.container+"/"
        download_url = "http://share.webduino.io/storage/_download/"+self.container+"/"
        print("open post...")
        wCli = MicroWebCli(url, 'POST')
        print("open post...done")
        fileSize = os.stat('/flash/'+srcFile)[6]
        print("fileSize:",fileSize)
        boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')
        bodyStart = \
        '------%s\r\n'%boundary+\
        'Content-Disposition: form-data; name="file"; filename="'+desFile+'"\r\n'+\
        'Content-Type: application/octet-stream\r\n\r\n'
        bodyEnd =  '\r\n------%s--' % boundary
        bodyLen = len(bodyStart) + fileSize + len(bodyEnd)
        wCli.OpenRequest(contentType='multipart/form-data; boundary=----%s' % boundary,contentLength=bodyLen)
        wCli._write(bodyStart)
        try:
            f = open(srcFile,'rb')
            readLen = 0
            bufLen = 10240
            while True:
                readBlock = f.read(bufLen)
                readBytes = len(readBlock)
                readLen += readBytes
                wCli._write(readBlock)
                print('upload...',readLen,'/',fileSize)
                if(readLen == fileSize):
                    break;
        finally:
            f.close()
        wCli._write(bodyEnd)
        wCli.Close()
        print("upload completed , spend time:",(time.ticks_ms()-startTime)/1000,"sec" )
        return download_url+desFile

class esp8285:
    def init(speed=115200):
        if not hasattr(esp8285,'subs'):
            esp8285.subs = {}
        esp8285.subQueue = {}
        esp8285.wifiConnect = False
        esp8285.mqttConnect = False
        esp8285.reset()
        fm.register(19, fm.fpioa.GPIOHS0)
        esp8285.wifiStatusPin = GPIO(GPIO.GPIOHS0, GPIO.IN)
        esp8285.wifiStatusPin.irq(esp8285.state,GPIO.IRQ_BOTH)
        fm.register(27, fm.fpioa.UART2_TX, force=True)
        fm.register(28, fm.fpioa.UART2_RX, force=True)
        esp8285.uart = UART(UART.UART2, 115200, timeout=5000,read_buf_len=2048)
        esp8285.mqttCallbackProc = True
        esp8285.waitInitFinish()
        if not speed == 115200:
            esp8285.reset()
            esp8285.waitInitFinish()
            esp8285.setBaudrate(speed)
            esp8285.uart.deinit()
            del esp8285.uart
            esp8285.uart = UART(UART.UART2, speed, timeout=5000, read_buf_len=1024*20)
        esp8285.wlan = network.ESP8285(esp8285.uart)
        # uart_logger
        fm.register(18, fm.fpioa.UART3_RX)
        esp8285.uart_cb = UART(UART.UART3, 115200,timeout=5000,read_buf_len=10240,callback=esp8285.mqttCallback)
        while esp8285.uart_cb.any():
            esp8285.uart_cb.readline()
        esp8285.getInfo()
        gc.collect()
        esp8285.wifiConnect = esp8285.wifiStatusPin.value()==1
        print("esp8285 init OK [ ",esp8285.deviceID," ]")

    #'mqttConnect' : mqtt 連線
    #'subscribed'  : mqtt 已訂閱
    #'mqtt,${Topic},${Data}
    def mqttCallback(uarObj):
        if not esp8285.mqttCallbackProc or esp8285.wifiConnect == False:
            return
        try:
            gc.collect()
            while esp8285.uart_cb.any():
                myLine = uarObj.readline()
                if(myLine==None):
                    #print("read myLine:",myLine)
                    break
                #print("[mqttCallback]:",myLine)
                myLine = myLine.decode().strip()
                if(myLine=='mqttConnect'):
                    esp8285.mqttConnect = True
                    esp8285.processSubscriber()
                elif(myLine=='subscribed'):
                    pass
                elif(myLine[:4]=='mqtt'):
                    sub = myLine[5:]
                    topic = sub[:sub.find(',')]
                    data = sub[sub.find(',')+1:]
                    if topic in esp8285.subs:
                        esp8285.subs[topic](topic,data)
        except Exception as ee:
            print('mqttCallback err:',ee)

    def wifiReady():
        while esp8285.wifiConnect == False:
            time.sleep(0.25)

    def mqttReady():
        while esp8285.mqttConnect == False:
            time.sleep(0.25)

    def processSubscriber():
        for key in esp8285.subs:
            esp8285.sub(key)

    def setSub(topic,callback,includeID=False):
        if includeID:
            esp8285.subs[esp8285.deviceID+"/"+topic] = callback
        else:
            esp8285.subs[topic] = callback
        return esp8285.sub(topic,includeID)

    def sub(topic,includeID=False):
        esp8285.mqttReady()
        if includeID:
            mqttSetSub = 'AT+MQTT="sub","{mqttUID}/{topic}"'.format(mqttUID=esp8285.deviceID, topic=topic)
        else:
            mqttSetSub = 'AT+MQTT="sub","{topic}"'.format(topic=topic)
        return esp8285.at(mqttSetSub)

    def pub(topic,msg,includeID=False):
        esp8285.mqttReady()
        if includeID:
            mqttSetPush = 'AT+MQTT="push","{mqttUID}/{topic}","{msg}"'.format(mqttUID=esp8285.deviceID, topic=topic, msg=msg)
        else:
            mqttSetPush = 'AT+MQTT="push","{topic}","{msg}"'.format(topic=topic, msg=msg)
        return esp8285.at(mqttSetPush)

    def waitInitFinish():
        myLine = ''
        while not "init finish" in myLine:
            while not esp8285.uart.any():
                pass
            myLine = esp8285.uart.readline()

    def setBaudrate(speed):
        resp = esp8285.at("AT+UART_CUR="+str(speed)+",8,1,0,0")
        return resp == 'OK'

    def reset():
        pin8285 = 20
        fm.register(pin8285, fm.fpioa.GPIO0, force=True)
        reset = GPIO(GPIO.GPIO0, GPIO.OUT)
        reset.value(0)
        time.sleep(0.01)
        reset.value(1)
        #fm.unregister(pin8285)

    def connect(SSID="webduino.io", PWD="webduino"):
        err = 0
        while 1:
            try:
                esp8285.at('')
                esp8285.wlan.connect(SSID, PWD)
                return True
            except Exception:
                err += 1
                print("Connect AP failed, now try again")
                if err > 3:
                    #raise Exception("Conenct AP fail")
                    return False
        time.sleep(0.25)

    def updateState():
        esp8285.wifiConnect = esp8285.wifiStatusPin.value()==1

    def state(sw):
        esp8285.wifiConnect = sw.value()==1
        print('[esp8285] wifi state:',esp8285.wifiConnect,str(esp8285.wifiStatusPin.value()))

    def getInfo():
        resp = esp8285.at('AT+GMR')
        esp8285.deviceID = ''
        esp8285.ver = ''
        for item in resp:
            info = item.decode()
            if(info[:8]=='deviceID'):
                esp8285.deviceID = info[9:-2]
            if(info[:12]=='Bin version:'):
                esp8285.ver = info[12:-2]
        return resp

    def at(command, timeout=5000):
        esp8285.uart.write(command + '\r\n')
        #print('at command:',command)
        myLine = ''
        data = []
        startTime = time.ticks_ms()
        ifdata = True
        try:
            while not "OK" in myLine:
                while not esp8285.uart.any():
                    endTime = time.ticks_ms()
                    if((endTime-startTime) >= timeout):
                        ifdata = False
                        break
                if(ifdata):
                    myLine = esp8285.uart.readline()
                    data.append(myLine)
                    #print("myLine:",myLine)
                    if "ERROR" in myLine:
                        return "ERROR"
                    elif "busy s" in myLine:
                        return "busy sending"
                    elif "busy p" in myLine:
                        return "busy processing"
                else:
                    print("esp8285 timeout!",data)
                    return "esp8285 timeout"
            return data
        except Exception as e:
            print(e)

    def ota():
        webai.esp8285.mqttCallbackProc = False
        webai.esp8285.at('AT+CIUPDATE')    
        printLogVersion=False
        startTime=time.ticks_ms()
        endTime=0
        ifdata=True
        timeout=15000
        myLine=''
        # showMessage("check version")
        try:
            while  not  "Starting OTA" in myLine:
                while not webai.esp8285.uart_cb.any():
                    endTime=time.ticks_ms()
                    # print(endTime-startTime)
                    if((endTime-startTime)>=timeout):
                        ifdata=False
                        break
                if(ifdata):
                    myLine = webai.esp8285.uart_cb.readline()
                    print('ota:',myLine)
                    if "newVersion:O" in myLine:
                        printLogVersion=True
                        myLine="Starting OTA"
                        webai.showMessage("update,please wait...",x=-1,y=2.5,center=False,clear=True)
                        break
                    if "newVersion:X" in myLine or "newVersion : X" in myLine: 
                        # showMessage("version is new")
                        raise Exception("version is new")
                        #sys.exit()
                else:
                    print("timeout")
                    raise Exception('timeout')

            if not printLogVersion:
                webai.showMessage("update,please wait...",clear=True)
            startTime=time.ticks_ms()
            ifdata=True
            timeout=60000
            try:
                while  not  "init finish" in myLine:
                    while not webai.esp8285.uart_cb.any():
                        endTime=time.ticks_ms()
                        if((endTime-startTime)>=timeout):
                            ifdata=False
                            break
                    if(ifdata):
                        myLine = webai.esp8285.uart_cb.readline()
                        print('ota:',myLine)
                        if printLogVersion:
                            if "Written length" in myLine:
                                try:
                                    myLine=myLine.decode()
                                    myLine=myLine.rstrip()
                                    webai.showMessage(myLine)
                                except Exception as e:
                                    print('ota exception:',e)
                                    sys.print_exception(e)
                    else:
                        print("timeout")
                        webai.showMessage("update error",clear=True)
                        raise Exception('timeout')
                webai.showMessage("succeeded,reboot...",clear=True)
                print("succeeded")
                import machine
                machine.reset()
            except Exception as e:
                print("update error, exception:",e)
                sys.print_exception(e)
                webai.showMessage("update error",clear=True)
                time.sleep(2)
        except Exception as f:
            print("update error , exception:",f)
        finally:
            webai.esp8285.mqttCallbackProc = True
            gc.collect()

class mqtt:

    def sub(topic,callback,includeID = False):
        esp8285.setSub(topic,callback,includeID)

    def pub(topic,msg,includeID = False):
        esp8285.pub(topic,msg,includeID)

class btn:
    def __init__(self,name,pin,fpioaGPIO,gpio):
        btn.UP = 0
        btn.DOWN = 1
        btn.CLICK = 2
        btn.LONG_PRESS = 3
        if not hasattr(btn,'btnStateQueue'):
            btn.btnStateQueue = {}
        fm.fpioa.set_function(pin, fpioaGPIO)
        self.idx = 0
        self.name = name
        self.pin = 'Pin('+str(pin)+')'
        btn.btnStateQueue[self.pin] = []
        self.eventHandler = []
        self.btn = GPIO(gpio, GPIO.IN)
        self.btn.irq(btn.process,GPIO.IRQ_BOTH)
        self.btnState = btn.DOWN if(self.btn.value()==0) else btn.UP
        self.longPressCheck = False
        self.lastPin = {'value':self.btn.value(),'time':0}
        _thread.start_new_thread(self.run,())

    def process(pinObj):
        info = {'value':pinObj.value(),'time':time.ticks_ms()}
        btn.btnStateQueue[str(pinObj)].append(info)

    def run(self):
        while True:
            stateList = btn.btnStateQueue[self.pin]
            if len(stateList) > 0:
                pin = stateList[0]
                del stateList[0]
                if pin['value'] == self.lastPin['value']:
                    continue #skip bounce rate
                pressTime = pin['time'] - self.lastPin['time']

                if pin['value'] == 0: # press
                    for evt in self.eventHandler:
                        btn.handlerBtnCallback(evt,self.name,btn.DOWN)
                    self.longPressCheck = True
                    self.longPressTime = pin['time']

                if pin['value'] == 1 and self.lastPin['time']!=0 : # up
                    self.longPressCheck = False
                    for evt in self.eventHandler:
                        btn.handlerBtnCallback(evt,self.name,btn.CLICK)
                self.lastPin = pin

            if self.longPressCheck and self.btn.value()==0 and (time.ticks_ms() - self.longPressTime)>500:
                for evt in self.eventHandler:
                    btn.handlerBtnCallback(evt,self.name,btn.LONG_PRESS)
                self.longPressCheck = False
                self.lastPin['time'] = 0
            time.sleep(0.001)

    #
    def handlerBtnCallback(evt,btnName,btnState):
        try:
            evt(btnName,btnState)
        except Exception as e:
            print(e)

    def state(self):
        self.btnState = btn.DOWN if(self.btn.value()==0) else btn.UP
        return self.btnState

    def addBtnEventListener(self,eventFunc):
        self.eventHandler = [] # Only supports one trigger event
        self.eventHandler.append(eventFunc)

    def removeBtnEventListener(self,eventFunc):
        idx = 0
        findIdx = -1
        for evt in self.eventHandler:
            if(evt == eventFunc):
                findIdx = idx
                break

class fs:
    def reset():
        #webai.cloud.download('https://share.webduino.io/storage/download/0422_121635.093_m_0x400000_maixpy_spiffs.img',address=0x400000,img=False,redirect=True,showProgress=True)
        webai.cloud.download('https://share.webduino.io/storage/download/0513_031833.705_m_0x400000_maixpy_spiffs.img',address=0x400000,img=False,redirect=True,showProgress=True)

    def ls():
        import os
        a = os.listdir()
        for file in a:
            print(file)

    def cat(file):
        import os
        lines = ''
        with open(file,"r") as f:
            lines = f.readlines()
        for line in lines:
            print(line.replace('\n',''))

    def load(file):
        import os
        code = ''
        with open(file,"r") as f:
            lines = f.readlines()
        for line in lines:
            code = code + line
        return code

    def save(file,src):
        if src.__class__.__name__ is 'Image':
            webai.img = src
            webai.img.save(file)
        else:
            try:
                f = open(file,'w')
                f.write(src)
            finally:
                f.close()
                del f
                gc.collect()

    def size(file):
        return os.stat(file)[6]

    def rm(file):
        import os
        if(file=="*"):
            a = os.listdir()
            for filename in a:
                os.remove(filename)
        else:
            os.remove(file)

    def exists(file):
        try:
            fs.size(file)
            return True
        except:
            return False

class mem:
    def info():
        from Maix import utils
        import KPU as kpu
        print("[ FirmwareType:",fw.fwType," v1.0]")
        print("heap size:",int(utils.gc_heap_size()/1024),"KB")
        print("mem_free:",int(gc.mem_free()/1024),"KB")
        print("memtest:",kpu.memtest())

    def heap(n):
        from Maix import utils
        utils.gc_heap_size(n*1024)
        import machine
        machine.reset()

class fw:
    def init():
        fw.fwType = None
        fw.kboot_fw_flag = 0x1ffff

    def now(fwType=None):
        if(fwType!=None):
            fw.fwType = fw.get()
        return fw.fwType

    def get():
        from Maix import utils
        fwType = utils.flash_read(fw.kboot_fw_flag,1)[0]
        return "min" if fwType==1 else "std"

    def set(name='min'):
        import machine,time
        from Maix import utils
        #time.sleep(0.25)
        if name == 'min' or name == 'mini':
            utils.flash_write(fw.kboot_fw_flag,bytearray([1]))
            if fw.now() != 'min':
                print("<<<<< wait to restart !!!!! >>>>>")
                webai.reset()
                print("<<<<< wait to restart OK >>>>>")
        elif name == 'std':
            utils.flash_write(fw.kboot_fw_flag,bytearray([0]))
            if fw.now() != 'std':
                print("<<<<< wait to restart @@@@@ >>>>>")
                webai.reset()
                print("<<<<< wait to restart OK >>>>>")
        else:
            raise Exception("wrong fw select !!!")


 #   _____                          _                  
 #  / ____|                        | |                 
 # | (___    _ __     ___    __ _  | | __   ___   _ __ 
 #  \___ \  | '_ \   / _ \  / _` | | |/ /  / _ \ | '__|
 #  ____) | | |_) | |  __/ | (_| | |   <  |  __/ | |   
 # |_____/  | .__/   \___|  \__,_| |_|\_\  \___| |_|   
 #          | |                                        
 #          |_|                                        

class speaker:
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

    def setVolume(self, volume):
        self.volume = volume

    def playAsync(self, folder='flash',filename=None, sample_rate=11025):
        _thread.start_new_thread(self.play,(folder,filename,sample_rate))

    def play(self, folder='flash',filename=None, sample_rate=11025):
        if hasattr(ASR, 'sr'):
            webai.asr.stop()

        if(len(filename.lower())<4 or filename.lower()[-4:] != '.wav'):
            filename = filename + ".wav"
        self.wav_dev.set_sample_rate(sample_rate)
        player = self.audio.Audio(path="/"+folder+"/"+filename)
        player.volume(self.volume)
        player.play_process(self.wav_dev)
        esp8285.at("AT+SPEAKER=1")
        while True:
           ret = player.play()
           if ret == None:
               print("format error")
               break
           elif ret == 0:
               break
        player.finish()

        if hasattr(ASR, 'sr'):
            webai.asr.run()

        esp8285.at("AT+SPEAKER=0")

    def start(self, folder="", filename=None, sample_rate=48000):
        if(filename != None):
            if folder=="":
                cwd = SYSTEM_DEFAULT_PATH
                if cwd == "flash":
                    folder = "flash"
                else:
                    folder = "sd"
            self.wav_dev.set_sample_rate(sample_rate)
            player = self.audio.Audio(path="/"+folder+"/"+filename+".wav")
            player.volume(self.volume)
            player.play_process(self.wav_dev)
            esp8285.at("AT+SPEAKER=1")
            while True:
               ret = player.play()
               if ret == None:
                   print("format error")
                   break
               elif ret == 0:
                   break
            player.finish()
            esp8285.at("AT+SPEAKER=0")
        else:
            print("filename error")

class cmdProcess:
    def load():
        print('[cmdProcess] load')
        if webai.esp8285.wifiConnect:
            print("report boot")
            cmdProcess.reportBoot()
            print("report boot...OK")

        json = webai.cfg.remove('cmd')
        #print(">>>> cmd >>>>>>",str(json))
        if not json==None:
            cmdProcess.msgParser(json)
            return 1
        else:
            return 0

    def sub(topic,cmdData):
        webai.img = None
        time.sleep(0.1)
        gc.collect()
        if(cmdData[:1]=='"' and cmdData[-1:]=='"'):
            cmdData = cmdData[1:-1]
        # specical process _DEPLOY    
        if(cmdData[:9]=='_DEPLOY/h'):
            #print("ignore! skip command")
            return
        #print("cmdData:",cmdData)  
        if cmdData[:8]=='_DEPLOY/' or cmdData[:5]=='_RUN/' or cmdData[:8]=='_TAKEPIC' or cmdData[:15]=='_DOWNLOAD_MODEL' or cmdData[:14]=='_DOWNLOAD_FILE':
            cmdProcess.saveCmd(cmdData)
            

    '''
    儲存命令前，先判斷是否有指定romType，有的話就進行設定 romType
    '''
    def saveCmd(cmdData):
        print("saveCmd:",cmdData)
        webai.cfg.put("cmd",cmdData)
        time.sleep(0.25)
        gc.collect()
        webai.mem.info()
        if webai.esp8285.wifiConnect:
            print("report save ok")
            cmdProcess.reportSaveOK()
            print("cmdProcess:",cmdData)
            
        if(cmdData[:8]=='_DEPLOY/'):
            print("_DEPLOY/",cmdData[8:])
            info = ujson.loads(cmdData[8:])
            print("set fw type:",info)
            if 'rom' in info:
                romType = info['rom'] # std or min
                print("!!!!! set romType=%s !!!!!"%romType)
                webai.fw.set(romType)

        elif(cmdData[:5]=='_RUN/'):
            info = ujson.loads(cmdData[5:])
            if 'rom' in info:
                romType = info['rom'] # std or min
                print("!!!!! set romType=%s !!!!!"%romType)
                webai.fw.set(romType)

            if 'args' in info:
                if info['args'] is 'voice':
                    print("!!!!! voice use romType=std !!!!!")
                    webai.fw.set('std')
                elif info['args'] in ['faceMask', 'face', 'monsters', 'yoloCar', 'mqttCar']:
                    print("!!!!! %s use romType=mini !!!!!"%info['args'])
                    webai.fw.set('mini')
                else:
                    print("!!!!! %s is not built-in python code"%info['args'])

        elif(cmdData[:8]=='_TAKEPIC'):
            webai.imgCache.clear()
            romType = 'std'
            print("!!!!! set romType=%s !!!!!"%romType)
            webai.fw.set(romType)

        webai.reset()
        #for test
        #cmdProcess.init()

    def msgParser(msg):
        #print("msgParser:",msg)
        if(msg[:1]=='[' and msg[-1:]==']'):
            jsonArray = ujson.loads(msg)
            for cmd in jsonArray:
                cmdProcess.exec(cmd)
        else:
            cmdProcess.exec(msg)

    def exec(msg):
        #print("exec cmd:",msg)
        cmd = msg[:msg.find('/')]
        jsonData = msg[msg.find("/")+1:]
        jsonArray = ""
        if len(jsonArray) != 0:
            jsonArray = ujson.loads(jsonData)
        func = getattr(cmdProcess,cmd)
        func(jsonData)
        func = None
        gc.collect()

    def reportSaveOK():
        webai.lcd.clear()
        webai.draw_string(100,90,"running...",scale=2,x_spacing=6)
        webai.mqtt.pub("PONG","saveCmd",includeID=True)

    def reportBoot():
        webai.mqtt.pub("PONG","boot",includeID=True)

    def _SAVE_FILE(base64):
        import ubinascii
        data = ubinascii.a2b_base64(base64)
        data = data.decode()
        filename = data[:data.find(',')]
        code = data[data.find(',')+1:]
        try:
            f = open(filename,'w')
            f.write(code)
        finally:
            f.close()
        print("_SAVE:",filename," ok")

    def _RUN(info):
        cmdObj = ujson.loads(info)
        webai.cfg.remove('cmd')
        pythonFile = cmdObj['args']
        try:
           exec(webai.res.loadPy(pythonFile))
        except Exception as e:
            print('file not found', e)
        while True:
            time.sleep(1)

    def _DEPLOY(info):
        # get pythonCode to main.py
        info = ujson.loads(info)
        print("DEPLOY CMD:",info)

        # usb 傳輸
        # 已透過 mpfshell 覆蓋 main.py， 直接預設執行
        if info['url'] == 'local':
            return

        # server 需改成提供 http:// 方式
        url = info['url'].replace('https://','http://')
        webai.cloud.download(url,img=False,redirect=False,filename='/flash/main.py')

    def _TAKEPIC_YOLO(jsonArray):
        print("_TAKEPIC_YOLO>",jsonArray)


    def _TAKEPIC_MOBILENET(strObj):
        jsonObj = ujson.loads(strObj)
        files = []
        completed = False
        dsname = jsonObj['dsname']
        count = int(jsonObj['count'])
        url = jsonObj['url']
        url = url.replace('https://','http://')
        hashKey = jsonObj['hashKey']
        flip = int(jsonObj['flip'])
        webai.initCamera(flip)
        self_taken = flip
        print("upload:",url)
        webai.initCamera(flip) #0:gigo , 1:webai
        mx = 48
        my = 10
        idx = 1
        rType = 0
        jpg = None
        snapshot = False
        rectType = [ [mx+0,my+0,224,224],
                     [mx+30,my+30,164,164],
                     [mx+40,my+40,144,144],
                     [mx+50,my+50,124,124],
                     [mx+60,my+60,104,104]]

        def upload(speed=10):
            try:
                atResp = webai.esp8285.at('AT')
                print("wifi checked:[",atResp,"]")
                if atResp == 'esp8285 timeout':
                    webai.esp8285.reset()
                    webai.esp8285.init(115200*speed)
                    time.sleep(3)
            except:
                print("連線異常！嘗試重新連線...")
                webai.esp8285.reset()
                webai.esp8285.init(115200*speed)
                time.sleep(1)
                
            #webai.draw_string(70,80,"Uploading...        ",scale=2,x_spacing=6)
            try:
                def cb(now,all):
                    if not webai.img == None:
                        webai.img.clear()
                    webai.draw_string(70,80,"Uploading...       ",scale=2,img=webai.img,lcd_show=False,x_spacing=6)
                    webai.draw_string(95,130,"("+str(now)+"/"+str(all)+")",scale=2,img=webai.img)
                    print(now,'/',all)
                print("files:",files)
                state = webai.cloud.uploadPic(url,hashKey,dsname,files,cb)
                time.sleep(0.001)
                gc.collect()
                webai.imgCache.clear()
                webai.img = image.Image()
                webai.draw_string(110,80,"上傳完成  ",scale=2,img=webai.img,lcd_show=False)
                webai.draw_string(95,130,"請重新開機  ",scale=2,img=webai.img)
                return True
            except Exception as ee:
                print('--- Caught Exception ---')
                import sys
                sys.print_exception(ee)
                print('----------------------------')
                time.sleep(0.001)
                gc.collect()
                webai.img = image.Image()
                webai.draw_string(110,80,"上傳失敗  ",scale=2,img=webai.img,lcd_show=False)
                webai.draw_string(110,130,"重新嘗試  ",scale=2,img=webai.img)
                webai.img = None
                gc.collect()
                return False


        def onclick(name,state):
            nonlocal idx,count,completed,snapshot,rectType,rType
            if completed:
                return
            if(name=='btnL' and state == 1):
                snapshot = True
                if(idx == count):
                    completed = True
            if name=='btnR' and state == 1:
                rType = (rType + 1) % len(rectType)

        webai.addBtnListener(onclick)
        clock = time.clock()

        while(True):
            clock.tick()
            time.sleep(0.001)
            rx = rectType[rType][0]
            ry = rectType[rType][1]
            rw = rectType[rType][2]
            rh = rectType[rType][3]
            webai.img = webai.snapshot()
            snap = "0"+str(idx)+" " if idx < 10 else str(idx)+" "
            end = "0"+str(count)+" " if count < 10 else str(count)+" "
            #jpg = webai.img.copy(roi=(48,16,48+224,16+224))
            webai.draw_string(25,5,snap,img=webai.img,scale=2,x_spacing=2,lcd_show=False)
            webai.draw_string(35,35,"/",img=webai.img,scale=2,x_spacing=2,lcd_show=False)
            webai.draw_string(25,65,end,img=webai.img,scale=2,x_spacing=2,lcd_show=False)
            filename = "take"+str(idx)+"-"+str(rx)+"_"+str(ry)+"_"+str(rw)+"_"+str(rh)+"_320_240.jpg"
            if snapshot:
                startTime = time.ticks_ms()
                webai.img = webai.snapshot()
                #print('save>>>',filename,webai.imgCache.save(filename,webai.img))
                files.append(filename)
                webai.img = None
                gc.collect()
                webai.img = webai.snapshot()
                webai.img.draw_rectangle(rx,ry,rw,rh,(255,100,100),2,False)
                time.sleep(0.25)
                webai.img.draw_rectangle(rx,ry,rw,rh,(255,100,100),2,False)
                webai.img.draw_string(90,215,"save...",scale=2)
                webai.img.draw_string(190,215,"    OK      ",scale=2)
                webai.show(img=webai.img)
                time.sleep(0.1)
                gc.collect()
                idx = idx + 1
                snapshot = False
            if completed:
                break
            #jpg = None
            gc.collect()
            webai.img.draw_rectangle(rx,ry,rw,rh,(255,255,255),2,False)
            webai.img.draw_cross(320//2,240//2,size=10,thickness=2)
            #webai.img.draw_string(10,10,"fps:"+str(clock.fps()))
            webai.show(img=webai.img)

        if not upload(speed=10):
            print("upload retry...1")
            if not upload(speed=5):
                print("upload retry...2")
                if not upload(speed=3):
                    print("upload retry...3")
                    while True:
                        print("upload retry.....")
                        if upload(speed=1):
                            break
                        
        while True:
            time.sleep(1)

    #{ "fileName":"k-model",
    #  "modelType":"mobileNet",
    #  "url":"http://vision-api.webduino.io/ml_models/5c129ef0-911f-11eb-83e1-536e68f620ec/model.kmodel",
    #  "modelAddress":"0xD40000"}
    def _DOWNLOAD_MODEL(strObj):
        jsonObj = ujson.loads(strObj)
        print("_DOWNLOAD_MODEL>",jsonObj)
        webai.cloud.download(jsonObj['url'],address=jsonObj['modelAddress'],img=False,redirect=True,showProgress=True)
        webai.img = image.Image()
        webai.draw_string(110,80,"下載完成  ",scale=2,img=webai.img,lcd_show=False)
        webai.draw_string(95,130,"請重新開機  ",scale=2,img=webai.img)
        while True:
            time.sleep(1)

    def _DOWNLOAD_FILE(jsonArray):
        print("_DOWNLOAD_FILE>",jsonArray)

class QRCodeRunner:

    # {"cmd":"run","args":"yoloCar"}
    # {"function":"wifi","ssid":"webduino.io","password":"webduino"}
    def scan():
        jsonData = QRCodeRunner.getCMD()
        code = ujson.loads(jsonData)
        if 'cmd' in code:
            cmd = code['cmd']
            if(cmd=='run'):
                cmdData = '_RUN/'+jsonData
                webai.cmdProcess.saveCmd(cmdData)

        if 'function' in code:
            func = code['function']
            if(func=='wifi'):
                ssid = code['ssid']
                pwd  = code['password']
                webai.cfg.put('wifi',{'ssid':ssid,'pwd':pwd})
                machine.reset()

    def run(pythonFile):
        webai.cmdProcess._RUN(pythonFIle)

    def getCMD():
        px = 0
        py = -15
        lt_x = 20
        lt_y = 20
        code = ""
        while True:
            webai.camera.set_hmirror(True)
            webai.img = webai.camera.snapshot()
            code = CodeScanner.findQRCode(webai.img)
            webai.camera.set_hmirror(False)
            webai.img = webai.camera.snapshot()
            if code=='':
                code = CodeScanner.findQRCode(webai.img)
            if not code=='':
                break
            #左上
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,98+lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,8+lt_y+py,48+lt_x+px,48+lt_y+py,0xFFFF,2)
            #右上
            webai.img.draw_line(222-lt_x+px,8+lt_y+py,272-lt_x+px,8+lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,8+lt_y+py,272-lt_x+px,48+lt_y+py,0xFFFF,2)
            #左下
            webai.img.draw_line(48+lt_x+px,232-lt_y+py,98+lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(48+lt_x+px,192-lt_y+py,48+lt_x+px,232-lt_y+py,0xFFFF,2)
            #右下
            webai.img.draw_line(222-lt_x+px,232-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_line(272-lt_x+px,192-lt_y+py,272-lt_x+px,232-lt_y+py,0xFFFF,2)
            webai.img.draw_string(90,208,"Scan QRCode",scale=2,x_spacing=2)
            webai.show(img=webai.img)
        #webai.img = None
        #gc.collect()
        return code


class ASR:
    model_address = 0x1329C
    model_size = 5256 + 2 # bytes
    dtw_threshold = 350
    recording = False

    def init(sample_rate=16000, fromRes=False, size=10):
        webai.fw.set('std')

        import time, _thread
        from Maix import GPIO, I2S
        from fpioa_manager import fm
        from speech_recognizer import isolated_word

        fm.register(12, fm.fpioa.I2S0_IN_D0, force=True)
        fm.register(13, fm.fpioa.I2S0_WS, force=True)
        fm.register(14, fm.fpioa.I2S0_SCLK, force=True)
        rx = I2S(I2S.DEVICE_0)
        rx.channel_config(rx.CHANNEL_0, rx.RECEIVER,
                          align_mode=I2S.STANDARD_MODE)
        rx.set_sample_rate(sample_rate)
        ASR.sr = isolated_word(dmac=2, i2s=I2S.DEVICE_0, size=size,
                                         shift=1)  # maix bit set shift=1
        ASR.sr.set_threshold(0, 0, 10000)
        ASR.asrList = [None]*size
        ASR.cbkList = [None]*size
        ASR.load(fromRes)
        _thread.start_new_thread(ASR.recognize, ())

    def set_dtw_threshold(dtw_threshold=350):
        ASR.dtw_threshold = dtw_threshold

    def run():
        ASR.sr.run()

    def stop():
        ASR.sr.stop()

    def record(index, name):
        # 0 Init
        # 1 Idle
        # 2 Ready
        # 3 MaybeNoise
        # 4 Restrain
        # 5 Speak
        # 6 Done
        ASR.recording = True
        while True:
            if ASR.sr.Done == ASR.sr.record(index):
                (frm_len, frm_data) = ASR.sr.get(index)
                ASR.asrList[index] = [name, frm_len]
                webai.cfg.put('asr', ASR.asrList)
                ASR.save(index, frm_data)
                print('save', index, 'ok')
                ASR.recording = False
                del frm_len, frm_data
                break
            state = ASR.sr.state()
            # if ASR.sr.Speak != state:
            #      print('state', state)
            time.sleep_ms(1)

    def load(fromRes=False):
        size = ASR.sr.size()
        # load built-in asr model
        if fromRes:
            ASR.asrList = [['0', 165], ['1', 120], ['2', 173], ['3', 177], ['4', 114], ['5', 179], ['6', 86], ['7', 94], ['8', 163]]
            print('load asr list', ASR.asrList)
            for index in range(len(ASR.asrList)):
                if ASR.asrList[index]:
                    frm_len = ASR.asrList[index][1]
                    frm_data = webai.res.loadAsr(index)
                    ASR.sr.set(index, (frm_len, frm_data))
                    del frm_len, frm_data
                    time.sleep(0.01)
                    gc.collect()
        else:
            ASR.asrList = webai.cfg.get('asr')
            print('load asr list', ASR.asrList)
            if ASR.asrList:
                asrListLen = len(ASR.asrList)
                for index in range(asrListLen):
                    if ASR.asrList[index]:
                        try:
                            frm_len = ASR.asrList[index][1]
                            frm_data = webai.cfg.loadBlobAddr(ASR.model_address + index * ASR.model_size)
                            ASR.sr.set(index, (frm_len, frm_data))
                            del frm_len, frm_data
                            time.sleep(0.01)
                            gc.collect()
                        except Exception as e:
                            print('load', index, 'error', e)
                            ASR.asrList[index] = None
            else:
                print('asr key no exist')
                ASR.asrList = [None]*10

    def save(index, frm_data):
        webai.cfg.saveBlobAddr(ASR.model_address + index * ASR.model_size, frm_data)

    def recognize():
        while True:
            if not ASR.recording:
                if ASR.sr.Done == ASR.sr.recognize():
                    result = ASR.sr.result()
                    if result:
                        model_index = result[0]
                        dtw = result[1]
                        callback = ASR.cbkList[model_index]
                        if callback and dtw < ASR.dtw_threshold:
                            callback()
            time.sleep_ms(100)

    def addASRListener(index, callback=None): # registry callback
        ASR.cbkList[index] = callback

class io:
    PWMPINUSE=[]
    PINUSE=[]
    PINIO=[]
    def init():
        __class__.PULL_UP = GPIO.PULL_UP
        __class__.PULL_DOWN = GPIO.PULL_DOWN
        __class__.PULL_NONE = GPIO.PULL_NONE
    
    def pin(PIN,pull_mode=GPIO.PULL_UP):
        if type(PIN) == int:
            PIN = str(PIN)
        PIN=webai.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)]
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,pull_mode)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO
    def read(PIN,pull_mode=GPIO.PULL_UP):
        if type(PIN) == int:
            PIN = str(PIN)
        PIN=webai.fpioaMapGPIO[PIN]
        if PIN in __class__.PINUSE:
            return __class__.PINIO[__class__.PINUSE.index(PIN)].value()
        else:
            fm.register(PIN[0], PIN[1],force=True)
            IO=GPIO(PIN[2],GPIO.IN,pull_mode)
            __class__.PINUSE.append(PIN)
            __class__.PINIO.append(IO)
            return IO.value()
    def write(PIN,PWMMODE=False,PWM_FREQ=50,VALUE=0):
        if type(PIN) == int:
            PIN = str(PIN)
        if PWMMODE:
            USER_PWM_LIST_COUNT=len(webai.USER_PWM_LIST)
            if USER_PWM_LIST_COUNT<8:
                if USER_PWM_LIST_COUNT<4:
                    BLOCKLY_SYSTEM_TIMER=0
                else:
                    BLOCKLY_SYSTEM_TIMER=1
                PIN=webai.fpioaMapGPIO[PIN]
                if PIN in __class__.PWMPINUSE:
                    #print("old",__class__.PWMPINUSE.index(PIN))
                    #print(__class__.PWMPINUSE)
                    webai.USER_PWM_LIST[__class__.PWMPINUSE.index(PIN)].duty(VALUE)
                else:
                    #print("new")
                    TIMER=Timer(BLOCKLY_SYSTEM_TIMER,USER_PWM_LIST_COUNT%4, mode=Timer.MODE_PWM)
                    Io_PWM = PWM(TIMER,freq=PWM_FREQ, duty=VALUE, pin=PIN[0])
                    __class__.PWMPINUSE.append(PIN)
                    webai.USER_PWM_LIST.append(Io_PWM)
                #print("USER_PWM_LIST_COUNT:"+str(USER_PWM_LIST_COUNT))
            else:
                raise Exception("Io error")
        else:
            PIN=webai.fpioaMapGPIO[PIN]
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


class webai:

    def wifi(ssid='KingKit_2.4G',pwd='webduino'):
        webai.cfg.put('wifi',{'ssid':ssid,'pwd':pwd})      

    def init(camera=True,speed=20):
        webai.btnHandler = []
        if hasattr(webai,'initialize'):
           return
        webai.fpioaMapGPIO={
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
        webai.img = None
        webai.debug = False
        webai.speed = speed
        webai.initialize = True
        webai.init_camera_ok = False
        webai.camera = sensor
        webai.lcd = lcd
        _res_.init()
        webai.res = _res_        
        fw.init()
        cfg.init()
        fw.now(fwType='qry')
        a = time.ticks()
        esp8285.init(115200*webai.speed)
        webai.esp8285 = esp8285
        webai.speaker = speaker()
        if cfg.get('cmd') == None:
            webai.logo()
        #link obj
        webai.cmdProcess = cmdProcess
        webai.cmdSerial = cmdSerial
        webai.io = io
        webai.io.init()
        webai.cfg = cfg
        webai.fs = fs
        webai.fw = fw
        webai.mem = mem
        webai.mqtt = mqtt
        webai.deviceID = esp8285.deviceID
        webai.asr = ASR
        webai.imgCache = imgCache

        if camera:
            print("init camera...")
            webai.initCamera()
            print("init camera done.")

        webai.btnL = btn("btnL",7,fm.fpioa.GPIOHS7,GPIO.GPIOHS7)
        webai.btnR = btn("btnR",16,fm.fpioa.GPIOHS16,GPIO.GPIOHS16)
        webai.btnL.addBtnEventListener(webai.onBtn)
        webai.btnR.addBtnEventListener(webai.onBtn)
        webai.cloud = cloud()
        webai.cloud.container = esp8285.deviceID
        webai.ver = os.uname()[6]
        gc.collect()
        time.sleep(0.01)
        gc.collect()
        print('')
        print('webai init completed.')
        print('spend time:', (time.ticks()-a)/1000,'sec')
        print('')
        webai.mem.info()
        # webai.clear()

    def clear():
        if not webai.img == None:
            webai.img.clear()
        webai.lcd.clear()

    def adc():
        return int(webai.esp8285.at("AT+SYSADC")[0].decode().strip())

    def showMessage(msg, x=-1, y=0, center=True, clear=False):
        if msg=="":
            msg=" "
        if clear:
            webai.lcd.clear()
        if center:
            webai.lcd.draw_string(int(320-len(msg)*8)//2, 112, msg, webai.lcd.WHITE)
        else:
            if x == -1:
                webai.lcd.draw_string(int(320-len(msg)*8)//2, int(224/7*y), msg, webai.lcd.WHITE)
            else:
                webai.lcd.draw_string(x, int(224/7*y), msg, webai.lcd.WHITE)

    def state():
        print("")
        print("device ID:",webai.deviceID)
        print("wifi state:",webai.esp8285.wifiConnect)
        print("mqtt state:",webai.esp8285.mqttConnect)
        print("")

    def draw_string(x, y, text, img=None, color=(255,255,255), scale=5,x_spacing=None, mono_space=False,lcd_show=True):
        clear = False
        if webai.img == None:
            gc.collect()
            webai.img = webai.res.loadImg('bg.jpg')
            clear = True
        if x_spacing==None:
            x_spacing = 8*scale
        image.font_load(image.UTF8, 16, 16, webai.res.font())
        webai.img.draw_string(x, y, text, scale=scale, color=color, x_spacing=x_spacing, mono_space=mono_space)
        image.font_free()
        if lcd_show:
            webai.lcd.display(webai.img)
        if clear:
            webai.img = None
            gc.collect()

    def logo():
        try:
            webai.img = webai.res.loadImg('logo.jpg')
            lcd.display(webai.img)
        except:
            print("logo image error")    
        finally:
            webai.img = None
        gc.collect()
        webai.speaker.setVolume(20)
        webai.speaker.playAsync(folder="flash", filename='logo', sample_rate=22050)

    def reset():
        print(" reset by machine !!!")
        #time.sleep(2)
        machine.reset()

    def resetESP8285():
        esp8285.init(115200*webai.speed)

    def connect(ssid="webduino.io",pwd="webduino"):        
        return esp8285.connect(ssid,pwd)

    def initCamera(flip):
        if not webai.init_camera_ok:
            webai.camera.reset()
            webai.camera.set_vflip(flip) #鏡頭上下翻轉
            webai.camera.set_pixformat(webai.camera.RGB565)
            webai.camera.set_framesize(webai.camera.QVGA) # 320x240
            webai.camera.skip_frames(30)
            webai.init_camera_ok = True

    def onBtn(name,state):
        for evt in webai.btnHandler:
            if(webai.btnL.state() == 1 and webai.btnR.state() == 1):
                state = 3
            try:
                evt(name,state)
            except Exception as e:
                print("onBtn exception:",e)

    def addBtnListener(evt):
        webai.btnHandler = [] # Only supports one trigger event
        webai.btnHandler.append(evt)

    def run(file):
        cmdProcess._RUN(file)

    def snapshot():
        if not webai.init_camera_ok:
            print("init camera...")
            webai.initCamera(True)
            print("init camera done.")        
        webai.img = None
        time.sleep(0.001)
        gc.collect()
        webai.img = webai.camera.snapshot()
        return webai.img
        
    def show(url="",file="logo.jpg",img=None):
        #magic delay , for thread switch!
        time.sleep(0.01) 
        if img != None:
            webai.lcd.display(img)
        else:
            if len(url)>0:
                img = webai.cloud.getImg(url)
            elif len(file)>0:
                img = webai.res.loadImg(file)
            webai.lcd.display(img)

    def log(enable=True,content=None):
        if enable:
            print(content)

webai.init(camera=False,speed=5)