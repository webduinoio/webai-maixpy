import time,lcd,sensor,image,gc,sys,json
import KPU as kpu

class ObjectTracking_Blockly():
    def showMessage(self,msg):
        print(msg)
        lcd.clear()
        lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)
        
    def __init__(self,flip=0,modelPath=None,threshold=0.1,nms_value=0.1,w=320,h=224):
        try:
            lcd.init()    
            self.showMessage("init camera")
            sensor.reset()
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.set_windowing((w, h))
            sensor.set_vflip(flip)
            sensor.set_auto_gain(1)
            sensor.set_auto_whitebal(1)
            sensor.set_auto_exposure(1)
            sensor.set_brightness(3)
            sensor.skip_frames(time = 2000)
            sensor.run(1)
        except Exception as e:
            print(e)
            self.showMessage("camera error")                        
            sys.exit()
            
        try:
            modelPathStart=modelPath.find('(')
            modelPathEnd=modelPath.rfind(')')
            classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            self.classes=classes
            self.showMessage("load model")
            self.task = kpu.load(modelPath)
            self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
            kpu.init_yolo2(self.task, threshold, nms_value, 5, self.anchor)
            self.showMessage("init finish")
        except Exception as e:
            print(e)
            self.showMessage("load model error")            
            sys.exit()
    def checkObjects(self):
        try:
            self.classesArr=[]
            img = sensor.snapshot()        
            code = kpu.run_yolo2(self.task, img)
            if code:
                for i in code:
                    img.draw_rectangle(i.rect())
                    lcd.display(img)
                    respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
                    self.classesArr.append(respList)
                    # print(self.classesArr)
                    for i in code:
                        lcd.draw_string(i.x(), i.y(), self.classes[i.classid()], lcd.RED, lcd.WHITE)
                        lcd.draw_string(i.x(), i.y()+12, '%.3f'%i.value(), lcd.RED, lcd.WHITE)
                return True
            else:
                lcd.display(img)
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
        kpu.deinit(self.task)
        gc.collect()

class ImageClassification_Blockly():
    def showMessage(self,msg):
        print(msg)
        lcd.clear()
        lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)
        
    def __init__(self,flip=0,modelPath=None,threshold=0.1,nms_value=0.1):
        try:
            lcd.init()    
            self.showMessage("init camera")
            sensor.reset()
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.set_windowing((320, 224))    
            sensor.set_vflip(flip)
            sensor.set_auto_gain(1)
            sensor.set_auto_whitebal(1)
            sensor.set_auto_exposure(1)
            sensor.set_brightness(3)
            sensor.skip_frames(time = 2000)
            sensor.run(1)
        except Exception as e:
            print(e)
            self.showMessage("camera error")            
            sys.exit()
            
        try:
            modelPathStart=modelPath.find('(')
            modelPathEnd=modelPath.rfind(')')
            classes=modelPath[modelPathStart+1:modelPathEnd].split(',')
            self.classes=classes
            self.showMessage("load model")
            self.task = kpu.load(modelPath)
            self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
            kpu.init_yolo2(self.task, threshold, nms_value, 5, self.anchor)
            self.showMessage("init finish")
        except Exception as e:
            print(e)
            self.showMessage("load model error")            
            sys.exit()
    def checkClasses(self):
        try:
            self.classesArr=[]
            img = sensor.snapshot()        
            code = kpu.run_yolo2(self.task, img)
            img=img.resize(224,224)
            if code:
                for i in code:
                    lcd.display(img)
                    respList={"x":i.x(),"y":i.y(),"w":i.w(),"h":i.h(),"value":i.value(),"classid":i.classid(),"index":i.index(),"objnum":i.objnum(),"objname":self.classes[i.classid()]}
                    self.classesArr.append(respList)
                    lcd.draw_string(0, 100, self.classes[i.classid()],lcd.RED, lcd.WHITE)
                    lcd.draw_string(0, 150, '%.3f'%i.value(),lcd.RED, lcd.WHITE)
                # print(self.classesArr)
                return True
            else:
                lcd.display(img)
                return False
        except Exception as e:
            print(e)
    def getClasses(self):
        #print(self.classesArr)
        if(len(self.classesArr)>0):
            self.classesArr.sort(key = lambda s: s['value'])
            #print(self.classesArr)            
            return self.classesArr[len(self.classesArr)-1]
        else:
            return []
            
    def __del__(self):
        kpu.deinit(self.task)
        gc.collect()
print("load board_kpu finish")
#object
# modelPath="/sd/monster(green,red,yellow,blue).kmodel"
#class
#modelPath="/sd/k210(apple,dog,tiger).kmodel"

# modelPathStart=modelPath.find('(')
# modelPathEnd=modelPath.rfind(')')
# classes=modelPath[modelPathStart+1:modelPathEnd].split(',')

# otb=ObjectTracking_Blockly(0,classes,modelPath)
# while 1:
#     otb.getObjects()

#icb=ImageClassification_Blockly(0,classes,modelPath)
#while 1:
    #icb.getClasses()
