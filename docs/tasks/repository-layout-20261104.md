# SWCELL-LAYOUT-20261104：多模块FPGA工程目录整理

2026-11-04，COMPLETED（目录整理与验证）。用户要求将原M11中心目录改为整个SwCell的设计/验证/测试目录，未来增加M20_CPU及其他模块，实际修改路径与文档。

## 决策与范围

- 公共板卡：fpga/boards/swcell_k325t（名称不声称未知硬件版本）；芯片/50MHz/公共IO/配置电压与Flash参数，M11七路IO从公共约束分开。
- 独立工程：fpga/projects/m11/functional、performance；板卡诊断放fpga/projects/diagnostics；M20/cpu_validation只建规划入口，不编造M20引脚/bitstream。
- 公共Vivado帮助与JTAG/Flash入口放fpga/common/tcl；不自动连接或写硬件。
- 维持rtl/common、rtl/modules/m11、冻结rtl/m20及sim/host/software的功能代码位置，避免与本次板级整理无关的核心重构；用项目清单/目录约定关联模块资源。
- M11技术文档集中docs/m11，根README和docs/architecture改为工程导航。当前文档链接/命令同步更新；历史JSON/CSV/SHA/任务快照与build/results保持字节，以版本标签及迁移索引解释历史路径。
- 原标签/索引记录不回写，必要的当前只读版本审计增加显式迁移验证，不能把缺失文件无条件跳过或改旧期望SHA。

## 检查点

- [x] main起点48564b5，原工作树干净，522文件和Git标签/索引SHA快照保存到build/repository_layout_20261104/baseline.json。
- [x] 移动27文件＋根README归档为M11指南；拆分约束保持13引脚，175逻辑源字节一致。
- [x] 构建/采集/仿真/文档入口已更新；旧数据及指纹保留，显式迁移验证通过。
- [x] 5工程登记（4实现/1规划）、板卡/工程模板、M20规划与模块导航已建立。
- [x] 最终156Python、M11全回归、M20门禁、Vivado创建/三Tcl源加载及迁移审计通过；结果落盘。

## 验证要求与禁止项

Python完整套件、M11基础/高速/phase2b/诊断仿真，M20独立563审计与现有核心门禁；Tcl引用及约束组合检查分开报告，不能当作实现/STA通过。没有源码功能变化不重跑全部13分钟CPU回归，若路径检查/生成失败须实际修复。

不删除缓存/结果/波形，不改CPU/ISA/ROM或失败分类，不自动commit/创建分支/远程Git，不执行实机/Flash。先从实际git diff和迁移清单恢复，不重复移动原文件。


## 已实际执行的检查（收尾中）

- 155首轮Python通过；新增回环13引脚覆盖测试后运行最终156套件。
- M11完整run_all_regressions.sh退出0：基础4fault/额外时序/50MHz/UART/POR/双引脚、高速百万PRBS、暂停/CDC及10频率grid、Phase2B三频率独立扫描均PASS。模拟源字节没有改动。
- M20 B/C门禁退出0：每模式7内存、7控制、2最小场景/9事件；原543/20审计保持。
- Vivado2026.1.1从/tmp成功创建新的M11基础工程，XPR实际加载base_io/m11_io/cdc/clock约束；不是综合/STA。
- 路径审计175逻辑源字节一致、138历史文件不变，22（后续26）条Tcl字面引用通过，旧Tag对象保持。旧192来源manifest的26条迁移和V24的44条显式迁移验证通过，没有刷新旧SHA。
- 链接检查37文档/159本地链接无新增缺失；7条原M11第一阶段raw链接在本轮前就不存在，已单独记录，不构造替代记录。
- 检查发现旧UART回环顶层含M11安全接口，已保持加载私有IO（总13）；私有约束不混回公共board。三套旧工程从公共board读取part/50MHz（保留原参考频率限制）。

证据均在build/repository_layout_20261104；最终源加载与156测试尚须核对，再写最终状态。无commit/stage/tag/远程/实机。


## 最终结果与恢复入口

最终156项Python通过（12.613s），三Tcl源加载都在综合前停止且成功，M11全回归和M20 B/C门禁已完成，未执行综合/实现/STA/bitstream/硬件。迁移前全部175逻辑源与138历史摘要字节保持，旧标签和Git索引blob保持，文档无本轮新增坏链接。

[最终验证](../repository_layout_validation.md)、[目录规范](../repository_layout.md)、[机器索引](../../config/repository_migration_20261104.json)。新模块入口fpga/projects，board公共资源fpga/boards，M20只有PLANNED。

下次先读根TASK与git diff/迁移表，不重复搬迁，不覆盖旧build/results。当前修改未提交/未暂存，旧路径的D和新目录的??表示搬迁工作树而非丢失；迁移表可逐项核实。若要复核执行project_catalog/check_layout和Python入口，使用新输出目录；未经用户新指令不commit、移标签、连接硬件或开始M20原型。7条旧M11第一阶段raw链接缺失是预先存在的资料缺口，未伪造/恢复。
