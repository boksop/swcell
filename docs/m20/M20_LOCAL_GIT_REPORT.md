# M20 本地Git封存记录

2026-11-03。状态：本地提交/恢复验证进行中；最终结果将在验证记录提交中更新。本次不进行PCB、逻辑优化或硬件设计。

已建立完整回溯快照、便携验证工具和当前源码清单；实际提交索引见[M20_RELEASE_HISTORY](M20_RELEASE_HISTORY.md)。全局行尾转换问题已通过.gitattributes与新增字节保留提交修复，未重写历史或改写工作树证据。

正在从独立、干净的本地detached worktree运行：只读release审计、全部Python、完整V2.1 XSIM、物理数字示例及新轨迹重新分析。该目录没有旧ignored V1输入manifest，不能依靠主机原build中的历史PASS蒙混恢复。

所有源文件与小型参考机器码应可从Git还原；历史实测数据和大波形另按索引管理。暂存的旧TASK文本和blob映射已纳管；其它三份stage原文保留。

本报告完成后的精确SHA、tag目标、跟踪文件数、工作区与remote状态由`tools/git/local_release_audit.py`读取本地Git生成JSON/Markdown；不访问网络，不在跟踪manifest中包含自身SHA。最终原始审计记录将保存在`build/local_git_20261103/`。
