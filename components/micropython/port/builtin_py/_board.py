'''
- 其他待整理功能
- mqtt 命令
- qrcode 命令
- 下載模型
- 下載程式運行
- 上傳照片(影像辨識)
- 上傳照片(物件分類)
- ota wifi
- ota k210
'''
from board import board_info
from machine import UART
from fpioa_manager import fm
from Maix import config,utils,GPIO
from microWebCli import MicroWebCli
import sensor,lcd,machine,time,network,ujson
import gc,uos,json,os,image,_thread,ubinascii

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

class cfg:

    def init():
        cfg.flag = 0x4000
        cfg.length = 0x4002
        # maxium size: 4096 - 4 bytes
        cfg.data = 0x4004
        cfg.blobData = 0x10000        
        id = utils.flash_read(cfg.flag,2)
        # check flag
        if id[0] != 119 or id[1] != 97:
            utils.flash_write(cfg.flag,bytearray([119,97]))
            cfg.save({})
        else:
            dataLen = utils.flash_read(cfg.length,2)
            cfg.size = dataLen[0]*0x100 + dataLen[1]

    def clear():
        cfg.save({})

    def load():
        jsonData = utils.flash_read(cfg.data,cfg.size)
        cfg.size = len(jsonData)
        return ujson.loads(jsonData)

    def save(obj):
        jsonData = ujson.dumps(obj)
        cfg.size = len(jsonData)
        #write size
        hi = cfg.size // 255
        lo = cfg.size % 255
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
        if not key in obj:
            raise Exception("key not found:"+key)
        del obj[key]
        cfg.save(obj)

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
        blobLength = len(barray)
        hi = blobLength // 255
        lo = blobLength % 255
        utils.flash_write(cfg.blobData,bytearray([hi,lo]))
        #write data
        utils.flash_write(cfg.blobData+2,barray)

    def loadBlob():
        blobLen = utils.flash_read(cfg.blobData,2)
        blobLen = blobLen[0]*0x100 + blobLen[1]
        return utils.flash_read(cfg.blobData+2,blobLen)

class cloud:
    container = 'user'

    def download(self,url,filename=None,address=None,redirect=True,resize=320,img=True,showProgress=False):
        if redirect:
            server = "http://share.webduino.io/storage/"
            #server = "http://192.168.0.48:3000/storage/"
            if img:
                url = server + "redirect/img_resize/" + str(resize) + "/?url=" + url
            else:
                url = server + "redirect?url=" + url
        if showProgress:
            print("redirect url:" , url)
        http = MiniHttp()
        block_size = 10240
        start = time.ticks()
        start_pos = address
        file_pos, filesize, errCount = 0, 0, 0
        if not filename==None:
            saveFile = open(filename,'wb')
            start_pos = 0
        while True:
            try:
                if http.raw is None:
                    http.connect(url)
                    if showProgress:
                        print("http connect.")
                else:
                    if filesize == 0:
                        res = http.request(b"HEAD", {b'Connection': b'keep-alive'})
                        #print("res>>>",res)
                        if res[0] == 200:
                            filesize = int(res[2][b'Content-Length'], 10)
                            print("")
                            print("filesize:",filesize)
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
                            webai.draw_string(70,110,"進度..."+str(percent)+"%",scale=2)
                        if len(data) == (file_end - file_pos):
                            print("writing:",hex(start_pos+file_pos),'~', hex(start_pos+file_end),percent,'% ,',speed,"KB")
                            if not address==None:
                                utils.flash_write(start_pos+file_pos,data)
                            if not filename==None:
                                saveFile.write(data)
                            if file_end == filesize:
                                print("100% , total time:",spendSec," seconds")
                                break
                            else:
                                file_pos = file_end
            except Exception as e:
                print(e,"errorCount:"+str(errCount))
                errCount+=1
                if errCount>2:
                    raise e
        if showProgress:
            webai.draw_string(50,10,"下載完成  ",scale=3)
        http.exit()
        if not filename==None:
            saveFile.close()

    def putBytearray(self,_bytearray,desFile,retry=3):
        while True:
            try:
                self._putBytearray(_bytearray,desFile,retry)
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
        while True:
            try:
                filename = '_tmp_.jpg'
                print("save...",filename)
                img.save(filename)
                print("save done.")
                self._putFile(filename,desFile,retry)
                os.remove(filename)
                break
            except:
                retry = retry - 1
                if(retry==0):
                    raise Exception("upload "+desFile+" fail")
                    break
                print("retry...",retry)
                webai.resetESP8285()

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
        img = image.Image(saveFile)
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

class esp8285:
    def init(speed=115200):
        if not hasattr(esp8285,'subs'):
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
        _thread.stack_size(16*1024)
        while esp8285.uart_cb.any():
            esp8285.uart_cb.readline()
        esp8285.getInfo()
        gc.collect()
        print("esp8285 init OK [ ",esp8285.deviceID," ]")

    #'mqttConnect' : mqtt 連線
    #'subscribed'  : mqtt 已訂閱
    #'mqtt,${Topic},${Data}
    def mqttCallback(uarObj):
        try:
            while esp8285.uart_cb.any():
                myLine = uarObj.readline()
                #print("mqtt debug:",myLine)
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
        except Exception as ee:
            print('mqttCallback:',ee)

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
            topic = esp8285.deviceID+"/"+topic
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

class btn:
    def __init__(self,name,pin,fpioaGPIO,gpio):
        btn.UP = 0
        btn.DOWN = 1
        btn.LONG_PRESS = 2
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
        self.irq_process = False
        self.lastProcessTime = time.ticks_ms()
        _thread.start_new_thread(self.run,())

    def process(pinInfo):
        btn.btnStateQueue[str(pinInfo)].append(pinInfo)

    def run(self):
        while True:
            stateList = btn.btnStateQueue[self.pin]
            if len(stateList) > 0:
                nowTime = time.ticks_ms()
                if (nowTime - self.lastProcessTime) > 10:
                    self.lastProcessTime = nowTime
                    val = stateList[0].value()
                    for evt in self.eventHandler:
                        if(val==0):
                            evt(self.name,1)
                        else:
                            evt(self.name,0)
                del stateList[0]
            time.sleep(0.001)

    def state(self):
        self.btnState = btn.DOWN if(self.btn.value()==0) else btn.UP
        return self.btnState

    def longPressEvent(self):
        self.idx = self.idx + 1
        nowIdx = self.idx
        time.sleep(1)
        if(self.btn.value() == 0 and nowIdx == self.idx):
            # create thread to process
            for evt in self.eventHandler:
                _thread.start_new_thread(evt,[self.name,btn.LONG_PRESS])

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

class fs:
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
        print()

    def load(file):
        import os
        code = ''
        with open(file,"r") as f:
            lines = f.readlines()
        for line in lines:
            code = code + line
        return code

    def save(file,line):
        try:
            f = open(file,'w')
            f.write(line)
        finally:
            f.close()

    def rm(file):
        import os
        if(file=="*"):
            a = os.listdir()
            for filename in a:
                os.remove(filename)
        else:
            os.remove(file)

class mem:
    def info():
        from Maix import utils
        import KPU as kpu
        print("[ FirmwareType:",fw.fwType," v1.0]")
        print("heap size:",int(utils.gc_heap_size()/1024),"KB")
        print("")
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
        if name == 'min' or name == 'mini':
            utils.flash_write(fw.kboot_fw_flag,bytearray([1]))
            if fw.now() != name:
                time.sleep(1)
                machine.reset()
        elif name == 'std':
            utils.flash_write(fw.kboot_fw_flag,bytearray([0]))
            if fw.now() != name:
                time.sleep(1)
                machine.reset()
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

    def play(self, folder='flash',filename=None, sample_rate=22030):
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
        esp8285.at("AT+SPEAKER=0")

    def start(self, folder="", fileName=None, sample_rate=48000):
        if(fileName != None):
            if folder=="":
                cwd = SYSTEM_DEFAULT_PATH
                if cwd == "flash":
                    folder = "flash"
                else:
                    folder = "sd"
            self.wav_dev.set_sample_rate(sample_rate)
            player = self.audio.Audio(path="/"+folder+"/"+fileName+".wav")
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
            print("fileName error")


class cmdProcess:
    def load():
        cmdProcess.reportBoot()
        json = webai.cfg.get("cmd")
        if not json==None:
            webai.cfg.remove("cmd")
            cmdProcess.msgParser(json)
            return 1
        else:
            return 0

    def run(cmdData):
        webai.img = None
        time.sleep(0.1)
        gc.collect()
        if(cmdData[:1]=='"' and cmdData[-1:]=='"'):
            cmdData = cmdData[1:-1]
        if(cmdData[:9]=='_DEPLOY/h'):
            #print("ignore! skip command")
            return
        #print("cmdData:",cmdData)
        cmdType = cmdData[:1]
        if cmdType=='!':
            cmdProcess.msgParser(cmdData[1:])
        else:
            cmdProcess.saveCmd(cmdData)

    '''
    儲存命令前，先判斷是否有指定romType，有的話就進行設定 romType
    '''
    def saveCmd(cmdData):
        #print("cmdProcess saving..",cmdData)
        webai.cfg.put("cmd",cmdData)
        cmdProcess.reportSaveOK()
        print("cmdProcess save done.")
        machine.reset()
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
        webai.draw_string(110,100,"下載完成  ",scale=2)
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

    def _RUN(pythonFile):
        __import__(pythonFile)
        del sys.modules[pythonFile]

    def _DEPLOY(info):
        # get pythonCode to main.py
        info = ujson.loads(info)
        # server 需改成提供 http:// 方式
        url = info['url'].replace('https://','http://')
        webai.cloud.download(url,img=False,redirect=False,filename='/flash/main.py')

    def _TAKEPIC_YOLO(jsonArray):
        print("_TAKEPIC_YOLO>",jsonArray)

    def _TAKEPIC_MOBILENET(jsonArray):
        print("_TAKEPIC_MOBILENET>",jsonArray)

    def _DOWNLOAD_MODEL(jsonArray):
        print("_DOWNLOAD_MODEL>",jsonArray)

    def _DOWNLOAD_FILE(jsonArray):
        print("_DOWNLOAD_FILE>",jsonArray)


class webai:

    def init(camera=True,speed=20):
        if hasattr(webai,'initialize'):
           return
        webai.img = None
        webai.debug = False
        webai.speed = speed
        webai.initialize = True
        fw.init()
        cfg.init()
        fw.now(fwType='qry')
        a = time.ticks()
        esp8285.init(115200*webai.speed)
        #link obj
        webai.cmdProcess = cmdProcess
        webai.cfg = cfg
        webai.fs = fs
        webai.fw = fw
        webai.mem = mem
        webai.mqtt = mqtt
        webai.esp8285 = esp8285
        webai.deviceID = esp8285.deviceID
        webai.lcd = lcd
        webai.camera = sensor
        webai.speaker = speaker()
        webai.init_camera_ok = False
        if camera:
            webai.initCamera()
        webai.btnHandler = []
        webai.btnL = btn("btnL",7,fm.fpioa.GPIOHS7,GPIO.GPIOHS7)
        webai.btnR = btn("btnR",16,fm.fpioa.GPIOHS16,GPIO.GPIOHS16)
        webai.btnL.addBtnEventListener(webai.onBtn)
        webai.btnR.addBtnEventListener(webai.onBtn)
        webai.cloud = cloud()
        webai.ver = os.uname()[6]
        gc.collect()

        if not cmdProcess.load():
            webai.logo()
            time.sleep(0.01)
            gc.collect()
            print('')
            print('webai init completed.')
            print('spend time:', (time.ticks()-a)/1000,'sec')
            print('')
            webai.mem.info()
        lcd.clear()    
        time.sleep(0.01)
        gc.collect()

    def draw_string(x, y, text, img=None, color=(255,255,255), scale=5,mono_space=False,lcd_show=True):
        if img == None:
            img = image.Image()
        x_spacing = 8*scale
        image.font_load(image.UTF8, 16, 16, 0x980000)
        img.draw_string(x, y, text, scale=scale, color=color, x_spacing=x_spacing, mono_space=mono_space)
        image.font_free()
        if lcd_show:
            webai.lcd.display(img)
        img = None
        del img

    def logo():
        try:
            img = image.Image('/flash/logo.jpg')
            lcd.display(img)
        except:
            print("logo image error")    
        finally:
            img = None
        gc.collect()
        webai.speaker.setVolume(20)
        webai.speaker.start(folder="flash", fileName='logo', sample_rate=22050)

    def reset():
        import machine
        machine.reset()

    def resetESP8285():
        esp8285.init(115200*webai.speed)

    def connect(ssid="webduino.io",pwd="webduino"):
        webai.cloud.container = esp8285.deviceID
        if(esp8285.wifiConnect == False):
            esp8285.connect(ssid,pwd)

    def initCamera():
        webai.camera.reset()
        webai.camera.set_vflip(1) #鏡頭上下翻轉
        webai.camera.set_pixformat(webai.camera.RGB565)
        webai.camera.set_framesize(webai.camera.QVGA) # 320x240
        webai.camera.skip_frames(30)
        webai.init_camera_ok = True

    def onBtn(name,state):
        for evt in webai.btnHandler:
            if(webai.btnL.state() == 1 and webai.btnR.state() == 1):
                state = 3
            evt(name,state)

    def addBtnListener(evt):
        webai.btnHandler.append(evt)

    def run(file):
        cmdProcess._RUN(file)

    def snapshot():
        webai.img = None
        time.sleep(0.001)
        gc.collect()
        webai.img = webai.camera.snapshot()
        return webai.img
        

    def show(url="",file="logo.jpg",img=None):
        if img != None:
            webai.lcd.display(img)
        else:
            if len(url)>0:
                img = webai.cloud.getImg(url)

            if len(file)>0:
                img = image.Image(file)
            webai.lcd.display(img)

webai.init(camera=True,speed=10)
webai.connect()
webai.mqtt.sub('PING',cmdProcess.run,includeID=True)