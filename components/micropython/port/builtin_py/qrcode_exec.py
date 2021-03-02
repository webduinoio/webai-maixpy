class function:
    def setWiFi(ssid,pwd):
        import machine
        with open('/flash/wifi.json','w') as f:
            #ujson.dump(, f)
            obj = '{"ssid":"%s","pwd":"%s"}'%(ssid,pwd)
            # jsDumps = ujson.dumps(obj)
            # print(jsDumps)
            f.write(obj)
        machine.reset()
    def tackYoloPic():
        print("b")
    def tackMobileNetPic(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,test_gpioA,test_gpioB,dsname,count,cameraFlip,url,hashKey):
        import sensor,image,lcd,time,math
        from fpioa_manager import *
        from Maix import GPIO
        from board_sensor import showMessage
        # def showMessage(msg):
        #     lcd.clear()
        #     lcd.draw_string(int(311-len(msg)*6.9)//2,224//2,msg,lcd.WHITE)


        # test_pinA=7#A
        # fm.fpioa.set_function(test_pinA,fm.fpioa.GPIO7)
        # test_gpioA=GPIO(GPIO.GPIO7,GPIO.IN)
        # test_pinB=16#B
        # fm.fpioa.set_function(test_pinB,fm.fpioa.GPIO6)
        # test_gpioB=GPIO(GPIO.GPIO6,GPIO.IN)


        lcd.init(freq=15000000)
        lcd.clear()
        showMessage("init camera",clear=True)
        sensor.reset(freq=20000000)
        #sensor.reset()

        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.set_windowing((224, 224))
        sensor.skip_frames(time = 2000)

        sensor.set_vflip(0)

        sensor.set_auto_gain(1)
        sensor.set_auto_whitebal(1)
        sensor.set_auto_exposure(1)
        sensor.set_brightness(3)

        sensor.run(1)

        picName=dsname
        picCount=int(count)
        countTmp=0
        # switchObj=0
        # tackPicNum=int(count)
        if SYSTEM_DEFAULT_PATH=="flash":
            savePath="flash"
        else:
            savePath="sd"
        import uos
        try:
            listFile=uos.listdir("/"+savePath)
            for i in listFile:
                # print(i)
                if "picTrain" in i:    
                    uos.remove("/"+savePath+"/"+i)
            del listFile
        except Exception as e:
            print(e)
        tackPicMode=True
        while tackPicMode:
            img = sensor.snapshot()
            img.draw_string(0,0,"take:"+str(countTmp))
            # img.draw_rectangle(40,40,224,224,(255,255,255),2,False)
            # img.draw_rectangle(0,0,224,224,(255,255,255),2,False)
            img.draw_rectangle(40,40,144,144,(255,255,255),2,False)
            img.draw_cross(224//2,224//2,size=10,thickness=3)

            if(test_gpioA.value()==0):
                showMessage("wait save",clear=True)
                img = sensor.snapshot()
                img.save('/'+savePath+'/picTrainMobilenet_'+picName+str(countTmp)+'.jpg')
                countTmp+=1
                # time.sleep(0.5)
                lcd.clear(lcd.BLACK)
            if(test_gpioB.value()==0):
                sensor.set_windowing((320, 224))
                break
            if countTmp==picCount:
                msg="press L Upload             press R Back"
                lcd.draw_string(0,223,msg,lcd.RED,lcd.BLACK)
                while 1:
                    if(test_gpioA.value()==0):
                        # time.sleep(1)
                        bak = time.ticks()
                        uploadStatus=__class__.uploadPic(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,dsname,count,url,hashKey)
                        if uploadStatus==True:
                            print("status:OK")
                            showMessage("ok",clear=True)
                            showMessage("total time:"+str(int((time.ticks() - bak)/1000))+" seconds",x=-1,y=6,center=False,clear=False)
                            msg="                            press R Back"
                            lcd.draw_string(0,223,msg,lcd.RED,lcd.BLACK)
                            while 1:
                                if(test_gpioB.value()==0):
                                    tackPicMode=False
                                    sensor.set_windowing((320, 224))
                                    break
                        else:
                            print("status:error")
                            showMessage("error",clear=True)
                            showMessage("total time:"+str(int((time.ticks() - bak)/1000))+" seconds",x=-1,y=6,center=False,clear=False)
                        break
                    if(test_gpioB.value()==0):
                        tackPicMode=False
                        sensor.set_windowing((320, 224))
                        break
            else:
                lcd.display(img)
                msg="press L Take                press R Back"
                lcd.draw_string(0,223,msg,lcd.RED,lcd.BLACK)

    def downloadModel(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,test_gpioA,test_gpioB,fileName,modelType,url):
        # global SYSTEM_AT_UART
        import time
        import network
        from machine import UART
        from fpioa_manager import fm
        from Maix import GPIO
        import gc
        import time
        from board_sensor import showMessage,lcd
        from board_sensor import commCycle,readUID
        bak = time.ticks()
        fm.register(19, fm.fpioa.GPIOHS0)
        wifiStatusPin = GPIO(GPIO.GPIOHS0, GPIO.IN)

        class MiniHttp:

            def readline(self):
                # return self.raw.readline() # mpy
                data = b""
                while True:
                    tmp = self.raw.recv(1)
                    data += tmp
                    if tmp == b'\n':
                        break
                return data

            def write(self, data):
                # return self.raw.write(data) # mpy
                self.raw.send(bytes(data))

            def read(self, len):
                return self.raw.read(len) # mpy
                # return self.raw.recv(len)

            def __init__(self):
                self.raw = None

            def connect(self, url, timeout=2):
                try:
                    proto, dummy, host, path = url.split("/", 3)
                except ValueError:
                    proto, dummy, host = url.split("/", 2)
                    path = ""

                if proto == "http:":
                    port = 80
                elif proto == "https:":
                    port = 443
                else:
                    raise ValueError("Unsupported protocol: " + proto)

                if ":" in host:
                    host, port = host.split(":", 1)
                    port = int(port)

                import socket
                ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
                ai = ai[0]
                if self.raw is not None:
                    self.raw.close()
                raw = socket.socket(ai[0], ai[1], ai[2])
                raw.settimeout(timeout)

                raw.connect(ai[-1])
                if proto == "https:":
                    import ussl as ssl
                    raw = ssl.wrap_socket(raw, server_hostname=host)
                self.raw = raw
                self.host = bytes(host, "utf-8")
                self.path = bytes(path, "utf-8")

            def exit(self):
                if self.raw != None:
                    self.raw.close()
                    self.raw = None

            def request(self, method, headers={}, data=None):
                try:
                    self.headers = headers
                    self.write(b"%s /%s HTTP/1.1\r\n" % (method, self.path))
                    if not "Host" in headers:
                        self.write(b"Host: %s\r\n" % self.host)
                    # Iterate over keys to avoid tuple alloc
                    for k in headers:
                        self.write(k)
                        self.write(b": ")
                        self.write(headers[k])
                        self.write(b"\r\n")
                    if data:
                        self.write(b"Content-Length: %d\r\n" % len(data))
                    self.write(b"\r\n")
                    if data:
                        self.write(data)
                    l = self.readline()
                    # print(l)
                    l = l.split(None, 2)
                    status = int(l[1])
                    reason = ""
                    response = {}
                    if len(l) > 2:
                        reason = l[2].rstrip()
                    while True:
                        l = self.readline()
                        if not l or l == b"\r\n":
                            break
                        if l.startswith(b"Transfer-Encoding:"):
                            if b"chunked" in l:
                                raise ValueError("Unsupported " + l)
                        elif l.startswith(b"Location:") and not 200 <= status <= 299:
                            raise NotImplementedError("Redirects not yet supported")
                        try:
                            tmp = l.split(b': ')
                            response[tmp[0]] = tmp[1][:-2]
                        except Exception as e:
                            print(e)
                except OSError:
                    self.exit()
                    raise
                return (status, reason, response)


        # fm.register(27, fm.fpioa.UART2_TX, force=True)
        # fm.register(28, fm.fpioa.UART2_RX, force=True)
        # SYSTEM_AT_UART = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)
        # showMessage("upgrade speed",clear=True)
        # pin8285=20
        # fm.register(pin8285, fm.fpioa.GPIO0)
        # reset=GPIO(GPIO.GPIO0,GPIO.OUT)
        # reset.value(0)
        # time.sleep(0.2)
        # reset.value(1)
        # fm.unregister(pin8285)
        # myLine=''
        # while not "init finish" in myLine:
        #     while not SYSTEM_AT_UART.any():
        #         #time.sleep(1)
        #         #print("not data")
        #         pass
        #     myLine = SYSTEM_AT_UART.readline()
        #     print(myLine)
        # time.sleep(0.5)
        #SYSTEM_AT_UART = UART(UART.UART2, 115200, timeout=5000, read_buf_len=40960)
        time.sleep(1)
        #commCycle(SYSTEM_AT_UART,"AT+GMR")
        print("uid:"+readUID(SYSTEM_AT_UART))
        print(globals())
        print(help(SYSTEM_AT_UART))
        commCycle(SYSTEM_AT_UART,"AT+GMR")
        #SYSTEM_AT_UART.write("AT+GMR"+"\r\n")    # Version
        #myLine = ''
        #while not "OK" in myLine:
            #while not SYSTEM_AT_UART.any():
                #pass
            #myLine = SYSTEM_AT_UART.readline()
            #print(myLine)
        #global uart3
        #uart3=SYSTEM_AT_UART
        speed = 115200*40
        commCycle(SYSTEM_AT_UART,"AT+UART_CUR="+str(speed)+",8,1,0,0")
        #SYSTEM_AT_UART.write("AT+UART_CUR="+str(speed)+",8,1,0,0"+"\r\n")    # Version
        #myLine = ''
        #while not "OK" in myLine:
            #while not SYSTEM_AT_UART.any():
                #pass
            #myLine = SYSTEM_AT_UART.readline()
            #print(myLine)
        time.sleep(1)
        SYSTEM_AT_UART = UART(UART.UART2, speed, timeout=5000, read_buf_len=40960)
        time.sleep(1)
        showMessage("wait init",clear=True)
        WIFI_SSID = ""
        WIFI_PASW = ""
        onlineStatus=True
        import ujson
        try:
            with open('/flash/wifi.json','r') as f:
                jsDumps = ujson.load(f)
                print(jsDumps)
                WIFI_SSID=jsDumps['ssid']
                WIFI_PASW=jsDumps['pwd']
                del jsDumps
            del f
        except Exception as e:
            print(e)
            print("not setting wifi")
            onlineStatus=False
        if onlineStatus==True:
            wlan = network.ESP8285(SYSTEM_AT_UART)
            err = 0
            while 1:
                try:
                    wlan.connect(WIFI_SSID, WIFI_PASW)
                except Exception:
                    err += 1
                    print("Connect AP failed, now try again")
                    if err > 1:
                        break
                    #raise Exception("Conenct AP fail")
                    continue
                break
        onlineCheck = 0
        offlineCheck = 0
        print("start check")
        while onlineCheck < 3:
            if wifiStatusPin.value() == 0:
                print("offline")
                offlineCheck+=1
                if offlineCheck>=2:
                    showMessage("init error",clear=True)
                    onlineStatus=False
                    #sys.exit()
            else:
                print("online")
                onlineCheck += 1
            time.sleep(1)
        print("end")
        # bak = time.ticks()
        start = time.time()
        print('start', start)

        #{"type":"download","function":"downloadModel","fileName":"????","url":"http://???????"}

        # fileName="gigoFinal.kmodel"
        # url = 'http://ota.webduino.io/WebAiOTA/monster(green,red,yellow,blue)gcp.kmodel'
        # modelType = "mobileNet"
        if modelType=="yolo":
            modelAddress=0x780000
        else:
            modelAddress=0x950000
        url="http"+url[url.find(":"):]
        downloadStatus=False
        try:
            if onlineStatus == True:
                if SYSTEM_DEFAULT_PATH=="flash":
                    from Maix import utils
                else:
                    sdFile=open('/sd/'+fileName+'.kmodel','w')
                tmp = MiniHttp()
                filename, file_pos, filesize = b'', 0, 0
                block_size = 20480
                block_size = 30720
                block_size = 40000
                errCount=0
                while True:
                    try:
                        if tmp.raw is None:
                            tmp.connect(url, 2)
                        else:
                            if filesize == 0:
                                res = tmp.request(b"HEAD", {b'Connection': b'keep-alive'})
                                print(res)
                                if res[0] == 200:
                                    # b'Accept-Ranges': b'bytes' b'Content-Length': b'16'
                                    print(res[1])
                                    file_pos = 0
                                    # print(res[2])
                                    # b'attachment; filename="test.bin";'
                                    #filename = res[2][b'Content-Disposition'].split(b"=")[1][1:-2]
                                    filesize = int(res[2][b'Content-Length'], 10)
                            else:
                                errCount=0
                                file_end = file_pos + block_size
                                if file_end > filesize:
                                    file_end = filesize
                                headers = {
                                        b'Connection': b'keep-alive',
                                        b'Range': b'bytes=%d-%d' % (file_pos, file_end - 1)
                                }
                                # print(headers)
                                res = tmp.request(b"GET", headers)
                                # print(res[0], res[1])
                                print("debug1")
                                print(res[2][b'Content-Length'])
                                # print(res[2][b'Content-Range'].split(b'/'))
                                data = tmp.read(int(res[2][b'Content-Length'], 10))
                                try:
                                    print(file_pos, len(data))
                                    print("debug2")
                                except Exception as f:
                                    print(f)
                                    print("len err")
                                    continue
                                try:
                                    if len(data) == (file_end - file_pos):
                                        print("debug3")
                                        if SYSTEM_DEFAULT_PATH=="flash":
                                            print("write1")
                                            utils.flash_write(modelAddress + file_pos, data)
                                            print("write2")
                                        else:
                                            print("write1")
                                            sdFile.write(data)
                                            print("write2")
                                        showMessage("download %s"%str(int(file_pos/filesize*100))+"%")
                                        showMessage("total time:"+str(int((time.ticks() - bak)/1000))+" seconds",x=-1,y=6,center=False,clear=False)
                                        if file_end == filesize:
                                            downloadStatus=True
                                            showMessage("please wait",clear=True)
                                            showMessage("total time:"+str(int((time.ticks() - bak)/1000))+" seconds",x=-1,y=6,center=False,clear=False)
                                            break
                                        else:
                                            file_pos = file_end
                                    else:
                                        print("len(data)!=end-pos")
                                except Exception as f:
                                    print(f)
                                    print("len err")
                                    continue

                    except Exception as e:
                        print(e)
                        #showMessage("error",clear=True)
                        print("errorCount:"+str(errCount))
                        time.sleep(2)
                        errCount+=1
                        if errCount>2:
                            raise e
            else:
                showMessage("network error",clear=True)
        except Exception as f:
            print(f)
            print("error>2")
        finally:
            if onlineStatus==True:
                if SYSTEM_DEFAULT_PATH=="sd":
                    try:
                        sdFile.close()
                    except Exception as e:
                        print(e)
                        print("sd close error")
                try:
                    tmp.exit()
                except Exception as e:
                    print(e)
                    print("http close error")
                finally:
                    print("uid:"+readUID(SYSTEM_AT_UART))
                    time.sleep(1)
                    print("uid:"+readUID(SYSTEM_AT_UART))
            print("reset speed")
            time.sleep(1)
            speed = 115200*1
            commCycle(SYSTEM_AT_UART,"AT+UART_CUR="+str(speed)+",8,1,0,0")
            #SYSTEM_AT_UART.write("AT+UART_CUR="+str(speed)+",8,1,0,0"+"\r\n")    # Version
            #myLine = ''
            #while not "OK" in myLine:
                #while not SYSTEM_AT_UART.any():
                    #pass
                #myLine = SYSTEM_AT_UART.readline()
                #print(myLine)
            SYSTEM_AT_UART = UART(UART.UART2, speed, timeout=5000, read_buf_len=40960)
            if downloadStatus==True:
                showMessage("ok",clear=True)
            else:
                showMessage("error",clear=True)
            msg="                            press R Back"
            lcd.draw_string(0,223,msg,lcd.RED,lcd.BLACK)
            while 1:
                if(test_gpioB.value()==0):
                    break
            print(filename, filesize, round(time.time() - start, 1), 'over')
            print('total time ', time.ticks() - bak)

    # def tackMobileNetPic(SYSTEM_DEFAULT_PATH,test_gpioA,test_gpioB,dsname,count,cameraFlip,url,hashKey):

    def uploadPic(SYSTEM_AT_UART,SYSTEM_DEFAULT_PATH,dsname,count,url,hashKey):
        import time
        from fpioa_manager import fm
        from Maix import GPIO
        import gc,time
        from board_sensor import showMessage,lcd
        import network    
        from microWebCli import MicroWebCli
        showMessage("wait init",clear=True)
        #fm.register(19, fm.fpioa.GPIO1)
        #pin8285wifi=GPIO(GPIO.GPIO1,GPIO.IN)
        fm.register(19, fm.fpioa.GPIOHS0)
        wifiStatusPin = GPIO(GPIO.GPIOHS0, GPIO.IN)

        #fm.register(18, fm.fpioa.UART1_RX, force=True)
        #uart = UART(UART.UART1, 115200*1, timeout=5000, read_buf_len=40960)
        #fm.register(27, fm.fpioa.UART2_TX, force=True)
        #fm.register(28, fm.fpioa.UART2_RX, force=True)
        #uart2 = UART(UART.UART2, 115200*1, timeout=5000, read_buf_len=40960)

        # pin8285=20
        # fm.register(pin8285, fm.fpioa.GPIO0)
        # reset=GPIO(GPIO.GPIO0,GPIO.OUT)
        # reset.value(0)
        # time.sleep(0.2)
        # reset.value(1)
        # fm.unregister(pin8285)
        # myLine=''
        # while not "init finish" in myLine:
        #     while not uart2.any():
        #         #time.sleep(1)
        #         #print("not data")
        #         pass
        #     myLine = uart2.readline()
        #     print(myLine)


        #speed=115200*20
        #uart2.write("AT+UART_CUR="+str(speed)+",8,1,0,0"+"\r\n")#Version
        #myLine = ''
        #while  not  "OK" in myLine:
            #while not uart2.any():
                #pass
            #myLine = uart2.readline()
            #print(myLine)

        #time.sleep(1)
        #uart2 = UART(UART.UART2, speed, timeout=5000, read_buf_len=40960)
        #uart2.write('AT+GMR\r\n')
        #myLine = ''
        #while  not  "OK" in myLine:
            #while not uart2.any():
                #pass
            #myLine = uart2.readline()
            #print(myLine)

        #time.sleep(3)
        print("connect wifi")
        WIFI_SSID = ""
        WIFI_PASW = ""
        onlineStatus=True
        import ujson
        try:
            with open('/flash/wifi.json','r') as f:
                jsDumps = ujson.load(f)
                print(jsDumps)
                WIFI_SSID=jsDumps['ssid']
                WIFI_PASW=jsDumps['pwd']
                del jsDumps
            del f
        except Exception as e:
            print(e)
            print("not setting wifi")
            onlineStatus=False
        if onlineStatus==True:
            wlan = network.ESP8285(SYSTEM_AT_UART)
            err = 0
            while 1:
                try:
                    wlan.connect(WIFI_SSID, WIFI_PASW)
                except Exception:
                    err += 1
                    print("Connect AP failed, now try again")
                    if err > 1:
                        break
                    #raise Exception("Conenct AP fail")
                    continue
                break
        onlineCheck = 0
        offlineCheck = 0
        print("start check")
        while onlineCheck < 3:
            if wifiStatusPin.value() == 0:
                print("offline")
                offlineCheck+=1
                if offlineCheck>=2:
                    showMessage("init error",clear=True)
                    onlineStatus=False
                    #sys.exit()
            else:
                print("online")
                onlineCheck += 1
            time.sleep(1)
        print("end")
        del wifiStatusPin,WIFI_SSID,WIFI_PASW,onlineCheck,offlineCheck,onlineStatus
        gc.collect()
        showMessage("uploading...",clear=True)
        import ubinascii,machine
        import uos
        # import urequests,gc
        import gc

        def make_request(data, fileList=None):
            #boundary = ubinascii.hexlify(10).decode('ascii')
            #boundary="57b5c8a55605dab80d665e34b52eee368"
            boundary = "webAI"+ubinascii.hexlify(machine.unique_id()[:14]).decode('ascii')
            # boundary="57b5c8a55605dab80d665e34b52eee370"

            def encode_field(field_name):
                return (
                    b'------%s' % boundary,
                    b'Content-Disposition: form-data; name="%s"' % field_name,
                    b'',
                    b'%s'% data[field_name]
                )

            def encode_file(field_name):
                # filename = field_name[4:]
                filename = field_name[field_name.find("/",1)+1:]
                print(filename)
                gc.collect()
                imageData=None
                with open(field_name, 'rb') as f:
                    imageData = f.read()
                return (
                    b'------%s' % boundary,
                    b'Content-Disposition: form-data; name="%s"; filename="%s"' % ('image', filename),
                    b'Content-Type: image/jpeg'
                    b'',
                    b'',
                    imageData
                )

            lines = []
            for name in data:
                lines.extend(encode_field(name))
            if fileList:
                for i in fileList:
                    lines.extend(encode_file(i))
            lines.extend((b'------%s--' % boundary, b''))
            body = b'\r\n'.join(lines)
            headers = {
                'content-type': 'multipart/form-data; boundary=----' + boundary,
                'content-length': str(len(body)),
                'Connection':'keep-alive'}
            del lines
            gc.collect()
            return body,headers,boundary


        # def upload_image(url, headers, data):
        #     http_response = urequests.post(
        #         url,
        #         headers=headers,
        #         data=data
        #     )
        #     print("response txt")
        #     # print(http_response.text)
        #     if http_response.status_code == 200:
        #         print('Uploaded request')
        #     else:
        #         print("error")
        #     print(help(http_response))
        #     http_response.close()
        #     return http_response.status_code
            
        # data = {"dsname":dsname,"shared":"false"}
        # fileList=[]
        # for i in range(0,int(count)):
        #     # picTrainMobilenet_picName0.jpg
        #     fileList.append('/'+SYSTEM_DEFAULT_PATH+'/picTrainMobilenet_'+dsname+str(i)+'.jpg')
        #     # print(fileList[i])
        # print(fileList)
        # data, headers = make_request(data, fileList)
        # # print(data)
        # # print(headers)
        # # print(url[url.find(":"):])
        # url="http"+url[url.find(":"):]+"?hashkey="+hashKey
        # print(url)
        # try:
        #     r=upload_image(url, headers=headers, data=data)
        #     if r==200:
        #         del data,fileList,headers,url,r
        #         gc.collect()
        #         return True
        #     else:
        #         del data,fileList,headers,url,r
        #         gc.collect()
        #         return False
        # except Exception as e:
        #     print("err")
        #     print(e)
        #     del data,fileList,headers,url
        #     gc.collect()
        #     return False




        gc.collect()
        data = {"dsname":dsname,"shared":"false"}
        fileList=[]
        for i in range(0,int(count)):
            # picTrainMobilenet_picName0.jpg
            fileList.append('/'+SYSTEM_DEFAULT_PATH+'/picTrainMobilenet_'+dsname+str(i)+'.jpg')
            # print(fileList[i])
        print(fileList)
        data, headers, boundary = make_request(data, fileList)
        # print(data)
        # print(headers)
        # print(url[url.find(":"):])
        # url = "https://vision-api.webduino.io/mlapi/datasets/uploadimgs"
        # hashKey="e6d893675bddced7396d254a8bead424"
        url="https"+url[url.find(":"):]+"?hashkey="+hashKey
        wCli = MicroWebCli(url, 'POST')
        # print('POST %s' % wCli.URL)
        print(url)
        print("add ok")
        # print(data)
        print("bodylen:"+str(len(data)))
        try:
            print(boundary)
            wCli.OpenRequest(None, 'multipart/form-data; boundary=----%s' % boundary, str(len(data)))
            print("write")
            wCli._write(data)
            print("write end")
            resp = wCli.GetResponse()
            if resp.IsSuccess():
                o = resp.ReadContent()
                print('POST success', o)
                del resp,o
                if wCli.IsClosed==False:
                    wCli.Close()
                    del wCli
                gc.collect()
                del data,fileList,headers,url
                return True
            else:
                print('POST return %d code (%s)' %(resp.GetStatusCode(), resp.GetStatusMessage()))
                del resp
                if wCli.IsClosed==False:
                    wCli.Close()
                    del wCli
                gc.collect()
                del data,fileList,headers,url
                return False
        except Exception as e:
            print("err")
            print(e)
            del data,fileList,headers,url
            try:
                del resp
            except Exception as f:
                print(f)
                print("error gc")
            try:
                wCli.Close()
                del wCli
            except Exception as f:
                print(f)
                print("error gc")
            gc.collect()
            return False

        # print('Uploading request success')
        #uart2.write("AT+UART_CUR="+str(115200)+",8,1,0,0"+"\r\n")#Version
        #myLine = ''
        #while  not  "OK" in myLine:
            #while not uart2.any():
                #pass
            #myLine = uart2.readline()
            #print(myLine)


print("load qrcode_exec finish")
    