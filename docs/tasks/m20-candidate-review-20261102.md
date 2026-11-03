# M20-CANDIDATE-REVIEW-20261102

状态：COMPLETED。2026-11-02，Asia/Shanghai。只分析/隔离验证，不采用或覆盖603基线；原ZIP不完全等价，不能标正式阶段通过。

## 结果与决定

- 原包545=479组合+66存储，状态33，reset选择33已含组合。译码132、AR51明显少于V2的169/79，最大拓扑30 vs50。
- 原样RTL的FFFF由EXEC进入HALT6，期望TRAP7；最小XSIM、原指令/内存回归分别复现。Python包只测trap_event，未测下一状态，漏检。
- 隔离删除状态低位的多余`!trap`条件，477+66=543、深度29；原49指令+38游戏/57331事件及7内存/reset全部PASS，V1/候选/Python、事务与最终RAM一致。没有增加状态或改变2/5周期。
- 543包含1个trap_event观察MUX，严格功能根为542；报告主数字保留完整候选端口计数。此非正式替换，源/ISA/原期望不改。
- 另一个显式OR trap修补为546/31层，仅结构审计，没有完整回归，不能称已验证替代版。
- 完整可读报告：[对比评审](../m20/M20_300_CANDIDATE_COMPARISON_20261102.md)。具体原ZIP及两版RTL SHA在报告与review_receipt.json。

## 已完成

- [x] AGENTS/进度/Git核对；main无commit，原四份staged不变。
- [x] 安全解压；23原包文件逐字节保留；SV/JSON逐pin、33FF-D/reset、无隐藏运算/未知叶/组合环审计。
- [x] 原Python65K合法性/27648数据向量/两游戏最大场景与boot实际PASS。
- [x] 原包Pong2500退役XSIM smoke PASS；原样RTL非法最小XSIM FAIL并保留证据。
- [x] 原包指令回归首14场景PASS后非法场景FAIL，游戏38/35108三方PASS；内存回归TRAP处FAIL。
- [x] 543临时修正三方全部87/57331事件、7memory/reset PASS，含连续64tick及同步/延迟RAM。
- [x] 同口径分组、拓扑和负载比较；source/index/原包保全检查；报告完成。

## 测试表

证据根：`build/m20_300/candidate_review_20261102/`。

|项目|方法|状态|证据|
|---|---|---|---|
|原包逐pin与结构|python -B audit_variants.py|PASS|variant_audits.json|
|原包Python|audit.py/test_isa.py/verify.py/verify_boot.py|PASS|package_python.log|
|原包HDL smoke|bash sim/run_xsim.sh pong|PASS|smoke_pong.console.log|
|原样RTL非法转态|tb_original_illegal|FAIL，6而非7|minimal/original.log|
|原包49指令|原V1锁步TB|FAIL，第15场景|full_regression/xsim/instructions.log|
|原包38游戏|原TB+v2_verify compare|PASS，35108事件|full_regression/games/three_way_comparison.json|
|原包memory/reset|原7组TB|FAIL，TRAP状态|full_regression/xsim/memory.log|
|543修正实验|原49/38/7 TB与Python|PASS，57331事件|corrected_remove_guard/full_regression.console.log及各suite JSON|
|原件保护|SHA/23原包逐字节/.git/index|PASS|review_receipt.json|
|综合/STA/实物|未执行|NOT_RUN|无|

## 已知边界与恢复入口

当前分析完成，无待验证的正式功能修改。修正RTL、适配器和复跑脚本均在build，仅作为分析证据。首次适配器声明位置编译失败已修正，失败日志adapter_attempt1_compile.log保留，不混作候选源码缺陷。生成器输出SV/连接JSON重生成字节一致，report JSON因set迭代键顺序不同仅解析值一致。

如用户要求正式采用，应另建优化版本、保留603/V1，带上非法转态修复与全非法终态专项测试，接入正式独立审计/回归。不得擅自把543拷到rtl或把候选标为形式等价/硬件通过。

先打开完整对比报告、variant_audits.json、corrected_remove_guard/change.diff及原样失败日志。复核可运行python -B build/m20_300/candidate_review_20261102/audit_variants.py；复跑脚本位于对应实验目录，须设置新输出路径保护已有失败/通过证据。Git旧201清单已因新增文档变为历史快照，若用户授权提交需重新生成，未授权不add/commit/push/切分支。
