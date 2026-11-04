# M20-V24-IMPLEMENTATION-20261103

状态IN_PROGRESS（理论/模型审查阻塞，按用户要求暂停），2026-11-03。用户批准先架构评审再实施；无V24验收tag授权，完成后交报告供审核。

## 已确认基线

V23原48文件已逐项索引SHA、2802原始证据哈希、477/33/66独立审计和临时重生成比对PASS，提交aecf570c2e33563179e95e1615fd005cc19817f5；annotated tag m20-v2.3-two-phase-sim-verified限定模式A。未混V24审查，无remote。旧V23/ISA/CPU源与原PASS不回写。

## 决策

先记录docs/m20/M20_V24_ARCHITECTURE.md，再实施：公共CLK_REF同时送Johnson与FPGA，下降沿采公开相位码及服务，不强制异步CDC。RAM2.5T返回/M3T关，ROM6.5T返回/下M8T开。V24持久写在D1下降沿，明确是新版服务接口，不冒充V23 M-close同刻；复位专项按真实提交点对齐。CPU2/5不变。

生成器纯MUX+双MUX状态：13位（Johnson4、请求同步4、token/ack2、active/step/fault3），88组合+26存储+2互锁=116，CPU543另计，共659未含Buffer。局部H/S反馈是有条件数字候选，单元先验；实际最小器件延迟/亚稳态/PCB未签核。非法状态先sticky故障/关闭输出并保持非法码，再下一边沿修复1000，须显式reset后恢复。正常STOP完成周期停车；停振依赖外部rst钳位，不宣称自动检测。

## 已完成与待验

- [x] V23模式A本地冻结，旧48暂存全部正确，原始证据保护。
- [x] 架构/服务窗口/持久写契约变更先落盘。
- [x] 生成器116颗独立审计，生成可重现；Python独立状态模型对8192×8=65536种状态/请求复位组合一致，新4项单元PASS。
- [x] unit_r4 nominal/fast/slow正常、6单步/RUN/STOP/停振rst、8非法锁定修复PASS，bad_skew触发真实有效相位重叠断言。
- [x] dev_r1带延迟B模式49指令/22223事件RTL执行完成，7内存/复位PASS；仅冒烟，不代表完整验收。
- [x] regression_r1（仅当前参数）：重新运行加脉宽断言的发生器unit gate后，再A/B/C零/带延迟各87/57331、B_timed50521非法终态恢复、各7memory、慢CPU压力。
- [x] 全127项Python、冻结源SHA与7477记录归档；独立混合选择弧不在已验证范围。
- [x] V24待审报告/预算与V23正式报告入口、进度已落盘。
- [ ] 新增独立混合弧模型与本机时序方案，等待用户决定后实施；不标完成。

## 测试证据

|项目|结果|证据|
|---|---|---|
|V23定版一致性|PASS|build/review/v23_freeze_20261103/consistency.json|
|V24结构审计|PASS|build/m20_300/v24/unit_r4/resource_audit.json|
|独立65536控制组合|PASS|build/m20_300/v24/python_unit_dev.log|
|有界时序单元/负测|PASS|unit_r4/{nominal,fast,slow,bad_skew}/run.log|
|B模式冒烟|PASS|dev_r1/xsim/{memory,cpu}.log|
|完整新回归|进行中|regression_r1，结束前不得称全通过|
|STA/实物|NOT_RUN|无板级/新选型/PCB工作|

## 开发失败保留

unit_r1编译变量before为SV关键字，改名；unit_r2事件监视器在active与初始0000不同传播时刻漏看0000，移至参考下降沿稳定观察。unit_r3及r4通过。属于TB修复，不是修改CPU/期望。dev非法watchdog20e9无尺寸十进制常量溢出警告，改为64'd常量，尚待完整非法测试。

## 恢复入口

先读架构/本文件/根TASK，核对regression_r1后台进程和日志，不重复覆盖已存在目录。入口sim/scripts/run_m20_v24.sh（新M20V24_OUTPUT_DIR）；单元入口run_m20_v24_unit.sh。所有V24都在新rtl/m20/v24、sim/m20_v24、host/python/m20/v24_*，旧V23和ISA不改。没有V24 commit/tag/远程，原48已在V23提交中。新理论缺陷无法闭合则先报告，不盲目续跑。

## 结束检查点：发现混合弧模型缺口，暂停

regression_r1实际完成：A/B/C各零/预设延迟87/57331，42内存组，B_timed50521非法及恢复，7配置短路径；127Python PASS。原结果verification.json保留PASS，明确只对其配置成立，不改写。新审查发现本机Master/Slave绑定同一SELECT_NS，独立快慢未覆盖；H/S源端先后不能保证有效锁存端先后，3.2ns理论重叠例见docs/m20/M20_V24_DESIGN_REVIEW.md。未运行该新例，未继续RTL/时序验证，等待用户决定独立弧模型/本机结构评审方向。不能标任务完成。

V23额外正式报告提交5e601a9，仅README+报告索引+V23正式报告3文件，tag仍指aecf570，不含V24。V24原始7477项证据索引保存在docs/m20/v24_resources/evidence_sha256.csv；review_status.json为NEEDS_ARCHITECTURE_REVIEW，当前无V24tag/提交。

恢复：先读设计审核稿第6/7节；不要直接跑run_m20_v24.sh。用户决定后先拆分本机独立弧并小型负测，局部条件明确后才重跑长回归。所有旧V23/ISA/CPU源不改；已有regression_r1不覆盖。
