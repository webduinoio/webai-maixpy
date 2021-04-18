import sensor, image, lcd, time
import KPU as kpu
# import _thread
from machine import Timer
from modules import ws2812
# class_ws2812 = ws2812(led_pin=3,led_num=4)
class_ws2812 = ws2812(led_pin=22,led_num=8)
for i in range(8):
    class_ws2812.set_led(i,(0,0,0))
class_ws2812.display()
threadStatus=False
color_R = (255, 0, 0)
color_G = (0, 255, 0)
color_B = (0, 0, 255)


class_IDs = ['no_mask', 'mask']

def showMessage(msg):
    print(msg)
    lcd.clear()
    lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)

def drawConfidenceText(image, rol, classid, value):
    text = ""
    _confidence = int(value * 100)

    if classid == 1:
        text = 'mask: ' + str(_confidence) + '%'
    else:
        text = 'no_mask: ' + str(_confidence) + '%'

    image.draw_string(rol[0], rol[1], text, color=color_R, scale=2.5)


#def on_timer(timer):
    #print("time up:",timer)
    #speaker.start(SYSTEM_AT_UART,cwd="sd",fileName="bbbb",sample_rate=48000)

#tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_ONE_SHOT, period=1, unit=Timer.UNIT_MS, callback=on_timer, arg=on_timer)

#def thread_entry(t):
    #try:
        #print("new thread")
        #global speaker,threadStatus
        #threadStatus=True
        #speaker.start(cwd="sd",fileName="bbbb",volume=100)
        #threadStatus=False
        #_thread.exit()
    #except Exception as e:
        #print("error")
        #print(e)
        #threadStatus=False
        #_thread.exit()

#tim.start()
#time.sleep(0.01)
#tim.stop()
#for i in range(0,1):
    #_thread.start_new_thread(thread_entry,("",))
    #time.sleep(0.5)
#time.sleep(2)


lcd.init()
showMessage("init camera")
sensor.reset()
#sensor.reset(dual_buff=True)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
#sensor.set_windowing((320, 224))
sensor.skip_frames(time = 2000)

sensor.set_vflip(1)

sensor.set_auto_gain(1)
sensor.set_auto_whitebal(1)
sensor.set_auto_exposure(1)
sensor.set_brightness(2)

sensor.run(1)

showMessage("load model")
task = kpu.load(0xD40000)


anchor = (0.1606, 0.3562, 0.4712, 0.9568, 0.9877, 1.9108, 1.8761, 3.5310, 3.4423, 5.6823)
_ = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)
img_lcd = image.Image()

clock = time.clock()
while (True):
    clock.tick()
    img = sensor.snapshot()
    code = kpu.run_yolo2(task, img)
    if code:

        for item in code:
            confidence = float(item.value())
            itemROL = item.rect()
            classID = int(item.classid())

            if confidence < 0.52:
                _ = img.draw_rectangle(itemROL, color=color_B, tickness=5)
                continue

            if classID == 1 and confidence > 0.65:
                _ = img.draw_rectangle(itemROL, color_G, tickness=5)
                #if totalRes == 1:
                    #drawConfidenceText(img, (0, 0), 1, confidence)
                for i in range(8):
                    class_ws2812.set_led(i,color_G)
                class_ws2812.display()
            else:
                _ = img.draw_rectangle(itemROL, color=color_R, tickness=5)
                for i in range(8):
                    class_ws2812.set_led(i,color_R)
                class_ws2812.display()

    _ = lcd.display(img)

_ = kpu.deinit(task)
