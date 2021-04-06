### 基本說明
k210是kendryte公司旗下的一個晶片，開發SDK有兩個，分別是standalone-sdk與freertos-sdk，[MaixPy](https://github.com/sipeed/MaixPy)是基於[kendryte-standalone-sdk](https://github.com/kendryte/kendryte-standalone-sdk)的MicroPython，還有另一個基於[kendryte-freertos-sdk](https://github.com/kendryte/kendryte-freertos-sdk
的[專案](https://github.com/loboris/MicroPython_K210_LoBo)，我個人是認為freertos的比較好(前陣子公告停更了，但我還是覺得freertos比較好)，但目前是用MaixPy，相關文件請至[maixpy官方文件](https://maixpy.sipeed.com/zh/)看會更清楚，主要需要理解的是[進階開發](https://maixpy.sipeed.com/zh/course/advance/project_framework.html)內的東西，可以全部都看，但主要用到的是目錄結構、用C新增MicroPython library與打包file system，打包file system目前已經成功，可是有遇到一點問題，後面會提到

目錄結構如下，看完就會知道如果要改程式要到哪裡改了
```
└── components
│   ├── drivers
│   │   ├── CMakeLists.txt
│   │   └── Kconfig
│   └── micropython
│       ├── CMakeLists.txt
│       ├── Kconfig
│       └── port
│           ├── builtin_py
│           │   ├── _boot.py
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
└── tools
    ├── docker
    │   ├── Dockerfile
    │   └── README.md
    ├── flash
    │   └── kflash_py
    │       └── kflash.py
    ├── release
    │   ├── readme.txt
    │   └── release.sh
    └── spiffs
        ├── README.md
        ├── gen_spiffs_image.py
        ├── fs
        │   └── ...
        └── mkspiffs
```

driver:有關硬體驅動的程式碼，有需要再改
micropython/CMakeLists.txt與Kconfig.txt:有需要在port/builtin_py新增library時就要來這邊新增
micropython/port/builtin_py:「python」library，不是C語言寫的哦，是純python
micropython/port/include/mpconfigport.h:函式庫啟用相關設定與版本號設定
micropython/port/src/audio:聲音輸出入的C與C Python library
micropython/port/src/modules:內建的幾個模組，我們有用到的是hcsr04與ws2812
micropython/port/src/omv:openmv相關演算法與ide相關程式
micropython/port/src/speech:語音辨識相關程式
micropython/port/src/standard_lib:i2c、pwm、sdcard、spi、timer、uart、wdt、machine、network、socket、os、time的C
特別需要注意的是目前i2c已經跟官方版本有很大的落差，其餘的沒有去確認

micropython/port/src/maixpy_main.c:程式的入口點，前半部C語言硬體初始化後，開始執行micropython的task

tool/spiffs:只能在linux環境下打包file system，在fs放入檔案，之後打包，目前有發現如果file system太小(1MB)很容易有問題，放大到3MB後就幾乎沒出狀況了，依照測試狀況推測，用到超過總容量的1/4後有可能會產生問題
```
python gen_spiffs_image.py ../../projects/maixpy_k210_minimum/config_defaults.mk
```
### 執行流程
板子一上電會執行maixpy_main，先進行硬體相關初始化，完成後執行micropython task，micropython開始會先執行`_boot.py`，這個`_boot.py`是包在底層，使用者沒機會修改，接著執行`_cmdExec.py`，此時會檢查「是不是手動reset或插電開機」，如果「是」就會依序執行`boot.py`與`main.py`，如果「不是」則會執行`_cmdCheck.py`，檢查「是不是部署程式碼」如果是則直接執行`main.py`，如果「不是」代表是mqtt控制指令，指令完成後進入`repl(交互模式)`，mqtt指令有拍照，下載模型等，裡面做的事情詳細敘述如下：

`_boot.py`:
- 掛載flash與sd到filesystem
- lcd初始化
- 檢查有沒有按下L鍵，有的話重置檔案(```boot.py、main.py、cmd.txt、qrcode.cmd與wifi.json```)
- 停頓200ms(此時可被uart中斷，就不繼續執行後續程式，這是留給maixpy_ide用的)
- `boot.py`與`main.py`檔案檢查，不存在就寫入當前儲存媒體(flash或sd卡)
- webai_blockly初始化，輸出k210、8285版本與deviceID
- 開機logo
- 開機音效

`_cmdExec`:
- 讀取與執行cmd指令
- 讀取與執行qrcode指令(qrcode可以是直接執行指令或暫存指令，重開機後馬上執行)
- 如果沒有執行任何指令，表示是reset或斷電重啟，就會執行`boot.py`

`_cmdCheck`:
- 檢查是否是使用mqtt部署程式，是的話下載完`main.py`後會直接執行`main.py`

`boot.py`:
- LR按鈕偵測
- 倒數計時計數器
- WiFi檢查
- qrcode模式
    - WiFi設定
    - 執行內建範例

`main.py`:
使用者自己寫的程式，預設是Webduino WebAI

流程圖如下：
```flow
st=>start: power up
op1=>operation: maixpy_main.c
op2=>operation: hardware init
op3=>operation: micropython task
_boot=>operation: _boot.py
exec=>operation: exec
_cmdExec=>condition: _cmdExec
_cmdCheck=>condition: deploy mode?
boot=>operation: boot.py
main=>operation: main.py
repl=>operation: repl
showboot=>condition: show boot?
e=>end

st->op1->op2->op3->_boot->_cmdExec
_cmdExec(yes)->exec->_cmdCheck->repl
_cmdExec(no,right)->boot->main->repl
_cmdCheck(yes,right)->main->relp
_cmdCheck(no,left)->repl
main->repl
repl->e
```

### 編譯相關請到另一份文件看