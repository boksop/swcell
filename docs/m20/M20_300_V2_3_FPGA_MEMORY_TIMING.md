# M20 V2.3：两相时钟与FPGA存储器接口时序契约

2026-11-03。供后续M20原理图/接口设计使用的**数字功能契约**。不指定新Buffer、引脚、器件或PCB参数；表中ns为仿真配置/推导值，不是实体NC7SZ157时序签核值。

## 接口职责与空间

CPU保留全部取指、译码、算术、PC/AR和微状态控制。FPGA仅提供4096×16只读指令空间、256×4 RAM、已寄存keys和GPO观察，以及注册两相调度。ROM按12位word地址寻址，未加载位置FFFF，执行时TRAP。无IR，指令必须保持到本次执行/访存结束。

`rtl/m20/v23/swc_fpga_memory_adapter.sv`为独立存储/事务RTL，ROM/RAM读取在sys_clk边沿完成，地址先锁存，输出寄存后保持。`sim/m20_v23/m20_v23_fpga_memory.sv`仅包装外部延迟、响应时序观察和计数；动态仿真延迟不属于可综合FPGA逻辑。本轮未进行板级综合/实现或证明具体BRAM映射，`ram_style`也不是映射验收证据。

## 四阶段约束

以本轮50MHz仿真sys_clk为20ns一tick，M窗口开始为t=0。阶段开始边沿设置phase_tick=0；配置的tick=k使能在阶段开始后(k+1)个sys_clk边沿采样，不能漏算这一个边沿。

|事件|零延迟配置|带延迟基准|职责|
|---|---:|---:|---|
|Master打开|0ns|0ns|Q保持；D函数可建立|
|RAM地址/控制采样，AT=4/24|100ns|500ns|锁存地址、写数据/写意图或启动同步读|
|RAM同步返回，L=2|140ns|540ns|输出保持至下次返回，另加包装IO延迟|
|Master关闭/commit_ce|240ns|1280ns|Master结束采样；如有pending ST，FPGA在此单次写入|
|Slave打开|320ns|1440ns|CPU可见Q开始提交|
|ROM地址采样，RT=2/8|380ns|1620ns|新PC已经稳定；所有指令和访存均重复服务同一PC|
|观察点，OT=2/8|380ns|1620ns|比较33位完整状态；不在相位翻转瞬间比较|
|ROM同步返回，L=2|420ns|1660ns|更新ROM输出，仅允许在Master关闭时发生|
|Slave关闭|560ns|2720ns|CPU可见Q保持|
|下一Master打开|640ns|2880ns|下一微周期；结束停钟时继续双方关闭|

带延迟实际引脚事件需叠加各位分支延迟及MUX选择/数据延迟，表中是调度器命令边沿。零/基准微周期频率分别1.5625MHz/约347.222kHz；普通指令分别1.28µs/5.76µs，RAM指令3.2µs/14.4µs。没有对外输出UART，本轮比较通过XSIM CSV文件。

## 必须满足的不等式

- D1有效死区：对任意位i、j，`SlaveOpen_j > MasterClose_i + 守护裕量`。D2亦要求`MasterOpen_i > SlaveClose_j + 守护裕量`。包括注册命令、分支偏斜、选择输入路径；不能仅核对调度器的原始信号。
- Q稳定后方可采ROM地址：Slave命令打开→最慢分支/CQ→PC与FPGA地址采样建立裕量，必须小于`(RT+1)*Tsys`。
- ROM返回及外部IO延迟必须早于下一Master打开；原始配置预算为`Tperiod - (M+D1+RT+1+ROM_LATENCY)*Tsys`。零延迟为220ns，基准为1220ns。还需扣除真实输出/PCB/输入建立和guard，不能全作可用裕量。
- RAM地址/WE/数据在AT采样前稳定，且保持满足FPGA输入要求。RAM读返回后必须有足够的**完整CPU组合路径建立时间**，不能仅满足RAM输出到Master选择端的2ns观察门槛。
- 原始RAM返回到Master关闭时间：`(M-AT-1-RAM_LATENCY)*Tsys`，零延迟100ns、基准740ns；扣除IO延迟、组合传播、Master建立要求及guard。2ns断言只是本次数字检查阈值，不是实体setup参数。
- CPU可见Q只在Slave有效透明窗口改变；Master/Slave不可同时有效透明。原语模型在延迟后选择端断言，CPU在M关闭前检查`QM==原D`且四核状态一致。

配置推导的跨位全局保护量见[phase_guards.csv](v23_resources/phase_guards.csv)：分别取所有33位Master关闭的最晚值与任一Slave打开的最早值，以及反向边界。模型两级选择延迟相同而相消，D1全局间隔=`D1×20 + SO − MO − 2×BS`，D2=`D2×20 + MO − SO − 2×BS`。六个正向配置均为正，最小为reduced的18.9/19.9ns。这是固定数字模型的配置推导；实际断言逐bit检查有效选择输入并在CPU边界比较完整状态，不把该推导写成实体跨位hold签核。

后续可降低时钟、扩大窗口、提前采RAM地址或缩短FPGA响应服务，以满足测得的边界；若仍需新CPU等待状态，必须先提交独立方案及2/5profile影响评估，不能自动改V2.1架构。

## RAM写语义与断言

RAM_CE/OE/WE与地址/数据在M阶段固定AT采样；仅`CE && WE && !OE`生成一次pending写。原CPU仅MEM_ACCESS置WE，commit_ce提交一次，因此MEM_RELEASE退役不能重复写。三个访存阶段的读可重复快照；最终退役读要求当前采样epoch已响应、数据已知、响应/输出稳定超过配置观察阈值。

复位取消未提交pending写；已经在ACCESS→RELEASE写入的内容不回滚。RAM不因CPU复位清空。HALT/TRAP后不出现总线写/退役，终态仍可安全单步。

## 安全启停与接口放行边界

上电/复位必须完整开Master、关Master、开Slave、关Slave以初始化反馈状态；双方关闭并不会自动复位33位。停钟必须完成当前周期，不能直接在外部打断透明窗口；单步是一个完整微周期。恢复运行前ROM、keys及复位输入必须满足窗口。

后续真实硬件还需标定：两相分支最早/最晚延迟、MUX污染/传播、真实DFF建立保持/脉宽、FPGA IO与BRAM响应、PCB往返、reset分发与供电。仿真参数不是这些量的替代，也不构成原理图/PCB时序放行。
