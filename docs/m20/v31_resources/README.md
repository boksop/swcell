# V3.1 当前证据与最终验收

- 最终固件0.2（4052字）和bit restart_plus_r2：acceptance_summary.json是当前阶段状态，user_acceptance_restart_plus_20261105.json为修复后原话，checks.json关联自动验证与硬件。
- summary.json和verification.json由离线仿真/STA工具生成，保留工具当时的DIGITAL_PASS_HARDWARE_PENDING/physical_hardware=NOT_RUN；不能把它们改成硬件实测。最终人工验收在上述独立文件中。
- source_manifest.json是版本化的当前32份来源指纹，声明相对初始r5的6个变更文件；baseline_sha256.json保护原V3。evidence_sha256.csv记录真实原始日志/bit/raw，清单不包含自身SHA。
- 原始数据在build/和results/M20_V31，须独立备份。小型报告、图表及人工确认保留在此处，不将截图模拟图冒充相机照片。
- ../v31_initial_r5_resources为未修复的初始版本指标/图/源清单与最小失败反例；初始user_acceptance_20261105.json只反映当时两项基本确认，后报缺陷及修复重验收单独保存。旧源/ROM在build/m20_v31/pre_fix_20261105，不据当前修复代码匹配旧指纹。
- 本阶段通过范围FUNCTIONAL_STORAGE；没有新增STRICT_MUX、实体157时序、ILA、Flash或长期可靠性验收。[正式报告](../../reports/m20_phaseV3.1_20261105.md)。
