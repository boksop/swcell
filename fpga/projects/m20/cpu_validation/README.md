# m20/cpu_validation

M20完整CPU的FPGA原型接入准备，不生成bitstream。状态：**PLANNED**。

工程参数与文件清单见 [project.json](project.json)。公共板卡参数和引脚归属于 `fpga/boards/swcell_k325t/`，本工程不拥有公共时钟/LED/UART引脚的另一份定义。

本目录只有工程规划和引用清单，尚无顶层、构建Tcl或M20引脚约束。`project_catalog check`通过仅表示登记路径存在，不代表FPGA工程已经实现。详见 [M20索引](../../../../docs/m20/README.md)。不要把当前纯数字仿真报告当作上板验收。
