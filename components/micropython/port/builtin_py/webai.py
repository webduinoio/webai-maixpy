import KPU as kpu
import machine , ubinascii , os , time , gc
from microWebCli import MicroWebCli

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
            with open(self.filename, 'rb') as f:
                self.DATA = f.read()
            return b''.join([self.boundary,self.name,self.CNT,self.CRLF,self.DATA,self.CRLF])
        def length(self):
            return os.stat(self.filename)[6]+len(b''.join([self.boundary,self.name,self.CNT,self.CRLF,self.CRLF]))


    def __init__(self,url,hashkey):
        self.url = url+'?hashkey='+hashkey
        self.boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')

    def countFilesSize(self,files):
        self.fileSize = 0
        for i in files:
            self.fileSize = self.fileSize + visionService.Filename(self.boundary,i).length()
        return self.fileSize

    def fileUpload(self,dsname,shared,files):
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
            for i in files:
                print("uploading...file:",i)
                _file = visionService.Filename(boundary,i)
                wCli._write(_file.data())
                _file.destroy()
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
        FaceDetect.task = kpu.load(address)
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
    def findQRCode(img):
        payload = ""
        find = False
        for code in img.find_qrcodes():
            payload = code.payload()
            find = True
            break
        if not find:
            img.replace(img, hmirror=True)
            for code in img.find_qrcodes():
                payload = code.payload()
                find = True
                break
            img.replace(img, hmirror=True)
        return payload

    def findBarCode(img):
        payload = ""
        find = False
        for code in img.find_barcodes():
            payload = code.payload()
            find = True
            break
        if not find:
            img.replace(img, hmirror=True)
            for code in img.find_barcodes():
                payload = code.payload()
                find = True
                break
            img.replace(img, hmirror=True)
        if not find:
            img.replace(img, vmirror=True)
            for code in img.find_barcodes():
                payload = code.payload()
                find = True
                break
            img.replace(img, vmirror=True)
        return payload
