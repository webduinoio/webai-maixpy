import sensor,image,lcd,time,math
import KPU as kpu
from machine import Timer,PWM
from fpioa_manager import *
from Maix import GPIO
from modules import ws2812

def showMessage(msg):
    lcd.clear()
    lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)
fm.register(6, fm.fpioa.GPIO0, force = True)
fm.register(11, fm.fpioa.GPIO1, force = True)

class_ws2812 = ws2812(led_pin=22,led_num=8)

leftTimer = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
rightTimer = Timer(Timer.TIMER0, Timer.CHANNEL1, mode=Timer.MODE_PWM)

leftWheel = PWM(leftTimer, freq=500000, duty=0, pin=10)#p8
rightWheel = PWM(rightTimer, freq=500000, duty=0, pin=8)#p6
fm.register(0, fm.fpioa.GPIO2)#p13
fm.register(1, fm.fpioa.GPIO3)#p14
leftFalse=GPIO(GPIO.GPIO2,GPIO.OUT)
leftFalse.value(0)
rightFalse=GPIO(GPIO.GPIO3,GPIO.OUT)
rightFalse.value(0)
leftSpeed=0
rightSpeed=0
leftWheel.duty(leftSpeed)
rightWheel.duty(rightSpeed)

lcd.init(freq=15000000)
lcd.clear()
showMessage("init camera")
sensor.reset(freq=20000000)

sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((320, 224))
sensor.skip_frames(time = 2000)

sensor.set_vflip(1)

sensor.set_auto_gain(1)
sensor.set_auto_whitebal(1)
sensor.set_auto_exposure(1)
sensor.set_brightness(2)

sensor.run(1)
print("init sensor finish")

classes = ['Green', 'Red', 'Yellow','Blue']
colors = [(0, 255, 0), (255, 0, 0),(255, 255, 0),(0, 0, 255)]
colors2 = [(0, 50//4, 0), (50//4, 0, 0),(50//4,50//4,0),(0,0,50//4)]

# load model
showMessage("load model")
task = kpu.load(0xB90000)

anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

print("init yolo finish")
cm=0
running=False
mycolor2=None

while(True):
    try:
        img = sensor.snapshot()

        code = kpu.run_yolo2(task, img)
        rawData=None
        objectClass=None
        if code:
            for i in code:
                mycolor = colors[i.classid()]
                mycolor2 = colors2[i.classid()]
                # draw rectangle
                img.draw_rectangle(i.rect(), color=mycolor, thickness=5, fill=False)
                # draw text
                rawData=i.rect()
            lcd.display(img)
            x=rawData[0]
            width=rawData[2]
            y=0

            if(x+width>=320):
                y=0
            else:
                y=320-x-width
            speed=abs(x-y)
            if(speed>=60):
                leftSpeed=int((1-x/320)*80)
                rightSpeed=int((1-y/320)*80)
                if(leftSpeed<=40):
                    leftSpeed=40
                if(rightSpeed<=40):
                    rightSpeed=40
            else:
                leftSpeed=65
                rightSpeed=65
            time.sleep(0.05)
        else:
            lcd.display(img)
            leftSpeed=0
            rightSpeed=0
    except Exception as e:
        print(e)
    finally:
        leftWheel.duty(leftSpeed)
        rightWheel.duty(rightSpeed)
        if(leftSpeed!=0):
            if(leftSpeed>rightSpeed):
                class_ws2812.set_led(0,mycolor2)
                class_ws2812.set_led(1,mycolor2)
                class_ws2812.set_led(6,mycolor2)
                class_ws2812.set_led(7,mycolor2)

                class_ws2812.set_led(2,(0,0,0))
                class_ws2812.set_led(3,(0,0,0))
                class_ws2812.set_led(4,(0,0,0))
                class_ws2812.set_led(5,(0,0,0))
            elif(leftSpeed<rightSpeed):
                class_ws2812.set_led(2,mycolor2)
                class_ws2812.set_led(3,mycolor2)
                class_ws2812.set_led(4,mycolor2)
                class_ws2812.set_led(5,mycolor2)

                class_ws2812.set_led(0,(0,0,0))
                class_ws2812.set_led(1,(0,0,0))
                class_ws2812.set_led(6,(0,0,0))
                class_ws2812.set_led(7,(0,0,0))
            else:
                for i in range(7):
                    class_ws2812.set_led(i,mycolor2)
        class_ws2812.display()
kpu.deinit(task)
