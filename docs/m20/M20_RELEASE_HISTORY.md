# M20 本地版本与验收边界

2026-11-03回溯整理。本表描述可核实的工程阶段，不倒填Git开发历史或提交时间。所有本地提交发生在本次整理期间。

|工程阶段|数量/状态|证据与边界|
|---|---|---|
|V0/V1|冻结ISA、33位状态、Python与行为RTL指定回归通过|[V1报告](M20_300_V1_TEST_REPORT.md)，游戏ROM168/368字；不代表物理157时序|
|V2 shared|537组合+66存储折算=603，已验证参考|[V2报告](M20_300_V2_TEST_REPORT.md)，原件独立保留，另有738基线|
|原545候选|479组合+66；**不合格正式版**|[候选评审](M20_300_CANDIDATE_COMPARISON_20261102.md)：非法编码识别后进入HALT6而非TRAP7|
|V2.1|477组合+66=543完整接口；纯功能476+66=542|[本轮结构报告](M20_300_V2_1_TEST_REPORT.md)，非法转态修复、50521非法实际终态/恢复、87场景57331事件通过|
|V2.2|物理分析完成；实物时序**未验收**|[物理分析](M20_PHYSICAL_FEASIBILITY.md)，79组同边沿活动见证，时钟/负载/接口/PCB仍有TBD|

## 本次真实提交组织

- A：`5b5a4dfae4df179d564eea4dd6f82f9416b9d5c9`，完整当前回溯源码快照，已包含当时存在的跨阶段文档/代码；不是伪造的早期V1/V2时点。
- B：`a964292e0408da6d8595eaf3c54f07c72608301c`，恢复能力：两份验证工具改读纳管V1来源清单、冻结小ROM、只读release审计和新单元测试。不改CPU功能。
- B补充：`c20501bef7666f2666d75838efb578dec7398cdf`，字节保留。全局autocrlf=input曾在A入库时规范化21个CSV；B的普通add未强制刷新stat缓存，补充commit明确renormalize后，Git中CSV字节与原位文件完全一致。未amend、未修改历史原文件。
- C及最终验证记录：以本地tag与[本地Git报告](M20_LOCAL_GIT_REPORT.md)解析，不在文件中写自身SHA形成自引用。

逻辑tag目标为`c20501bef7666f2666d75838efb578dec7398cdf`，已从没有旧V1 build的干净worktree完成113 Python、完整XSIM与新轨迹79组分析再验证。

Tags均为本地annotated对象。`m20-v2.1-logic-verified`只表示数字功能/恢复验证；`m20-v2.2-physical-analysis`只表示分析交付。两者均不表示真实DFF建立保持、最高主频、PCB或上板验收。

关键源码和ROM清单见[M20_SOURCE_MANIFEST.md](M20_SOURCE_MANIFEST.md)；原始仪器/历史build证据另有[独立索引](../evidence/historical_20261103.csv)，保留原位，不借Git提交记录冒充测试证据。

最终验证记录提交保存两轮干净恢复结果，主分支HEAD可在物理tag之后；没有移动tag，核心/物理封存文件不变。所有具体SHA和测试口径见M20_LOCAL_GIT_REPORT.md，最后记录提交自身SHA由Git解析，避免自引用。

## 2026-11-03：V2.3模式A本地定版 / V2.4候选审核

- aecf570c2e33563179e95e1615fd005cc19817f5：原48文件/证据一致性通过后提交；annotated tag m20-v2.3-two-phase-sim-verified仅模式A数字仿真，非外部Johnson或实体时序。
- 5e601a9：V2.3用户确认正式报告及3个入口文件，未混V24审查。
- V2.4候选：116发生器MUX+543核心，当前参数A/B/C完整对照PASS；独立Master/Slave选择弧混合角未覆盖，按用户要求暂停，不创建验收tag，不作正式通过结论。见M20_V24_DESIGN_REVIEW.md。

## 2026-11-04：V2.4前馈主线A/B，未定版

用户确定固定16级/4静态抽头的20颗前馈方案为主线；17/116颗Johnson保留为历史。新[报告](M20_V24_TEST_REPORT.md)中结构及模型检错VERIFIED，56组为32 CONDITIONAL/24 FAILED；快速链最小延迟敏感性四tap均负裕量且有真实流水错误，门禁STOP_BEFORE_C_AND_D。实体抽头、完整服务/CPU联合与物理时序NOT_VERIFIED。没有新commit或验收tag，V2.3原tag和证据保持，不把旧候选的PASS借给本版本。

## 2026-11-04：V2.4-C/D 数字系统交付，未定版

用户明确授权数字功能与实体时序分别验收。新服务/控制实际对接单路 REF 和原 20 颗发生器，保持 543 CPU/ISA/ROM。六配置 A/B/C logic/timed 各 87 场景、57,331 事件与全部微状态通过；B/C 各 50,521 非法终态和恢复，151 Python 通过；TAP16 条件下叶端 D1/D2=22ns。原 56/632 负测重放保留失败；[完整报告](M20_V24_FULL_SYSTEM_VERIFICATION.md)。数字交付完成供审核，实体时序仍 OPEN。HEAD/tag/原索引保持，无新 commit、Tag 或远程操作；未进入 V3。

## 2026-11-04：用户批准 V2.4 有条件数字验收与本地定版

- 用户明确批准数字验收；模式A/B/C的logic/timed各87场景/57331事件通过，B/C各50521非法终态/恢复；543+20=563，实体时序/FPGA实现/硬件仍OPEN。
- `86fdc9e036fb7beee16c896ee00e5502b5391708`：原90暂存blob逐字保留的历史快照（含116候选和前馈A/B），不伪造开发时间点，也不将该提交单独视为验收。
- 完整当前源码、生成器、独立审计、79原向量重放、关键结果及正式报告按[定版报告](M20_V24_LOCAL_GIT_REPORT.md)纳管；最终目标以本地annotated tag `m20-v2.4-digital-verified`解析，避免自身SHA循环。
- V23 tag不移动；原失败仍24问题配置/131局部错误，不重写；不进行远程Git或新硬件阶段。

本地定版恢复补充：完整当前源码提交4a95665；干净树暴露2个旧输出保护测试的目录夹具前提，修复入口提交80593a1，未动冻结测试。最终干净检出151 Python、56/632负测及B/C门禁均通过，7个生成文件字节一致。首轮失败与最终通过分开保留；最后文档提交记录恢复结果，最终tag仍只作有条件数字验收。


## V3 FPGA功能原型（2026-11-04用户确认）

用户在首次Private GitHub发布任务明确确认XC7K325T上两游戏、按键/OLED已通过；[正式V3报告](../reports/m20_phaseV3_20261104.md)与74份原样精选证据纳管。当前F06使用FUNCTIONAL_STORAGE：477逻辑组合MUX＋33原生FF，CPU预算仍543。STRICT_MUX实际P&R有85项LUTLP-1/WNS−22.002ns，无bit/无硬件放行，实体157时序开放。原603、缺陷545、V2.1修复543及V2.3/V2.4原Tag全部保留。

V3 commit/annotated Tag及干净恢复结果以[发布记录](../GITHUB_PUBLISH_REPORT.md)实际输出为准；不倒填历史，不将FPGA原生FF验证冒充双MUX DFF签核。
