# SWC-LOCAL-GIT-FREEZE-20261103

状态COMPLETED，2026-11-03。用户授权本轮本地commits/annotated tags；禁止添加remote、远程访问、push/pull/fetch/上传。结束后停止，不进行PCB/优化/硬件设计。

## 实际提交与stage保全

- A 5b5a4dfae4df179d564eea4dd6f82f9416b9d5c9：269文件回溯完整快照，原文件已有跨阶段内容，不伪造早期时间点。
- B a964292e0408da6d8595eaf3c54f07c72608301c：改两份验证工具来源路径、纳管原V1路径定义与小ROM、只读审计及3项新测试。
- B补充 c20501bef7666f2666d75838efb578dec7398cdf：字节保留。A受全局autocrlf=input影响规范化21CSV，B普通add未强制刷新缓存；renormalize补充后Git字节匹配原文件，无amend/旧数据改写。
- C 7742a637e41794636f4e8dc4966b1c3e8ac090d4：物理分析SHA与版本索引封存。最终记录提交SHA由Git解析，避免自引用。

原四份stage已逐一核对：三份与工作树相同、A保留原blob；旧TASK归档原全文。INITIAL_STAGED_20261103.json保留OID/内容SHA；未reset或丢弃内容。

## 完成清单

- [x] AGENTS/TASK/提案/报告/源码与Git实际状态核对，作者经用户提供配置本仓库。
- [x] 全现存源码纳管，ignored文件原位保留。11534历史文件/1513822062字节只读索引并末尾核验未改；原3原始模块目录范围common/m11/m20，无额外M0–M19目录可虚构。
- [x] .gitattributes字节保留及安全ignore；不按.bin/.memh/.json一刀切。正式生成物与小ROM可再生。
- [x] 两annotated tags实际对象类型/目标核对，未移动tag或改历史；无remote。
- [x] 两个独立干净detached worktree没有旧V1 build，实际再生14文件/资源独立审计、冻结ISA/ROM、113 Python、完整XSIM、物理示例和新轨迹分析PASS。
- [x] 本轮新验证数据1730文件/41065753字节复制到build/local_git_20261103/recovery_evidence，另有新SHA索引，不覆盖旧日志。
- [x] workflow/release history/source manifest/local report和最终任务状态已纳管；最终主工作区clean检查在提交后执行。

## 验证证据

|项目|逻辑worktree|物理worktree|证据|
|---|---|---|---|
|SOURCE/ISA/ROM/14文件再生|PASS|PASS|各build/recovery/audit/release_audit.json|
|独立477/33/543/542与603参照|PASS|PASS|同上|
|Python|113 PASS/10.982s|113 PASS/10.937s|python_tests.log|
|完整V2.1 XSIM|PASS/40.855s|PASS/40.064s|xsim_v21.log及v21目录|
|50521非法实际终态/恢复|PASS|PASS|v21/xsim/illegal.log|
|87场景/57331事件与RAM|PASS|PASS|v21/verification.json及CSV|
|DFF/接口模型与79轨迹见证|PASS，仅数字/分析|PASS，仅数字/分析|models与physical_analysis|
|真实157时序/PCB/上板|NOT_RUN|NOT_RUN|本轮范围外|

详细路径由build/local_git_20261103/{logic_recovery.json,physical_recovery.json,recovery_paths.json}记录；新证据已另存主工程build，即使/tmp临时副本被系统清理也有日志/CSV/输入/期望/审计。

## 风险和下一次恢复

当前无未验证正式源码修改；最终main在tag之后可有记录提交，核心/物理字节不变。Git不是原1.51GB数据的异机备份，外部介质备份由用户另行安排。本轮未进行任何网络/上传/同步。

先读M20_LOCAL_GIT_REPORT和本地Git实际状态，不重复commit/tag，不移动tag，不清理历史build/results。只读审计命令写新build目录。旧192/168等manifest仅指各版本实际来源范围，不以提交记录证明实物时序。当前任务结束，后续PCB、硬件或优化需另给范围。
