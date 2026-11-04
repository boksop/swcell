# UART引脚回环诊断

这是临时通信诊断镜像，与M11功能测试镜像分开。引脚仍使用用户确认的FPGA TX=W23、RX=V20；UART_TX直接连接UART_RXD，不经过RTL UART发送器，也不依赖系统时钟。M11输出固定在低速初始化电平，不执行功能测试。

```bash
vivado -mode batch -source fpga/projects/diagnostics/uart_loopback/scripts/build.tcl
vivado -mode batch -source fpga/common/tcl/program.tcl -tclargs build/fpga/diagnostics/uart_loopback/swcell_uart_loopback_top.bit xc7k325t_0
build/venvs/python312/bin/python host/python/swcell_uart_probe.py --port /dev/ttyUSB1
```

诊断镜像的LED含义与主测试不同：绿灯约1Hz闪烁，红灯反映同步后的RX低电平，黄灯是粗略RX低电平锁存指示（包含同步流水线上电过程，不能单独作为收到PC数据的证据）。通信验收只看PC发送的文本前缀及全部256字节值是否逐字节原样返回。

配合逻辑分析仪时，先在FPGA_RXD（V20）设置下降沿触发，同时采集FPGA_TXD（W23），共地，采样率至少10MHz，窗口20ms；进入等待触发后执行：

```bash
build/venvs/python312/bin/python host/python/swcell_uart_probe.py --port /dev/ttyUSB1 --pattern 555555555555555555555555555555555555555555555555555555555555555500ffa55a0d0a
```

该命令发送32个0x55和00 FF A5 5A 0D 0A，共38字节。按115200、8N1、非反相解码，单个比特约8.68µs；正常情况下两路字节应一致。探针程序将实际收发字节及JSON报告保存在带时间戳的results子目录。RXD无跳变时先检查PC到FPGA路径；RXD有跳变而TXD无跳变时检查回环镜像、测点与引脚；两路一致而PC收不到时检查FPGA到USB-UART接收路径。

接口测点上的RXD波形不能单独证明信号到达V20。观察板上红灯并在分析仪重新准备好后，可以用`--break-seconds 5`先发送5秒BREAK（PC TX/FPGA RX持续低电平），再发送数据；红灯应在BREAK期间持续亮起，结束后熄灭。直接回环的TXD也应在同一时段保持低电平。构建脚本检查布线后V20输入、W23输出及IBUF至OBUF直接连通，保存`build/fpga/diagnostics/uart_loopback/io.rpt`、`connectivity.rpt`和`routed.dcp`，便于对照物理测点。

诊断完成后必须重新通过JTAG加载`build/fpga/m11/functional/swcell_m11.runs/impl_1/swcell_fpga_top.bit`，再执行M11采集。本诊断不操作Flash。

## V20 / W23 双输出引脚辨认

独立镜像`swcell_uart_pin_id_top`将两个引脚都设为LVCMOS33输出。下载前必须断开USB-UART的TX至V20的连接，防止两个输出驱动同一根线。V20仅接逻辑分析仪；W23可以接分析仪及USB-UART的RX。该镜像不接收PC命令，也不运行M11功能测试。

| FPGA引脚 | 周期发送文本 | 十六进制字节 |
| --- | --- | --- |
| V20 | `V20\r\n` | `56 32 30 0D 0A` |
| W23 | `W23\r\n` | `57 32 33 0D 0A` |

两路独立UART发送器均使用50MHz系统时钟，115200、8N1、LSB先发、空闲高电平、不反相，实际分频434，比特时间8.68µs。每组5字节发送结束后空闲500ms，再循环；两路同时开始。上电复位约100ms。M11驱动保持D=0、DL_EN=1、DFF_CLK=0。此镜像绿灯约1Hz闪烁、黄灯常亮、红灯熄灭；复位时三灯熄灭。

```bash
sim/scripts/run_uart_pin_id.sh
vivado -mode batch -source fpga/projects/diagnostics/uart_pin_id/scripts/build.tcl
vivado -mode batch -source fpga/common/tcl/program.tcl -tclargs build/fpga/diagnostics/uart_pin_id/swcell_uart_pin_id_top.bit xc7k325t_0
```

分析仪任选V20或W23下降沿触发，至少10MHz采样，采集窗口10ms即可完整包含一组字符串。因为持续循环，可以在下载完成后再启动等待触发，通常0.5秒内采到下一组。按两路实际解码文本确认测点，不能只依赖接口丝印。若测点出现另一引脚的文本，应核对接口丝印/探针与FPGA焊球之间的对应关系。

`build/fpga/diagnostics/uart_pin_id/io.rpt`明确记录两引脚均为OUTPUT，`routed.dcp`保留布局布线结果；构建检查时序和DRC。独立XSIM测试在真实50MHz/115200参数下解码每路连续3组、15字节，检查两路各自文本、起止位、重发空闲间隔及安全输出；仅将仿真空闲缩短为100µs和POR缩短为16周期。主回归`sim/scripts/run_xsim.sh`也执行此测试。

恢复M11主镜像后V20重新变为输入，才可重新连接USB-UART的TX。本镜像仅用于JTAG临时诊断，不写Flash。

目录迁移保留了旧回环RTL的七路M11安全接口，因此回环工程同时加载公共base_io和M11私有IO约束。它不是没有DUT接口的全新诊断RTL；pin-ID工程仍使用其独立方向约束。
