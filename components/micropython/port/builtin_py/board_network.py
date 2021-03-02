# from board_sensor import SYSTEM_AT_UART as uart
from board import board_info,fpioaMapGPIO
from Maix import GPIO
from fpioa_manager import fm
import time

class Network_Blockly:
    def __init__(self,SYSTEM_AT_UART,SSID,PWD):
        import network, socket
        pin8285=20
        fm.register(pin8285, fm.fpioa.GPIO0,force=True)
        reset=GPIO(GPIO.GPIO0,GPIO.OUT)
        reset.value(0)
        time.sleep(0.01)
        reset.value(1)
        # time.sleep(0.5)
        fm.unregister(pin8285)
        myLine = ''
        while  not  "init finish" in myLine:
            while not SYSTEM_AT_UART.any():
                pass
            myLine = SYSTEM_AT_UART.readline()
        wlan = network.ESP8285(SYSTEM_AT_UART)
        err = 0
        while 1:
            try:
                wlan.connect(SSID, PWD)
            except Exception:
                err += 1
                print("Connect AP failed, now try again")
                if err > 3:
                    raise Exception("Conenct AP fail")
                continue
            break
        #time.sleep(1)
        self.WiFiInfo=wlan.ifconfig()
        del err,wlan
        print(self.WiFiInfo)
        time.sleep(1)
    def info(self):
        return self.WiFiInfo
    def __del__(self):
        del self
        print("Network_Blockly __del__")
class Mqtt_Blockly:
    def __init__(self,SYSTEM_AT_UART):
        from board_sensor import commCycle,readUID
        self.commCycle=commCycle
        self.mqttUID=readUID(SYSTEM_AT_UART)
        self.SYSTEM_AT_UART=SYSTEM_AT_UART
    def sub(self,topic):
        print("subscribe topic ...")
        mqttSetSub='AT+MQTT="sub","{topic}"'.format(topic=topic)
        self.commCycle(self.SYSTEM_AT_UART,mqttSetSub)
        print("subscribe "+topic+" finish")
        time.sleep(0.5)
    def push(self,topic,msg):
        mqttSetPush='AT+MQTT="push","{topic}","{msg}"'.format(topic=topic,msg=msg)
        self.commCycle(self.SYSTEM_AT_UART,mqttSetPush)
        time.sleep(0.15)
    def subID(self,topic):
        print("subscribeID topic ...")
        mqttSetSub='AT+MQTT="sub","{mqttUID}/{topic}"'.format(mqttUID=self.mqttUID,topic=topic)
        self.commCycle(self.SYSTEM_AT_UART,mqttSetSub)
        print("subscribeID "+topic+" finish")
        time.sleep(0.5)
    def pushID(self,topic,msg):
        mqttSetPush='AT+MQTT="push","{mqttUID}/{topic}","{msg}"'.format(mqttUID=self.mqttUID,topic=topic,msg=msg)
        self.commCycle(self.SYSTEM_AT_UART,mqttSetPush)
        time.sleep(0.15)
    def waitMsg(self):
        try:
            if self.SYSTEM_AT_UART.any():
                myLine = self.SYSTEM_AT_UART.readline()
                # print(myLine)
                subscribeMsg=myLine.decode().strip()
                if "mqtt" in subscribeMsg[0:4]:            
                    subscribeMsg=subscribeMsg.split(',')
                    # print( [True,[None,subscribeMsg[1],None,subscribeMsg[2]]])
                    return [True,[None,subscribeMsg[1],None,subscribeMsg[2]]]
                else:
                    return [False,[None,None,None,None]]
            else:
                return [False,[None,None,None,None]]
        except Exception as e:
            print(e)
            return [False,[None,None,None,None]]

    def __del__(self):
        del self
        print("Mqtt_Blockly __del__")



# class Mqtt_Blockly:
#     def __init__(self):
#         from board_sensor import readUID,commCycle
#         #time.sleep(5)
#         self.commCycle=commCycle
#         mqttUID=readUID()
#         mqttSetConfig='AT+MQTTUSERCFG=0,1,"{mqttUID}","mqttAccount","mqttPassword",0,0,""'.format(mqttUID=mqttUID)
#         # try:
#         #     self.commCycle(self.SYSTEM_AT_UART,'AT+MQTTCLEAN=0',2000)
#         # except Exception as e:
#         #     print(e)
#         try:
#             self.commCycle(self.SYSTEM_AT_UART,mqttSetConfig)
#         except Exception as e:
#             print(e)
#         self.commCycle(self.SYSTEM_AT_UART,'AT+MQTTUSERCFG?')
#         self.commCycle(self.SYSTEM_AT_UART,'AT+MQTTCONNCFG?')
#         print("connect MQTT ...")
#         try:
#             self.commCycle(self.SYSTEM_AT_UART,'AT+MQTTCONN=0,"mqttServer",mqttPort,1')
#         except Exception as e:
#             print(e)
#         #time.sleep(3)
#         print("connect finish")
#         time.sleep(1)
#     def sub(self,topic):
#         print("subscribe topic ...")
#         mqttSetSub='AT+MQTTSUB=0,"{topic}",1'.format(topic=topic)
#         self.commCycle(self.SYSTEM_AT_UART,mqttSetSub)
#         print("subscribe "+topic+" finish")
#         time.sleep(1)
#     def push(self,topic,msg):
#         mqttSetPush='AT+MQTTPUB=0,"{topic}","{msg}",1,0'.format(topic=topic,msg=msg)
#         self.commCycle(self.SYSTEM_AT_UART,mqttSetPush)
#         time.sleep(0.15)
#     def waitMsg(self):
#         try:
#             if uart.any():
#                 myLine = uart.readline()
#                 print(myLine)
#                 subscribeMsg=myLine.decode().strip()
#                 subscribeMsg=subscribeMsg.split(',',3)
#                 subscribeMsg[1]=subscribeMsg[1].replace("\"","")
#                 return [True,subscribeMsg]
#             else:
#                 return [False,[None,None,None,None]]
#         except Exception as e:
#             print(e)
#             return [False,[None,None,None,None]]
# [True, ['+MQTTSUBRECV:0', 'k210test', '3', 'lll']]
# [uart any,[always 0,topic,datalen,data]]

    def __del__(self):
        del self
        print("Mqtt_Blockly __del__")
print("load board_network finish")