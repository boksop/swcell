# SwCell多模块目录迁移验证

2026-11-04，目录迁移与验证完成。起点为main /48564b5；本轮修改留工作区供审阅，没有stage/commit/tag/分支/远程操作，没有上板或Flash写入。

## 实际变更

- 原混合fpga/xc7k325t下18个文件与9个M11文档实际移动到新位置；原根README中的M11操作指南另归入docs/m11/README。
- 板卡公共资源位于fpga/boards/swcell_k325t，模块工程位于fpga/projects；M11基础、高速和两种UART诊断分别登记。M20/cpu_validation只有明确PLANNED入口及TODO，没有假顶层/引脚/bitstream。
- 公共board profile统一part/50MHz/Flash物理参数。基础工程保留可配置应用参数；其余旧镜像明确保留50MHz参考限制，不能改board参数后静默使用原MMCM/RTL频率假设。
- 公共XDC与M11私有XDC组合保持原13个引脚及IO标准/配置电压。回环诊断保留旧七路安全接口，因此显式加载M11私有约束；pin-ID使用自身方向约束。
- 当前构建/仿真/采集、文档命令与链接更新。新输出隔离到build/fpga与build/sim；旧build/results、原始清单/SHA及Tag不移动或改写。

入口：[目录规范](repository_layout.md)｜[逐文件迁移](repository_migration_20261104.csv)｜[机器摘要](repository_layout_resources/validation.json)｜[检查证据SHA](repository_layout_resources/evidence_sha256.csv)。

## 测试结果

|检查|实际命令/方法|结果与证据|
|---|---|---|
|工程登记|`python3 tools/fpga/project_catalog.py check`|PASS：4个已实现＋1个规划；不等于综合/实机通过|
|完整Python|`build/venvs/python312/bin/python -B tools/test/run_python_tests.py`|PASS：156项，12.613s；原151项＋5目录/引脚/配置/指纹检查|
|M11完整XSIM|`SWCELL_PYTHON=... bash sim/scripts/run_all_regressions.sh`，Vivado bin在PATH|PASS：基础4故障模式＋两时序变体、UART/POR/引脚辨认；25高速用例含百万PRBS；控制专项与10频率grid；Phase2B三频率/96独立相位点|
|M20恢复门禁|`M20_FFCD_STAGE=dev`运行`run_m20_ffcd.sh`，新输出目录|PASS：B/C各7内存＋7控制＋2最小程序/9事件；原563资源审计保持；未重复完整87场景|
|Vivado实际工程创建|从/tmp以绝对路径source新的functional/scripts/build.tcl，`--stage create`|PASS：2026.1.1，项目实际加载clock/cdc/base_io/m11_io；不是综合/实现|
|其他Tcl源加载|从/tmp加载performance/loopback/pin-ID新入口，在synth_design前显式停止|PASS：三套Verilog/板卡源加载；不执行综合，不当作布局布线通过|
|Flash纯参数检查|`tclsh sim/scripts/test_flash_config.tcl`|PASS：原SDR/速率预算与错误拒绝；未操作硬件|
|高速未知频率协议|tclsh调用原7参数接口，给未支持频率|按预期UNSUPPORTED/FREQUENCY_PLAN，证明新根定位及错误状态流程保留|
|目录/源/引用|`python3 tools/fpga/check_layout.py`|PASS：44显式迁移条目、175逻辑源字节一致、138历史文件未改、26条Tcl字面引用有效、旧Tag对象保持|
|旧版本来源审计|原192来源manifest及V2.4的513条来源，以旧Git blob＋当前目标分别核验|PASS；历史期望SHA没有刷新，错误SHA仍被拒绝|
|文档链接|迁移前Git内容与当前文档逐项比较|没有本轮引入的缺失；7条旧M11原始记录链接缺失另列|
|综合/布局布线/STA/bitstream/硬件|本轮未执行|NOT_RUN，不以仿真/创建工程代替|

完整原始检查日志：`build/repository_layout_20261104/`。M11新仿真记录：`build/sim/m11/`和`build/sim/diagnostics/`；M20本轮门禁：`build/m20_300/v24_ffcd/layout_migration_gate_20261104/`。原始输出留build、只将少量摘要与索引作为文档。

## 与历史证据的关系

迁移前固定commit：48564b53cd9121b827af4f4692cd798303d3512e。M20所有旧Tag对象/目标保持，CPU/ISA/机器码、477组合＋66存储和20前馈结构未改。完整V2.4原full_r1模拟源指纹及8089原始文件另复核；原24问题配置、131局部错误没有修改。

当前工具遇到显式迁移时先验证旧Git内容与原SHA，再验证迁移后文件及新SHA，并把两者分别报告。没有“缺失就跳过”的逻辑，也不通过改旧manifest让审计通过。仓库迁移表是本轮技术内容检查点；任务进度文件不锁定在其中。

## 已存在的资料缺口

M11第一阶段报告引用的164852/164735两轮共7个原始文件，在本轮开始前就没有保存在这些路径，旧历史证据总索引也没有相应条目。本轮没有删除它们、没有换成其他轮结果，也没有连接旧主机恢复。具体7条在机器摘要中保留，独立于本次路径迁移结果。

当前results/M11保存了后续阶段数据，仍在原位置；不能把它们当成缺失的早期记录。若需要完整追溯第一阶段，后续可单独核对备份/旧主机。

## 下一步

目录已可支持后续模块独立接入。[M20原型准备](../fpga/projects/m20/cpu_validation/README.md)保留了功能边界、顶层/存储/调试集成、引脚与综合/STA/实物验收TODO。本轮不自动进入该开发阶段；新增工程按模板登记，不能将PLANNED改成实现通过而没有代码和证据。
