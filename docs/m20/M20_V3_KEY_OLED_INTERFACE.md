# M20 V3 真实按键及OLED呈现

复用独立诊断通过的 `fpga/boards/swcell_k325t/oled_keys.json` 和 `fpga/projects/diagnostics/oled_keys/constraints/io.xdc`，不猜测新引脚。OLED：RST=Y28/DC=M30/SCK=M29/MOSI=N24/CS=P22；UART=W23/V20；系统50MHz/D27。全部3.3V。

|CPU逻辑位|实体键 / 球脚|Snake|Pong|
|---|---|---|---|
|K0 / IN0[0]|KEY2 / AE26|上|左上|
|K1 / IN0[1]|KEY0 / AK28|下|左下|
|K2 / IN0[2]|KEY3 / AG28|左|右球拍上|
|K3 / IN0[3]|KEY1 / AF26|右|右球拍下|
|K4 / IN1[0]|KEY5 / N19|原ROM预留A；FPGA切换游戏并复位|同左|
|K5 / IN1[1]|KEY6 / M19|原CPU程序重启|原ROM预留；板级CPU复位请求|

实体KEY4（AF27）为五向按键的易误触中键，当前无控制作用。F05按用户要求交换：KEY5(A)选择另一ROM并复位，同时仍作为逻辑K4输入，原游戏忽略该逻辑位；KEY7（M27）暂停/继续。切换游戏保持当前运行/暂停请求，暂停时切换后仍须按KEY7恢复。RST_N（N27）复位当前CPU。均低按下，两级同步加20ms独立消抖；IN1高两位由冻结CPU保证0。板级控制不写游戏RAM。F03/F04的KEY5暂停、KEY7切换是历史版本，见[互换记录](M20_V3_KEY_SWAP_F05.md)。

F06进一步按用户要求统一启动入口：**无游戏快照的“M20 CPU BOOT”页面按KEY5启动当前游戏，不切ROM；KEY7只在已有游戏画面时暂停/继续**。暂停切换或复位后出现BOOT页，同样用KEY5进入，替代上段F05的KEY7恢复方式；正常游戏中的切换/暂停映射保持。页面增加`KEY5: START`提示，默认自动运行与UART调试不变。见[F06定位及验证](M20_V3_BOOT_ENTRY_F06.md)。

F04增加独立公共模块`rtl/common/swc_key_event_buffer.sv`：深度8方向按下状态FIFO，动作键sticky；只有实际CPU IN0/IN1退役才确认消费，通过已有CPU节点n0338/n0194观察，不增设游戏运算或修改译码。取样后才到达的事件不能被旧确认清除，FIFO空时保留按住电平。溢出计数饱和上报到UART并点亮LED7，不静默覆盖。用户已确认短按明显改善；消抖仍为20ms，不能保证任意更短脉冲都被接受。单元证据`build/sim/m20_v3/inputs_r1/`，板级证据`board_r9/`及`shuffled_board_r1/`。

OLED复用 `swc_ssd1306` 和已有字体；SPI10MHz（高40ns/低60ns），A0/C0相对原安装方向旋转180°。不重做连通性测试，不处理用户已明确延期的反显白底闪烁。游戏默认黑底正常显示。

`swc_m20_v3_display`明确为 **FPGA State Visualizer**：Pong只读RAM00..09绘球、球拍、8位分数；Snake只读CPU生成的身体占用位图C0..DF、头索引/身体环、食物及状态。可视化模块没有RAM写端口，没有移动、碰撞、得分或食物选择逻辑。按键也不直接改这些变量。

首行显示游戏/分数，HALT/TRAP优先显示异常；Snake死亡后提示B重启。内容传输与游戏tick独立，SPI/CPU频率/游戏速度/面板内部扫描四者不能混称。

未来CPU直接驱动显示可使用现有GPO作为串行输出配合ISA软件例程，但当前原ROM只计算游戏状态；需要安排SPI位流、显示内存/快照和刷新预算，不应把本轮FPGA只读渲染宣传成软件原生OLED驱动。
