# SwCell 当前任务进度

最近更新：2026-11-02（Asia/Shanghai）。根Agent维护；工程证据优先于历史检查点。

## 当前任务

|项目|内容|
|---|---|
|Task ID|M20-V21-PHYSICAL-20261102|
|目标|543结构正式化/全异常与功能重验；真实157路径、DFF、时钟复位、电源、FPGA接口和PCB初步规格|
|状态|COMPLETED：V2.1自动结构级验收通过；V2.2分析/规格完成，实物与PCB放行TBD，待用户确认阶段验收|
|范围|ISA/33状态/2-5profile不变；用户接受500+，不再以300为硬限制；原V1/603/历史证据保留|
|Git|main无首个commit；原四份staged未变，未add/commit/push/切分支；新纳管提案待确认|
|结果|477组合+66存储折算=543完整接口；纯功能476+66=542；1个trap_event观察MUX|
|详情|[任务/恢复入口](docs/tasks/m20-v21-physical-20261102.md)|

## 已完成及证据

- [x] 正式源码rtl/m20/v21及v21_build/audit/verify；两份SV/JSON隔离重生成逐字节相同；独立pin/FF/图/功能与debug锥审计。
- [x] 本轮regression_r3：65536合法性、50521非法实际TRAP/保持/逐一复位执行NOP、27840数学向量/3 XZ观察、7memory/reset；49指令+38游戏/57331事件V1/正式结构/Python三方、完整RAM、64tick及FSM断言全部PASS。
- [x] 全Python110项/10.163s PASS；3种防写历史路径负测；最初宏泄漏/负向测试自身错误已修正，失败证据保留，不能改记PASS。
- [x] 原厂三候选条件参数库、静态图/Top50/最短路径/负载/功耗/频率CSV。29层ROM→state，内部FF→FF16层；79对来自实际RTL轨迹的短路径同边沿活动见证，最短4层。
- [x] 简化DFF模型：4bit/16捕获非重叠示例PASS，预期主从重叠穿透被捕获；非SPICE/非实物。FPGA同步存储适配联合5指令、16执行+1reset周期、单写、reset取消、窗口外WE毛刺不写PASS。
- [x] 十二份要求文档、辅助BOM/DFF33绑定/59基本IO表及Git提案；V1/603/ISA/游戏/索引144初始项及1191旧清单均保持SHA。

入口：[V2.1结果](docs/m20/M20_300_V2_1_TEST_REPORT.md)、[物理规格总览](docs/m20/M20_PHYSICAL_FEASIBILITY.md)、[Git计划](docs/m20/M20_V21_GIT_PLAN.md)。

权威本轮证据：build/m20_300/v21/regression_r3/verification.json；session_20261102/python_tests_final.log、reproduction.json、final_receipt.json；physical_models_r2。审计/物理CSV在docs/m20/{v21_resources,physical_resources}/。

## 下一次恢复入口与边界

1. 本轮无落盘未验证的正式功能修改。先读上述两份结果及详细任务，检查final_receipt与Git状态；不要按旧检查点覆盖原V1/V2、候选失败证据或重做完成实现。
2. 重验必须新目录：`M20V21_OUTPUT_DIR=build/m20_300/v21/new_run sim/scripts/run_m20_v21.sh`；物理示例用`M20_PHYSICAL_MODEL_OUTPUT=build/m20_300/v21/new_models sim/scripts/run_m20_physical_models.sh`。
3. 实物频率/hold/死区/PCB寄生/供电及FPGA引脚均TBD。优先P1单/4bit DFF与P3时钟负载，100kHz开始；降低频率不能消除竞态。不创建PCB/XDC/bitstream，不自动上板，不再盲目追300。
4. 后续是否正式进入小样、选择厂商/缓冲器、冻结物理相位及接口服务，需用户另定范围。本轮规格指导评审，不能冒充PCB制造放行。
5. 正式阶段报告按AGENTS待用户确认后写docs/reports；现只有技术测试报告。Git清单为待确认提案，任何文件变化后须重算；不自动add/commit/push。

## 历史任务索引

|任务|状态|详情|
|---|---|---|
|M20-V21-PHYSICAL-20261102|COMPLETED，实物待测|[本轮](docs/tasks/m20-v21-physical-20261102.md)|
|M20-CANDIDATE-REVIEW-20261102|COMPLETED，原545有缺陷/543隔离修正|[评审](docs/tasks/m20-candidate-review-20261102.md)|
|M20-300-V2-20261029|COMPLETED，603历史参考|[V2](docs/tasks/m20-300-v2-20261029.md)|
|M20-300-V1-20261028|COMPLETED，冻结功能参考|[V1](docs/tasks/m20-300-v1-20261028.md)|
|M20-300-SOFTWARE-20261028|COMPLETED|[V0](docs/tasks/m20-300-software-20261028.md)|
|SWC-ENV-PY312-20261028|COMPLETED|[环境](docs/tasks/env-prep-20261028.md)|
|M11-PHASE2B-20261016|COMPLETED|[M11](docs/tasks/m11-phase2b-20261016.md)|
