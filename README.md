# SwCell FPGA 自动化测试系统：M11 第一、二阶段

纯 SystemVerilog 的模块化自动测试工程。第一阶段使用单系统时钟FSM测试三颗74LVC1G157实现的D-Latch与Master/Slave DFF；第二阶段新增MMCM/ODDR高速激励、独立相位采样和长PRBS测试。两者均使用可综合UART输出JSONL，PC保存原始数据与CSV。默认第一阶段镜像配置完成后内部上电复位约100ms，再自动执行一次L01–L08、F01–F09；重新配置可重跑。第二阶段采用独立构建与自动JTAG入口。

**已接入用户提供的板卡配置：XC7K325T-2FFG900C、D27上的50 MHz单端时钟、全部13个3.3V引脚。** Vivado part为`xc7k325tffg900-2`。默认使用工程内的`board_50mhz.tcl`和真实XDC，保留通用空白模板；没有外部复位端口。配置bank0已确认3.3V、CFGBVS接VCCO。N25Q256A13EF840F使用x4 SDR、下降沿采样、32位地址和压缩镜像；按明确时序预算自动选择标称50MHz配置时钟，另提供MCS/BIN生成、校验及显式固化脚本。

2026-10-16实测：用户修复板卡版本造成的UART未连接问题，并断电接回M11子卡后，通过JTAG运行主镜像，17项、4742次检查全部PASS，Q/QM错误均为0。`/dev/ttyUSB1`收到35条完整JSONL、格式错误0，CSV核验通过，两轮通过结果一致；XSIM完整回归和13项Python检查也均PASS。之前的3 PASS/14 FAIL记录对应子卡未安装状态。用户已正式确认本阶段通过，详见[图文验收报告](docs/reports/m11_phase1_20261016.md)及[原始验证记录](docs/verification.md)。仅操作JTAG，Flash未擦写。

每个阶段正式通过后，都会在[阶段报告索引](docs/reports/README.md)保存一份中文Markdown报告，列明测试内容、实际参数、频率与时序、逐项结果、通过意义及证据。后续阶段沿用同一[报告模板](docs/reports/stage_report_template.md)。

第二阶段已增量加入M11高速DFF测试架构：静态MMCM/ODDR、Q/QM独立采样、相位窗口选择、64bit长PRBS统计及Python多bitstream扫频。第一阶段顶层与构建入口保留。使用方式、约束边界和结果格式见[第二阶段说明](docs/phase2.md)，实际完成的仿真/实现/实物测试见[开发验证记录](docs/phase2_validation.md)。新增实现不代表用户已正式验收第二阶段。

2026-10-16原第二阶段开发实测：25MHz完成百万/千万/亿次零错误；50MHz经独立选窗到Q7/QM6后完成亿次零错误。固定Q4/QM12的50–125MHz错误不能当作DUT上限；150/200MHz的该代表配置因FPGA内部时序不满足被跳过。这些历史记录保留在原验证文档中，不与后续源码轮次合并。

2026-10-17 Phase 2B实测完成：75/100/125MHz的Q、QM各16点共96个轴测点全部采集；每频率又完成0101、0011、PRBS百万次及亿次检查。75MHz（Q12/QM4）与100MHz（Q13/QM5）具有连续零错窗口，均为`PASS_1E8_ZERO_ERRORS`；125MHz（Q15/QM7）虽也取得两路各0/1e8，但各路仅一个零错相位点，保留`MARGINAL_WINDOW`。按当前窗口判据最高已验证100MHz，最高观测亿次零错125MHz，均不是器件保证Fmax。108个有效测点/105个独立镜像的内部STA和DRC核验通过，完整XSIM回归与最新52项Python检查PASS。参数、曲线、校验值和边界见[Phase 2B验证记录](docs/phase2b_validation.md)；尚待用户正式验收。

```bash
# 两阶段完整回归；含百万次高速PRBS仿真与Python检查。
sim/scripts/run_all_regressions.sh
# 默认自动扫频：构建160个短扫描配置，窗口合格后再长测；可能持续数小时。
.venv/bin/python host/python/swcell_sweep.py --port /dev/ttyUSB1
```

## M20 游戏CPU

V2.3已按用户限定的模式A数字仿真正式定版，见[正式阶段报告](docs/reports/m20_phaseV2.3_20261103.md)；本地提交aecf570及标签m20-v2.3-two-phase-sim-verified。V2.4自主时钟与同源存储服务独立开发，不纳入V23验收。

2026-11-03：新增[V2.3双相锁存器与同步FPGA存储联合验证](docs/m20/M20_300_V2_3_TEST_REPORT.md)，保留477组合MUX，状态切换为66个真实反馈MUX；原ISA和游戏码不变。架构、完整回归与[两相/存储时序契约](docs/m20/M20_300_V2_3_FPGA_MEMORY_TIMING.md)独立交付；只属数字模型验证，未作实物时序签核。

当前入口：[V2.1正式543结构与本轮验证](docs/m20/M20_300_V2_1_TEST_REPORT.md)、[真实157物理规格](docs/m20/M20_PHYSICAL_FEASIBILITY.md)。2026-11-02：接受500+核心规模，已补全部非法编码实际TRAP/恢复验证；物理时序/时钟/电源/接口仍按VERIFIED、ESTIMATED、TBD分别记录，未进行PCB或实物测试。

历史记录：M20-300的ISA与V1.3功能RTL已通过真实XSIM指令差分，用户在V2任务确认，见[V1正式报告](docs/reports/m20_phaseV1_20261029.md)。V2已新增显式157结构与精确审计：朴素738颗、共享603颗核心等价，两版功能三方回归通过，但未达到原328或300目标。当前仅数字仿真，未综合/STA或上板；后续决定见[V2结果](docs/m20/M20_300_V2_TEST_REPORT.md)。[M20索引](docs/m20/README.md)与[TASK_PROGRESS](TASK_PROGRESS.md)记录源码、命令和恢复入口。

## 环境

Ubuntu24.04新机已建立独立Python3.12环境`build/venvs/python312`，保留旧`.venv`不变；52项Python测试及P2B离线统计/绘图均通过。请优先阅读[新机Python环境说明](docs/environment_python312.md)。首次Git提交的文件范围和备份建议见[纳管方案](docs/git_tracking_plan.md)，尚未执行提交或推送。

- Ubuntu 22.04、Vivado 2022.1 / XSIM，安装 Kintex-7 器件支持。
- Python 3.10+（Ubuntu 22.04 自带）；串口采集依赖 pyserial，离线解析和单元测试只使用标准库。
- 使用虚拟环境需要系统安装 `python3-venv`；若创建时报 ensurepip 不可用，请先安装该系统包。
- VS Code 可直接打开本目录。所有命令从工程根目录执行。

```bash
# 按实际安装路径加载环境（当前机器安装在 ~/Software/Xilinx）：
source ~/Software/Xilinx/Vivado/2022.1/settings64.sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r host/python/requirements.txt
```

## 目录

| 路径 | 内容 |
|---|---|
| `rtl/common/` | 复位/输入同步、步骤定时、PRBS31、序列、比较器、64bit 记录器、JSON 编码器、UART TX |
| `rtl/modules/m11/` | Latch/DFF 控制器、可综合参考模型、M11 编排 |
| `fpga/xc7k325t/` | 板级封装、配置示例、XDC 模板、创建/综合/实现/下载 Tcl |
| `sim/models/` | 无系统时钟的独立外部 MUX 反馈行为模型 |
| `sim/m11/` | M11 自检 TB 与默认波特率 UART 单元 TB |
| `sim/scripts/` | 一键 XSIM 回归、串行 JSONL 语义检查 |
| `host/python/` | 采集/离线回放、依赖、Python 自动测试 |
| `docs/` | 架构、测试计划、通信、板级操作和验证记录 |
| `results/` | 实测原始 JSONL、CSV 和采集元数据；结果数据不提交 Git |
| `build/` | 可重建的仿真/工程/日志输出，不提交 Git |

`.gitignore` 还忽略板卡本地配置、Xilinx 日志和 Python 缓存；保留 `results/.gitkeep`。当前已获授权初始化本地Git `main`，仅四份进度文档暂存，尚无提交；其它源码尚未纳管。新会话先读[TASK_PROGRESS.md](TASK_PROGRESS.md)，核实文件、日志与实际进程后继续。

## 一条命令运行 XSIM 回归

无需板卡、part 或引脚：

```bash
./sim/scripts/run_xsim.sh
```

命令编译 RTL 与 TB，运行正常、Latch Q 错误、QM 错误、Q/QM 同时错误四个场景；再运行20 MHz/700 ns/三级同步、板卡50 MHz配置、内部上电复位、115200 UART单元测试及双引脚辨认诊断测试。每次均检查 HDL 成功标志，解析实际 UART_TX 解码得到的 JSONL，并运行 Python 自动检查。任何编译、断言、超时、协议错误都会返回非零。故障场景中的 DUT FAIL 是预期结果，只有正确检出错误才算回归 PASS。

脚本优先使用项目 `.venv/bin/python`，也可通过 `SWCELL_PYTHON` 指定解释器；无 pyserial 时仅跳过两项可选伪终端串口集成检查，其他检查无需该依赖。

输出：`build/xsim/fault_0.jsonl`（正常）、`fault_1..3.jsonl`（注入错误）、`slow.jsonl`，以及各阶段日志。仿真加速仅提高套件测试 UART 波特率，保持每步骤至少 500 ns；另有独立 115200 测试。

```bash
python3 -m unittest discover -s host/python/tests -v
python3 -m py_compile host/python/swcell_capture.py sim/scripts/check_uart.py
# 离线验证完整保存链路，不需要 pyserial：
python3 host/python/swcell_capture.py --input build/xsim/fault_0.jsonl --output-root build/replay
```

## 创建工程、综合和 bitstream

```bash
# 默认使用已填写的 board_50mhz.tcl；不需要复制空白模板。
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl -tclargs --stage synth
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl -tclargs --stage bitstream
```

`create`/`synth`仍支持使用其他显式配置；默认配置为本次提供的真实板卡。指定其他配置时，允许暂时没有物理XDC，但仍必须指定真实part和频率；无板卡数据的 RTL 回归使用前述独立脚本。bitstream 要求全部顶层端口有 `PACKAGE_PIN` 和 `IOSTANDARD`，不降低 UCIO/NSTD 检查等级。每次构建会重建 `build/vivado/swcell_m11.xpr`，不要把手工修改只保存在生成工程内。支持`--config /path/board.tcl`或`SWCELL_BOARD_CONFIG`环境变量；优先使用本地`board.local.tcl`，不存在时使用工程内的`board_50mhz.tcl`。

bitstream阶段同时生成`build/vivado/flash/swcell_m11.mcs`和配套BIN（32MiB容量、地址0）。

板级设置、报告检查及 JTAG 下载见 [docs/fpga_workflow.md](docs/fpga_workflow.md)。

## PC 采集

```bash
# 先打开串口采集，再JTAG重新配置FPGA；板卡没有外部复位键。
python3 host/python/swcell_capture.py --port /dev/ttyUSB1 --baud 115200 --stop-on-complete
# 长期监听多次重新配置/上电运行，Ctrl+C安全退出：
python3 host/python/swcell_capture.py --port /dev/ttyUSB1 --output-root results
```

自动生成 `results/m11_时间戳/`：`raw.jsonl`（全部原始字节）、`results.csv`（十六进制计数已转换成十进制）、`metadata.json` 和 `capture_summary.json`。非法行告警并保留原始数据，截断数据不当作有效结果。采集工具不会主动清空串口缓冲或控制 DUT 复位。

串口访问如受限，按所在系统的设备权限策略配置 `dialout`，重新登录后再运行；串口节点和 USB-UART 型号由实际板卡决定。

## 板卡启动与指示灯

- FPGA配置中的INIT值启动内部POR，默认保持5,000,000个50MHz周期（100 ms），再经两级同步寄存器释放；可通过`swc(por_ms)`调整。
- 黄灯LED_Y亮：测试运行；绿灯LED_G亮：完成且PASS；红灯LED_R亮：完成且FAIL。复位期间三灯熄灭，结果保持到重新配置。
- UART_RXD(V20)只预留，不实现命令或串口复位。再次测试需JTAG重新配置，或在已固化且启动模式正确时完整断电上电。PC应在配置前开始监听。
- 这是用户逻辑的配置后复位，不是模拟电源监测器；运行中停钟/掉压不会主动重新触发它。

Master SPI物理M[2:0]应为001，x4由bitstream选择。下降沿采样不等于DDR双边沿传输；Kintex-7硬配置控制器使用SDR读命令。50MHz配置速度基于显式2ns板级走线预算，尚未做PCB实测速度验收。固化命令见[Flash说明](docs/flash_boot.md)，构建不会自动擦写硬件。第二阶段高速扫频采用独立入口和JTAG下载，见本文前部链接；不实现完整Setup/Hold扫描、以太网或GUI。

详细说明：[架构与扩展](docs/architecture.md)、[M11 测试计划](docs/m11_test_plan.md)、[UART 协议](docs/uart_protocol.md)、[实际验证记录](docs/verification.md)。

75/100/125MHz 独立相位扫描、全部候选窗口、1e6→1e8 门控及中断恢复见 [M11 Phase 2B 操作说明](docs/phase2b.md)。新增回归命令为 `sim/scripts/run_phase2b.sh`，保留原有 `run_all_regressions.sh`。

## 本地版本封存

2026-11-03完成本地Git基线与M20逻辑/物理分析标签，真实硬件时序仍未验收。[本地工作流](docs/GIT_LOCAL_WORKFLOW.md)、[版本历史](docs/m20/M20_RELEASE_HISTORY.md)、[恢复验证报告](docs/m20/M20_LOCAL_GIT_REPORT.md)。无remote或自动上传；历史原始数据继续原位保留并有独立SHA索引。
