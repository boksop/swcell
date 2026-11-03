# SWC-LOCAL-GIT-FREEZE-20261103

状态IN_PROGRESS，2026-11-03。用户授权本地commits/annotated tags，禁止remote增删/远程访问/push/pull/fetch。当前main无commit，原四份staged核对已保存；仅TASK与工作树不同，原全文归档。

## 计划与口径

当前README/任务/设计已混合V2.1/V2.2，不能伪装历史时间点。采用完整回溯基线A，再对恢复性工具与封存记录作真实增量提交；tag只标逻辑/分析验收，不标实物通过。原545保留缺陷标签，603原件不改。

- [x] 执行前命令/源码与报告检查，原stage保存和作者确认。
- [ ] 独立历史证据索引/流式SHA；完善ignore且不删除文件。
- [x] A当前源码完整快照；不倒填日期。
- [ ] 移除回归对ignored build原始manifest的依赖，保留静态来源清单，不改RTL或历史证据。
- [ ] 本地只读release审计及干净副本恢复验证；完整ISA/ROM/生成器/pin计数/Python/关键XSIM。
- [ ] B逻辑冻结tag/C物理分析tag，必要的最后验证记录提交。
- [ ] 最终清单/报告/进度，确认无remote且状态干净。

恢复入口：先读本记录及TASK，检查git log/status/tags，别重复commit或移动既有tag。预检与1244项保护清单在build/local_git_20261103。未有commit时不虚构hash；提交后实时更新。所有原build/results/ZIP原位保留，不允许清理换SHA。本轮只做版本管理和恢复能力修复。

## 新检查点

A已提交：`5b5a4dfae4df179d564eea4dd6f82f9416b9d5c9`。269文件当前回溯快照；Python结果以实际日志为准。原4份stage已保全；全局autocrlf=input使A中21份CSV行尾被Git规范化，工作树原文件未改；B将用.gitattributes的* -text按原始字节恢复入库，不amend A。历史11534文件/1513822062字节已只读索引，build/results原位保留。

B准备：两个验证工具改读纳管v1_source_paths.json，不读ignored历史build；原历史SHA不改。新增冻结小ROM、只读审计与168条核心来源SHA。待干净worktree恢复性验证后创建logic标签。
