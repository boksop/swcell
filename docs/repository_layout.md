# SwCell目录规范与2026-11-04迁移

本轮将原`fpga/xc7k325t`中的M11顶层/配置/脚本/诊断拆成公共板卡和独立工程，根README改为SwCell导航。没有实现M20板级功能，没有修改逻辑、引脚数值、ISA/网表或已有Tag，没有自动提交。

## 1. 责任分层

|目录|职责|新增模块如何接入|
|---|---|---|
|fpga/boards/board_id|精确part、参考时钟/电源、公共IO、Flash物理参数|仅按原理图填写，版本未知不编造|
|fpga/projects/module/test|板级顶层、构建Tcl、私有约束、项目参数、README/project.json|同一模块可有多套测试/实现|
|fpga/projects/diagnostics|跨模块的板卡诊断|明确每个镜像引脚方向和接线要求|
|fpga/common/tcl|共享路径/JTAG/Flash辅助|显式运行才访问硬件，不混模块算法|
|rtl/common /rtl/modules/module|共享/模块逻辑|避免把UART/算法/板级顶层堆到一个文件|
|sim/module /sim/scripts|独立DUT模型、TB和回归入口|每套测试明确源清单，不递归编译所有CPU版本|
|host/python|采集、离线分析、黄金模型/测试|模块分包，共享协议/工具明确复用|
|software/module|汇编、ROM与参考软件|小型冻结ROM纳管，依赖与生成命令明确|
|docs/module|架构、方法、验证结果|正式确认后的报告仍放docs/reports|
|config/module|逻辑、分析或非板级参数|应用步数/模式不要塞进公共板卡配置|
|build/fpga /build/sim|新可再生模块输出|分别以module/test或module/suite隔离|
|results/module/time|实际采集数据|保留原始JSONL/CSV/配置与SHA并独立备份|

不批量制造M0～M20的空目录。需要接入时使用[工程模板](../fpga/projects/_template/README.md)和[板卡规范](../fpga/boards/_template/README.md)。`rtl/m20`、`sim/m20*`、`host/python/m20`、`software/m20_300`是已冻结的参考位置，保留以减少无关代码/证据指纹变化；未来FPGA封装都在独立project中。

## 2. 当前工程

`python3 tools/fpga/project_catalog.py list/check/show`是只读检查，不运行Vivado或硬件。

|ID|状态|入口|
|---|---|---|
|m11/functional|IMPLEMENTED|fpga/projects/m11/functional/scripts/build.tcl|
|m11/performance|IMPLEMENTED|fpga/projects/m11/performance/scripts/build_hs.tcl|
|diagnostics/uart_loopback|IMPLEMENTED|fpga/projects/diagnostics/uart_loopback/scripts/build.tcl|
|diagnostics/uart_pin_id|IMPLEMENTED|fpga/projects/diagnostics/uart_pin_id/scripts/build.tcl|
|m20/cpu_validation|PLANNED|只含README/project.json和明确TODO；无构建/引脚/bitstream|

IMPLEMENTED表示原工程代码已存在；目录迁移的检查/回归结果另记录，不自动等价为当前Vivado综合/实现通过。双输出pin-ID仍要求V20断开USB-UART TX，不能当普通回环直接运行。

公共XDC只定义D27/LED/UART及配置电压，M11的7条D/EN/CLK/Q/QM在m11/common/constraints。两者组合等价于旧引脚表，SYS时钟约束由各工程创建一次。对尚未提供的M20引脚不写约束。

## 3. 文档和历史路径

M11原根目录文档移动至docs/m11，旧根README中的M11操作说明归入docs/m11/README。`docs/architecture.md`现在说明整个SwCell架构。当前脚本、Python构建/JTAG引用和Markdown链接/命令随迁移更新。

**原始证据不改写：**docs/history、docs/evidence及各resources中的CSV/JSON/SHA、历史版本文件清单和build/results保留原字节；其中旧路径是当时记录，不是当前入口。不能通过批量替换修改原始SHA或测试结果。正式报告中的路径链接维护不改变原测试统计，原文本版本可由对应Tag读取。

- [逐文件路径与指纹迁移表](repository_migration_20261104.csv)同时列旧/新路径、旧/新SHA，明确纯移动、路径更新、公共约束拆分。
- 机器索引 `config/repository_migration_20261104.json`以固定基线commit48564b5验证旧Git blob，再验证当前实际文件；不是忽略缺失文件或把旧SHA改成新值。
- 当前只读release审计遇到显式迁移时分别报告历史SHA和当前目标SHA；未列入映射的缺失/修改仍失败。不要对旧manifest盲目“刷新全部SHA”。

旧build/vivado、build/phase2、M20各回归与results没有搬动。新的M11构建/仿真使用新输出目录；不能用新输出路径声称原历史数据已存在于那里。迁移检查证据在`build/repository_layout_20261104/`，最终摘要见[迁移验证](repository_layout_validation.md)。

## 4. 新增工程步骤

1. 在project目录创建清单和README，选择已有board或填写真实新板卡；只引用真实存在资源。
2. 添加模块顶层/约束/构建脚本；用repo_paths.tcl定位仓库，不依赖当前CWD或散落的固定层数。
3. 明确RTL/仿真/采集文件清单和独立输出位置，先跑catalog检查和对应单元/仿真。
4. 分别完成综合/实现/STA后再允许硬件测试，未知引脚/时序保留TODO。
5. 按AGENTS更新进度、证据及用户确认后的中文阶段报告；提交/Tag需另获授权。


## 5. 检查入口

`python3 tools/fpga/check_doc_links.py`检查当前/迁移文档的本地文件链接，单列原先就缺失的链接，不联网检查URL或锚点。

`python3 tools/fpga/check_layout.py`独立验证迁移前Git内容、当前目标SHA、保留的历史证据与标签、逻辑字节及Tcl引用；它是本次迁移检查点，不是综合/STA。原始manifest保持不变，后续合法修改应产生新的审阅记录，不为了旧PASS静默刷新旧期望。任务进度文件不列入迁移内容指纹，便于日常更新。

文档链接检查发现M11第一阶段正式报告中的7处原始采集路径在本次开始前就不存在（对应164852/164735两轮）；当前results/M11内有后续阶段数据，没有据此伪造早期记录或改成别轮数据。该缺口独立记录于验证页，不归因于本次搬迁，也不自动执行恢复。
