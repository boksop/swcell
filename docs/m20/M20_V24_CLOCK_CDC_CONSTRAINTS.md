# V2.4 C/D：时钟、CDC与IO约束契约

2026-11-04。本轮只实现/验证数字服务，**不创建板级工程、不分配PACKAGE_PIN、不作布局布线/STA签核**。以下是后续FPGA实现所需约束要求，不回写旧M11或V23 Tcl/XDC。

## FPGA时钟与参考

- 唯一FPGA控制/存储时基为sys_clk=50MHz（周期20ns）。运行控制、age计数、BRAM、按键和结果观察均在此域。
- B参考是FPGA寄存分频输出，25tick半周期，50tick/周期，1MHz；外部20颗产生H/S，并非FPGA另一个隐藏理想发生器。分频关系在实现时应声明派生关系，并计入输出/PCB/返回输入路径。
- C参考是独立约1MHz输入源，仿真初相17ns、高500/505/510ns、低500/507ns；同时送同一20颗发生器与FPGA同步器。sys_clk保持20ns独立时基，不以C作为FPGA存储时钟。
- A是冻结V23原直接两相调度器，logic下周期640ns、timed下周期2880ns。它用于事件/架构对照，不把不同墙钟时间直接逐点比较。

## REF CDC与捆绑总线

`swc_ffcd_service`用ref_meta/ref_sync两级ASYNC_REG，ref_prev作边沿历史。同步后的电平和age只在sys_clk使用，不逐位同步任何高速递增计数器。数字模型识别延迟有界于选定参考相位关系，但**没有模拟亚稳态，也不承诺实体绝对40～60ns上界**；后续需计算MTBF、布局同步寄存器及增加失步/停振诊断。

PC12、RAM地址/数据和控制是“已在约定相位稳定的捆绑总线”，由一次service事件原子锁存整条总线；不声称两个单bit同步器能保证每个总线位一致。跨域安全来自参考/延迟/相位窗口及稳定时间的组合预算，必须验证最大IO、PCB和CPU组合传播，而不是给所有路径加false_path。

## 实现时必须建立

1. 对实际sys_clk端口执行50MHz主时钟约束，端口/引脚以新M20顶层和用户硬件连接为准。
2. 对B寄存分频/输出参考声明正确派生关系；对C实际输入定义频率、波形、jitter/uncertainty，不误称其与sys_clk同步。
3. 仅对异步REF进入**第一级**同步器的采样路径使用经核实的局部例外；第二级仍正常sys_clk时序，并保留ASYNC_REG属性/布置要求。不得全局false_path消除CPU总线或后级时序告警。
4. 给CPU→FPGA的PC/RAM地址数据及FPGA→CPU的ROM/RAM返回、SAFE_HOLD建立输入/输出延迟或有物理依据的max_delay约束；当前板级值未知，保留TODO，不能填0ns冒充测量。
5. 后续分别跑report_clocks、report_clock_interaction、report_cdc、report_timing_summary；FFCD RTL编译/仿真通过不等于这些报告通过。

本轮没有可用的新M20引脚/完整PCB预算，因此只交付契约，不生成一个看似有效的假XDC。

## 仿真条件下的服务截止时间

约500ns半周期中，RAM采样位于下降后约140～160ns，2服务周期后返回；PREVIEW位于约340～360ns，物理CPU直到下一REF上升后Master有效关闭才采样。ROM在上升后约220～240ns锁存PC并同步返回，下一Master开放约在下一下降后36～43ns。实际范围以service_latency.csv和VCD为准。

这些窗口覆盖FPGA同步识别与BRAM访问；不要求在22ns死区里完成全部服务。时基升频或增加服务/IO延迟必须重算预算，不隐含增加CPU微周期。PREVIEW只用于验证快照/参考模型，不能接成外部CPU采样时钟。

## 数字与实体结论

数字功能验收允许明确的assumed延迟；实体时序仍需得到NC7SZ157链min/max、独立有效锁存边界、Buffer跨相/分支/负载、PCB和测量不确定度。原快速链负裕量和局部路径反例保留为FAILED配置。缺少实体min不阻止本次C/D数字回归，但不允许据此宣传实体可靠工作频率。
