# N25Q256A13EF840F 启动与固化

## 使用的配置

用户已确认VCCO_0=3.3V、CFGBVS接VCCO，以及x4 SPI启动连接。配置bank属性已经写入真实XDC，Flash参数集中在`fpga/xc7k325t/config/board_50mhz.tcl`，由`flash_config.tcl`检查并生成构建目录中的`flash_config.xdc`。

| 项目 | 当前设置 |
|---|---|
| CONFIG_VOLTAGE / CFGBVS | 3.3 / VCCO |
| CONFIG_MODE / SPI_BUSWIDTH | SPIx4 / 4 |
| 物理模式绑带M[2:0] | Master SPI需要001，请按板卡拨码标识核对 |
| SPI_FALL_EDGE | YES，下降沿采样 |
| SPI传输 | SDR，每个时钟每线1bit |
| 配置时钟源 | 内部振荡器，EXTMASTERCCLK_EN=DISABLE |
| CONFIGRATE | 自动计算为标称50MHz；考虑+50%偏差时75MHz |
| SPI_32BIT_ADDR | YES，Flash容量256Mbit/32MiB |
| STARTUPCLK | CCLK |
| COMPRESS | TRUE，减少配置数据量 |

7系列配置控制器使用STR的Quad Output读命令。SPI_FALL_EDGE改变采样边沿，不提供DTR双边沿传输；Flash支持DTR并不代表硬配置控制器会发出DTR命令。x4由bitstream选择，M[2:0]不是另一个独立的“x4编码”。参见[UG470的Master SPI及SPI时序章节](https://docs.amd.com/v/u/en-US/ug470_7Series_Config)和[AMD配置属性表](https://docs.amd.com/r/en-US/xapp586-spi-flash/SPI-Flash-configuration-Options)。

## 50MHz的计算依据和适用范围

采用Micron同族器件原厂数据手册的STR输出延迟上限7ns（负载不超过30pF）、最大STR频率108MHz、高/低电平各至少4ns；32位地址读命令0Ch/6Ch也在其命令表中。[Micron N25Q256A数据手册，页24、28、44、81](https://datasheet.octopart.com/N25Q256A13ESF40F-Micron-datasheet-11858552.pdf)

XC7K325T的SPI建立时间取3ns，内部配置振荡器频率容差取±50%。2ns是**显式工程走线预算，不是用户已确认的测量值**，包含CCLK去程与最慢DQ回程；计算方法参见[AMD XAPP586](https://docs.amd.com/r/en-US/xapp586-spi-flash/Configuration-Clock-Calculation-Example)。本工程自行按这些输入计算：

```text
完整周期预算 = Flash tCO 7ns + FPGA tSU 3ns + 板级预算2ns = 12ns
实际频率上限 = min(108MHz, FPGA上限100MHz, 1000/12 MHz) = 83.333MHz
标称频率上限 = 83.333 / 1.5 = 55.556MHz
Vivado允许的档位中取不超过它的最大值：50MHz
最坏实际CCLK = 50 × 1.5 = 75MHz
最坏周期 = 13.333ns；周期余量 = 1.333ns
最短高/低电平（40%占空比）= 5.333ns，满足Flash的4ns要求
```

66MHz档位最坏99MHz，周期约10.101ns，无法满足12ns预算。不能只按Flash的108MHz标称上限选择FPGA配置频率。当前50MHz是上述预算下的最高档位，**尚未证明为该PCB的实测最高可靠速度**。应测量负载、传播延迟及启动可靠性；若超出预算，增大`flash_board_delay_budget_ns`后自动选择更低档位，或将`configrate_mhz`显式设为33/40。设置66或DTR会明确报错。

板上50MHz系统时钟D27与此CCLK互相独立；没有把LED_G所在的EMCCLK复用脚R24当作配置时钟输入。

## 生成与校验镜像

```bash
vivado -mode batch -source fpga/xc7k325t/scripts/build.tcl -tclargs --stage bitstream
.venv/bin/python host/python/swcell_check_flash_image.py \
  --mcs build/vivado/flash/swcell_m11.mcs \
  --bin build/vivado/flash/swcell_m11.bin \
  --size-mib 32 --report build/vivado/flash/image_check.json
```

输出：

- `.bit`：`build/vivado/swcell_m11.runs/impl_1/swcell_fpga_top.bit`，可直接JTAG配置。
- `.mcs`与`.bin`：`build/vivado/flash/swcell_m11.*`，SPIx4、Flash容量32MiB、起始地址0。
- `flash_settings.rpt`：实际计算的速度、最坏CCLK、时序余量、编程器器件项等。
- `image_check.json`：MCS/BIN数据一致性、地址范围、长度及SHA-256。

Python校验器检查Intel HEX各记录校验和、EOF、地址连续性、越界/重叠，以及MCS与BIN逐字节一致。它不替代真实Flash读取、信号完整性和断电启动测试。

## 编程器器件项

Vivado2022.1的实际器件库查询结果：

```text
NAME             = mt25ql256-spi-x1_x2_x4
MEM_DEVICE_ALIAS = n25q256-3.3v-spi-x1_x2_x4
MEM_DENSITY      = 256
```

这是工具提供的N25Q256 3.3V别名映射，不是任意换用另一个电压/容量的Flash。脚本会复核这些属性。不要选1.8V的mt25qu，也不要选双芯片x8或Zynq专用qspi单/堆叠项。查询证据为`build/flash_checks/part.log`和Vivado安装目录的`data/xicom/xicom_cfgmem_part_table.csv`。

## 显式执行Flash固化

先确认直接JTAG配置后的M11功能结果，再按实际Hardware Manager设备名执行：

```bash
vivado -mode batch -source fpga/xc7k325t/scripts/program_flash.tcl -tclargs \
  build/vivado/flash/swcell_m11.mcs ACTUAL_DEVICE_NAME
```

可在设备名之后指定板卡配置路径，以及完整JTAG target名称。多目标环境要求明确target，不自动取第一个目标。脚本在连接硬件前校验同目录配套BIN，随后选择唯一指定设备，下载Vivado生成的间接SPI访问bitstream，按镜像覆盖范围擦除、写入并读回验证；该范围按Flash扇区对齐，执行前应保存其中原有内容。

本次仅编写和离线检查固化脚本，**未连接板卡、未擦除或烧写任何Flash**。脚本实际设备操作仍需上板验证。

Flash应保持启动所需的Extended SPI协议和匹配的dummy-cycle设置，不要因为“x4”而强制切换成4-4-4 QPI或DTR协议。完整断电上电验证实际M[2:0]=001下的自主加载，观察DONE、三色LED和17条结果；FPGA完成配置后内部POR约100ms，再运行测试。USB-UART需要在测试开始前可用；如果板卡断电也使串口重新枚举，应调整POR等待时间并重建，或先打开采集再通过JTAG触发重新配置。
