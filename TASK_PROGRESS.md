# SwCell 当前任务进度

2026-11-04，Asia/Shanghai。分支main；本地定版进行中，起点HEAD5e601a9，V23 tag目标aecf570保持。

## 当前任务

**M20-V24-RELEASE-20261104：IN_PROGRESS。** 用户已批准V2.4有条件数字验收，授权本地commit及annotated tag `m20-v2.4-digital-verified`。仅定版，不进入V3/PCB/实机或远程Git。

[定版检查点](docs/tasks/m20-v24-release-20261104.md)｜[数字开发已完成记录](docs/tasks/m20-v24-ffcd-20261104.md)｜[完整数字报告](docs/m20/M20_V24_FULL_SYSTEM_VERIFICATION.md)。

## 已核实和正在执行

- [x] 原90份暂存内容逐项核对、索引及blob备份完成，计划独立历史提交，不混为正式验收结果。
- [x] V23保护206文件、C/D源和8089原始文件SHA复核一致；CPU543、20发生器、ISA/ROM与失败证据不改。
- [x] 纳管原79条向量，新增不依赖ignored历史build的632负测重放入口；原历史review入口保留。
- [ ] 全151Python和新重放运行中，完成后再修改Git索引。
- [ ] 正式阶段报告、版本纳管/排除清单、完整提交、干净恢复和annotated tag待完成。

## 恢复入口

先读定版检查点，检查 `build/m20_300/v24_release_20261104/` 日志、Git HEAD/tag/索引，避免重复提交或覆盖旧产物。原90stage来自历史116/A-B资料，本轮用户授权后按清单单独保存；禁止reset/clean、远程操作、移动V23 tag或把失败改判PASS。实体时序、FPGA实现和硬件验证仍OPEN。
