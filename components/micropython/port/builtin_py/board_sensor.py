import gc,time
from board import board_info
class Lcd_Blockly:
    import lcd
    def __init__(self):
        self.lcd.init()
        self.lcd.clear()
        print('Lcd_Blockly __init__')
    def __del__(self):
        del self
        print('Lcd_Blockly __del__')
    def clear(self):
        self.lcd.clear()
    def draw_string(self,x,y,msg,strColor,bgColor):
        if not msg == '':
            self.lcd.draw_string(x,y,msg,strColor,bgColor)
    def displayImg(self,img):
        self.lcd.display(img)
    def displayColor(self,color):
        self.lcd.clear(color)
    def selfObject(self):
        return self.lcd
    def width(self):
        return self.lcd.width()
    def height(self):
        return self.lcd.height()
        
class Camera_Blockly:
    import sensor
    def __init__(self,flip=1,auto_gain=1,auto_whitebal=1,auto_exposure=1,brightness=3):
        #self.sensor=sensor
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

    def start(self,folder="sd",fileName="recorder",record_time=5):
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
    from Maix import I2S
    from fpioa_manager import fm
    import audio
    # from machine import UART
    sample_rate = 48000
    #sample_rate = 44100
    #uart = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)
    #fm.register(27, fm.fpioa.UART2_TX, force=True)
    #fm.register(28, fm.fpioa.UART2_RX, force=True)

    # register i2s(i2s2) pin
    fm.register(board_info.SPK_I2S_OUT,fm.fpioa.I2S2_OUT_D1, force=True)
    fm.register(board_info.SPK_I2S_WS,fm.fpioa.I2S2_WS, force=True)
    fm.register(board_info.SPK_I2S_SCLK,fm.fpioa.I2S2_SCLK, force=True)
    ##init audio
    wav_dev = I2S(I2S.DEVICE_2)
    wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER,resolution = I2S.RESOLUTION_16_BIT ,cycles = I2S.SCLK_CYCLES_32, align_mode = I2S.RIGHT_JUSTIFYING_MODE)
    wav_dev.set_sample_rate(sample_rate)
    #def commCycle(self,command): #This controls one command exection cycle.
        #self.uart.write(command + '\r\n')
        #myLine = ''
        #while  not  "OK" in myLine:
            #while not self.uart.any():
                #pass
            #myLine = self.uart.readline()
            #print(myLine)
    def __init__(self):
        print("SPEAKER __init__")
    def __del__(self):
        del self
        print("SPEAKER __del__")
    def start(self,folder="sd",fileName=None,volume=2):
        if(fileName!=None):
            player = self.audio.Audio(path = "/"+folder+"/"+fileName+".wav")
            player.volume(volume)
            # read audio info
            #wav_info = player.play_process(wav_dev)
            #print("wav file head information: ", wav_info)
            player.play_process(self.wav_dev)
            print("start play")
            #self.commCycle("AT+SPEAKER=1")
            commCycle("AT+SPEAKER=1")

            while True:
               ret = player.play()
               if ret == None:
                   print("format error")
                   break
               elif ret==0:
                   print("end")
                   break

            #self.commCycle("AT+SPEAKER=0")
            commCycle("AT+SPEAKER=0")
            player.finish()
            #print(time.time())
            print("play finish")
        else:
            print("fileName error")

from fpioa_manager import fm
from machine import UART
def commCycle(command,timeout=5000): #This controls one command exection cycle.
    uart.write(command + '\r\n')
    myLine = ''
    # while  not  "OK" in myLine:
    #     while not uart.any():
    #         pass
    #     myLine = uart.readline()
    #     print(myLine)


    startTime=time.ticks_ms()
    ifdata=True
    while  not  "OK" in myLine:
        while not uart.any():
            endTime=time.ticks_ms()
            # print(end-start)
            if((endTime-startTime)>=timeout):
                ifdata=False
                break
        if(ifdata):
            myLine = uart.readline()
            print(myLine)
        else:
            print("timeout")
            raise Exception('timeout')
            # break


def readUID(timeout=2000): #This controls one command exection cycle.
    # uart.write('AT+SYSUID' + '\r\n')
    # myLine = ''
    # respUID = ''
    # while  not  "OK" in myLine:
    #     while not uart.any():
    #         pass
    #     myLine = uart.readline()
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
    uart.write('AT+SYSUID' + '\r\n')
    while  not  "OK" in myLine:
        while not uart.any():
            endTime=time.ticks_ms()
            # print(end-start)
            if((endTime-startTime)>=timeout):
                ifdata=False
                break
        if(ifdata):
            myLine = uart.readline()
            print(myLine)
            if "unique id" in myLine:
                myLine=myLine.strip().decode()
                #print(myLine[10:])
                respUID=myLine[10:]

        else:
            print("timeout")
            raise Exception('timeout')
            # break
    return respUID

fm.register(board_info.ESP_UART0RX, fm.fpioa.UART2_TX, force=True)
fm.register(board_info.ESP_UART0TX, fm.fpioa.UART2_RX, force=True)

#uart = UART(UART.UART2, 115200*5, 8, 2, 2, timeout=5000, read_buf_len=40960)
uart = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)
print("load board_sensor finish")