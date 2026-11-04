# M20 V3 结构级FPGA原型阶段报告（功能存储实机完成，待用户审阅）

2026-11-04。**用户已在首次Private发布任务确认V3 FUNCTIONAL_STORAGE功能原型整体通过**，见[整体正式报告](../reports/m20_phaseV3_20261104.md)。本页保留开发期间各版本的分项证据；原来的“待整体审阅”状态由最新确认取代，严格反馈存储和实体157时序不在通过范围。F06最终启动/切游戏键位已单独确认，历史KEY5暂停是F03/F04记录。

|层级|结论|
|---|---|
|477网络来源/ISA/原游戏ROM|生成器逐连接校验、冻结文件未改|
|功能存储模式核心数字回归|PASS：87场景57331事件、27840算术、50521非法及恢复、7访存|
|新同步存储/启停/一致快照|PASS：F/S提交比较40398、129帧，两游戏各64tick完整RAM对照|
|键/OLED/UART集成仿真|PASS：6键、SPI像素、3918字节及UART控制|
|Python|164项PASS|
|F模式综合/实现/STA/DRC|当前F04及乱序配置PASS，WNS0.735ns/WHS0.060ns，477逻辑LUT3＋33FF|
|S模式严格反馈实现|不支持可靠放行：P&R后85项LUTLP-1，无bit/无下载|
|F模式初次实机运行|JTAG/UART、约十分钟Pong计数及58份RAM快照对照已完成|
|实机游戏画面及操作|用户确认Pong/Snake正常；原固定发球体验限制已说明|
|输入事件缓存|单元/板级通过，F04下载，用户确认短按明显改善|
|独立乱序食物软件|315场景154611事件；变体SPI/键/UART仿真；实机66tick/12份完整RAM对照PASS；人工新体验待确认|

CPU实际使用冻结结构；F模式以原生FF替代66存储MUX，不能冒充543颗实体MUX的存储时序验证。FPGA实现结果不改变543颗CPU预算，原物理时序风险不因此消失。

主时钟50MHz；CPU主动微周期默认1MHz；当前Pong/ Snake外部节奏10/5tick/s（原F02为30/10）；OLED内容约58Hz、SPI10MHz、UART115200。原生FF仍完全适用于FPGA原型。显示为只读状态呈现，不是FPGA另写游戏引擎或CPU原生OLED程序。

结论边界：可推进FPGA功能原型及软件/接口调试；不能凭本轮关闭实体157最小延迟、反馈竞态、时钟分配、电源与PCB验证要求。是否进入实体157原理图最终设计仍需用户审阅及独立物理条件，不由本报告自动放行。

入口：[工程指南](../../fpga/projects/m20/cpu_validation/README.md)、[结构](M20_V3_STRUCTURAL_IMPLEMENTATION.md)、[时钟内存](M20_V3_CLOCK_MEMORY_INTEGRATION.md)、[按键显示](M20_V3_KEY_OLED_INTERFACE.md)、[游戏](M20_V3_GAME_VERIFICATION.md)、[资源时序](M20_V3_TIMING_RESOURCE_REPORT.md)、[实机](M20_V3_HARDWARE_TEST_REPORT.md)、[进度](../tasks/m20-v3-fpga-20261104.md)。原始失败、诊断和游戏记录分别保留，不重写历史PASS/FAIL，不创建V3最终Tag。

独立71向量硬件指令诊断、非法0010 TRAP、实机STOP/STEP/停止复位/三速度均通过，原始摘要在v3_resources。当前F04 WNS0.735/WHS0.060ns、8787LUT/5986FF，CPU477逻辑MUX＋33FF，1BUFG、4RAMB36＋1RAMB18、4个外设LUTRAM、DSP0；当前bit与命令见工程指南及[乱序食物报告](M20_V3_SNAKE_SHUFFLED.md)。源码和报告尚在工作树，未自动commit/Tag。

后续F05已按用户要求仅交换KEY5切游戏、KEY7暂停，保留同一乱序食物机器码。164项Python及板级按键/SPI/UART通过，路由WNS0.849/WHS0.042ns、DRC0，21:00:11已下载；当前8789LUT/5986FF，CPU477逻辑MUX＋33FF不变。F04上述资源作为历史保留，F05证据与实机新键位反馈见[互换记录](M20_V3_KEY_SWAP_F05.md)。

用户确认F05互换符合预期，新增BOOT页KEY5入口的F06已独立通过Python164项、板级提示SPI像素/BOOT及正常键位断言；WNS0.982/WHS0.062ns、DRC0，21:27:31下载。8774LUT/5986FF、CPU477逻辑MUX/33原生FF不变；原F05记录不改写。BOOT入口定位、复现及实机反馈见[F06记录](M20_V3_BOOT_ENTRY_F06.md)。


## 首次Private发布时的整体确认

用户在本次GitHub任务明确确认V3 FPGA实机验证已完成。由[整体正式报告](../reports/m20_phaseV3_20261104.md)承接本页此前“待审阅”的时点状态，原始采集、F06交互报告及失败不回写。验收仅FUNCTIONAL_STORAGE，STRICT_MUX及实体157时序保持开放。新的版本Tag需完成本地纳管和隔离恢复后再建立，真实SHA见发布记录。
