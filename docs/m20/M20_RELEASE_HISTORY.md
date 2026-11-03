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
