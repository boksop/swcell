# M20 V3：结构级CPU FPGA原型

本工程复用已实测OLED/按键引脚与驱动。板卡XC7K325T-2FFG900C，50MHz，所有用户IO为3.3V。组合CPU是冻结V21的477颗MUX逐连接派生；ISA和两款游戏原ROM不改。

`FUNCTIONAL_STORAGE`保留477个可追溯LUT3实例、以33个原生FF存储状态，已完成初次综合/实现/STA和JTAG/UART运行。`STRICT_MUX`还保留66个反馈存储MUX，实际布局布线后85个LUTLP-1违规；没有生成/下载严格模式bit，不关闭DRC。数字双锁存器仿真通过不等于该反馈电路适合FPGA物理实现。

## 构建与复现

所有构建输出须使用新目录，不覆盖旧证据：

```bash
cd /home/boksop/swcell
build/venvs/python312/bin/python tools/m20/v3_generate.py --output build/m20_v3_regenerated
bash sim/scripts/run_m20_v3_core.sh       # 原87场景/57331事件、非法/算术/访存
bash sim/scripts/run_m20_v3_system.sh     # 新同步内存、F/S模型、两游戏64tick与Python
bash sim/scripts/run_m20_v3_board.sh      # 真实按键映射、SPI像素、8N1 UART及控制
vivado -mode batch -source "$PWD/fpga/projects/m20/cpu_validation/scripts/build.tcl" \
  -tclargs --mode FUNCTIONAL_STORAGE --output build/fpga/m20/cpu_validation/run_new
```

原版游戏F04镜像保存在 `build/fpga/m20/cpu_validation/functional_r6/swcell_m20_v3_top.bit`。当前推荐镜像为F06启动入口＋键位互换＋固定乱序食物变体 `build/fpga/m20/cpu_validation/snake_shuffled_boot_r1/swcell_m20_v3_top.bit`；[F06验证/下载状态](../../../../docs/m20/M20_V3_BOOT_ENTRY_F06.md)、[F05历史互换验证](../../../../docs/m20/M20_V3_KEY_SWAP_F05.md)、[变体说明与旧镜像回退](../../../../docs/m20/M20_V3_SNAKE_SHUFFLED.md)。仅在完成仿真及STA后JTAG，不写Flash：

```bash
vivado -mode batch -source fpga/common/tcl/program.tcl \
  -tclargs build/fpga/m20/cpu_validation/snake_shuffled_boot_r1/swcell_m20_v3_top.bit xc7k325t_0
build/venvs/python312/bin/python host/python/swcell_m20_v3.py --port /dev/ttyUSB1 --seconds 120
```

采集默认保存在 `results/M20_V3/<时间戳>/`；原始JSONL、整数CSV、RAM转储和summary分开，raw保留启动异常/截断。UART读回是观察接口，不代CPU运算，不宣称自动证明屏幕正确。

## 按键与显示

|逻辑|实体键|Snake|Pong|
|---|---|---|---|
|K0 / IN0 bit0|KEY2|上|左球拍上|
|K1 / IN0 bit1|KEY0|下|左球拍下|
|K2 / IN0 bit2|KEY3|左|右球拍上|
|K3 / IN0 bit3|KEY1|右|右球拍下|
|K4 / IN1 bit0|KEY5|原ROM预留A；板级切换游戏并复位CPU|同左|
|K5 / IN1 bit1|KEY6|原程序执行重启|原ROM预留，板级请求CPU复位|
|板级控制|KEY5（A，同时仍为逻辑K4）|切换游戏并复位CPU，保留运行/暂停状态|同左|
|板级控制|KEY7|FPGA暂停/继续|同左|
|板级控制|RST_N|CPU复位，当前游戏保留|同左|

F06启动页规则：若显示“M20 CPU BOOT”，按KEY5/A启动当前游戏（不切到另一个游戏）；KEY7不再是启动入口。暂停时切换游戏或复位后无有效快照，按KEY5进入。进入游戏后仍是KEY5切换、KEY7暂停/继续。启动页第二行提示`KEY5: START`；[定位与验证](../../../../docs/m20/M20_V3_BOOT_ENTRY_F06.md)。

按键均两级同步/20ms独立消抖，低按下转逻辑1。F04增加8项方向事件队列和动作sticky，由真实CPU IN0/IN1退役确认消费；短按不必覆盖整个200ms游戏tick间隔，20ms以内的脉冲仍可能被消抖拒绝。LED0～3为GPO，LED4运行请求，LED5为Snake，LED6为HALT/TRAP，LED7为周期错误或输入队列溢出；全部低亮。本工程的LED含义与独立引脚诊断不同，原工程不修改。

上电默认Pong。OLED为 **FPGA State Visualizer**：只读CPU RAM的一致快照，显示球/球拍/分数、或蛇/食物/状态；计算和状态写入全部由原CPU机器码完成。Pong约10tick/s，Snake约5tick/s，CPU主动运行阶段的微周期频率为1MHz；显存内容更新约58Hz、SPI10MHz、180°。暂停、初始化、指令开销会改变墙钟吞吐，不能把这些频率混为一谈。

## UART控制和调试

`p`选择Pong、`s`选择Snake，均在完整微周期后复位；`r`复位；空格暂停/继续；`n`在暂停时执行一个微周期。暂停后`1/2/3`分别选择100kHz/500kHz/1MHz。例：`--command ' 1 '`按顺序暂停、改速、继续，发送字节间UART时间大于安全周期。程序选择不改变CPU ISA或游戏ROM。

```bash
build/venvs/python312/bin/python host/python/swcell_m20_v3.py --port /dev/ttyUSB1 --seconds 30 --command s
build/venvs/python312/bin/python host/python/swcell_m20_v3.py --input results/M20_V3/RUN/raw.jsonl --output build/v3_replay
```

快照提供完整33位CPU状态、ROM字、RAM总线、Master/Slave相位历史、64位微周期/退役/实际BRAM读/持久写/tick/错误计数，以及完整256nibble只读RAM快照及epoch。这是UART调试接口，不包含ILA/VIO IP。RAM字段按FF→00顺序十六进制编码，Python会反转至地址00→FF。计数reads是物理同步读服务次数，可能每个逻辑RAM读采样3次；writes是持久写次数。

正式源码、资源、仿真和实机证据以[任务记录](../../../../docs/tasks/m20-v3-fpga-20261104.md)和V3报告为准；初次JTAG/通信通过不能冒充完整游戏人工验收、全部ISA实机穷举或实体NC7SZ157时序签核。

2026-11-04用户确认两游戏实机操作正常、10/5节奏及KEY5暂停合适，F04短按“正常，明显改善”。原F02的30/10配置与原KEY4操作作为历史保留。球反复回中场且分数增加是原ROM固定发球后连续漏接的规则，见[专项说明](../../../../docs/m20/M20_V3_PONG_SERVE_REVIEW.md)。乱序食物是独立软件变体，不改原游戏ROM；需要显式指定`--snake-rom`与`--snake-done 313`一起构建，默认构建仍为冻结原版。

后续用户明确要求交换切换与暂停：**F05起KEY5/A切游戏、KEY7暂停/继续**，上表反映F05；F03/F04的旧键位验收和镜像保留。四方向、KEY6/B、KEY4忽略及UART命令均不变。新验证入口及镜像见[互换记录](../../../../docs/m20/M20_V3_KEY_SWAP_F05.md)。
