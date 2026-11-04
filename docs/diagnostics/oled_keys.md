# swcell_k325t独立OLED/按键/LED验证

2026-11-04，开发验证中。此项目不依赖M20 CPU或M11功能测试；目录整理已先提交70daf6f。用户已授权本次通过检查后的JTAG下载/UART采集，不写Flash。

## 连接

所有IO为3.3V，默认系统时钟50MHz/D27。OLED为SSD1306 128×64、4线SPI，模块自身必须已选择SPI模式并供电/共地。

|信号|FPGA引脚|含义|
|---|---|---|
|OLED_RST_N /DC /SCK /MOSI /CS_N|Y28 /M30 /M29 /N24 /P22|复位低有效，数据在SCK上升沿采样，MSB先发|
|RST_N|N27|低按下，作为第9个待测输入，不复位FPGA|
|KEY0..7|AK28 /AF26 /AE26 /AG28 /AF27 /N19 /M19 /M27|低按下，逐位消抖|
|LED0..7|AD27 /AD28 /AE29 /AD29 /AB28 /AA27 /Y30 /Y29|低亮，严格对应KEY0..7|
|UART_TX /RXD|W23 /V20|115200、8N1；/dev/ttyUSB1|

引脚权威表为 `fpga/boards/swcell_k325t/oled_keys.json`；本工程独立io.xdc，不加载旧三色LED/M11约束。

## 显示与操作

上电内部POR100ms，OLED复位低10ms、释放后10ms，初始化/清零GDDRAM、AF开启后等待100ms。通常约0.222s可开始自检。8种全屏图案各约1s：黑、白、8像素棋盘、1像素棋盘反显、竖条、横条、边框/对角线、移动十字。自动结束进入8行按键状态页。

任意键按下切实时页。RST_N短按切正反显，长按至少2s后释放重播自检；KEY始终直接映射对应LED，不以自检灯效掩盖。多键位图、每键按下次数、最后事件、已见掩码/计数都会保留。SPI整帧输入快照（OLED不是双缓冲，不承诺物理扫描无撕裂），按键20ms独立过滤；当前OLEDKEYS04每帧0.98516ms发送＋16ms间隔及握手，共16.98518ms，58.874854fps（50MHz默认配置XSIM周期计数），按键到显示有过滤/下一帧延迟。

先观察完整自检约9秒，然后按KEY0..7及RST_N逐一按下、释放各至少0.2s，核对屏幕标签和LED；再试多键与短促抖动、RST_N长按重播。SPI无读回/ACK；UART的oled字段只表示驱动已完成初始化发送，不证明OLED真正亮。

## UART与采集

IO_STATE是原子快照，keys/seen为3位HEX（bit0..7=KEY，bit8=RST_N），events/presses/frame/up/merged为HEX计数。presses为9个32位按下计数，前8是KEY、最后RST；mode0..7图案、8实时页，patterns累计已发送图案掩码。UART繁忙期间合并状态，merged可观测合并次数；事件计数仍保存，不能把快照条数当按键事件数。

```bash
build/venvs/python312/bin/python host/python/swcell_io_diag.py --port /dev/ttyUSB1 --duration 180 --probe-rx
# 离线重新解析，保存raw/CSV/summary/metadata到新目录
build/venvs/python312/bin/python host/python/swcell_io_diag.py --input results/BOARD_IO/RUN/raw.jsonl --output build/IO_REPLAY
```

采集检测FPGA重启后分代计算覆盖。raw.jsonl保存原始字节，states.csv为整数，summary保留输入覆盖、图案已发送、视觉未确认。probe-rx仅发送8个0x55以观察RX低活动，未实现UART命令协议，不影响OLED。

## 设计依据与验证边界

初始化与SPI按Solomon Systech SSD1306 Rev1.5的4-wire接口/命令及Table13-4设计，参考[原厂撰写数据手册（RS镜像）](https://docs.rs-online.com/5182/A700000012854741.pdf)。其串行周期下限100ns、数据建立/保持15ns；本工程当前默认周期100ns、高40ns/低60ns（common SPI/SSD驱动未覆写时仍兼容原1MHz），复位远大于3µs，AF后保留100ms。模块电源上升、PCB/线缆和IO边沿未外部标定，数字时序/内部STA不冒充外部电气签核。

公共SPI/SSD1306以req/valid提供像素流，未来可接 framebuffer。独立接收模型从实际CS/SCK/DC/MOSI重建1024字节RAM，检查命令、清屏、图案、文字数位、有效时序；真实UART_TX也由TB解码。FPGA工程检查setup/hold/pulse/DRC与引脚，任何失败不得下载。

## 实测与版本区分

原OLEDKEYS01：1MHz SPI，40ms帧间隔，2450022个系统周期/帧=20.407980Hz。用户已确认8类图案、文字、9键与8LED对应、多键等功能正常，但反显白底整体明暗闪动，板卡安装方向需翻转。该轮原始数据 `results/BOARD_IO/20261104_160402_oled_connected/`：859条有效状态、116次按下/232次按下释放事件，9键两种电平均被采集；38条未识别启动输入原样保留。原镜像/源SHA快照在 `build/oled_keys_20261104/r2_hardware_pass_before_rotation/`。

当前OLEDKEYS04：旋转180°（A0/C0，相对原A1/C8同时反转两轴）；只在反显变化时发A6/A7。SPI HIGH_CYCLES=2、LOW_CYCLES=3，50MHz÷5=10MHz；FRAME_GAP_CYCLES=800000，PATTERN_FRAMES=60，每图约1.019s。TB使用生产SPI/间隔默认值，断言SCK周期100ns、高40ns，帧周期不超过1000000系统周期（至少50Hz）。独立模型同时验证common默认原方向与板级180°方向、各图案1024字节、真实UART及每键状态。

|配置|SPI|完整帧周期（50MHz周期数）|内容更新率|用途|
|---|---:|---:|---:|---|
|OLEDKEYS01|1MHz|2450022|20.407980Hz|原实物功能确认，白底闪烁保留|
|OLEDKEYS02|1MHz|2449595|20.411537Hz|旋转/仅变化发反显命令；短暂下载，未获目视复验|
|OLEDKEYS03|10MHz|2049259|24.399063Hz|40ms间隔仿真；用户提高帧率要求后停止实现，未下载|
|OLEDKEYS04|10MHz|849259|58.874854Hz|16ms间隔；当前仿真/Python通过，实现及实物状态见任务记录|

上述数值是RTL/XSIM推导，未用示波器标定。SSD1306从显存自行扫描，不能将内容更新率当作面板扫描频率。D5=80、D9=F1、contrast=7F等扫描/亮度参数未变；全白大面积点亮时的供电、驱动器内部扫描及相机混叠都尚未实测。提高SPI/内容更新率后需用户观察比较，不能把闪烁原因预先归结为低刷新率。

首次 `results/BOARD_IO/20261104_154609_oled_keys/` 未接OLED，无按键操作，作为诊断记录保留，不参与实体显示验收。详细测试/下载状态见[任务记录](../tasks/oled-keys-20261104.md)。
