# 第一阶段实际验证记录

验证日期：2026-10-16（Asia/Shanghai）。工作目录 `/home/boksop/swcell`，Vivado/XSIM 2022.1，Python 3.10.12。本文分别记录无需板卡的RTL仿真、真实器件构建和实际JTAG/UART测试。

用户已正式确认M11第一阶段通过。面向阅读与交接的参数、逐项结果和图表总结见[正式验收报告](../reports/m11_phase1_20261016.md)；本文保留工具执行与诊断过程的详细记录。

本文的文件清单、工具与测试数量为第一阶段验收时的历史记录；第二阶段的新增代码、回归与上板结果另见[第二阶段验证记录](phase2_validation.md)，不据此改写第一阶段验收条件。

## XSIM 与 UART

执行 `./sim/scripts/run_xsim.sh`，最终成功标志应为：

```text
UART_PARSE_PASS fault=0 records=35 checks=422
UART_PARSE_PASS fault=1 records=36 checks=422
UART_PARSE_PASS fault=2 records=36 checks=422
UART_PARSE_PASS fault=3 records=36 checks=422
UART_PARSE_PASS fault=0 records=35 checks=422
UART_PARSE_PASS fault=0 records=35 checks=422
POWER_ON_RESET_PASS init=PASS hold=PASS release=PASS
UART_UNIT_PASS baud=115200 divisor=868 bytes=4 reset_recovery=PASS
UART_PIN_ID_REGRESSION_PASS
XSIM_REGRESSION_PASS (4 M11 scenarios + alternate timing + board 50MHz + UART 115200 + POR + dual pin-ID)
```

POR和UART的单元成功标志保存在各自日志，不直接打印到脚本终端；UART_UNIT_PASS保存在 `build/xsim/uart_unit.log`；脚本检查该标志，正常终端只显示总成功信息。四个主场景均运行17项、每套422次检查；故障场景中的功能FAIL及FIRST_ERROR是预期验收目标。第五个M11场景使用20MHz、700ns、三级同步；第六个使用板卡实际50MHz配置，均全部功能PASS。全部M11场景通过内部POR启动，不提供外部复位输入。POR独立单元测试验证INIT初始高复位、1/4个保持周期、两级同步释放及不自行重触发；整套仿真缩短保持为16周期，板上默认5,000,000周期。独立UART测试使用实际默认115200分频，覆盖0x00、0xff、0xa5、0x3c和发送中复位恢复。

实际UART_TX串行引脚经TB接收器解码后写JSONL；Python逐行检查类型、顺序、数值、掩码、状态与完整结束标志。不是直接导出RTL内部消息，也不以人工波形检查作为验收。

可查看：

- `build/xsim/compile.log`、`elaborate.log`：XSIM编译/展开。
- `build/xsim/fault_0..3.log`：每个场景的REGRESSION_PASS标志。
- `build/xsim/fault_0..3.jsonl`：实际串行解码数据。
- `build/xsim/slow.log`、`slow.jsonl`：参数变化场景。
- `build/xsim/board50.log`、`board50.jsonl`：50MHz板卡配置。
- `build/xsim/por_unit.log`：内部POR初始化与同步释放。
- `build/xsim/uart_unit.log`：115200及复位恢复。
- `build/xsim_uart_pin_id/simulation.log`：独立双输出引脚辨认测试，50MHz/115200、两路各3组15字节。

Codex沙箱内启动XSIM内核曾遇到工具启动异常；授权后在沙箱外执行上述回归成功。普通本机终端不需要更改脚本或仿真模型。

## Python 与保存链路

项目 `.venv` 已安装 pyserial 3.5。执行：

```bash
.venv/bin/python -m unittest discover -s host/python/tests -v
.venv/bin/python -m py_compile host/python/swcell_capture.py sim/scripts/check_uart.py
.venv/bin/python host/python/swcell_capture.py --input build/xsim/fault_0.jsonl --output-root build/replay --stop-on-complete
```

13项Python自动检查通过（原8项采集检查及新增5项Flash镜像检查），包含：64bit最大值与CSV十进制精度、非法JSON/重复字段/NaN及计数矛盾、跨块输入、超长/截断行、原始字节保留、异常关闭、离线回放退出码；另外两项Linux伪终端集成测试实际使用pyserial接收分段数据，并验证Ctrl+C退出码130和文件安全保存。

正常仿真数据的离线回放返回0，CSV包含17条结果，原始JSONL、metadata和capture_summary正确生成于 `build/replay/`。伪终端只验证PC串口软件链路，不代表物理USB-UART或板卡已经测通。

回归脚本自动优先使用项目 `.venv/bin/python`，可用 `SWCELL_PYTHON` 指定其他解释器；无pyserial时两项伪终端测试明确SKIP，其他Python检查仍可运行。

## RTL静态检查与构建防护

通过：

```bash
verilator --lint-only -Wall -Wno-UNUSED --top-module swcell_fpga_top rtl/common/*.sv rtl/modules/m11/*.sv fpga/projects/m11/functional/rtl/*.sv
bash -n sim/scripts/run_xsim.sh
```

Verilator版本4.225，忽略有意保留的未使用状态位/调试输出，其他检查无告警或错误。Vivado实际执行构建防护检查：显式指定的配置文件缺失、示例中part为空均明确报错并返回1。默认现在选用已确认的board_50mhz.tcl，不再要求填写空白模板；早期防护日志保存在 `build/config_checks/`。XSIM早期断言失败时，也验证了一键脚本会返回非零，即使XSIM自身退出码可能为0。

## 板卡接入与Vivado验证

已按用户提供的XC7K325T-2FFG900C建立真实器件工程（Vivado part：xc7k325tffg900-2），默认50MHz，所有13个端口约束为用户给定引脚及LVCMOS33。Vivado器件查询确认D27为MRCC，LED/UART在bank14、时钟在bank16、M11在bank18。配置文件和引脚表见docs/m11/fpga_workflow.md。

创建工程命令实际成功，日志为`build/board_checks/create.log`；最终源码已完成真实器件综合、布局布线和bitstream生成；详细时序与剩余警告见后续“最终构建结果”。已按用户后续授权连接并配置物理板卡；Flash未擦写。

异步Q/QM输入到首级同步器采用false path；8条低速异步输出（DUT驱动、UART、LED）不虚构外部同步接收时钟/输出delay，时序报告会列出no_output_delay。FPGA内部时序与CDC检查不替代实际板外传播/采样窗口测量。

用户已确认配置bank0为3.3V、CFGBVS接VCCO和x4连接；生成了SPIx4 SDR/下降沿/32位地址的镜像，但用户随后要求先只进行JTAG实测，Flash从未擦写。

## 最终构建结果

最终RTL执行`vivado -mode batch -source fpga/projects/m11/functional/scripts/build.tcl -tclargs --stage bitstream`返回0，生成标志SWCELL_BITSTREAM_PASS。最新日志：`build/flash_checks/build.log`。真实XDC已加入CFGBVS=VCCO和CONFIG_VOLTAGE=3.3，构建加入SPI启动属性；RTL保持此前回归通过的版本。

- 真实器件综合与布局布线通过；综合资源1249个Slice LUT、1385个寄存器，无BRAM/DSP需求。
- 布线后`timing.rpt`：WNS=+14.538ns，WHS=+0.076ns，WPWS=+9.358ns，setup/hold/pulse-width失败端点均为0。
- 最新设计DRC为0 violations，CFGBVS-1已消除；未降低任何DRC严重级别。
- 最新bitstream：`build/vivado/swcell_m11.runs/impl_1/swcell_fpga_top.bit`（压缩后约1.1MiB）。已按用户授权通过JTAG配置，未固化Flash。
- 从最终综合DCP检查到`power_on_reset/hold_reset_reg`和`release_pipe_reg[0:1]`三颗触发器INIT均为1；三条DUT同步器首级D引脚匹配正确。证据为`build/board_checks/check_por_init.log`中的POR_NETLIST_PASS。
- 工具本地TclStore只读提示是当前执行环境告警，使用安装目录回退；设计相关的XDC不支持if语句问题已修复，最终构建中不存在该告警。

## Flash配置和镜像离线校验

标称CONFIGRATE自动选择50MHz，考虑+50%时钟偏差为75MHz，7ns输出延迟+3ns建立时间+2ns明确工程走线预算给出1.333ns余量。该预算不是PCB实测值；不宣称已找到板上极限速度。7系列使用SDR；SPI_FALL_EDGE不是DTR。详见docs/flash_boot.md。

`tclsh8.6 sim/scripts/test_flash_config.tcl`及Vivado自带Tcl执行同一测试均PASS，覆盖50MHz选择、66MHz拒绝、降频、走线预算变化、半周期采样限制、DTR拒绝与32位地址要求。MCS/BIN已实际生成，`swcell_check_flash_image.py`检查70,185条数据记录、1,122,952字节，校验和、地址范围、EOF和逐字节一致性PASS。SHA-256见build/vivado/flash/image_check.json。

Flash固化脚本仅检查了无参数报错路径，未执行实际硬件固化；用户当前要求仅JTAG测试。

## 接回M11子卡后的最新实测：全部PASS

用户确认此前改UART线路时拆掉了M11子卡，随后已断电接回子卡并重新上电。保持原引脚约束和主镜像不变，先打开/dev/ttyUSB1（115200 8N1），再通过JTAG下载。两次下载均成功，Vivado启动状态HIGH；Flash未擦写。

2026-10-16 16:47至16:48（Asia/Shanghai）第一轮目录`results/m11_20261016_164735_233687+0800/`的17条TEST_RESULT均PASS，总4742次、错误0；下载前的W23文本与第一条START拼行，因此原始记录仍存在前缀污染，采集程序返回2，不将其标成完整协议验收通过。

16:48至16:49再次打开采集并JTAG重跑，获得干净验收目录`results/m11_20261016_164852_164402+0800/`：

- L01–L08、F01–F09全部PASS，17项总4742次检查；错误检查、Q错误、QM错误均为0。
- 35条JSONL包含17条START、17条RESULT、1条COMPLETE，无FIRST_ERROR；消息顺序、逐项检查次数及汇总独立核验通过。
- JSON格式错误0；CSV十进制计数与JSONL逐字段一致，两轮通过结果的CSV完全相同。
- 采集进程返回0，文件均安全关闭。最新板上镜像为M11主测试，V20为输入；该PASS状态应对应绿灯亮。
- `hardware_validation.json`保存核验结论及实际bitstream/raw JSONL的SHA-256；`operator_context.json`记录用户确认已接回子卡。

JTAG日志为`build/hardware/program_m11_subcard_connected.log`和`program_m11_subcard_clean.log`。本结论仅覆盖当前3.3V、默认低速功能序列；不代表高速频率或setup/hold裕量验收。未改动测试条件以消除错误，子卡接回前后的结果均保留。

## UART硬件修复后、未安装M11子卡的实测

用户确认硬件版本差异导致原UART接口未连接到W23/V20，已通过硬件修改接通；工程约束仍为FPGA TX=W23、RX=V20。2026-10-16 16:43至16:44（Asia/Shanghai）先打开/dev/ttyUSB1（115200 8N1），再通过JTAG重新加载M11主镜像，Vivado启动状态HIGH。V20已恢复输入，不再运行双输出诊断；未操作Flash。

第一轮目录`results/m11_20261016_164245_210006+0800/`包含切换前的65行W23诊断文本，采集程序正确告警并返回2；其后完整收到M11结果。第二轮从静默的M11镜像重新启动，获得干净记录`results/m11_20261016_164337_989890+0800/`：

- 49条有效JSONL，格式错误0；17条TEST_START、17条TEST_RESULT、14条FIRST_ERROR、1条TEST_COMPLETE，顺序核验通过。
- 各项检查次数与默认配置一致，总4742次；CSV数值转换与JSONL逐字段一致。两轮CSV完全相同。
- 功能结果3 PASS（L02/L03/L04）、14 FAIL；错误检查2721次，Q错误2450次，QM错误1833次。错误类型有重叠，Q和QM错误不能直接相加当作错误检查总数。
- 所有首次错误快照actual=0b111；例如F01的96次Q和QM检查均错误。用户随后确认这两轮测试时M11子卡尚未安装，因此该记录不能用于判断已连接M11电路的好坏。补充的operator_context.json记录了此硬件状态。
- 干净轮采集退出码1，正确表示比较结果FAIL；串口协议、结果计数和保存链路已验证通过，不能据此宣称M11功能通过。
- L02/L03/L04的检查均要求Latch Q=1；无子卡时本轮输入采样与持续高电平一致，局部检查条件恰好满足。当前初始化激励不独立计入检查，单项PASS不能判断子卡存在；全套汇总仍为FAIL。

原始JSONL、CSV、metadata、capture_summary及独立核验摘要`hardware_validation.json`均保存在第二轮目录。JTAG日志为`build/hardware/program_m11_uart_repaired.log`和`program_m11_uart_clean.log`。所有串口文件均已安全关闭。当时的FAIL状态应对应红灯亮；后续接回子卡的最新PASS结果见前节。

## 早期物理上板与通信定位记录

- JTAG目标唯一，器件NAME=xc7k325t_0、PART=xc7k325t，已两次加载最新bitstream；Vivado报告End of startup status: HIGH。
- /dev/ttyUSB1确认为Digilent Adept USB串口，115200 8N1，接收使能、无流控，只有本项目采集程序占用。
- 用户观察板上仅绿灯亮，符合整套内部PASS指示。
- 两次采集原始数据均无UART字节，尚不能通过JSONL/CSV验收具体计数；已排除串口未打开以及JTAG连接初始化顺序问题。用户确认W23为FPGA输出、V20为FPGA输入。
- 实测目录：results/m11_20261016_153734_446952+0800/和results/m11_20261016_154215_058701+0800/；两次采集均已安全关闭。不能把空结果目录当作完整PASS数据。
- 为定位通信问题，另建独立UART回环诊断镜像并通过JTAG加载；V20直接组合连接W23，绕过M11控制器及UART发送器。该镜像的LED含义与M11主镜像不同，见fpga/projects/diagnostics/README.md。诊断结束需恢复M11主镜像；未写Flash。
- 回环发送278字节、接收0字节，记录results/uart_loopback_20261016_154945_361509+0800/。逻辑分析仪准备就绪后又发送32个0x55及00 FF A5 5A 0D 0A，共38字节，仍接收0字节，记录results/uart_loopback_20261016_155443_952350+0800/。
- 用户提供逻辑分析仪截图：板载UART接口RXD能解码连续0x55及尾部字节，TXD大部分为高电平，仅见少量窄低脉冲，不能视为有效回环字节。用户确认绿灯闪烁，符合诊断镜像。当前仍需确认UART接口至V20/W23的实际电气路径，不能仅凭接口测点认定信号已到达FPGA焊球。
- 回环镜像重新综合、布局布线，实际检查V20为IN、W23为OUT，IBUF输出与OBUF输入为同一网络。证据在build/uart_loopback/connectivity.rpt、io.rpt及routed.dcp；DRC为0。随后再次通过JTAG加载，启动状态HIGH，日志build/hardware/program_loopback_verified.log。
- 共两次发送5秒BREAK及38字节：results/uart_loopback_20261016_155901_875966+0800/、results/uart_loopback_20261016_160041_194313+0800/。PC均接收0字节；第二次在重新加载的已核验镜像上执行。用户报告红灯没亮，接口RXD为低、TXD为高。该结果提示接口测点与V20/W23实际连接或诊断LED路径仍待核验，不能宣称板上UART通信PASS；已暂停发送并请求核对原理图和跳线状态。
- JTAG及串口检查日志保存在build/hardware/。

## V20/W23双输出诊断

用户要求两引脚分别周期发送引脚名，并已确认断开USB-UART的TX至V20连接，仅接分析仪。新建独立顶层`swcell_uart_pin_id_top.sv`及独立XDC，两引脚均为LVCMOS33输出，4mA、SLOW；不改M11主镜像的方向和约束。V20发送56 32 30 0D 0A，W23发送57 32 33 0D 0A；115200 8N1，每组发送完后空闲500ms。

XSIM独立仿真与接入后的完整一键回归均PASS，13项Python检查PASS，Verilator静态检查PASS。仿真曾发现字符串转义未产生所需CR字节，已改为显式十六进制字节常量并重新仿真、构建。`build/xsim_uart_pin_id/simulation.log`含UART_PIN_ID_SIM_PASS。最终构建返回0，`build/uart_pin_id/io.rpt`确认V20、W23均为OUTPUT；DRC为0，WNS=+17.088ns、WHS=+0.105ns，全部内部时序满足。bitstream为`build/uart_pin_id/swcell_uart_pin_id_top.bit`；仅用于临时JTAG诊断，不写Flash。

2026-10-16 16:12（Asia/Shanghai）曾通过JTAG加载双输出镜像，Vivado启动状态HIGH，日志`build/hardware/program_uart_pin_id.log`。当时只接收/dev/ttyUSB1三秒，仍为0字节；结果保存于`results/uart_pin_id_20261016_161256_233480+0800/`。用户随后确认硬件接口未连接并修复，16:43已恢复M11主镜像，后续实测见前节。诊断期间V20需外部TX断开；主镜像中V20重新为输入。

## 正式报告的补充时序核对

为准确说明本次测试频率，在50MHz、STEP_NS=500的现有RTL上增加临时观测TB，采用已有理想模型及F03三阶段刺激。XSIM核对24次施加激励、24次采样，连续更新间隔520ns、采样等待500ns、CLK高1040ns/低520ns、上升沿周期1560ns；日志含REPORT_TIMING_PASS，并继续取得REGRESSION_PASS。复核只缩短仿真序列并加速UART，不改变M11步骤定时。证据在build/report_timing/，未重新配置板卡。

因此本阶段DFF连续三阶段测试的RTL推导频率约641.0kHz，高电平占比约2/3；50MHz为FPGA系统时钟。该数值已通过RTL仿真核对，不是板外频率实测或最高工作频率结论。正式报告附检查次数分布图、时序图、数据来源与适用边界。

## 交付文件
共65个工程文件（不计虚拟环境、缓存与可重建日志）：

```text
.gitignore
AGENTS.md
README.md
docs/m11/architecture.md
docs/flash_boot.md
docs/m11/fpga_workflow.md
docs/m11/test_plan.md
docs/reports/README.md
docs/reports/stage_report_template.md
docs/reports/m11_phase1_20261016.md
docs/reports/assets/m11_phase1_20261016_checks.png
docs/reports/assets/m11_phase1_20261016_checks.svg
docs/reports/assets/m11_phase1_20261016_timing.png
docs/reports/assets/m11_phase1_20261016_timing.svg
docs/m11/uart_protocol.md
docs/m11/verification.md
fpga/projects/m11/functional/config/board.example.tcl
fpga/projects/m11/functional/config/default.tcl
fpga/projects/m11/common/constraints/m11_io.xdc
fpga/projects/m11/common/constraints/board_template.xdc
fpga/projects/m11/functional/constraints/cdc.xdc
fpga/projects/diagnostics/uart_pin_id/constraints/uart_pin_id.xdc
fpga/projects/diagnostics/README.md
fpga/projects/diagnostics/uart_loopback/rtl/swcell_uart_loopback_top.sv
fpga/projects/diagnostics/uart_pin_id/rtl/swcell_uart_pin_id_top.sv
fpga/projects/m11/functional/rtl/swcell_fpga_top.sv
fpga/projects/m11/functional/scripts/build.tcl
fpga/projects/diagnostics/uart_loopback/scripts/build.tcl
fpga/projects/diagnostics/uart_pin_id/scripts/build.tcl
fpga/common/tcl/flash_config.tcl
fpga/common/tcl/program.tcl
fpga/common/tcl/program_flash.tcl
host/python/requirements.txt
host/python/swcell_capture.py
host/python/swcell_check_flash_image.py
host/python/swcell_uart_probe.py
host/python/tests/test_capture.py
host/python/tests/test_flash_image.py
host/python/tests/test_serial_integration.py
results/.gitkeep
rtl/common/swc_comparator.sv
rtl/common/swc_input_sync.sv
rtl/common/swc_json_reporter.sv
rtl/common/swc_power_on_reset.sv
rtl/common/swc_prbs31.sv
rtl/common/swc_reset_sync.sv
rtl/common/swc_sequence_gen.sv
rtl/common/swc_step_timer.sv
rtl/common/swc_test_logger.sv
rtl/common/swc_uart_tx.sv
rtl/common/swc_uart_text_beacon.sv
rtl/modules/m11/m11_dff_tester.sv
rtl/modules/m11/m11_latch_tester.sv
rtl/modules/m11/m11_reference_model.sv
rtl/modules/m11/m11_test_top.sv
sim/m11/tb_m11.sv
sim/m11/tb_power_on_reset.sv
sim/m11/tb_uart.sv
sim/m11/tb_uart_pin_id.sv
sim/models/m11_behavioral_model.sv
sim/scripts/check_uart.py
sim/scripts/run_all.tcl
sim/scripts/run_xsim.sh
sim/scripts/run_uart_pin_id.sh
sim/scripts/test_flash_config.tcl
```
