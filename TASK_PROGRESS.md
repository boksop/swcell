# SwCell 当前任务进度

2026-11-04，Asia/Shanghai。分支main。**M20-V24-RELEASE-20261104：COMPLETED。** 用户批准有条件数字验收，已按本地流程定版；标签 `m20-v2.4-digital-verified`，目标用 `git rev-parse m20-v2.4-digital-verified^{}` 解析，避免文档自身SHA循环。

[正式阶段报告](docs/reports/m20_phaseV2.4_20261104.md)｜[本地定版报告](docs/m20/M20_V24_LOCAL_GIT_REPORT.md)｜[详细任务](docs/tasks/m20-v24-release-20261104.md)｜[恢复机器结果](docs/m20/v24_release_resources/recovery_validation.json)。

## 已完成与实际证据

- [x] 原90份stage逐blob归档为历史提交86fdc9e，未reset或丢弃；完整当前源码/报告提交4a95665，干净测试夹具入口修复80593a1。最后文档提交记录实际恢复，不改CPU/ISA/ROM/20发生器。
- [x] 纳管RTL、正式生成SV/JSON、生成器、独立资源审计、测试、复现入口、原79向量、关键CSV/JSON/图和SHA索引；build/缓存/大型波形/bitstream不纳管，保留原位。
- [x] 原始full_r1六配置各87/57331、B/C各50521非法及恢复保持通过；原8089文件/系统tar复核一致。
- [x] 新无历史build的干净检出：151 Python PASS（13.309s），56组仍24问题配置，632实验仍131错误，B/C各7内存＋7控制＋最小程序通过；7生成件字节一致，563预算和206份V23保护通过。
- [x] 首轮干净树2个旧目录夹具失败记录保留；新增入口临时创建空目录夹具，未修改冻结V23测试或断言，不伪造旧数据。原时序失败也未改判。

## 验收与版本边界

数字功能VERIFIED；指定TAP16/链2ns及独立叶端假设下CONDITIONAL，D1/D2有效最低22/22ns。实体min/max、Buffer/PCB、真实锁存边界、FPGA实现/STA和硬件仍OPEN。V23 tag对象与目标aecf570保持。annotated tag正文明确这些限制；无远程仓库/上传/同步，无V3、PCB或实机。

## 下一次恢复

先读定版报告和Git状态/标签；本次已完成，不重复commit/tag或覆盖原full_r1。若需复现，设置工具路径后运行 `bash sim/scripts/run_m20_v24_system.sh`，使用新输出目录；单独Python用 `python -B tools/test/run_python_tests.py`，自足负测用 `bash sim/scripts/run_m20_ff16_cones_replay.sh`。旧review入口仅用于有原始build证据时的历史审计。

当前应无未提交非忽略文件；目录 `build/m20_300/v24_release_20261104/` 保留本次索引备份、两次detached恢复及原始日志，源清单见 `docs/m20/M20_V24_GIT_FILES.csv`。忽略数据需另行离线备份；未上传或删除。等待用户新任务，不自行进入硬件阶段。

历史：[C/D开发](docs/tasks/m20-v24-ffcd-20261104.md)、[B深化](docs/tasks/m20-v24-b-review-20261104.md)、[A/B](docs/tasks/m20-v24-ff16-20261103.md)。
