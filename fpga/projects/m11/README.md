# M11 FPGA验证工程

- [functional](functional/README.md)：低速17项基础功能，注册输出激励＋同步返回＋UART JSONL。
- [performance](performance/README.md)：MMCM/ODDR、多bitstream频率/独立采样相位与长PRBS。
- `common/constraints/m11_io.xdc`：用户确认的七路M11连接；公共板卡IO不在此重复。
- UART板卡诊断在 [diagnostics](../diagnostics/README.md)，不是M11 CPU或DUT算法的一部分。

完整操作与历史实测见 [M11指南](../../../docs/m11/README.md)。当前文档中的新路径用于今后构建；旧results/build证据留在原位置，通过迁移表及历史Git标签定位。
