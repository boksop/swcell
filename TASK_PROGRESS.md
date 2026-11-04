# SwCell 当前任务进度

2026-11-04，Asia/Shanghai；main，HEAD保持48564b5，既有Tag保持。

## 当前任务

**SWCELL-LAYOUT-20261104：COMPLETED（多模块目录整理与验证）。** 原M11混合FPGA目录已拆为公共board、公共Tcl和模块独立project；M20_CPU仅预留PLANNED入口。本轮未自动stage/commit/tag/创建分支或操作硬件。

[目录规范](docs/repository_layout.md)｜[验证总结](docs/repository_layout_validation.md)｜[详细任务](docs/tasks/repository-layout-20261104.md)｜[路径迁移表](docs/repository_migration_20261104.csv)。

## 已完成、已验证

- [x] 27文件搬迁＋原根README的M11指南归档；fpga/boards与fpga/projects分层，公共与M11私有约束保持原13引脚，旧RTL逻辑不变。
- [x] M11基础/高速、两种UART诊断独立project；M20/cpu_validation明确PLANNED/TODO；新增模块/板卡模板、只读catalog和检查工具。
- [x] 当前构建/采集/仿真/文档路径更新；M11文档集中docs/m11，根README和docs/architecture服务整个SwCell。
- [x] 156 Python、M11全XSIM（25高速含百万PRBS、控制/10频率grid、Phase2B三频率）、M20 B/C门禁通过。
- [x] Vivado2026.1.1从/tmp实际创建基础工程；三套其余Tcl完成源加载并在综合前停止。未执行综合/实现/STA/bitstream/硬件。
- [x] 175逻辑源字节、138历史摘要/数据及原Tag保持；旧192/513来源清单用显式迁移核验，不刷新旧SHA或跳过缺失。

## 证据与边界

当前机器摘要：`docs/repository_layout_resources/validation.json`。原始检查在 `build/repository_layout_20261104/`，新M11模拟在 `build/sim/m11/`，M20本轮门禁在 `build/m20_300/v24_ffcd/layout_migration_gate_20261104/`。旧build/results没有搬迁或覆盖。

目录/仿真通过不等于板级实现或真实157时序通过；M20 V2.4条件数字验收和物理/FPGA实现/硬件OPEN保持。文档核对另发现7条M11早期raw链接原先就缺失，详见验证总结，未替换成其他轮数据。

## 下一次恢复入口

1. 先读验证总结、迁移表和git diff，不重复搬迁。当前均留工作区未提交/未暂存，旧路径D与新目录??是迁移结果；所有原文件有映射或未改记录。
2. 只读检查：`python3 tools/fpga/project_catalog.py list` / `check`；`python3 tools/fpga/check_layout.py`。Python完整套件用 `build/venvs/python312/bin/python -B tools/test/run_python_tests.py`。
3. 下一个工程入口是 `fpga/projects/m20/cpu_validation/README.md`，当前只规划；等待用户新任务再实现板级顶层/存储/调试/约束，不直接用M11引脚或原CPU仿真报告当上板验收。
4. 旧版本查原Tag，历史manifest/SHA保留字节；当前迁移由config/repository_migration_20261104.json记录。不得移动V23/V24标签、改ISA/网表或失败分类、重写raw、自动commit/硬件操作。

历史：[V2.4本地定版](docs/tasks/m20-v24-release-20261104.md)、[C/D数字开发](docs/tasks/m20-v24-ffcd-20261104.md)。
