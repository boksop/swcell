# M20 V3.1 测试报告（当前固件0.2）

2026-11-05。**用户已确认修正版两处显示修复正常；V3.1 FUNCTIONAL_STORAGE功能阶段正式通过。** 原r5基本功能曾获初次确认，但随后用户发现Pong A重开球拍消失和球/食物横条图案问题；原结论不能替代修正版验收。不创建commit、Tag或push。

## 本次显示修复

- 旧r5已实际复现：Pong从菜单进入后按A重开，屏幕清空，但OLDL/OLDR仍等于初始球拍位置，跳过重绘，左右三格球拍均为0。
- 每次launch_pong都将两个旧位置置无效值15，清屏后即使位置不变也必须重画。游戏规则、CPU ISA/477网表/FPGA RTL不改。
- PIX6原来把0x66重复8次，形成横条；现按00/00/18/7E/7E/18/00/00逐列输出加号，Pong球和Snake食物共用。
- 新增连续两次真实A按下/释放的重开检查和两处加号逐像素检查。首版加号比较方向错误被新断言抓到，181项中2项失败，修正后181项全通过；错误版本未下载。相关失败保留。

|层次|状态|真实证据|
|---|---|---|
|原V3/ISA保护|PASS|baseline_sha256.json；本次只改6个软件/生成/测试文件，平台RTL不变|
|Python全套|PASS，181项|build/m20_v31/restart_plus_python_r2.txt|
|原CPU功能基线|PASS，沿用未变源码的既有验证|v3_core_baseline_r1：87/57331，50521非法及恢复、27840数学、7访存；本次不重复计数|
|新CPU/同步BRAM/V1/Python联合|PASS|restart_plus_joint_r2：2589535退役、9566SPI字节、373773次RAM写，最终256nibble一致|
|Pong A重开与像素|PASS，仿真|连续2次重开，球拍不消失；球与食物符合独立加号像素期望|
|迁移游戏规则|PASS|177 Pong/315 Snake；restart_plus_relocation.json，Python规则对照|
|GPIO/STOP/STEP/RESET等平台|PASS，原平台未变|units_r4和原r5实机UART调试；不冒充本次又执行了一套硬件控制|
|综合/实现/STA/DRC/CDC|PASS|restart_plus_r2，750LUT/984FF，WNS1.972/WHS0.092/WPWS9.6ns，DRC0、9条2FF Info|
|路由审计|PASS|477显式MUX、33CPU FF、4路OLED直接GPO/Q，1BUFG|
|新bit/JTAG|PASS|restart_plus_r2/swcell_m20_v31_top.bit，restart_plus_program_r2.txt，12:31:13 startup HIGH|
|新固件UART|PASS，45条有效/错误0，1起始残行另计|results/M20_V31/20261105_restart_plus_r2；关联本次bit SHA|
|两处显示修复人工确认|用户确认PASS|“重开后两边球拍均正常”“两处均已显示为加号”；user_acceptance_restart_plus_20261105.json|
|ILA/STRICT_MUX/实体157/Flash|NOT_RUN|本轮UART辅助，FUNCTIONAL_STORAGE，不扩张验收边界|

ROM4052/4096字，剩44；软件RAM仍剩10nibble。Pong常规样本104.227..104.316ms（约9.59Hz），Snake209.884..209.978ms（约4.76Hz）；均为指令/仿真预算，不是板外仪器实测。CPU仍477组合MUX＋33原生FF，实体等价预算543不变。

当前bit SHA256：`181fb8844407a69f405594440245dc5ed1e50a24e81e103d194aa531835cfd0f`；ROM SHA256：`ae5be5055052c8ea9c8a5e4d00de5dcaf2dfe531e84a57fb9dec0b4feef71619`。

[架构](M20_V31_ARCHITECTURE.md)｜[软件SPI](M20_V31_SOFTWARE_SPI.md)｜[性能/图表](M20_V31_SOFTWARE_PERFORMANCE.md)｜[验证方法](M20_V31_VERIFICATION.md)。新证据v31_resources；初始r5独立保存在v31_initial_r5_resources，原始build/results和V3 F06 bit未覆盖。首个修复构建在ROM被修改时被SOURCE_CHANGED_DURING_BUILD保护拒绝，没有生成可下载bit；新r2锁定输入后成功。

已知限制保留：ROM只剩44字、无整屏framebuffer；软件帧率随路径变化，最长轮询间隙58.523ms；Pong顶行小比分局部覆盖画面；3样本消抖不能保证所有短按；没有真实157、电气、温压/长期可靠性或ILA验收。原179/2051485等数字属于初始r5，不回写其原日志为新版本。

正式阶段报告：[m20_phaseV3.1_20261105.md](../reports/m20_phaseV3.1_20261105.md)。新人工确认与此前基本功能确认分别保留，原r5失败不改写。
