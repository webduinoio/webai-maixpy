import gc
import uos
import json
from Maix import config

class board_info:
    def set(key, value=None):
        return setattr(__class__, key, value)

    def all():
        return dir(__class__)

    def get():
        return getattr(__class__, key)

    def load(__map__={}):
        for k, v in __map__.items():
            __class__.set(k, v)


webAIVersion = uos.uname()
configFile = {
    "type": "ai",
    "version": webAIVersion[5],
    "board_info": {
        'P0': 24,
        'P1': 25,
        'P2': 26,
        'P3': 6,
        'P4': None,  # esp adc
        'P5': 7,
        'P6': 8,
        'P7': 9,
        'P8': 10,
        'P9': 11,
        'P10': 22,
        'P11': 16,
        'P12': 23,  # LCDPWM?
        'P13': 0,
        'P14': 1,
        'P15': 2,
        'P16': 3,
        'P19': 17,
        'P20': 15,
        'UARTHS_RX': 4,
        'UARTHS_TX': 5,
        'MIC_I2S_IN': 12,
        'MIC_I2S_WS': 13,
        'MIC_I2S_SCLK': 14,
        'BOOT': 16,
        'I2C_SDA': 15,
        'I2C_SCLK': 17,
        'ESP_UART1RX': 18,
        'ESP_UART1TX': 19,
        'ESP_RST': 20,
        'ESP_XPD': 21,
        'LCDPWM': 23,
        'ESP_UART0RX': 27,
        'ESP_UART0TX': 28,
        'SPK_I2S_OUT': 33,
        'SPK_I2S_WS': 34,
        'SPK_I2S_SCLK': 35
    }
}
cfg = json.dumps(configFile)
#print(cfg)
try:
    with open('/flash/config.json', 'rb') as f:
        tmp = json.loads(f.read())
        if tmp["version"] != configFile["version"]:
            raise Exception('config.json no exist')
except Exception as e:
    with open('/flash/config.json', "w") as f:
        f.write(cfg)
    try:
        uos.remove('/flash/boot.py')
    except Exception as f:
        print("del /flash/boot.py")
    try:
        uos.remove('/sd/boot.py')
    except Exception as f:
        print("del /sd/boot.py")
    uos.sync()
    import machine
    machine.reset()

print("init board_info")
gc.collect()
print(config.__init__())
tmp = config.get_value('board_info', None)
if tmp != None:
    board_info.load(tmp)
else:
    print('[Warning] Not loaded from /flash/config.json to board_info.')
    board_info.load(configFile)
del webAIVersion, configFile, cfg



import os,image
import ubinascii
from microWebCli import MicroWebCli


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


class cloud:
    container = 'user'
    def downloadModel(self,url,fileName):
        http = MiniHttp()
        block_size = 20480
        start = time.ticks()
        saveFile=open('/flash/'+fileName,'w')
        filename, file_pos, filesize, errCount = b'', 0, 0, 0
        while True:
            try:
                if http.raw is None:
                    http.connect(url)
                    print("http connect.")
                else:
                    if filesize == 0:
                        res = http.request(b"HEAD", {b'Connection': b'keep-alive'})
                        print(res)
                        if res[0] == 200:
                            filesize = int(res[2][b'Content-Length'], 10)
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
                        speed = int(file_pos/1024/spendSec*100)/100
                        print("read data:",file_pos, filesize, speed, "KB/sec")
                        if len(data) == (file_end - file_pos):
                            saveFile.write(data)
                            if file_end == filesize:
                                print("total time:",spendSec," seconds")
                                break
                            else:
                                file_pos = file_end
            except Exception as e:
                print(e,"errorCount:"+str(errCount))
                errCount+=1
                if errCount>2:
                    raise e
        http.exit()
        saveFile.close()

    def putImg(self,img,filename):
        destName = filename
        filename = '_tmp_.jpg'
        img.save(filename)
        url = "http://share.webduino.io/_upload/"+self.container+"/"
        wCli = MicroWebCli(url, 'POST')
        fileSize = os.stat('/flash/'+filename)[6]
        print("fileSize:",fileSize)
        boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')
        bodyStart = \
        '------%s\r\n'%boundary+\
        'Content-Disposition: form-data; name="file"; filename="'+destName+'"\r\n'+\
        'Content-Type: application/octet-stream\r\n\r\n'
        bodyEnd =  '\r\n------%s--' % boundary
        bodyLen = len(bodyStart) + fileSize + len(bodyEnd)
        wCli.OpenRequest(contentType='multipart/form-data; boundary=----%s' % boundary,contentLength=bodyLen)
        wCli._write(bodyStart)
        try:
            f = open(filename,'rb')
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
            os.remove(filename)
        print("upload completed.")
        wCli._write(bodyEnd)
        wCli.Close()

    def getImg(self,uploadFile):
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
        img = image.Image(saveFile)
        os.remove(saveFile)
        return img


from machine import UART
from Maix import GPIO
from fpioa_manager import fm
import sensor,lcd,machine,time,network

class esp8285:
    def init(speed=115200):
        esp8285.subs = {}
        esp8285.wifiConnect = False
        esp8285.mqttConnect = False
        fm.register(19, fm.fpioa.GPIOHS0)
        wifiStatusPin = GPIO(GPIO.GPIOHS0, GPIO.IN)
        wifiStatusPin.irq(esp8285.state,GPIO.IRQ_BOTH)
        esp8285.reset()
        fm.register(27, fm.fpioa.UART2_TX, force=True)
        fm.register(28, fm.fpioa.UART2_RX, force=True)
        esp8285.uart = UART(UART.UART2, 115200, timeout=5000,read_buf_len=512)
        esp8285.waitInitFinish()
        esp8285.reset()
        esp8285.waitInitFinish()
        esp8285.setBaudrate(speed)
        esp8285.uart.deinit()
        del esp8285.uart
        esp8285.uart = UART(UART.UART2, speed, timeout=5000, read_buf_len=1024*40)
        esp8285.wlan = network.ESP8285(esp8285.uart)
        fm.register(18, fm.fpioa.UART3_RX, force=True)
        esp8285.uart_cb = UART(UART.UART3, 115200,timeout=5000,read_buf_len=10240,callback=esp8285.mqttCallback)
        while esp8285.uart_cb.any():
            esp8285.uart_cb.readline()
        esp8285.getInfo()
        print("esp8285 init OK [ ",esp8285.deviceID," ]")

    #'mqttConnect' : mqtt 連線
    #'subscribed'  : mqtt 已訂閱
    #'mqtt,${Topic},${Data}
    def mqttCallback(uarObj):
        try:
            if hasattr(esp8285,'uart_cb'):
                while esp8285.uart_cb.any():
                    myLine = uarObj.readline()
                    if(myLine==None):
                        break
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
                            esp8285.subs[topic](data)
                        pass # process mqtt Message
        except Exception as ee:
            print(ee)

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
        esp8285.sub(topic,includeID)
        esp8285.subs[topic] = callback

    def sub(topic,includeID=False):
        esp8285.mqttReady()
        if includeID:
            mqttSetSub = 'AT+MQTT="sub","{mqttUID}/{topic}"'.format(mqttUID=esp8285.deviceID, topic=topic)
        else:
            mqttSetSub = 'AT+MQTT="sub","{topic}"'.format(topic=topic)
        status=esp8285.at(mqttSetSub)

    def pub(topic,msg,includeID=False):
        esp8285.mqttReady()
        if includeID:
            mqttSetPush = 'AT+MQTT="push","{mqttUID}/{topic}","{msg}"'.format(mqttUID=esp8285.deviceID, topic=topic, msg=msg)
        else:
            mqttSetPush = 'AT+MQTT="push","{topic}","{msg}"'.format(topic=topic, msg=msg)
        status=esp8285.at(mqttSetPush)

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
        fm.unregister(pin8285)

    def connect(SSID="webduino.io", PWD="webduino"):
        err = 0
        while 1:
            try:
                esp8285.wlan.connect(SSID, PWD)
            except Exception:
                err += 1
                print("Connect AP failed, now try again")
                if err > 3:
                    raise Exception("Conenct AP fail")
                continue
            break
        time.sleep(0.25)

    def state(sw):
        esp8285.wifiConnect = sw.value()==1
        #print('wifi state:',esp8285.wifiConnect)

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

    def at(command, timeout=5000):
        esp8285.uart.write(command + '\r\n')
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
                    #print(">>>>>",myLine)
                    if "ERROR" in myLine:
                        return "ERROR"
                    elif "busy s" in myLine:
                        return "busy sending"
                    elif "busy p" in myLine:
                        return "busy processing"
                else:
                    print("timeout")
                    return "timeout"
            return data
        except Exception as e:
            print(e)

import _thread

class Btn:
    def __init__(self,name,pin,fpioaGPIO,gpio):
        Btn.UP = 0
        Btn.DOWN = 1
        Btn.LONG_PRESS = 2
        fm.fpioa.set_function(pin, fpioaGPIO)
        self.idx = 0
        self.name = name
        self.pin = pin
        self.eventHandler = []
        self.btn = GPIO(gpio, GPIO.IN)
        self.btn.irq(self.process,GPIO.IRQ_BOTH)
        self.btnState = Btn.DOWN if(self.btn.value()==0) else Btn.UP

    def state(self):
        self.btnState = Btn.DOWN if(self.btn.value()==0) else Btn.UP
        return self.btnState

    def longPressEvent(self):
        self.idx = self.idx + 1
        nowIdx = self.idx
        time.sleep(1)
        if(self.btn.value() == 0 and nowIdx == self.idx):
            # create thread to process
            for evt in self.eventHandler:
                _thread.start_new_thread(evt,[self.name,Btn.LONG_PRESS])

    def process(self,state):
        # create thread to process
        for evt in self.eventHandler:
            state = Btn.DOWN if(self.btn.value()==0) else Btn.UP
            _thread.start_new_thread(evt,[self.name,state])
            _thread.start_new_thread(self.longPressEvent,())

    def addBtnEventListener(self,eventFunc):
        self.eventHandler.append(eventFunc)

    def removeBtnEventListener(self,eventFunc):
        idx = 0
        findIdx = -1
        for evt in self.eventHandler:
            if(evt == eventFunc):
                findIdx = idx
                break
        if(findIdx >=0):
            del self.eventHandler[findIdx]

class mqtt:

    def sub(topic,callback,includeID = False):
        esp8285.setSub(topic,callback,includeID)

    def pub(topic,msg,includeID = False):
        esp8285.pub(topic,msg,includeID)

import lcd,sensor,time

class webai:

    def init():
        lcd.init()
        webai.init_camera_ok = False
        a = time.ticks()
        webai.initSensor()
        webai.btnHandler = []
        webai.btnL = Btn("btnL",7,fm.fpioa.GPIOHS7,GPIO.GPIOHS7)
        webai.btnR = Btn("btnR",16,fm.fpioa.GPIOHS16,GPIO.GPIOHS16)
        webai.btnL.addBtnEventListener(webai.onBtn)
        webai.btnR.addBtnEventListener(webai.onBtn)
        webai.mqtt = mqtt
        webai.cloud = cloud()
        webai.lcd = lcd
        webai.camera = sensor
        print('webai init completed. spend time:', (time.ticks()-a)/1000,'sec')

    def connect(ssid,pwd):
        esp8285.init(115200*20)
        webai.cloud.container = esp8285.deviceID
        if(esp8285.wifiConnect == False):
            esp8285.connect(ssid,pwd)


    def initSensor():
        sensor.reset()
        sensor.set_vflip(1) #鏡頭上下翻轉
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA) # 320x240
        sensor.skip_frames(30)
        webai.init_camera_ok = True

    def onBtn(name,state):
        for evt in webai.btnHandler:
            if(webai.btnL.state() == 1 and webai.btnR.state() == 1):
                state = 3
            evt(name,state)

    def addBtnListener(evt):
        webai.btnHandler.append(evt)

    def take():
        return sensor.snapshot()

    def show(cloudImg):
        img = webai.cloud.getImg(cloudImg)
        webai.lcd.display(img)

