from fpioa_manager import fm
import image,lcd,time,math
from machine import Timer,PWM,UART
from Maix import GPIO
from webai_blockly import SYSTEM_AT_UART


lcd.init()
lcd.clear()
img = image.Image('mooncar.jpg')
lcd.display(img)
#fm.register(6, fm.fpioa.GPIO0, force = True)
#device = hcsr04(fm.fpioa.GPIO0)
fm.register(6, fm.fpioa.GPIO0, force = True)
fm.register(11, fm.fpioa.GPIO1, force = True)
#fm.fpioa.help(fm.fpioa.GPIO0)
#fm.fpioa.help(fm.fpioa.GPIO1)

#device = hcsr04(fm.fpioa.GPIO7,fm.fpioa.GPIO1)
leftTimer = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
rightTimer = Timer(Timer.TIMER0, Timer.CHANNEL1, mode=Timer.MODE_PWM)
#leftWheel = PWM(leftTimer, freq=500000, duty=0, pin=9)#p8
#rightWheel = PWM(rightTimer, freq=500000, duty=0, pin=7)#p6

leftWheel = PWM(leftTimer, freq=500000, duty=0, pin=10)#p8
rightWheel = PWM(rightTimer, freq=500000, duty=0, pin=8)#p6
#fm.register(7, fm.fpioa.GPIO4)#p6
#fm.register(9, fm.fpioa.GPIO5)#p8
#fm.register(22, fm.fpioa.GPIO1)
#fm.register(19, fm.fpioa.GPIO2)
fm.register(0, fm.fpioa.GPIO2)#p13
fm.register(1, fm.fpioa.GPIO3)#p14
#w=GPIO(GPIO.GPIO4,GPIO.OUT)
#w.value(0)
#s=GPIO(GPIO.GPIO5,GPIO.OUT)
#s.value(0)
leftFalse=GPIO(GPIO.GPIO2,GPIO.OUT)
leftFalse.value(0)
rightFalse=GPIO(GPIO.GPIO3,GPIO.OUT)
rightFalse.value(0)
leftSpeed=0
rightSpeed=0
leftWheel.duty(leftSpeed)
rightWheel.duty(rightSpeed)


# from board_sensor import SYSTEM_atUart as uart

#fm.register(27, fm.fpioa.UART2_TX, force=True)
#fm.register(28, fm.fpioa.UART2_RX, force=True)

#uart = UART(UART.UART2, 115200*5, 8, 2, 2, timeout=5000, read_buf_len=40960)
#uart = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)


while True:
    while not SYSTEM_AT_UART.any():
        pass
    myLine = SYSTEM_AT_UART.readline()
    print(myLine)
    data=myLine.decode().strip()
    data=data.split(',')
    ##data=
    print(data)
    img = image.Image()
    try:
        if data[2]=="up":
            leftFalse.value(0)
            rightFalse.value(0)
            leftSpeed=90
            rightSpeed=90
            # showMessage("forward",clear=True)
            img = image.Image("mrun.jpg")
            lcd.display(img)

        elif(data[2]=="down"):
            leftFalse.value(1)
            rightFalse.value(1)
            leftSpeed=0
            rightSpeed=0
            # showMessage("back",clear=True)
            img = image.Image("m02.jpg")
            lcd.display(img)

        elif(data[2]=="left"):
            leftFalse.value(0)
            rightFalse.value(0)
            leftSpeed=0
            rightSpeed=90
            # showMessage("left",clear=True)
            img = image.Image("mleft.jpg")
            lcd.display(img)

        elif(data[2]=="right"):
            leftFalse.value(0)
            rightFalse.value(0)
            leftSpeed=90
            rightSpeed=0
            # showMessage("right",clear=True)
            img = image.Image("mright.jpg")
            lcd.display(img)


        elif(data[2]=="reset"):
            leftFalse.value(0)
            rightFalse.value(0)
            leftSpeed=0
            rightSpeed=0
            # showMessage("stop",clear=True)
            img = image.Image("m01.jpg")
            lcd.display(img)

        leftWheel.duty(leftSpeed)
        rightWheel.duty(rightSpeed)
        print(data[2])
    except Exception as e:
        print("err:"+str(e))