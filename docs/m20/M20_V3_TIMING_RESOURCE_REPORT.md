# M20 V3 FPGA时序与资源

## FUNCTIONAL_STORAGE：functional_r6及snake_shuffled_r1（M20V3F04历史）

Vivado2026.1.1，XC7K325T-2FFG900C；唯一sys_clk=50MHz。综合、布局布线、DRC及STA通过，已生成并下载bit。

|指标|结果|
|---|---:|
|WNS / TNS|+0.735ns / 0|
|WHS / THS|+0.060ns / 0|
|WPWS|+9.232ns|
|无时钟寄存器 / 未约束内部终点 / 环路|0 / 0 / 0|
|异步输入无input_delay|9，均为有效键/UART首级同步例外；KEY4忽略后优化|
|CDC|9个CDC-3信息，双级ASYNC_REG|
|DRC|0违规|
|CPU逻辑MUX实例 / 原生状态FF|477 / 33，路由checkpoint独立审计确认|
|物理总LUT / FF|8787 / 5986|
|ROM / RAM|4×RAMB36 / 1×RAMB18|
|LUTRAM / DSP|4（外设事件队列）/ 0|

|层级|物理LUT位置|FF|BRAM|
|---|---:|---:|---|
|CPU|260|33|0|
|system含CPU/内存/快照/控制|以当前utilization.rpt层级为准|以当前报告为准|4×36＋1×18|
|OLED呈现与驱动|以当前utilization.rpt为准|1197|0|
|UART报告|635|1660|0|
|消抖|63|192|0|
|UART RX|53|37|0|

层级可因跨层共享/小LUT打包而不严格相加。260个物理LUT位置不是260颗157；477个逻辑LUT3及原节点身份保持。显示资源主要来自并行只读像素选择网络，不包含游戏推进逻辑。乱序变体只有ROM内容及完成断点参数不同，当前实现资源和上述slack与原版F04相同；逐次报告仍独立保留。

早期functional_r1的WNS=-7.059ns，原因是外部帧定时器将变量置于除数位置而生成运行时除法；改为两个编译期常量再选择后通过。失败报告保留，CPU及约束未改、未下载失败bit。

## STRICT_MUX：strict_r2

543逻辑LUT3，CPU没有原生FF；P&R完成，但85个LUTLP-1、WNS=-22.002ns。无bit、无实机下载。不能使用ALLOW_COMBINATORIAL_LOOPS绕过，也不能把这份STA当作真实双锁存器时序证明。

原始证据在 `build/fpga/m20/cpu_validation/` 下各独立目录，含functional_r2、functional_r3、functional_r4、functional_r6、snake_shuffled_r1及strict_r2。以实际路由报告为准；这是FPGA内部50MHz与给定IO放置预算的分析，不是外接157、OLED电源/边沿或实体PCB签核。

functional_r2原1.474/0.071、8749LUT/5965FF；functional_r3（RUN快照修正）为1.693/0.084、8748LUT/5965FF；r4（F03慢速/改键）为1.474/0.085、8739LUT/5942FF。F04增加输入事件缓存与观测字段。差异来自板级参数/观测控制和打包，477个CPU逻辑MUX及33状态FF不变。路由审计记录1个全局BUFG；未使用MMCM/PLL、没有DSP或CPU时钟域切换。

## F05键位互换实现

`snake_shuffled_keys_r1`路由报告：WNS+0.849ns、WHS+0.042ns、WPWS+9.232ns、DRC0；总8789LUT（含4LUTRAM）、5986FF、4RAMB36＋1RAMB18、DSP0。CPU仍260个物理LUT位置和33FF，477个逻辑MUX不变。仅板级按键请求来源交换及UART版本变化引起实现放置差异，不能解释成CPU预算增加。完整放行/下载情况见[F05记录](M20_V3_KEY_SWAP_F05.md)。

## F06启动入口

`snake_shuffled_boot_r1`路由报告：WNS+0.982ns、WHS+0.062ns、WPWS+9.232ns、DRC0；8774LUT（含4LUTRAM）、5986FF、4RAMB36＋1RAMB18、DSP0。CPU477个逻辑MUX/33原生FF、1BUFG保持，仍使用同一50MHz约束。改动仅板级BOOT控制/提示和版本，不把LUT打包/布局变化解释成CPU逻辑优化。[详细记录](M20_V3_BOOT_ENTRY_F06.md)。
