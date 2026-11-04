# SwCell：数字逻辑设计、验证与 FPGA 测试

SwCell 覆盖 M0～M20 等模块的逻辑设计、仿真和实体测试。仓库按“可复用逻辑 / 模块验证 / 公共板卡”分层；FPGA 芯片型号不再作为所有测试工程的混合目录。

当前板卡为用户确认的 **XC7K325T-2FFG900C，50MHz，3.3V 单端 IO**；具体 PCB 修订未记录。M11 已有上板验证工程，M20 已完成 CPU 数字联合验收，下一步 FPGA 原型尚未实现。

## 从这里开始

|任务|入口|状态|
|---|---|---|
|查看目录、增加模块或工程|[目录规范](docs/repository_layout.md)、[总体架构](docs/architecture.md)|公共规范|
|查看/检查 FPGA 工程|`python3 tools/fpga/project_catalog.py list` / `check`|只读，不连接硬件|
|M11 基础/高速测试|[模块指南](docs/m11/README.md)、[FPGA 工程](fpga/projects/m11/README.md)|已实现，历史实测记录保留|
|M20 CPU 设计与验证|[模块索引](docs/m20/README.md)、[FPGA 原型准备](fpga/projects/m20/cpu_validation/README.md)|CPU数字通过；上板工程 PLANNED|
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
    m20/cpu_validation/   # M20 FPGA原型接入准备，尚无板级实现
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
```

新构建输出按 `build/fpga/<模块>/<工程>/` 和 `build/sim/<模块>/<套件>/` 区分。已存在的 `build/vivado`、`build/phase2`、M20证据和 `results/` 不迁移、不覆盖；历史路径通过[迁移说明](docs/repository_layout.md)和清单定位。不要将被忽略的原始证据误认为不需要备份。

M20 正式标签 `m20-v2.4-digital-verified` 仅表示声明时序假设下数字联合通过；实体时序、FPGA 实现及硬件验证仍 OPEN。M11 的引脚不能直接套给 M20；本轮未新增引脚、bitstream 或硬件下载。
