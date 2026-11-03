# SwCell V2 开始前的 Git 基线纳管提案

日期：2026-10-29（Asia/Shanghai）。**仅为待用户确认的方案；不执行 add/commit/push、不创建或切换分支。** 当前 main 没有首个 commit，原来四份已暂存 Markdown 保持原状。此前110文件清单是旧快照，不能当作已经包含M20的新清单。

## 1. 哪些文件进入首次提交

精确逐文件列表为[M20_300_V2_GIT_FILES.csv](M20_300_V2_GIT_FILES.csv)（任务结束前从实际文件重新生成，含类别、大小、SHA256和纳管/排除理由）。建议首次提交记录**当前工程的已验证源码快照**，不伪造过去不存在的提交历史，也不将提交等同于测试通过。

|范围|建议纳管内容|
|---|---|
|根入口|`.gitignore`、`README.md`、`AGENTS.md`、`TASK_PROGRESS.md`|
|M11与公共RTL|既有 `rtl/common/`、`rtl/modules/`，保持原内容|
|M20 V0/V1|`rtl/m20/`原七文件、冻结ISA/规则、Python模型/汇编器、Pong/Snake汇编、原仿真脚本/模型/TB|
|M20 V2|唯一MUX原语、DAG/ALU/CPU生成源码、baseline/shared生成的可审阅SV和连接JSON、独立审计脚本及小型CSV/MD、三方回归源码|
|FPGA配置|`fpga/`内SV/Tcl/XDC/配置示例与已确认的真实板卡配置；机器本地覆盖项排除|
|自动化工具|`host/python/`中源码/单测/requirements及依赖版本快照、`sim/`中SV/SVH/Shell/Tcl/Python入口|
|文档|`docs/`中设计/协议/测试报告/进度、历史正式报告、小型插图和规则/预算表；本提案与新清单|
|结果占位|仅`results/.gitkeep`|

V2生成的SV/连接JSON虽然可再生，仍建议纳管：它们是本轮被计数、仿真和评审的具体结构设计，体量小，方便审查每个157实例；同时纳入生成器，并要求重新生成内容与版本化网表一致。它们不同于Vivado运行缓存或大型波形。

## 2. 哪些内容排除

|范围|处理|理由/备份需求|
|---|---|---|
|`.git/`|不作为普通文件add|Git内部状态不能混入工程文件；需要另做仓库备份|
|`.venv/`、`build/venvs/`等|不纳管环境目录|保留requirements/版本/来源，环境可重建；旧venv不改|
|`build/`、`.Xil/`、`xsim.dir/`、Vivado缓存|排除运行产物|缓存可重建；其中实际验收证据必须先区分并归档，不能一律当垃圾删除|
|`*.wdb/*.vcd/*.fst`、日志、`.pb/.jou`、对象/仿真可执行文件|不入普通Git|失败和验收波形按证据归档保存|
|`results/*`|保留原忽略规则|原JSONL/CSV/图片/采集检查点不能因Git忽略而丢失|
|bitstream、routed DCP、旧timing/utilization、来源tar|不入普通Git|已实测版本需与源码/配置/测试时间一起归档；未来重新构建不能替代旧证据|
|`M11_P1&P2.zip`、`M11_P2B.zip`、`docs/m20.zip`等归档|独立保留，不直接add|可能包含唯一历史原始记录，也可能是重复快照；先核对内容/哈希，不删除|
|`board.local.tcl`、`board.local.xdc`|排除本地覆盖项|若实验实际使用，应独立归档并关联报告|
|`codex提示词.txt`、本地助手/账户状态/密钥|不默认纳入工程|个人配置或机密不属于源码基线；本任务不操作认证数据|

现有 `.gitignore` 已覆盖 build/results/.venv/.Xil/Python缓存和常用Xilinx日志，但仍可能显示根ZIP、个人提示词或根xsim.dir。建议合并此前 `docs/gitignore.proposed`，补充 `xsim.dir/`、`*.vcd/*.fst` 等具体规则；**本轮只提出方案，不修改现有忽略文件**。不要用 `*.json`、`*.csv`、`*.png` 宽规则误排规则表、预算和报告图。

## 3. 历史证据如何归档

源码提交与证据备份分开，建议在工程外的 `~/swcell_evidence_backups/` 或独立磁盘按模块/阶段/时间保存。保留至少一份异机或离线副本，完成哈希和解压抽检后才认为备份有效。本任务不自动同步、覆盖或删除任何历史文件。

|证据集|至少保存|
|---|---|
|M11 P1|正式17项结果、原JSONL/CSV、当时源/配置/镜像哈希；若原始数据只在旧ZIP中，ZIP必须完整保留|
|M11 P2/P2B|原始相位/长测结果、重分析所需数据、频率/相位配置、对应bitstream、source archive、routed timing及关联清单|
|M20 V0|原程序镜像、汇编器/解释器指纹、场景夹具/统计、最大轨迹和报告|
|M20 V1|完整`build/m20_300/v1/`证据（含原CSV/输入/预期/完整RAM/日志/WDB），32源指纹/规则/镜像；原件保留|
|M20 V2|`baseline.json`、V1源快照和复跑、两版网表/审计/三方CSV/最终RAM/波形、版本与保护检查|

每份归档配相对路径→大小→SHA256清单，记录工具版本、UTC/本地时间、ISA与周期profile、源文件指纹、结果目录和报告链接。tar/zstd/zip格式均可，选择已安装工具；不把文件名当数据完整性的证明。报告中的路径+SHA可进入Git，原始大文件留在备份介质。

本轮已经在 `build/m20_300/v2/baseline.json` 对1191项既有文件和V1原始证据建立SHA保护，并创建小型 `v1_source_baseline.tar.gz`；原V1复跑输出另放`v2/v1_recheck`，没有覆盖原`v1/`。该源码tar不是完整证据备份，也不能替代上述外部归档。

## 4. 确认后的建议操作顺序

1. 用户确认精确纳管清单和忽略提案；若文件有更新，先重生成大小/SHA清单和回归证据。
2. 完成证据独立归档与校验，明确恢复位置。
3. 经授权后按清单逐文件暂存，检查 staged diff，无缓存/波形/机密夹带。
4. 再经授权形成明确基线commit，例如`Record validated M11 and M20 V0/V1 baselines`；V2可另成独立commit以便审查。当前工作区快照没有历史开发提交，不能将两次提交伪装为旧时间的开发过程。
5. push、分支/远端配置另行授权。本轮不会执行这些操作。
