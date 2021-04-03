import KPU as kpu

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