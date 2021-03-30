if deployFlag:
    from webai_blockly import Mqtt
    Mqtt.pushID("PONG", "ready")
    print("deploy true,run main.py")
else:
    import webai_blockly
    from machine import UART
    webai_blockly.SYSTEM_LOG_UART = UART(UART.UART3, 115200, timeout=5000,read_buf_len=10240, callback=webai_blockly.MQTT_CALLBACK)
    raise Exception("deploy false,run repl")