# M20 V3 实机验证记录（功能原型及参数调整）

2026-11-04。硬件：Digilent/210017563713A，`xc7k325t_0`；UART `/dev/ttyUSB1`，1152008N1。不写Flash、不改原Tag。

## 已执行

- 17:47:30，functional_r2通过JTAG下载，startup HIGH、退出0。
- bit SHA256：`ece164a689127bbcb739549f839c5b6e054e577d6d971d78ebc57abbf8f3f787`。
- 原始600s采集：`results/M20_V3/20261104_174721_functional_first/`，591有效记录、16未识别启动行；错误计数保持0。
- raw SHA256：`a08b59caf98dcd3442e7ea4dbaeea1b401f9455c9c151fdb315f89bb51711579`。
- 末计数：micro=3583459、retired=1168551、writes=165683、reads=749307、tick=17705、cycle_ticks=50、phase_trace=B8。
- 58份Pong无键RAM快照与Python原ROM一致，最后tick1715；独立摘要 `build/m20_v3_hardware_pong_prefix/verification.json`。

本镜像是477结构MUX＋33原生FF，不代表严格反馈存储实机通过。0错误表示有限的2/5周期运行检查未报错，不是芯片全条件误码率为0。

## 分项结论

|项目|当前结论|
|---|---|
|人工确认Pong/Snake画面与操作|用户确认正常；慢速/KEY5配置合适；F04短按明显改善|
|硬件各ISA类别有限向量诊断|PASS：1081退役、3111含启动周期、278写、寄存器/全RAM与Python一致|
|硬件非法编码TRAP|PASS：0010进入TRAP、micro3、retire0、write0|
|硬件UART STOP/STEP/RESET与100k/500k/1MHz|PASS，另有Snake131tick/12份全RAM对照|
|更多时长/随机环境可靠性|NOT_RUN|

诊断程序用CPU执行并将结果存RAM，Python只读比较，不能作为Pong/Snake实机画面证据。诊断结束必须恢复上述游戏镜像；不能把辅助诊断ROM称为原游戏运行。

## 后续配置与诊断分离

- ISA诊断原始目录 `results/M20_V3/20261104_180407_isa_diagnostic/`；71有限向量覆盖各类别、两RAM模式、C输入0/1、PC/AR回绕、分支、IO/HALT。不是15015合法编码的硬件穷举；50521非法穷举属于XSIM。
- TRAP诊断 `results/M20_V3/20261104_180622_trap_diagnostic/`，51份TRAP终态观察，原字0010；没有改写Pong/Snake。
- F01的停车调试RUN值陈旧已修复，F02/F03停车状态更新；原失败/旧观测保留。
- F02控制实测目录 `results/M20_V3/20261104_181159_controls_and_snake/`；硬件STEP从7582到7583微周期，STOP写计数不动，停止复位返回PC0/FETCH，三速度运行均计数增加且错误0；Snake131tick/12份全RAM与Python一致。
- 历史F03：`build/fpga/m20/cpu_validation/functional_r4/swcell_m20_v3_top.bit`，SHA256 `ab9cbf4000c8b9a3bc3700764a7af3fafe7efefe607f6eb074a53e4467afd675`，19:15:44 JTAG成功；Pong10/Snake5tick/s、KEY5暂停，KEY4无作用。新原始目录见build/m20_v3_slow_capture_path.txt。
- 原版F04：`build/fpga/m20/cpu_validation/functional_r6/swcell_m20_v3_top.bit`，SHA256 `a8807b476199a73ab8d52ff707f9211d55a960da2944592991aa7c0d8acae441`，19:46:30下载；方向事件队列和动作保留，用户确认短按改善。600s/599条有效/错误0；原始`results/M20_V3/20261104_194621_buffered_keys/`。
- F04乱序食物配置：`build/fpga/m20/cpu_validation/snake_shuffled_r1/swcell_m20_v3_top.bit`，20:14:18下载；哈希、自动控制及66tick/12份完整RAM对照见[变体报告](M20_V3_SNAKE_SHUFFLED.md)。原版F04及此前诊断数据不覆盖。该变体的食物分布人工体验尚未确认。
- 历史F05：`build/fpga/m20/cpu_validation/snake_shuffled_keys_r1/swcell_m20_v3_top.bit`，21:00:11下载，KEY5/A切游戏、KEY7暂停/继续；WNS0.849/WHS0.042ns、DRC0，UART60有效记录错误0，用户确认互换符合预期。[F05记录](M20_V3_KEY_SWAP_F05.md)保留。
- 当前F06：21:27:31下载snake_shuffled_boot_r1，BOOT页KEY5进入当前游戏、KEY7不启动；游戏中仍KEY5切换/KEY7暂停。WNS0.982/WHS0.062ns、DRC0、477逻辑MUX/33原生FF，UART已收到F06并复现暂停/复位BOOT页。新的启动入口人工确认与采集结果见[F06报告](M20_V3_BOOT_ENTRY_F06.md)。

用户随后确认F06启动/键位“已经完全正常了”，正式范围及参数汇总见[验收报告](../reports/m20_phaseV3-F06_20261104.md)。原75条采集没有实体按键轨迹，保留原字段；用户确认另存f06_user_acceptance.json，不将人工反馈伪装成UART自动检测。

所有测试摘要及原始哈希见v3_resources中的hardware_* JSON；原始采集自动视觉NOT_CONFIRMED字段不改写，用户确认独立记录。原F02速度为30/10并用KEY4暂停，不能把新参数倒填到旧记录。
