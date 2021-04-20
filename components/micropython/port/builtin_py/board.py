import gc
import uos
import json
from Maix import config

class board_info:
    def set(key, value=None):
        return setattr(__class__, key, value)

    def all():
        return dir(__class__)

    def get():
        return getattr(__class__, key)

    def load(__map__={}):
        for k, v in __map__.items():
            __class__.set(k, v)


webAIVersion = uos.uname()
configFile = {
    "type": "ai",
    "version": webAIVersion[5],
    "board_info": {
        'P0': 24,
        'P1': 25,
        'P2': 26,
        'P3': 6,
        'P4': None,  # esp adc
        'P5': 7,
        'P6': 8,
        'P7': 9,
        'P8': 10,
        'P9': 11,
        'P10': 22,
        'P11': 16,
        'P12': 23,  # LCDPWM?
        'P13': 0,
        'P14': 1,
        'P15': 2,
        'P16': 3,
        'P19': 17,
        'P20': 15,
        'UARTHS_RX': 4,
        'UARTHS_TX': 5,
        'MIC_I2S_IN': 12,
        'MIC_I2S_WS': 13,
        'MIC_I2S_SCLK': 14,
        'BOOT': 16,
        'I2C_SDA': 15,
        'I2C_SCLK': 17,
        'ESP_UART1RX': 18,
        'ESP_UART1TX': 19,
        'ESP_RST': 20,
        'ESP_XPD': 21,
        'LCDPWM': 23,
        'ESP_UART0RX': 27,
        'ESP_UART0TX': 28,
        'SPK_I2S_OUT': 33,
        'SPK_I2S_WS': 34,
        'SPK_I2S_SCLK': 35
    }
}
cfg = json.dumps(configFile)
#print(cfg)
try:
    with open('/flash/config.json', 'rb') as f:
        tmp = json.loads(f.read())
        if tmp["version"] != configFile["version"]:
            raise Exception('config.json no exist')
except Exception as e:
    with open('/flash/config.json', "w") as f:
        f.write(cfg)
    try:
        uos.remove('/flash/boot.py')
    except Exception as f:
        print("del /flash/boot.py")
    try:
        uos.remove('/sd/boot.py')
    except Exception as f:
        print("del /sd/boot.py")
    uos.sync()
    import machine
    machine.reset()

print("init board_info")
gc.collect()
print(config.__init__())
tmp = config.get_value('board_info', None)
if tmp != None:
    board_info.load(tmp)
else:
    print('[Warning] Not loaded from /flash/config.json to board_info.')
    board_info.load(configFile)
del webAIVersion, configFile, cfg
