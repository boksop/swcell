# SWC-PROGRESS-PERSISTENCE-20261016：长期任务状态持久化

- 目标：根TASK_PROGRESS作为状态入口，Git保存真实文件历史；支持上下文压缩、会话更换、额度/系统/VS Code中断后恢复。
- 当前状态：COMPLETED；文档机制核对通过，用户已授权初始化Git main及仅暂存四份文档，未提交/推送。
- 时间：2026-10-16 +08:00。主任务继续入口在 [TASK_PROGRESS.md](../../TASK_PROGRESS.md)。
- 范围：只创建/维护进度文档和合并AGENTS；不在本任务中修改RTL、Python、Tcl或工程架构。
- 分支：main（尚无首个commit）。开始时并非Git仓库；用户明确授权后已初始化且仅暂存四份Markdown，未commit/push。

## 已完成 / 待完成

- [x] 核对Git根目录/分支/status/diff/log：均确认当前无仓库，而不是假定干净工作区。
- [x] 阅读AGENTS、README、Phase2/2B架构与验证记录、检查点和日志。
- [x] 核实完整XSIM回归PASS和Python49项PASS；校验已实采Q0–4的raw和bitstream hash。
- [x] 核对实际进程，识别VS Code闪退后“检查点RUNNING但进程已退出”的不一致。
- [x] 创建根状态入口与任务索引，主任务详情拆分，保留原有工程约束并合并维护/Git规则。
- [x] 核对本次变更仅涉及4份Markdown文件，路径/恢复命令与差异可读；73份功能文件SHA256保持一致，原AGENTS前缀完整保留。
- [x] 用户明确授权后建立Git main并仅暂存本次四份文档；未commit/push，未添加功能源码或构建产物。

## 设计决策

- 根文件保持当前目标、事实摘要与恢复入口，复杂证据放任务详情和验证记录，不复制全部原始日志。
- 维护者在子任务验收、重大决策、失败/风险、新重要阶段、结束/中断前写检查点；不要求逐行修改都更新。
- 字段的RUNNING/COMPLETED必须核实实际日志及进程，不因上下文中断就相信最后一次写入。
- 没有Git时准确记录缺失；可用`git diff --no-index`展示本次文档差异，但不得称为相对HEAD的工作区diff。
- Git commit不能作为测试证据。未验证/未执行/被阻塞分别记录。

## 验证

|测试|方法|结果|证据|
|---|---|---|---|
|Git状态|rev-parse、branch、status、cached diff|PASS：main，四份文档暂存，无commit|`build/progress_persistence/git_validation.log`|
|原有约束保留|AGENTS前后对比|PASS|`build/progress_persistence/AGENTS.before.md`|
|未更改功能代码|rtl/fpga/sim/host逐文件SHA256前后比对|PASS（73文件无变化）|`build/progress_persistence/functional_before.json`|
|状态与工程一致|源码指纹、采集job校验、测试标记、进程核查|PASS|当前任务详情引用的真实日志|
|文档链接/恢复入口|检查本次4份Markdown的链接、字段和命令|PASS|本任务最终检查日志|

## 风险与恢复

文档不能保证突发断电时最后一次更新完成；下次应先对照源码、日志、实际进程修正它。目前仍无首个提交，暂存不等于版本历史或备份；其它源码尚未纳管。初次检查时的无仓库事实与后续授权初始化分别记录，不能混同。不得擅自把全部results/build加入仓库。

最终摘要：4份Markdown已建立、核对并暂存，73份功能文件无变化；原AGENTS约束完整保留，根入口可独立指导恢复。没有Git commit可引用。M11 Phase2B已恢复运行，后续由根进度维护。不需要为了修改文档重跑RTL仿真。

完成核实时间：2026-10-16 22:47:18 +0800。Git初始化与四文档暂存是用户明确授权；不包含提交、推送或添加其它源文件的授权。
