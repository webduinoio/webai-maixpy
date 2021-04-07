import KPU as kpu
import machine , ubinascii , os
from microWebCli import MicroWebCli

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



class Web:

    def uploadFile(filename,destName):
        url = "http://share.webduino.io/_upload/db"
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
        f.close()
        wCli._write(bodyEnd)
        wCli.Close()

    def downloadFile(uploadFile,saveFile):
        url = "http://share.webduino.io/storage/download/"+uploadFile
        wCli = MicroWebCli(url)
        f = open(saveFile,"wb")
        #wCli.QueryParams['pet'] = 'cat'
        #print('GET %s' % wCli.URL)
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
        f.close()
        wCli.Close()


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
        for code in img.find_qrcodes():
            payload = code.payload()
            break
        return payload

    def findBarCode(img):
        payload = ""
        for code in img.find_barcodes():
            payload = code.payload()
            break
        return payload