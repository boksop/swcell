# diagnostics/uart_pin_id

V20/W23双输出引脚识别（需断开外部TX驱动）。状态：**IMPLEMENTED**。

工程参数与文件清单见 [project.json](project.json)。公共板卡参数和引脚归属于 `fpga/boards/swcell_k325t/`，本工程不拥有公共时钟/LED/UART引脚的另一份定义。

构建入口：`fpga/projects/diagnostics/uart_pin_id/scripts/build.tcl`；从仓库根目录运行。阶段和参数保持原脚本协议。仿真/操作说明见 [诊断说明](../README.md)。
