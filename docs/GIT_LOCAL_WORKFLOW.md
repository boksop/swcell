# SwCell 本地 Git 工作流

2026-11-03。用户本轮授权本地 commits 和 annotated tags；严格禁止添加remote、远程访问、push/pull/fetch、上传或同步。当前不是远程备份方案。

## 纳管边界

纳管全部现存工程源码，不限于M20：RTL/SV、公共UART/PRBS/CDC、M11与诊断/测试工具、Tcl/XDC/板卡公共配置、Python/依赖、ISA/汇编/解释器/游戏、TB/回归定义、正式MUX生成器与生成SV/连接JSON、独立审计、FPGA外设适配器、物理参数/分析器、技术文档和小型汇总、README/AGENTS/任务状态。

当前实际RTL目录只有common、modules/m11与m20；未找到独立M0～M10、M12～M19目录。所有现存源码均保留/纳管，不虚构尚不存在的模块；工程外资料不在本仓库恢复保证范围。

按用途判断文件，而非扩展名：游戏未填充ROM .memh/.bin是小型冻结参考，纳管；正式网表JSON及参数JSON纳管；.bit/.ltx原则上作为独立证据索引；仪器raw JSONL/CSV与波形不混入源码仓库。

默认忽略build、虚拟环境、Vivado/XSIM缓存、.Xil、WDB/VCD/FST/FSDB、DCP、临时日志、旧重复ZIP、本机board.local配置、个人提示词、许可文件和凭据。忽略不等于删除，原文件原位置保留。不要无差别git add或为了干净状态清理证据。

## 历史证据

[历史证据索引](evidence/historical_20261103.csv)列出results、非缓存build证据及原ZIP的相对路径、大小、SHA256和类别；[摘要](evidence/historical_20261103.summary.json)记录范围及排除。索引不是原始数据备份，也不是测试PASS证明。

重建索引命令仅用于新的审计日期/新输出路径：

```bash
python3 -B tools/git/index_historical_evidence.py --output docs/evidence/NEW_DATE.csv
```

不覆盖旧索引来追求预期SHA。长期建议将索引对应数据复制到独立介质并读回核对，再进行任何人工清理；本轮不删除/同步/上传。results .gitkeep只保留目录入口。

## 提交策略与历史真实性

现有文件已包含V2.1/V2.2，README和依赖交叉引用，无法安全伪装三个原始开发时点。因此A为当前完整回溯快照（非原始V1开发日期）；B为实际新增的可恢复性修复、冻结ROM和本地审计；C为物理分析封存/版本索引；必要的D只记录提交后的真实恢复验证结果。所有日期为实际本地提交时间，不amend/rebase或倒填日期。

原四份stage均已核对。三个文件与工作树相同；旧TASK blob全文保存在[历史暂存TASK](history/TASK_PROGRESS_staged_20261017.md)，四份blob/SHA映射见[初始索引](history/INITIAL_STAGED_20261103.json)。A提交当前已检查的TASK，不reset索引，也不丢失原stage内容。

两个本地annotated tags：m20-v2.1-logic-verified仅指指定数字回归/543完整接口与542纯功能；m20-v2.2-physical-analysis仅指物理分析完成。两者都不承诺真实157时序/主频或PCB放行。tag所指树可能含既有跨阶段文档，不能据此虚构开发顺序。原545候选有非法HALT缺陷，不作正式通过标签。

## 日常操作

开始先读TASK并检查status/diff；按明确路径暂存并审查cached diff。只有得到授权才commit/tag；本轮授权不延伸为未来自动提交/远程权限。禁止reset --hard、clean、rebase、amend及用户列出的全部远程操作。

本轮作者仅配置在本仓库：boksop <boksop@163.com>（用户提供）。本地提交禁用外部hooks和签名调用以保证不触发仓库外动作，不修改全局配置。

## 恢复与审计

干净本地detached worktree用于恢复检查，不创建remote；所有新缓存写在临时worktree中，旧build不复制作为成功前提。审计器使用版本化来源清单，从跟踪文件生成MUX网表、比对SHA和独立477/33/543计数，另检查ISA/ROM和脏状态。报告写新build目录或临时目录，不修改源码/索引/提交。

最终命令与提交/tag索引见[M20本地Git报告](m20/M20_LOCAL_GIT_REPORT.md)。本轮结束即停止，不进行PCB/逻辑优化或硬件测试。

本轮完成：两个annotated tags及后续恢复记录已建立，最终实际状态见M20_LOCAL_GIT_REPORT.md。只读审计命令为`python3 -B tools/git/local_release_audit.py --output build/NEW_RELEASE_AUDIT`；报告目录需全新，旧索引/证据不覆盖。
