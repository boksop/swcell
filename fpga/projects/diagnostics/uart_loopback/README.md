# diagnostics/uart_loopback

板卡UART直接回环诊断。状态：**IMPLEMENTED**。

工程参数与文件清单见 [project.json](project.json)。公共板卡参数和引脚归属于 `fpga/boards/swcell_k325t/`，本工程不拥有公共时钟/LED/UART引脚的另一份定义。

构建入口：`fpga/projects/diagnostics/uart_loopback/scripts/build.tcl`；从仓库根目录运行。阶段和参数保持原脚本协议。仿真/操作说明见 [诊断说明](../README.md)。

目录迁移保留了旧回环RTL的七路M11安全接口，因此回环工程同时加载公共base_io和M11私有IO约束。它不是没有DUT接口的全新诊断RTL；pin-ID工程仍使用其独立方向约束。
