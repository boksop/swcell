# M20 V2.4：固定20颗前馈时钟结构审计

2026-11-04。**VERIFIED：仅结构、连接和数字真值表。** 时序结论另见[时序验证](M20_V24_NONOVERLAP_VERIFICATION.md)，本审计不证明物理死区。

## 审计对象与唯一计数

正式结构为 `rtl/m20/v24_ff16/swc_ff16_phasegen.sv`，每个 `swc_ff16_mux157` 实例对应一颗 NC7SZ157P6X。审计工具独立解析实际SV实例、端口和驱动关系，不用LUT数量或预计BOM代替计数。

|部分|实际实例|颗数|连接|
|---|---|---:|---|
|固定延迟链|u_delay01～u_delay16|16|S=0，I0=前一级，I1=0，非反相|
|Master译码|u_decode_h|1|S=C，I0=Cd，I1=1；H_RAW=C OR Cd|
|Slave译码|u_decode_s|1|S=C，I0=0，I1=Cd；S_RAW=C AND Cd|
|Master钳位|u_hold_h|1|S=SAFE_HOLD，I0=H_RAW，I1=1|
|Slave钳位|u_hold_s|1|S=SAFE_HOLD，I0=S_RAW，I1=0|
|**发生器**||**20**|0状态位、0内部DFF、0反馈环|
|冻结CPU||543|477组合＋33位×2存储|
|**CPU＋发生器**||**563**|不含外部分配Buffer和FPGA服务|

常量为接电源/地，不另计MUX。抽头选择是导线/0Ω装配连接，不是额外的MUX实例。参数选择没有删除未选中的后续级。

|TAP_STAGES|经过的有效延迟级数|仍保留的后续级数|物理链/总数|所选节点直接MUX输入端负载|
|---:|---:|---:|---|---:|
|4|4|12|16 / 20|3|
|8|8|8|16 / 20|3|
|12|12|4|16 / 20|3|
|16|16|0|16 / 20|2|

前3种负载是下一级I0加两译码器数据端；不能把所有后续级输入并联计算，也不能把后续链删除。走线、焊盘、探头和器件输入电容尚未物理标定。

## 原始参考核查

`rtl/m20/clock_proposals/swc157_phase_feedforward.sv` 与原提案记录SHA一致：

```
dd21dca10aafb45555c810fc95ae8b82be847658560223d2ea90f9f1d5ec855a
```

已检查 `Y=S?I1:I0`、正反相、级联方向、OR/AND数据与选择端、两路SAFE_HOLD钳位极性、输出无反馈、显式网络及模块命名。**没有发现需要修正的连接错误，原文件保持不变。** 新文件固定16级而原模板仍为可变N级，二者定位不同。零延迟时Cd=C，不据此宣称形成死区。

## 实际执行与重现

```bash
PYTHONPATH=host/python build/venvs/python312/bin/python -B \
  -m m20.ff16_structure \
  --output build/m20_300/v24_ff16/structure_review_new

PYTHONPATH=host/python build/venvs/python312/bin/python -B \
  -m unittest discover -s host/python/tests -p 'test_m20_ff16_structure.py' -v
```

工具拒绝覆盖已有输出。最终小型运行 `build/m20_300/v24_ff16/small_r4/structure/` 已执行同一审计。9项结构测试包括正确网络、非法tap、实例/连接篡改等；XSIM另实际执行8个MUX真值向量及4个C/SAFE组合×4tap，共24项，并检查每种tap下的末级实体输出仍存在。

|检查|状态|证据|
|---|---|---|
|原提案指纹及极性|VERIFIED|[structure_audit.json](ff16_resources/structure_audit.json)|
|四tap固定20实例、驱动及无环|VERIFIED|同上，各tap独立条目|
|9项结构单元测试|VERIFIED|Python全量142项日志中的结构测试|
|实际SV真值/四tap/末级存在|VERIFIED|small_r4/xsim/structure.log，`vectors=24`|
|综合优化后的16级物理保留|NOT_VERIFIED|本结构描述外部实体BOM；FPGA综合可把恒选MUX化成导线|
|真实非重叠/电气负载|NOT_VERIFIED|不能由结构审计或零延迟仿真推出|

## 逐实例、装配和测试点交付

- [20颗逐实例连接清单](ff16_resources/mux_connections.csv)：含逻辑网络和SC-88引脚映射。
- [四抽头0Ω装配表](ff16_resources/tap_assembly.csv)：每种配置仅装一个；其余DNP，禁止推挽输出短接。
- [各节点负载表](ff16_resources/tap_loads.csv)：固定链始终存在，未知寄生单列。
- [时钟测试点/接口信号](ff16_resources/signal_probes.csv)：CLK_REF、4tap、Cd、原始/最终两相及控制定义。
- [结构审计JSON](ff16_resources/structure_audit.json)和[源码SHA](ff16_resources/source_sha256.json)。

引脚映射以[onsemi Rev.7](https://www.onsemi.com/download/data-sheet/pdf/nc7sz157-d.pdf)的SC-88为依据。本轮不绘制原理图、不分配FPGA引脚、不确定Buffer树实体数量。17颗及116颗Johnson历史文件、原543 CPU和V2.3标签不变。
