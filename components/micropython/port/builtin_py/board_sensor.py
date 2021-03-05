import gc,time
import lcd
from fpioa_manager import fm
from board import board_info,fpioaMapGPIO
from machine import UART
class Lcd_Blockly:
    def __init__(self):
        import image
        self.lcd=lcd
        self.image=image
        self.lcd.init()
        self.lcd.clear()
        self.img=self.image.Image()
        print('Lcd_Blockly __init__')
    def __del__(self):
        del self
        print('Lcd_Blockly __del__')
    def clear(self):
        self.lcd.clear()
        self.img.clear()
    def draw_string(self,x,y,msg,strColor,bgColor):
        if not msg == '':
            self.lcd.draw_string(x,y,str(msg),strColor,bgColor)
    def displayImg(self,cwd=None,img=None):
        if type(img)==str:
            if cwd=="flash":
                self.path="/flash/"+img
            else:
                self.path="/sd/"+img
            self.img=self.image.Image(self.path)
            self.lcd.display(self.img)
        else:
            self.lcd.display(img)
    def displayColor(self,color):
        self.lcd.clear(color)
    def selfObject(self):
        return self.lcd
    def width(self):
        return self.lcd.width()
    def height(self):
        return self.lcd.height()
    def drawCircle(self,x,y,radius,color=0xffffff,thickness=1,fill=False):
        self.img.draw_circle(x,y,radius,color,thickness,fill)
        self.lcd.display(self.img)
    def drawLine(self,x0,y0,x1,y1,color=0xffffff,thickness=1):
        self.img.draw_line(x0,y0,x1,y1,color,thickness)
        self.lcd.display(self.img)
    def drawRectangle(self,x,y,w,h,color=0xffffff,thickness=1,fill=False):
        self.img.draw_rectangle(x,y,w,h,color,thickness,fill)
        self.lcd.display(self.img)
    def drawArrow(self,x0,y0,x1,y1,color=0xffffff,thickness=1):
        self.img.draw_arrow(x0,y0,x1,y1,color,thickness)
        self.lcd.display(self.img)
    def drawCross(self,x,y,color=0xffffff,size=5,thickness=1):
        self.img.draw_cross(x,y,color,size,thickness)
        self.lcd.display(self.img)
    def drawString(self,x,y,text,color=0xffffff,scale=5,x_spacing=3,y_spacing=1,mono_space=False):
        if not text == '':
            self.img.draw_string(x,y,text,color,scale,x_spacing,y_spacing,mono_space)
            self.lcd.display(self.img)
        
class Camera_Blockly:
    import sensor
    def __init__(self,flip=1,auto_gain=1,auto_whitebal=1,auto_exposure=1,brightness=3):
        #self.sensor=sensor
        try:
            showMessage("init camera")
            self.sensor.reset()
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.skip_frames(time = 2000)
            self.sensor.set_vflip(flip)
            self.sensor.set_auto_gain(auto_gain)
            self.sensor.set_auto_whitebal(auto_whitebal)
            self.sensor.set_auto_exposure(auto_exposure)
            self.sensor.set_brightness(brightness)
            print('Camera_Blockly __init__')
            showMessage("init camera OK")
        except Exception as e:
            print(e)
            showMessage("init camera ERROR")

    def shutdown(self,enable):
        self.sensor.shutdown(enable)
    def snapshot(self):
        return self.sensor.snapshot()
    def stream(self):
        self.sensor.run(1)
    def selfObject(self):
        return self.sensor
    def __del__(self):
        del self
        print('Camera_Blockly __del__')

class Mic_Blockly:
    import audio
    from Maix import I2S
    from fpioa_manager import fm
    # user setting
    #sample_rate   = 16000
    sample_rate   = 48000

    # default seting
    sample_points = 2048
    wav_ch        = 2

    fm.register(board_info.MIC_I2S_IN,fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(board_info.MIC_I2S_WS,fm.fpioa.I2S0_WS, force=True)    # 19 on Go Board and Bit(new version)
    fm.register(board_info.MIC_I2S_SCLK,fm.fpioa.I2S0_SCLK, force=True)  # 18 on Go Board and Bit(new version)

    rx = I2S(I2S.DEVICE_0)
    rx.channel_config(rx.CHANNEL_0, rx.RECEIVER, align_mode=I2S.STANDARD_MODE)
    rx.set_sample_rate(sample_rate)

    def start(self,cwd=None,folder="sd",fileName="recorder",record_time=5):
        if cwd=="flash":
            folder="flash"
            record_time=1
        else:
            folder="sd"
        self.recorder = self.audio.Audio(path="/"+folder+"/"+fileName+".wav", is_create=True, samplerate=self.sample_rate)
        self.queue = []
        print("start recorder")
        frame_cnt = record_time*self.sample_rate//self.sample_points

        for i in range(frame_cnt):
            tmp = self.rx.record(self.sample_points*self.wav_ch)
            if len(self.queue) > 0:
                ret = self.recorder.record(self.queue[0])
                self.queue.pop(0)
            self.rx.wait_record()
            self.queue.append(tmp)
            #lcdTmp.draw_string(int(311-len("please wait 10s ...")*6.9)//2,int(224//1.5),"please wait 10s ...",lcd.GREEN,lcd.BLACK)
            #lcd.draw_string(int(311-len("please wait 10s ...")*6.9)//2,int(224//1.5),"please wait 10s ...",lcd.GREEN,lcd.BLACK)
            print(str(i) + ":" + str(time.ticks()))

        self.recorder.finish()
        print("finish")


class Speaker_Blockly:
    def __init__(self):
        from Maix import I2S
        from fpioa_manager import fm
        import audio
        fm.register(board_info.SPK_I2S_OUT,fm.fpioa.I2S2_OUT_D1, force=True)
        fm.register(board_info.SPK_I2S_WS,fm.fpioa.I2S2_WS, force=True)
        fm.register(board_info.SPK_I2S_SCLK,fm.fpioa.I2S2_SCLK, force=True)
        self.wav_dev = I2S(I2S.DEVICE_2)
        self.wav_dev.channel_config(self.wav_dev.CHANNEL_1, I2S.TRANSMITTER,resolution = I2S.RESOLUTION_16_BIT ,cycles = I2S.SCLK_CYCLES_32, align_mode = I2S.RIGHT_JUSTIFYING_MODE)
        self.audio=audio
        self.volume=5
        print("SPEAKER __init__")
    def __del__(self):
        del self
        print("SPEAKER __del__")
    def setVolume(self,volume):
        self.volume=volume
    def start(self,SYSTEM_AT_UART,cwd=None,folder="sd",fileName=None,sample_rate=48000):
        if(fileName!=None):
            if cwd=="flash":
                folder="flash"
            else:
                folder="sd"
            self.wav_dev.set_sample_rate(sample_rate)
            player = self.audio.Audio(path = "/"+folder+"/"+fileName+".wav")
            player.volume(self.volume)
            # read audio info
            #wav_info = player.play_process(wav_dev)
            #print("wav file head information: ", wav_info)
            player.play_process(self.wav_dev)
            print("start play")
            #self.commCycle(self.SYSTEM_AT_UART,"AT+SPEAKER=1")
            commCycle(SYSTEM_AT_UART,"AT+SPEAKER=1")

            while True:
               ret = player.play()
               if ret == None:
                   print("format error")
                   break
               elif ret==0:
                   print("end")
                   break

            #self.commCycle(SYSTEM_AT_UART,"AT+SPEAKER=0")
            commCycle(SYSTEM_AT_UART,"AT+SPEAKER=0")
            player.finish()
            #print(time.time())
            print("play finish")
        else:
            print("fileName error")

# def showMessage(msg):
#     lcd.clear()
#     lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)

def commCycle(SYSTEM_AT_UART,command,timeout=5000): #This controls one command exection cycle.
    SYSTEM_AT_UART.write(command + '\r\n')
    myLine = ''
    # while  not  "OK" in myLine:
    #     while not SYSTEM_AT_UART.any():
    #         pass
    #     myLine = SYSTEM_AT_UART.readline()
    #     print(myLine)


    startTime=time.ticks_ms()
    ifdata=True
    try:
        while  not  "OK" in myLine:
            while not SYSTEM_AT_UART.any():
                endTime=time.ticks_ms()
                # print(endTime-startTime)
                if((endTime-startTime)>=timeout):
                    ifdata=False
                    break
            if(ifdata):
                myLine = SYSTEM_AT_UART.readline()
                print(myLine)
                if "ERROR" in myLine:
                    # print("ERROR")
                    # raise Exception('ERROR')
                    return "ERROR"
                elif "busy s" in myLine:
                    # print("busy sending")
                    # raise Exception('busy sending')
                    return "busy sending"
                elif "busy p" in myLine:
                    # print("busy processing")
                    # raise Exception('busy processing')
                    return "busy processing"
            else:
                print("timeout")
                # raise Exception('timeout')
                return "timeout"
                # break
        return "OK"
    except Exception as e:
        print(e)

def readUID(SYSTEM_AT_UART,timeout=2000): #This controls one command exection cycle.
    # SYSTEM_AT_UART.write('AT+SYSUID' + '\r\n')
    # myLine = ''
    # respUID = ''
    # while  not  "OK" in myLine:
    #     while not SYSTEM_AT_UART.any():
    #         pass
    #     myLine = SYSTEM_AT_UART.readline()
    #     print(myLine)
    #     if "unique id" in myLine:
    #         myLine=myLine.strip().decode()
    #         #print(myLine[10:])
    #         respUID=myLine[10:]
    # return respUID

    myLine = ''
    respUID = ''
    startTime=time.ticks_ms()
    ifdata=True
    SYSTEM_AT_UART.write('AT+SYSUID' + '\r\n')
    try:
        while  not  "OK" in myLine:
            while not SYSTEM_AT_UART.any():
                endTime=time.ticks_ms()
                # print(end-start)
                if((endTime-startTime)>=timeout):
                    ifdata=False
                    break
            if(ifdata):
                myLine = SYSTEM_AT_UART.readline()
                print(myLine)
                if "unique id" in myLine:
                    myLine=myLine.strip().decode()
                    #print(myLine[10:])
                    respUID=myLine[10:]
                elif "ERROR" in myLine:
                    # print("ERROR")
                    # raise Exception('ERROR')
                    return "ERROR"
                elif "busy s" in myLine:
                    # print("busy sending")
                    # raise Exception('busy sending')
                    return "busy sending"
                elif "busy p" in myLine:
                    # print("busy processing")
                    # raise Exception('busy processing')
                    return "busy processing"
            else:
                print("timeout")
                # raise Exception('timeout')
                return "timeout"
                # break
        return respUID
    except Exception as e:
        print(e)
        return "ERROR"
def showMessage(msg,x=-1,y=0,center=True,clear=False):
    if clear:
        lcd.clear()
    if center:
        lcd.draw_string(int(320-len(msg)*8)//2,112,msg,lcd.WHITE)
    else:
        if x == -1:
            lcd.draw_string(int(320-len(msg)*8)//2,int(224/7*y),msg,lcd.WHITE)
        else:
            lcd.draw_string(x,int(224/7*y),msg,lcd.WHITE)

lcd.init()
# fm.register(board_info.ESP_UART0RX, fm.fpioa.UART2_TX, force=True)
# fm.register(board_info.ESP_UART0TX, fm.fpioa.UART2_RX, force=True)

# #SYSTEM_AT_UART = UART(UART.UART2, 115200*5, 8, 2, 2, timeout=5000, read_buf_len=40960)
# SYSTEM_AT_UART = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)
print("load board_sensor finish")