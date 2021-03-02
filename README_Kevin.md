### 基本說明
k210是kendryte公司旗下的一個晶片，開發SDK有兩個，分別是standalone-sdk與freertos-sdk，[MaixPy](https://github.com/sipeed/MaixPy)是基於[kendryte-standalone-sdk](https://github.com/kendryte/kendryte-standalone-sdk)的MicroPython，還有另一個基於[kendryte-freertos-sdk](https://github.com/kendryte/kendryte-freertos-sdk
)的[專案](https://github.com/loboris/MicroPython_K210_LoBo)，我個人是認為freertos的比較好，但目前是用MaixPy，相關文件請至[maixpy官方文件](https://maixpy.sipeed.com/zh/)看會更清楚，主要需要理解的是[進階開發](https://maixpy.sipeed.com/zh/course/advance/project_framework.html)內的東西，可以全部都看，但主要用到的是目錄結構、用C新增MicroPython library與打包file system，打包file system我們應該會用到，但我也還沒試過

看完目錄結構之後，就會知道如果要改程式要到哪裡改了
```
└── components
|   └── drivers
|       └── ...
|   └── micropython
|       ├── CMakeLists.txt
|       ├── Kconfig.txt
|       └── port
|           └── builtin_py
|               └── ...
|           └── include
|               └── mpconfigport.h
|           └── src
|               └── audio
|                   └── ...
|               └── modules
|                   └── ...
|               └── omv
|                   └── ...
|               └── speech
|                   └── ...
|               └── standard_lib
|                   └── ...
|               └── maixpy_main.c
├── tools
|   └── flash
|       └── kflash_py
|           └── kflash.py
```

driver:有關硬體驅動的程式碼，有需要再改
micropython/CMakeLists.txt與Kconfig.txt:有需要在port/builtin_py新增library時就要來這邊新增
micropython/port/builtin_py:「python」library，不是C語言寫的哦，是純python
micropython/port/include/mpconfigport.h:函式庫啟用相關設定
micropython/port/src/audio:聲音輸出入的C與C Python library
micropython/port/src/modules:內建的幾個模組，我們有用到的是hcsr04與ws2812
micropython/port/src/omv:openmv相關演算法與ide相關程式
micropython/port/src/speech:語音辨識相關程式
micropython/port/src/standard_lib:i2c、pwm、sdcard、spi、timer、uart、wdt、machine、network、socket、os、time的C
micropython/port/src/maixpy_main.c:程式的入口點，前半部C語言硬體初始化後，開始執行micropython的task
tool/

### 執行流程
板子一上電會執行maixpy_main，先進行硬體相關初始化，完成後執行micropython task，micropython開始會先執行`_boot.py`，這個`_boot.py`是包在底層，使用者沒機會修改，接著執行`boot.py`，最後執行`main.py`，裡面做的事情詳細敘述如下：

`_boot.py`:
- 掛載flash與sd到filesystem
- 停頓200ms(此時可被uart中斷，就不繼續執行`boot.py`與`main.py`，這是留給maixpy_ide用的)
- `boot.py`與`main.py`檔案檢查，不存在就寫入當前儲存媒體(flash或sd卡)
- 輸出k210、8285版本與deviceID
- 停頓200ms(同上)

`boot.py`:
- LR按鈕偵測
- 倒數計時計數器
- WiFi檢查
- qrcode模式
    - WiFi設定
    - 影像取材yolo
    - 影像取材mobileNet
    - 下載模型

`main.py`:
使用者自己寫的程式

version、IO、ADC與MQTT等，流程圖如下：
```flow
st=>start: start
op1=>operation: startup.c
op2=>operation: app_main.c
e=>end
st->op1->op2->e
```

### 初始化
- clone project
預設應該在webAI，如果不是就checkout到webAI
`git clone https://git.kingkit.codes/kevin/esp-at`
- config
等他clone依賴套件，之後會出現GUI可以設定，直接離開不要儲存設定，直接用原本的sdkconfig就可以了，後需有需要在進來修改
`make menuconfig`
### 編譯
- build
`make`
- erase
如果有遇到很奇怪的bug或者修改程式碼後沒動作，請執行erase
 `python esptool.py --chip esp8266 --port /dev/<port> --baud 230400 --before default_reset --after hard_reset erase_flash`
 ### 燒錄
virtualbox只做編譯，燒錄請到mac燒錄，使用esptool
 - 完整燒錄
 `python esptool.py --chip esp8266 --port /dev/<port> --baud 230400 --before default_reset --after hard_reset write_flash -z --flash_mode dout --flash_freq 80m --flash_size 2MB 0x9000 <path>/esp-at/build/ota_data_initial.bin 0x0000 <path>/esp-at/build/bootloader/bootloader.bin 0xF0000 <path>/esp-at/build/at_customize.bin 0xF1000 <path>/esp-at/build/customized_partitions/factory_param.bin 0xF2000 <path>/esp-at/build/customized_partitions/server_cert.bin 0xF4000 <path>/esp-at/build/customized_partitions/server_key.bin 0xF6000 <path>/esp-at/build/customized_partitions/server_ca.bin 0xF8000 <path>/esp-at/build/customized_partitions/client_cert.bin 0xFA000 <path>/esp-at/build/customized_partitions/client_key.bin 0xFC000 <path>/esp-at/build/customized_partitions/client_ca.bin 0x10000 <path>/esp-at/build/esp-at.bin 0x8000 <path>/esp-at/build/partitions_at.bin`

- 部分燒錄
之前釋出的版本都已經是燒錄過上面的韌體的版本，平常更新的程式只更新esp-at.bin，所以可以只燒錄esp-at.bin，但不建議，我沒這樣試過，只是照邏輯來說是可以的，平常我都用完整燒錄
 `python esptool.py --chip esp8266 --port /dev/<port> --baud 230400 --before default_reset --after hard_reset write_flash -z --flash_mode dout --flash_freq 80m --flash_size 2MB 0x10000 <path>/esp-at/build/esp-at.bin`