# SwCell 首次Git提交准备方案

日期：2026-10-28。**本文件是待用户确认的方案；尚未commit/push、未新增暂存文件，也未自动合并忽略规则。** 当前main没有首个commit，索引原来仅有四份进度Markdown。本轮在工作区更新进度和准备文档，索引仍保持原样。

## 1. 首次提交的范围

首次提交应记录迁移后、已核验的源码/配置/小型文档快照。它不能重建过去没有Git提交的RTL开发历史，也不能以commit本身证明测试通过。

精确逐文件清单在[git_first_commit_files.txt](git_first_commit_files.txt)：当前共**110个文件，约1.38MiB**。该清单由当前实际文件生成，路径以工程根为基准，包含自身；不是泛指整个目录。带大小/SHA256的审核清单保存在`build/env_setup_20261028/git_first_commit_manifest.csv`，仅用于本次审核，不提交庞大的构建内容。

|类别|计划纳管|
|---|---|
|根入口|`.gitignore`、`README.md`、`AGENTS.md`、`TASK_PROGRESS.md`|
|RTL|`rtl/`内公共模块、M11 Phase1/Phase2实现|
|板卡/构建|`fpga/`内SV、Tcl、真实XDC、空白模板、配置示例、诊断说明；排除board.local覆盖项|
|仿真|`sim/`内独立模型、全部Testbench、Tcl/脚本及串行协议检查程序|
|PC端|`host/python/`内程序、单元测试、原requirements及新Python3.12已验证版本快照|
|文档与小型插图|`docs/`内架构、测试说明、协议、历史验证/正式报告、任务进度、图表和审计摘要；本次环境和Git方案|
|结果目录占位|`results/.gitkeep`，不包含实际测量数据|

历史正式报告和少量图文证据摘要值得进入Git；原始数据、镜像、路由设计和长日志独立保存，报告通过路径和SHA指向它们。CSV纳管清单每项均基于当前实际内容；用户确认后若文件又改变，应重新生成审核清单。

## 2. 排除的文件

|路径/模式|原因|是否需要另行备份|
|---|---|---|
|`.git/`|Git内部对象/索引/辅助refs，不作为普通文件add|需要Git备份时另做仓库级备份；不复制旧.git覆盖当前|
|`.venv/`|旧Python3.10环境，原样保留；二进制与路径依赖|可保留迁移快照；不作为新环境重建依据|
|`build/venvs/python312/`及其它本地venv|新环境可按版本快照重建|版本快照和安装来源纳入文档；环境目录不用提交|
|`results/*`（`.gitkeep`除外）|原始JSONL/CSV/检查点/图表/证据包|**必须备份**，不能因为Git忽略而删除|
|`build/phase2/`、`build/phase2b/`、`build/vivado/`|包含镜像、routed DCP、timing/utilization、来源和历史回归日志|**证据部分必须备份**；不能整体当垃圾清理|
|`build/env_setup_20261028/`|环境准备日志、安装引导、隔离重分析副本、审核manifest|建议保存验证摘要与版本信息；不必提交所有安装/重绘副本|
|`.Xil/`、`__pycache__/`、`*.pyc/*.jou/*.log/*.wdb/*.pb`|运行/编译缓存和大型波形|诊断日志按需留档；不能用这些模式决定删除已引用的测试证据|
|`M11_P1&P2.zip`、`M11_P2B.zip`|历史工程/结果归档，重复且不适合普通Git增量|**必须备份**；P1正式原始数据目前在前者内部|
|`fpga/projects/m11/functional/config/board.local.tcl`、`constraints/board.local.xdc`|机器/板卡本地覆盖项|若实际使用，独立备份并审查；当前默认真实board_50mhz文件仍提交|
|`codex提示词.txt`|个人工作提示词，首次提交不默认纳入|另存个人资料，内容评审后再决定是否公开|
|`.agents/`、`.codex/`、`.aws/`、认证文件/数据库|本地助手/账户状态，非工程源码|按各自安全策略管理，不并入源码仓库|

完整逐文件排除清单（含分类和原因）在`build/env_setup_20261028/git_excluded_files.csv`。它会列明实际存在的文件；上表额外包含未来可能出现的模式。

## 3. 现有.gitignore检查

当前已有results/build/.Xil/旧.venv、Python缓存、Xilinx日志波形和board.local排除规则；`results/.gitkeep`例外有效。新环境放在build内，已实际用git check-ignore核验，无需为本轮环境修改根忽略文件。

现有规则的不足：根目录历史ZIP和个人提示词未忽略；若以后新建`.venv312`等根目录环境，也不会被`.venv/`覆盖；本地助手目录和更多Python工具缓存可补充排除。

拟议补充规则保存为[gitignore.proposed](gitignore.proposed)，**仅为待审文本，不是已生效规则**。建议用户确认后将其补充到根`.gitignore`，保留现有results/.gitkeep例外。不要用`*.png`或`*.json`这种宽规则忽略正式报告插图/小型摘要，也不要为了纳管而取消results/build的忽略。

未来若确实需要版本化选定数据，应单独定义data manifest和存储策略；本次无需引入LFS或将全部bitstream/raw塞进首个commit。

## 4. 数据备份建议

建议源码Git与测试证据备份分开，并建立SHA256清单。至少保留本机、另一块独立介质/主机以及一份离线或远端副本；旧Ubuntu主机目前仍有相同工程，可作来源，但不能替代长期独立备份。

|必须保留|内容/理由|
|---|---|
|`results/`完整目录|所有正式/诊断/中断attempt、raw、CSV、JSON、checkpoint、summary、图表及数据配置；失败记录同样保留|
|两个根ZIP|尤其M11_P1&P2.zip中的正式P1轮次；未展开不是没有证据|
|P2/P2B构建证据|每个测点的source_manifest、build_status、bitstream、routed timing/utilization/CDC/IO/DRC；用于证明镜像与记录关联|
|routed DCP及历史源码归档|保存确切布局布线与对应源码，避免后来工具/参数重建无法逐字节复现|
|仿真与验证日志|原2022.1回归、环境准备52项测试及离线重生成检查，不能拿新环境PASS替代旧硬件证据|
|工程外审计资料|`/home/boksop/swcell_migration_audit.md`、`swcell_migration_diff.csv`；保持迁移来源记录|
|原始需求附件|审计已列出的旧机`.codex/attachments/.../已粘贴的文本.txt`新机缺少；需要时用户决定定向恢复，不迁移认证数据库|

`results/M11/m11_phase2b_20261017_evidence.tar.gz`约5.4MiB，适合上传分析；它只有三份亿次bitstream及各镜像文本报告，**不包含全部105份bitstream/routed DCP**，所以不能替代build证据完整备份。对应包外SHA256、包内逐成员SHA均应保留。

实际重要归档大小/SHA清单保存在`build/env_setup_20261028/backup_archive_manifest.json`。备份完成后应在目标端验证SHA，再抽样离线读取raw及图表。不要仅依据文件数量相同判备份成功。

## 5. 用户确认后才执行的步骤

1. 确认本逐文件清单、是否合并gitignore.proposed、是否排除个人提示词及数据备份位置。
2. 对最新工作区重新生成清单，逐项审查，不执行`git add .`或`git add -A`。
3. 仅按已确认清单暂存；重新查看cached diff、大小、敏感配置和测试结果。原四份进度文档如内容更新，也要按最新内容重新暂存。
4. 用户授权首次commit后再提交；push/远端创建另行明确授权。本轮不假定首次commit意味着允许push。

本次只是准备可审查结果，不执行这些步骤。没有更改分支或Git历史。
