# SwCell：数字逻辑设计、验证与 FPGA 测试

SwCell 覆盖 M0～M20 等模块的逻辑设计、仿真和实体测试。仓库按“可复用逻辑 / 模块验证 / 公共板卡”分层；FPGA 芯片型号不再作为所有测试工程的混合目录。

当前板卡为用户确认的 **XC7K325T-2FFG900C，50MHz，3.3V 单端 IO**；具体 PCB 修订未记录。M11 已有上板验证工程，M20 已完成 CPU 数字联合验收，V3功能存储FPGA原型已上板，严格反馈存储未放行。

## 项目与正式版本

基础逻辑单元为NC7SZ157P6X单路2:1 MUX，`Y=S?I1:I0`。M20是一颗4位数据、12位PC、8位AR的简易游戏CPU，16位ISA v0.1已冻结；RAM/ROM由FPGA提供，不用157搭建容量阵列。

|模块 / 阶段|已完成|边界|
|---|---|---|
|M0～M10、M12～M19|保留模块编号及未来接入空间|当前仓库未找到独立实现或实际原理图，不宣称已完成|
|M11|D-Latch/主从DFF功能、高速采集与独立Q/QM相位扫描；P1/P2/P2B历史报告/工具保留|历史实测不代表M20的允许主频；部分原始数据依赖独立归档|
|M20 V1 / V2 / V2.1|冻结ISA、Python/RTL差分、原603与修正543结构并存|原545候选有非法HALT缺陷，保留分析而不标为正式通过|
|M20 V2.3|模式A非重叠两相＋CPU＋FPGA存储数字联合|Tag m20-v2.3-two-phase-sim-verified；不是外部发生器实物签核|
|M20 V2.4|固定16级、TAP4/8/12/16静态选择的20-MUX前馈发生器，声明时序假设下完整数字验证|Tag m20-v2.4-digital-verified；保留重叠/穿透负例及实体最小延迟开放项|
|M20 V3|XC7K325T运行Pong/Snake、真实按键/OLED、同步ROM/RAM、UART与单步；用户确认实机通过|FUNCTIONAL_STORAGE 477组合MUX＋33原生FF；STRICT_MUX 85 LUTLP-1，无bit/无实机放行|

真实157预算为 **477组合＋33位×2存储＝543**，加20颗发生器共563，不含Buffer。FPGA LUT位置数不能当作157数量。V3没有把前馈延迟链放入FPGA时钟路径，以50MHz单域CE调度完成原型；原生FF不能冒充真实双MUX DFF时序验证。

V3正式整体结论见[阶段报告](docs/reports/m20_phaseV3_20261104.md)，最终F06为Pong10/Snake5 tick/s、SPI10MHz：KEY5/A在BOOT页启动、游戏中切换，KEY7暂停/继续、KEY6/B重启，四方向为KEY2/0/3/1。OLED为CPU RAM的只读呈现，FPGA不替CPU计算游戏规则。精选[原样证据及SHA](docs/evidence/m20_v3/README.md)随源码保存，大波形/bit/DCP不纳入Git。

## 从这里开始

|任务|入口|状态|
|---|---|---|
|查看目录、增加模块或工程|[目录规范](docs/repository_layout.md)、[总体架构](docs/architecture.md)|公共规范|
|查看/检查 FPGA 工程|`python3 tools/fpga/project_catalog.py list` / `check`|只读，不连接硬件|
|M11 基础/高速测试|[模块指南](docs/m11/README.md)、[FPGA 工程](fpga/projects/m11/README.md)|已实现，历史实测记录保留|
|M20 CPU 设计与验证|[模块索引](docs/m20/README.md)、[FPGA 原型](fpga/projects/m20/cpu_validation/README.md)|477结构MUX＋33FF已上板，Pong/Snake操作已确认|
|M20 F06启动/按键交互|[阶段验收报告](docs/reports/m20_phaseV3-F06_20261104.md)|用户确认正常；KEY5启动/切游戏，KEY7暂停，KEY6重启|
|OLED、按键、LED独立诊断|[工程](fpga/projects/diagnostics/oled_keys/README.md)、[引脚验收报告](docs/reports/board_io_phase1_20261104.md)|基础引脚/方向已确认；白底闪烁按用户要求暂不处理|
|Snake固定乱序食物|[软件变体与验证](docs/m20/M20_V3_SNAKE_SHUFFLED.md)|315场景差分及实机66tick/12份全RAM对照通过，已下载；新分布试玩待确认|
|正式阶段结论|[报告索引](docs/reports/README.md)|区别仿真、条件时序和实物|
|当前任务与恢复|[TASK_PROGRESS](TASK_PROGRESS.md)|每次开始任务先读|
|Python 环境与本地 Git|[Python3.12](docs/environment_python312.md)、[Git流程](docs/GIT_LOCAL_WORKFLOW.md)|原虚拟环境/数据保留|

## 目录分工

```text
fpga/
  boards/                 # 板卡身份、共享IO/电压/时钟/Flash参数
    swcell_k325t/
  common/tcl/             # 仓库定位、JTAG和Flash辅助（显式调用才写硬件）
  projects/
    m11/functional/       # M11低速基础功能工程
    m11/performance/      # M11高速/多镜像扫描工程
    m11/common/           # M11独有的子卡引脚约束
    m20/cpu_validation/   # M20结构级CPU FPGA原型、只读游戏显示
    diagnostics/          # UART回环、双引脚识别等独立诊断
    _template/            # 后续模块工程的接入模板
rtl/                      # 公共与模块逻辑，不混入板级引脚
sim/                      # 仿真模型、Testbench和回归入口
host/python/              # UART采集、离线分析、M20工具与测试
software/                 # ISA软件、汇编、冻结游戏ROM
config/                   # 逻辑/分析参数及目录迁移信息
tools/                   # 工程检查、资源审计、测试与维护工具
docs/                    # 总体规范、M11/M20文档、正式报告及任务
build/                   # 可再生输出与本机环境，Git忽略
results/                 # 原始实测数据，Git忽略
```

`rtl/m20/`、`sim/m20*`、`software/m20_300/` 是既有冻结基线位置，保留以维持 ISA/网表及证据兼容；未来模块遵循目录规范，不为排列整齐重写既有核心。仅现存 M11/M20 有实际源码，不为尚未实现的 M0～M19 创建空工程。

## 常用命令

所有命令从仓库根目录执行，工具路径按本机安装设置。

```bash
# 新检出的Python环境；Vivado须由使用者单独安装并配置许可
python3.12 -m venv build/venvs/python312
build/venvs/python312/bin/python -m pip install -r host/python/requirements-py312-ubuntu24.lock.txt

# 检查工程登记和路径，不构建/下载
python3 tools/fpga/project_catalog.py check

# M11：创建工程；改为 --stage synth 或 bitstream 才执行相应阶段
vivado -mode batch -source fpga/projects/m11/functional/scripts/build.tcl

# Python完整套件（包含干净检出的受控空目录夹具）
build/venvs/python312/bin/python -B tools/test/run_python_tests.py

# M11仿真回归；需Vivado/XSIM在PATH
SWCELL_PYTHON="$PWD/build/venvs/python312/bin/python" bash sim/scripts/run_all_regressions.sh

# M20已定版的条件数字联合，不等于上板测试
bash sim/scripts/run_m20_v24_system.sh

# V3冻结核心/真实板级SPI与按键；XSIM实际bin可通过M20_VIVADO_BIN指定
bash sim/scripts/run_m20_v3_core.sh
M20V3_BOARD_SNAKE_FILE="$PWD/software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.memh" \
M20V3_BOARD_SNAKE_DONE=313 bash sim/scripts/run_m20_v3_board.sh

# 重建最终F06乱序版（新输出目录）；不自动下载，也不写Flash
vivado -mode batch -source "$PWD/fpga/projects/m20/cpu_validation/scripts/build.tcl" \
  -tclargs --mode FUNCTIONAL_STORAGE --output build/fpga/m20/cpu_validation/run_new \
  --snake-rom software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.memh --snake-done 313
```

V3实际验证使用Vivado/XSIM2026.1.1；M11保留2022.1原工具版本及参数配置，不承诺跨版本全部等效。当前V3为纯RTL和显式7-Series原语，无外部XCI/IP仓库，ROM初始化文件与生成器均纳管。主机Python依赖声明和经过验证的版本快照随仓库保留；工具安装、FPGA驱动、串口权限与板卡不随Git提供。

默认无`--snake-rom/--snake-done`时构建的是冻结原Snake版，不能把它当作最终乱序配置。所有输出必须使用未存在的新目录，历史采集/构建证据不覆盖。[V3工程指南](fpga/projects/m20/cpu_validation/README.md)列出JTAG命令与参数；未连接真实硬件时不要执行program脚本。

新构建输出按 `build/fpga/<模块>/<工程>/` 和 `build/sim/<模块>/<套件>/` 区分。已存在的 `build/vivado`、`build/phase2`、M20证据和 `results/` 不迁移、不覆盖；历史路径通过[迁移说明](docs/repository_layout.md)和清单定位。不要将被忽略的原始证据误认为不需要备份。

M20 正式标签 `m20-v2.4-digital-verified` 仅表示声明时序假设下数字联合通过，其实体时序与实物验收范围未改变。后续V3已独立实现477组合MUX＋33原生FF的FPGA功能原型；不把原生FF通过当作实体66颗存储MUX时序通过。M11引脚不能直接套给M20，V3使用已确认的OLED/按键板卡配置，见独立工程指南。

## 纳管、依赖与开放事项

全部现存正式源码、生成器/SV/连接JSON、ISA/游戏ROM、TB/Tcl/XDC、物理参数/资源清单和小型验证证据纳管；build、虚拟环境、Vivado数据库、大型波形、bitstream、旧ZIP、个人配置和凭据默认忽略。原始数据不因忽略而删除，备份与来源SHA见[工作流](docs/GIT_LOCAL_WORKFLOW.md)及[历史证据索引](docs/evidence/historical_20261103.csv)。

本项目尚未选择开源许可证，本次仅授权Private发布，不自动增加LICENSE。第三方工具、器件数据手册/完整IP不打包；已生成报告中的厂商抬头保留，原资料来源链接在相应技术文档。当前仓库无Git LFS/子模块依赖；实际PCB原理图/布局在本树未找到，资源预算及接口契约见docs/m20，未来应按目录规范接入真实文件。

实体157全芯片时序、时钟Buffer/PCB、电压温度与长期可靠性、Flash固化仍开放；OLED反显白底闪烁按用户要求延期。7个旧M11原始数据链接在当前磁盘缺失，报告入口保留，不伪造恢复。

GitHub首次发布的实际URL、提交、标签、完整性和恢复测试见[发布记录](docs/GITHUB_PUBLISH_REPORT.md)；只有成功验证的远程结果才记为完成。Private仓库的在线审查需要相应账号/连接器得到访问授权，链接本身不是访问凭据。
