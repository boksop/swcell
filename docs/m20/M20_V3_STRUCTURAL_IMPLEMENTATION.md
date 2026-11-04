# M20 V3 结构映射及存储边界

原始输入：`rtl/m20/v21/generated/m20v21_cpu_core.sv` 与 `.netlist.json`。生成器只替换模块绑定、原生状态提交使能及存储分支；逐项比较477个原始实例编号和s/i0/i1/y连接。没有行为ALU、隐藏指令译码、额外CPU状态、乘除单元或新ISA。

|对象|模式F：FUNCTIONAL_STORAGE|模式S：STRICT_MUX|
|---|---|---|
|组合CPU|477个原节点 → 显式LUT3 INIT=CA|相同477节点|
|存储|33个原生FF，sys_clk＋CE|33对Master/Slave反馈MUX，66个LUT3|
|逻辑MUX追溯|477|543|
|CPU状态位|33|33位等价状态；没有原生CPU FF|
|数字仿真|原87/57331、非法/算术/访存通过|从RESET执行两游戏、129帧与F一致；强制初态的完整套件尝试未通过|
|Vivado|综合/P&R/STA通过；已下载|综合/P&R可完成，85项LUTLP-1，未生成bit|

模式S使用真实两颗MUX自反馈，不使用原生FF冒充。85项包括66个局部存储环和19个跨逻辑反馈环；这不是可按普通同步逻辑完整分析的存储实现。没有设置ALLOW_COMBINATORIAL_LOOPS或关闭规则。严格模式的WNS也为负，不能以路由完成认定可靠实现。

`core_strict_r1`尝试相同回归时，ISA阶段完成，datapath强制注入初态后PC与参考不一致，未宣称后续87场景全套通过；其初始化夹具与反馈模型的交互尚待定位。该结果与从真实RESET运行的F/S提交一致证据分开保留。

F模式已路由审计确认477个LUT3实例编号和33个FD类存储单元。当前F04及乱序软件配置中CPU为260个物理LUT位置、33FF（较早F03为261）：小LUT可在同一物理LUT资源中打包，**物理LUT位置数不等于157数量**。追溯信息由 `tools/m20/v3_route_audit.tcl` 导出实例、INIT、LOC、BEL和输入网名；原实例和存储对应见 generated/binding_manifest.json。输入确认仅引出原节点n0338/n0194；生成器断言未增加组合MUX，并逐项保留全部477连接。

结论：FPGA功能原型保留原477组合网络，但33原生FF不构成66颗实体157 DFF实物验证。原543等价预算不变，FPGA外设/快照/调试资源不计入CPU的157预算。
