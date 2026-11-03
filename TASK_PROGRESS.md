# SwCell 当前任务进度

更新2026-11-03（Asia/Shanghai）。

## 当前任务

- **M20-V23-TWO-PHASE-20261103：COMPLETED**（RTL与数字联合仿真；等待用户阶段确认，不代表实物签核）。
- main，原HEAD `c2edd9ba5baff58c86ef471b4435275e3f1bc876`；本轮不创建commit/移动tag/远程操作。
- 保留V2.1原477组合MUX/33状态D函数/ISA和2/5profile；新增66反馈MUX状态、四阶段调度、同步FPGA ROM/RAM、完整联合/压力回归与接口时序契约。
- 最终证据 `build/m20_300/v23/regression_r6/verification.json` PASS；SHA256 `38b3de525918fcbd0689150f349e5e71f6bc01d0997b8956696d83cc7630adaa`。
- 零/带延迟各87场景57331事件；50521非法实际TRAP及恢复；每配置7内存/复位；单步/安全停钟；5短路径×6配置；穿透及两项存储窗口负测；123 Python测试全部PASS。
- 原V2.1入口本轮独立复跑PASS，证据`build/m20_300/v23/v21_baseline_20261103/verification.json`。未做综合、实现、STA、板级/实体157验证。
- [测试报告](docs/m20/M20_300_V2_3_TEST_REPORT.md)；[接口时序契约](docs/m20/M20_300_V2_3_FPGA_MEMORY_TIMING.md)；[详细任务与恢复入口](docs/tasks/m20-v23-two-phase-20261103.md)。

## 恢复入口

本任务已完成，无未验证RTL修改。先核对Git和`docs/m20/v23_resources/`摘要/源码SHA，不重复实现。若要复跑：`M20V23_OUTPUT_DIR="$PWD/build/m20_300/v23/新的目录" sim/scripts/run_m20_v23.sh`，禁止覆盖r1–r6或旧证据。旧源与两个tag不动；新增源码/小型报告按Git暂存审阅，大量原始数据留build并有SHA索引。下一步等待用户审阅结果/确认正式阶段通过；不自行继续PCB、选型、逻辑优化或硬件测试。新提交需本轮明确授权。
