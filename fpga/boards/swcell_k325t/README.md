# SwCell Kintex-7 公共板卡资源

`swcell_k325t`是仓库标识，不代表已知PCB版本号。用户确认：XC7K325T-2FFG900C，Vivado part `xc7k325tffg900-2`，50MHz单端D27，3.3V IO，配置bank0=3.3V/CFGBVS接VCCO。

- `board.tcl`：芯片/频率与原已审查Flash参数；不包含测试步数或M11算法参数，source不会操作硬件。
- `constraints/base_io.xdc`：系统时钟引脚、三LED、UART、IOSTANDARD与配置电压。每个工程按其真实频率建立create_clock。
- M11七路连接位于 `fpga/projects/m11/common/constraints/m11_io.xdc`；M20接线未知，不能套用。
- JTAG/Flash显式工具位于 `fpga/common/tcl/`；本轮目录整理不调用它们连接/写入硬件。

默认flash profile继续保留旧SDR参数及工程预算，不将其改写成实体实测。UART双输出诊断因端口方向不同，使用项目自己的约束，不和base_io.xdc同时加载。
