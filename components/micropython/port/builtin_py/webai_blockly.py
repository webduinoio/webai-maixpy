print('exec by /flash/webai_blockly.py')
from _board import webai
import image,gc,sys

class Lcd:
	def __init__(self):
		print("webai lcd init")
		webai.img = image.Image()

	def clear(self):
		webai.lcd.clear()


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


	def drawString(self, x, y, text, color=(255,255,255), scale=2, x_spacing=20, mono_space=False,img=None):
		if not img==None:
			webai.img = img
		webai.draw_string(x, y, text, img=webai.img, color=color, scale=scale,mono_space=mono_space,lcd_show=True)

	def draw_string(self, x, y, msg, strColor, bgColor):
		if not msg == '':
			webai.lcd.draw_string(x, y, str(msg), strColor, bgColor)

	def displayImg(self,img=None):
		webai.img = None
		gc.collect()
		if type(img) is str:
			if(len(img.lower())<4 or img.lower()[-4:] != '.jpg'):
				img = img + ".jpg"
			webai.img = image.Image(img)
		else:
			webai.img = img
		webai.show(img=webai.img)

class Camera:
	def snapshot(self):
		return webai.snapshot()

class Speaker:
	def start(self,fileName='logo', sample_rate=11025):
		webai.speaker.play(filename=fileName,sample_rate=sample_rate)

	def setVolume(self,vol):
		webai.speaker.setVolume(vol)


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
            webai.camera.set_auto_gain(1)
            webai.camera.set_auto_whitebal(1)
            webai.camera.set_auto_exposure(1)
            webai.camera.set_brightness(3)
            webai.camera.skip_frames(time = 2000)
            webai.camera.run(1)
        except Exception as e:
            print(e)
            sys.exit()
            
        try:
            # modelPathStart=modelPath.find('(')
            # modelPathEnd=modelPath.rfind(')')
            # classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            cwd="flash"
            if cwd=="flash":
                model=0xB90000
            else:
                model="/sd/"+model+".kmodel"
            self.classes=classes
            self.task = self.kpu.load(model)
            self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
            self.kpu.init_yolo2(self.task, threshold, nms_value, 5, self.anchor)
        except Exception as e:
            print(e)
            sys.exit()
    def checkObjects(self):
        try:
            self.classesArr=[]
            img = self.sensor.snapshot()        
            code = self.kpu.run_yolo2(self.task, img)
            if code:
                for i in code:
                    img.draw_rectangle(i.rect())
                    webai.lcd.display(img)
                    respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
                    self.classesArr.append(respList)
                    # print(self.classesArr)
                    # for i in code:
                    #     lcd.draw_string(i.x(), i.y(), self.classes[i.classid()], lcd.RED, lcd.WHITE)
                    #     lcd.draw_string(i.x(), i.y()+12, '%.3f'%i.value(), lcd.RED, lcd.WHITE)
                return True
            else:
                webai.lcd.display(img)
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
