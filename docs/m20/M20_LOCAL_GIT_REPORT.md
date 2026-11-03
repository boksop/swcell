# SwCell / M20 本地Git封存与恢复验证报告

日期2026-11-03。**本地版本管理与两轮干净恢复验证完成；真实157硬件时序未验收。** 本轮不进行PCB、逻辑优化或硬件设计。

## 分支、提交和标签

当前工作分支main。原仓库无首个commit，未删除或重新初始化.git；按现有混合工作树建立回溯基线，不伪造早期开发时间。

|实际本地提交|完整SHA|内容|
|---|---|---|
|A|`5b5a4dfae4df179d564eea4dd6f82f9416b9d5c9`|完整当前源码快照，包含既有跨阶段文件；269文件|
|B|`a964292e0408da6d8595eaf3c54f07c72608301c`|便携来源清单、冻结ROM、只读审计及恢复工具测试|
|B字节修复|`c20501bef7666f2666d75838efb578dec7398cdf`|使21份CSV的Git blob恢复为未改动工作树的原始CRLF字节|
|C|`7742a637e41794636f4e8dc4966b1c3e8ac090d4`|物理分析封存manifest与版本索引；硬件仍TBD|
|最终验证记录|本文所在提交，以`git log -1 --format=%H -- docs/m20/M20_LOCAL_GIT_REPORT.md`解析|仅验证记录/索引/任务状态，避免文件内写自身提交SHA形成循环|

|本地annotated tag|目标commit|验收含义|
|---|---|---|
|m20-v2.1-logic-verified|`c20501bef7666f2666d75838efb578dec7398cdf`|数字功能/结构与本地恢复通过；不代表硬件时序|
|m20-v2.2-physical-analysis|`7742a637e41794636f4e8dc4966b1c3e8ac090d4`|分析交付；实物时序/PCB未验收|

最终main比物理tag多一个记录提交，CPU源码/生成网表与标签保持相同；不移动标签、不amend/rebase。两tag实际对象类型为tag，目标已逐一检查。所有作者/提交者均为用户提供的boksop <boksop@163.com>，只设置本仓库，不配置remote。

## 纳管与排除

最终跟踪284文件，包含现存M11/公共RTL/UART/PRBS/CDC/FPGA脚本、M20 V0/V1/V2/V2.1/V2.2、ISA/软件/测试/小型ROM及可再生网表、参数、审计/文档。没有只收M20而遗漏现有其它源码。

当前工作区没有独立M0～M10、M12～M19目录；无法凭本仓库恢复工程外资料，但没有删除任何现有文件。两个board.local文件当前也不存在，公共模板/实际50MHz配置已纳管。

build、虚拟环境、Vivado/XSIM缓存、大波形/bitstream、原始大量采集、旧ZIP、个人提示词、许可和凭据排除，原位保留。[工作流](../GIT_LOCAL_WORKFLOW.md)说明扩展名例外：Pong/Snake小型.bin/.memh纳管，正式连接JSON纳管，大型.bit/.ltx走证据索引。

历史文件独立索引11534项、1513822062字节：[CSV](../evidence/historical_20261103.csv)及摘要；索引SHA `5ff4610147ec02eb62a476ccb0de0991c462af97893be4ecebb1532b4e818596`。本轮末尾逐文件重新读回比较，原历史内容没有改写。它们尚不是异机备份，需要用户另行安排介质保全。

## 四份旧staged文档

已检查AGENTS、TASK_PROGRESS及两个旧任务文档。三个文件的staged/worktree字节相同，原blob保留在A；TASK的旧stage全文以[历史TASK](../history/TASK_PROGRESS_staged_20261017.md)纳管，SHA与原stage完全相同，当前TASK则正常演进。四份blob/OID映射见[初始索引](../history/INITIAL_STAGED_20261103.json)。未reset索引或丢弃未提交内容。

## 恢复性问题及真实修复

1. V2/V2.1验证工具原先读取ignored build/m20_300/v1/inputs_manifest.json，纯Git恢复会失败。现在改读software/m20_300/reference/v1_source_paths.json，保留原32个来源及历史SHA，新运行计算当前SHA。两份验证Python工具仅作来源可移植性修改；RTL/ISA/原游戏/原证据未改。
2. 全局core.autocrlf=input使首次入库21份CSV被规范化；普通add未强制刷新已有stat缓存。通过.gitattributes的* -text及补充renormalize提交修复，所有目标Git blob与原工作树字节相同。保留A/B原历史，不以改写原文件匹配SHA。

当前192条核心/物理来源SHA见[M20_SOURCE_MANIFEST](M20_SOURCE_MANIFEST.md)。机器manifest不含自身SHA；旧阶段manifest保持原样。

## 提交后两轮实际恢复验证

两个独立、干净、本地detached worktree分别恢复逻辑tag目标及物理tag目标。未使用clone/remote，目录中没有旧V1 build清单，所有输入/期望/回归结果都从跟踪源码重新生成。

|项目|逻辑目标c20501b|物理目标7742a63|
|---|---|---|
|当前源码SHA/ISA/小ROM核对|PASS|PASS|
|14份V2/V2.1 SV/JSON重生成字节比较|PASS|PASS|
|独立477组合/33状态/543完整/542功能计数|PASS|PASS|
|603结构级参照|PASS|PASS|
|全Python|113 PASS，10.982s|113 PASS，10.937s|
|V2.1完整XSIM|PASS，40.855s|PASS，40.064s|
|全非法实际TRAP及恢复|50521 PASS|50521 PASS|
|CPU/游戏三方与完整RAM|87场景/57331事件PASS|87场景/57331事件PASS|
|内存/reset、FSM、X/Z、数学数据通路|PASS|PASS|
|物理数字示例/FPGA适配器|PASS，仅示例|PASS，仅示例|
|新真实RTL轨迹分析|79组同边沿活动见证|79组同边沿活动见证|
|检查后临时worktree状态|干净|干净|

XSIM脚本实际运行，不引用旧PASS代替恢复。113包含原110及新增3项本地审计/缺失旧build依赖保护测试；本轮没有重新测试FPGA实物。545旧候选始终保留“非法进入HALT”缺陷标识，没有功能通过tag。

本轮新证据已复制到build/local_git_20261103/recovery_evidence/{logic,physical}，共1730文件/41065753字节，另有[新验证SHA索引](../evidence/local_git_recovery_20261103.csv)和摘要。它们是本轮新产物，不覆盖原历史目录。临时目录路径及各原始日志见summary和build中的recovery_paths.json；可由用户后续仅清理这些本轮临时副本。

## 最终检查与停止边界

提交后的最终审计写入build/local_git_20261103/final_audit/release_audit.json及.md：解析实际HEAD/tag、192条SHA、网表/ROM/ISA、跟踪文件数和status。最终应为284文件、主工作区干净、无未提交/未跟踪文件、remote为空；被忽略数据仍在。最后记录提交SHA由该JSON/本地Git读取，避免自引用。

本轮未执行添加remote、push、pull、fetch、远程同步或上传，没有GitHub/GitLab访问。没有reset --hard、clean、rebase、amend、分支切换或历史重写。没有待确认的现存工程源码；若另有M0～M19资料在工程外，应后续另行纳管。

版本管理工作完成后停止，不继续PCB开发、逻辑优化或硬件设计。
