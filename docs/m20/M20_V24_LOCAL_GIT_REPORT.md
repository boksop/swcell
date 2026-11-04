# M20 V2.4：有条件数字验收本地 Git 定版

2026-11-04。用户批准指定数字假设下验收，授权本地commit/annotated tag。**不表示实体时序、FPGA实现或实物验证通过。** 无远程仓库/网络Git/上传，不改V23 tag。

## 版本和提交策略

main起点5e601a9，V23 annotated tag对象/目标已存原位快照。原90个stage全部属于V24历史候选及A/B开发，逐路径/大小/blob/SHA审查后，先形成独立历史提交 `86fdc9e036fb7beee16c896ee00e5502b5391708`；全部90个blob与原索引一致。工作树比stage更新的文件随后进入完整当前版本，不reset/覆盖任何原修改，也不冒充原始开发时点。

目标标签：`m20-v2.4-digital-verified`，annotated，仅本地。要求标签正文逐字含：

> 20-MUX feedforward two-phase clock generator and 543-MUX CPU full-system digital verification passed under declared timing assumptions. Physical timing, FPGA implementation and hardware validation remain open.

当前完整版本和恢复结果的实际commit、tag对象/目标，以最终Git解析和本报告的“恢复记录”补充为准；不在文件内写自身commitSHA形成循环。V23对象与目标必须与preflight完全一致。

## 最后纳管审核

[逐文件清单](M20_V24_GIT_FILES.csv)记录当前整棵源码树的纳管类别与技术指纹；[技术源manifest](M20_V24_SOURCE_MANIFEST.json)不包含自身SHA，也不把会更新的定版进度/控制清单纳入递归哈希。原 `ffcd_resources/delivery_sources.json/final_checks.json` 等是提交前原始开发检查点，保留其中原HEAD和旧索引验证口径，不回写历史以匹配新SHA。

|纳管类别|内容|
|---|---|
|CPU/发生器|原543 CPU/ISA/ROM、固定16级四tap20-MUX、正式生成SV及连接/绑定JSON|
|工具|生成器、独立477/33/66/20审计、Python黄金模型、参数与五种Buffer资料边界|
|测试/复现|Testbench、断言、全系统入口、56负测、79向量/632局部实验、151 Python|
|证据与报告|关键结果CSV/JSON、有限图、SHA索引、参数来源、正式阶段报告与恢复记录|
|历史资料|原17/116候选、缺陷/失败/未验收说明，原V23与M11等既有模块完整保留|

`.gitignore`现有规则足够：忽略build、虚拟环境、XSIM/Vivado缓存、大型WDB/VCD/FST/FSDB、DCP/bit/ltx、日志、机密与重复ZIP；无须为定版放开这些规则。原有2KB V23负向VCD例外保持，不新增大型波形。1.6MB TAP16包络SVG是技术报告图，不是原始波形；约0.95MB系统SHA CSV是必要证据索引，均按用途审核纳管。

本轮所有新增/修改非忽略文件须在清单中说明；不使用git add全仓、不force纳管build、不删除忽略数据。精确paths逐个暂存并审查cached内容，禁止遗留新RTL/脚本在Git之外。

## 原始数据保存与备份

原系统数据 `build/m20_300/v24_ffcd/full_r1/`，8089文件、211505057字节；tar25187797字节，SHA256 `c1ceb0f32f305aa1ee567620f4d014799c8e27638c4d4bc70618bed2aa21c0f3`。负测两个独立目录 `build/m20_300/v24_ff16/full_r1_ffcd_negative_small/`、`full_r1_ffcd_negative_cones/` 和原small/deep_review历史目录仍在原位；Git中的索引不能替代它们。

建议在独立离线介质备份系统tar、两套负测原始目录、M11 results及其哈希清单，并读回校验；本轮不复制到外部介质、不删除、不上传。旧失败不改判，仍24问题配置、131局部错误。

## 恢复依赖修正

审核发现原 `run_m20_ff16_review.sh`调用历史build原始审计及绝对历史trace目录；这属于“重新核查旧实验”的入口，原样保留。

从 `deep_review_r4/cpu_witness_vectors.json`逐字保留157071字节原79向量到 `docs/m20/ff16_review_resources/`，来源及SHA在相邻origin.json。新增独立 `run_m20_ff16_cones_replay.sh`使用相同网表/时序模型/既有结果判据，逐项比较错误path ID；一键system改调用该入口，干净源码不再为此读取旧build。未修改CPU/ISA/时序模型或历史预期。新632实验实际通过，结果与旧JSON完全一致。

## 本地检查及恢复记录

原位检查：206份V23保护文件、C/D源及8089原始数据SHA一致；151Python再次通过（12.858s）。差异检查使用 `git -c core.whitespace=cr-at-eol diff --check`，保留原CSV的CRLF字节，不为默认空白提示改变历史证据。

完整版本提交后，在新detached worktree执行不依赖旧build的恢复检查：生成器临时重建字节比较，独立563预算，全部Python，56场景与632重放，B/C存储控制/最小CPU门禁。完整六配置87/57331与非法专项沿用源码指纹一致的full_r1实绩，不为纯定版重复13分钟模拟。此处将追加实际恢复结果、提交和证据；追加前不声称干净检出已经通过。

## 验收边界

VERIFIED：结构/功能与故障检出；CONDITIONAL：指定TAP16延迟/偏斜下的系统；FAILED：原问题配置和穿透反例；NOT_VERIFIED：实体时序、综合/实现/STA、硬件。正式中文阶段报告见[验收报告](../reports/m20_phaseV2.4_20261104.md)。

### 首轮干净恢复的实际失败及处理

`4a95665`干净树首次151测试有2个失败：旧FF16/V23“拒绝覆盖旧输出”的测试假定历史目录存在；新树没有对应目录。`clean_python_initial_FAILED.log`保留，不改成PASS。56/632负测及B/C门禁独立结果不受影响。

冻结V23测试/逻辑不修改。新增 `tools/test/run_python_tests.py`在两个目录缺少时创建空夹具，跑同一151测试，最后只对自己创建且仍为空的目录rmdir；已有历史目录不触碰，不补造原日志。一键system调用此入口。原直接unittest命令在完全干净树仍有上述夹具前提，使用公开入口可自足复现；这属于测试环境修复，非放宽断言。

生成的SVG带Matplotlib路径格式行尾空格；保留原始字节，未为默认空白提示改写证据。CRLF-aware的源码检查排除原SVG，技术清单逐字节指纹验证仍完整执行。

### 最终干净恢复：PASS

- `4a95665966edff747f04963f5b1869ca46ee83ba`：完整源码、正式验收报告与自足79向量重放入口提交。
- `80593a1cca39dd1df632b1934878ce4fd63d2ecd`：明确的空目录夹具测试入口修复，不改冻结V23/CPU/断言。
- 新detached worktree `build/m20_300/v24_release_20261104/clean_final`开始时没有build历史；最终151测试全部通过（13.309s），确实创建2个空夹具且结束后清理。
- 实际XSIM：56组仍32 CONDITIONAL/24 FAILED；632局部实验仍131错误、316正向无错，所有错误path ID与原JSON相同；B/C各7内存＋7控制（26显式单步）＋2最小场景9事件通过。
- 生成器从跟踪文件重建7个CPU绑定/manifest/平台文件，字节一致；独立563预算、206份V23保护文件、全部513技术指纹与full_r1模拟源指纹一致。原8089原始文件和系统tar重新校验。

[机器结果](v24_release_resources/recovery_validation.json)保留首轮2失败及最终通过，[恢复原始SHA索引](v24_release_resources/recovery_evidence_sha256.csv)管理本轮新增日志/CSV/VCD；原始内容仍在build，未纳入Git。最后一份文档提交仅记录这些实际结果/清单/进度，验收tag指完整最终树，代码与80593a1一致。

最终状态应由以下本地只读命令核对：

```bash
git status --short
git rev-parse m20-v2.4-digital-verified^{}
git cat-file -t m20-v2.4-digital-verified
git for-each-ref --format='%(contents)' refs/tags/m20-v2.4-digital-verified
git remote -v
```

已有V23 tag对象/目标均保持；原90 staged blob已经单独历史提交，并非丢弃或混入未审内容。所有当前非忽略文件均纳管；生成缓存/大型波形仍排除且原位保留。没有远程操作，没有进入下一硬件阶段。
