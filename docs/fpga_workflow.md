# 板级配置、构建和上板

## 已确认的板卡配置

用户提供XC7K325T-2FFG900C，Vivado 2022.1器件库已确认对应part为`xc7k325tffg900-2`。本板50MHz单端系统时钟，全部列出IO为3.3V。已提交配置`config/board_50mhz.tcl`和约束`constraints/board_50mhz.xdc`：

| 顶层端口 | 物理引脚 | 方向/说明 | Vivado bank |
|---|---|---|---:|
| sys_clk | D27 | 输入，50MHz单端，MRCC时钟引脚 | 16 |
| LED_G | R24 | 输出，高亮，完成且PASS | 14 |
| LED_Y | T20 | 输出，高亮，测试运行 | 14 |
| LED_R | T21 | 输出，高亮，完成且FAIL | 14 |
| UART_TX | W23 | 输出，对应UART_TXD，115200 8N1 | 14 |
| UART_RXD | V20 | 预留输入，第一阶段不解析命令 | 14 |
| M11_DL_D | L12 | 输出 | 18 |
| M11_DL_EN | F16 | 输出 | 18 |
| M11_DL_Q | E15 | 输入 | 18 |
| M11_DFF_D | H12 | 输出 | 18 |
| M11_DFF_CLK | L11 | 输出，普通数据引脚驱动 | 18 |
| M11_DFF_Q | J11 | 输入 | 18 |
| M11_DFF_QM | E11 | 输入 | 18 |

bank和时钟能力来自Vivado实际器件查询，记录在`build/board_checks/inspect.log`。全部端口IOSTANDARD=LVCMOS33，时钟周期20ns。用户也已确认配置bank0的VCCO_0为3.3V、CFGBVS接VCCO，真实XDC已写入对应属性；XDC不能改变板上的供电。CDC仅将三条DUT输入到同步器首级置false path；同步器后级和内部POR保留系统时序分析。没有外部reset端口，不需要复位引脚约束，也未禁用时钟专用布线检查。

## 内部上电复位与重新测试

实物版本注意：本次板卡原UART接口未实际连接到W23/V20，用户已通过硬件修改接通，XDC引脚号保持不变。修复UART后的两轮测试因M11子卡尚未安装，出现3项PASS、14项FAIL；其中单项PASS不能判断子卡存在。用户已断电接回子卡，后续实测17项全部PASS，详见[验证记录](verification.md)。物理接口连通与XDC约束正确是两项独立条件。

配置完成后，`swc_power_on_reset`基于INIT初值运行，保持内部复位5,000,000个系统周期，再经过两级寄存器释放，约100ms。通过配置`swc(por_ms)`调整。所有可综合状态仍由同一个50MHz系统时钟驱动。复位期间LED熄灭，之后黄灯运行，完成后绿/红灯指示PASS/FAIL。

本逻辑只在配置时初始化，不是运行中可调用的软复位，也不监测模拟电源或时钟丢失。UART_RXD当前只预留。重新运行测试可重新通过JTAG配置FPGA；固化后且模式正确时也可完整断电上电重新加载。100ms不保证USB枚举/串口打开完成，推荐先启动采集再JTAG配置。

## 创建、综合与实现

默认使用已提交的板卡配置，无需复制空白模板：

```bash
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl -tclargs --stage synth
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl -tclargs --stage bitstream
```

选择优先级：`--config` > `SWCELL_BOARD_CONFIG` > 存在的`board.local.tcl` > `board_50mhz.tcl`。通用模板仍保留；显式指定的文件缺失、part为空/不准确、频率/定时不合法时会报错，不自动回退覆盖错误。

`create`只建立工程；`synth`产生资源及综合时序报告；`bitstream`执行综合、实现、时序与DRC以及bitstream生成，逐端口检查PACKAGE_PIN和IOSTANDARD，不降低UCIO/NSTD检查等级。脚本在综合后检查三条DUT同步器首级D引脚存在，防止CDC约束随层次修改失效。

生成工程`build/vivado/swcell_m11.xpr`可用Vivado GUI打开，含全部RTL和仿真源。完整自检回归使用`./sim/scripts/run_xsim.sh`，与板卡引脚独立。

每次构建重建生成工程，因此约束/参数的唯一副本应保存在源码配置文件，不要只手工修改build目录中的工程。其他板卡可显式指定配置，或从`board.example.tcl`和XDC模板创建本地配置。

输出路径：

- bitstream：`build/vivado/swcell_m11.runs/impl_1/swcell_fpga_top.bit`。
- 报告：`build/vivado/utilization.rpt`、`synth_timing.rpt`、`timing.rpt`、`drc.rpt`。
- 实际构建状态、布线后时序、DRC及镜像校验记录见`docs/verification.md`。配置bank0已按用户确认值补齐，构建会拒绝剩余设计DRC违规。

## JTAG下载与采集

1. 按原理图核对M11七线、参考地和3.3V电平，配置bank0使用已确认的3.3V/CFGBVS接VCCO。上电，通过Hardware Manager核对实际设备和part。
2. **先打开采集**：

```bash
.venv/bin/python host/python/swcell_capture.py --port /dev/ttyUSB1 --baud 115200 --stop-on-complete
```

3. 再用Hardware Manager配置bitstream，或使用脚本；设备名必须取自实际连接目标：

```bash
vivado -mode batch -source fpga/xc7k325t/scripts/program.tcl -tclargs build/vivado/swcell_m11.runs/impl_1/swcell_fpga_top.bit ACTUAL_DEVICE_NAME
```

4. 无需外部复位。约100ms后黄灯运行，最终绿灯通过或红灯失败。默认17条RESULT、总4742次检查，PASS时全部错误计数为0。
5. 确认CSV有17行结果，raw.jsonl以完整COMPLETE结束，保存时间戳目录。FAIL时按FIRST_ERROR的mask分析DL_Q、Q或QM。

脚本不会自动连接并下载至任何板卡；本次工程验证不含物理JTAG操作。

## Flash固化

已接入N25Q256A13EF840F：x4 SDR、下降沿采样、32位地址、CCLK启动与压缩bitstream。默认标称CONFIGRATE=50MHz，按振荡器+50%偏差为75MHz；是显式板级时序预算下的最高可选档位，不能把它当作已测量的PCB最高速度。物理M[2:0]应设Master SPI的001。

bitstream阶段同时生成地址0、32MiB容量的MCS和配套BIN；构建不自动连接或烧写板卡。具体速度计算、镜像校验、Vivado器件别名和显式固化命令见[flash_boot.md](flash_boot.md)。

第一阶段仍只做低速稳定功能判断；Flash配置速度不会改变DUT功能测试频率。
