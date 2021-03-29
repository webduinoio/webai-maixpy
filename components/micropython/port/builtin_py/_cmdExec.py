from webai_api import takeMobileNetPic,downloadModel,downloadFile
import gc,os,lcd
import ujson
gc.collect()
resetFlag=False
cmdFlag=True
qrcodeFlag=True
deployFlag=False
try:
    lcd.init()
    with open('/flash/cmd.txt', 'r') as f:
        mqttJsonData = f.read()
    del f
    with open('/flash/cmd.txt', 'w') as f:
        f.write("")
    del f
    os.sync()
    print("mqtt txt1:"+mqttJsonData)
    if mqttJsonData == "":
        print("cmd.txt content is null")
        cmdFlag=False
    elif mqttJsonData.find("_DEPLOY/") == 0:
        # downloadModel('main.py', 'yolo',
        #               mqttJsonData[mqttJsonData.find("/")+1:], True)
        # downloadFile('main.py',mqttJsonData[mqttJsonData.find("/")+1:]+str(time.ticks_cpu()))
        downloadFile('main.py',mqttJsonData[mqttJsonData.find("/")+1:])
        deployFlag=True
    elif mqttJsonData.find("_TAKEPIC_YOLO/") == 0:
        print("_TAKEPIC_YOLO")
    elif mqttJsonData.find("_TAKEPIC_MOBILENET/") == 0:
        mqttJsonData = ujson.loads(mqttJsonData[mqttJsonData.find("/")+1:])
        print(mqttJsonData)
        takeMobileNetPic(mqttJsonData['dsname'], mqttJsonData['count'],
                            1, mqttJsonData['url'], mqttJsonData['hashKey'])
    elif mqttJsonData.find("_DOWNLOAD_MODEL/") == 0:
        mqttJsonData = ujson.loads(mqttJsonData[mqttJsonData.find("/")+1:])
        downloadModel(
            mqttJsonData['fileName'], mqttJsonData['modelType'], mqttJsonData['url'])
        # resetFlag=True
    elif mqttJsonData.find("_DOWNLOAD_FILE/") == 0:
        mqttJsonData = ujson.loads(mqttJsonData[mqttJsonData.find("/")+1:])
        # downloadFile(mqttJsonData['fileName'],mqttJsonData['url']+str(time.ticks_cpu()))
        downloadFile(mqttJsonData['fileName'],mqttJsonData['url'])
        # downloadModel(mqttJsonData['fileName'],
        #               'yolo', mqttJsonData['url'], True)
        # resetFlag=True
    else:
        print("mqtt txt2:"+mqttJsonData)
    del mqttJsonData

    with open('/flash/qrcode.cmd', 'r') as f:
        QRCodeJsonData = f.read()
    del f
    with open('/flash/qrcode.cmd', 'w') as f:
        f.write("")
    del f
    os.sync()
    if QRCodeJsonData == "":
        print("qrcode.cmd content is null")
        qrcodeFlag=False
    else:
        QRCodeJsonData = ujson.loads(QRCodeJsonData)
        #print(QRCodeJsonData)
        for i in QRCodeJsonData:
            #print(i)
            dataParse = ujson.dumps(i['data'])
            dataParse = ujson.loads(dataParse)
            #print(dataParse)
            if i['cmd']=="downloadModel":
                print(dataParse)
                downloadModel(
                    dataParse['fileName'], dataParse['modelType'], dataParse['url'])
            elif i['cmd']=="deploy":
                print(dataParse)
                # downloadModel('main.py', 'yolo',
                #             dataParse['url'], True)
                # downloadFile('main.py',dataParse['url']+str(time.ticks_cpu()))
                downloadFile('main.py',dataParse['url'])
                deployFlag=True
    del QRCodeJsonData

except Exception as e:
    print(e)
    sys.print_exception(e)
    print("not find cmd.txt")
finally:
    gc.collect()
    if (not cmdFlag) and  (not qrcodeFlag):
        raise Exception("cmd false,run boot.py")
    # print("wait interrupt")
    # time.sleep(3)
    # raise Exception("_mqtt error")