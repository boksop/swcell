# M20：FPGA外设接口与存储服务契约

2026-11-02。方向/数量VERIFIED；时序服务与电气约束ESTIMATED/TBD，无PACKAGE_PIN。

## 边界与IO

FPGA提供ROM/RAM、OLED、按键采集、外部IO、时钟/测试和监视。CPU的PC/AR/A/Z/C/GPO/FSM/ALU/译码/条件跳转仍为157。

|接口|CPU→FPGA|FPGA→CPU|
|---|---:|---:|
|ROM addr12/data16|12|16|
|RAM addr8/wdata4/rdata4/CE/OE/WE|15|4|
|clock/reset/keys6/GPO4|4|8|
|合计，单clock|31|28|

共59根逻辑IO（不含地/电源），两相clock增一根至60。PC可复用rom_addr观测、A可复用ram_wdata、GPO已在表中；全状态另需AR8、Z/C2、uSTATE3，共13根。再加retire_valid/trap_event两根为74（两相75）；全部QM33另加，不能把重复别名再次计数。连接器必须另给足地和电源，数量不是针脚分配。

3.3V需确认[AMD UG471的HR/HP银行限制](https://docs.amd.com/api/khub/documents/IbGcnPFe6eF19RHma_Y~IA/content)：HR支持3.3V，HP不支持LVCMOS33。现有M11少量引脚成功不能证明新增59+引脚均可用，银行/连接器/保留资源仍TBD。

## 无IR的ROM契约

接口调度草案ID：`M20-FPGA-MEM-SERVICE-0.1`。它版本化FPGA采样/提交相位，CPU微周期计数仍为原2/5profile；两相实际绑定另须在物理试验前冻结相位与有效采样边界。

PC只在提交时变；FPGA在PC/Q稳定之后服务同步ROM，将返回word寄存并保持。FETCH_WAIT提供一个完整微周期，在EXEC及RAM三态期间同一word必须稳定。不能直接把不受控跨时钟BRAM输出挂到CPU，也不能逐位两级同步地址后拼成一次事务。

FPGA应拥有CPU时钟和固定服务调度，采用有时序界限的总线快照：

|周期内时刻，示例|动作|
|---|---|
|t=0|逻辑CPU边沿；提交上周期已采样ST，CPU Q随后稳定|
|约0.2T|采样稳定PC，启动同步ROM读取；输出寄存保持|
|约0.7T|ROM/地址/控制充分稳定后，采样RAM总线，启动同步读并锁存待写事务|
|下一t=0之前|RAM返回数据必须满足真实CPU建立时间；已采样ST在下一逻辑边沿写一次|

示例实际TB系统50MHz、CPU1MHz，ROM服务CE位于第10/50个系统tick，RAM采样第35/50个tick；这只是模型时序，不是已合格的1MHz实物方案。周期相位必须容纳tCQ、PCB、ROM/BRAM延迟、译码、setup和skew，不能仅按BRAM一拍计算。

## 适配器实现与验证

`rtl/m20/interface/m20_fpga_memory_adapter.sv`是FPGA外设模块：sys_clk唯一内部时钟；rom_read_ce/ram_sample_ce/cpu_rise_ce由外部CPU时钟拥有者提供。同步ROM/RAM读数据寄存保持；ST在稳定窗口采样，cpu_rise_ce一次提交；rst撤销pending_write，不清RAM。该模块不产生CPU指令控制，也不计算CPU地址或运算。

CE互斥和服务窗口由调度器契约保证；当前只提供接口适配器和验证调度，不是完整板级时钟控制器。实际引脚IOB寄存、约束、CDC/源同步时序预算仍须板级阶段闭合。若改为任意异步CPU clock，需要另外的事务握手/CDC设计；不能复用本同步调度假设。

联合XSIM通过5条LDI/ST/LD/OUT/HALT、16执行周期+1 RESET、恰1次物理RAM写、数据/输出正确，另验证已采样待写在reset时取消、采样窗口外WE毛刺不触发写。命令sim/scripts/run_m20_physical_models.sh；原CPU87场景的同步/异步RAM回归另已通过。

## 毛刺和复位

FSM二进制多位变化可能使原始CE/OE/WE毛刺；FPGA在稳定相位采样而不是把ram_we当时钟或异步写脉冲。ST物理提交与逻辑CPU边沿对应；已提交写不回滚。正常复位由同一控制器立即屏蔽pending写，再驱动CPU完成安全复位周期。FPGA配置/程序加载未完成前保持CPU reset。

两相实际绑定中以Master关闭对应逻辑提交，Slave延迟开放更新Q；所有服务窗口还须减去deadtime和clock-buffer差。该绑定不改2/5指令数，但若最终服务无法在周期内完成，必须降频；如需增加WAIT，应另评审/version微周期profile，当前没有增加。
