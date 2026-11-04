# M20-COMPACT-CLOCK-REDESIGN-20261103

状态PLANNING，已交从零方案，等待时序/控制分工评审。用户停止116版本，要求少量157单路转两相，不能继续参考Johnson优化。

已完成：读取实际AGENTS/TASK/Git/旧报告；两个独立理论分析均建议前馈延迟参考窗口译码；在线核对NC7SZ157 Rev7第3/5页（输入转换条件、AC min缺失）。新提案H=C|Cd/S=C&Cd，N延迟+2译码+2保持=N+4，4级8颗/8级12颗是结构候选，非保证级数。无计数器/DFF/反馈环，f微周期=fREF。

交付docs/m20/M20_COMPACT_TWO_PHASE_PROPOSAL.md，rtl/m20/clock_proposals/swc157_phase_feedforward.sv（仅连线，未验证），docs/m20/compact_clock/{connections_n8.csv,proposal.json}。FPGA可负责RUN/STEP/reset协调，不计入纯157时钟核；完全自主运行控制另议。原V24同REF两边沿BRAM不能复用，需快时基与窗口/CDC预算。

|项|状态|证据|
|---|---|---|
|逻辑/数量|静态推导完成|提案表格与12颗连接CSV|
|datasheet核对|完成|原厂https://www.onsemi.com/download/data-sheet/pdf/nc7sz157-d.pdf，Rev7 p3/p5|
|新结构SV|已落盘、未验证|clock_proposals目录|
|保证最小死区|未闭合|无传播/污染最小规格，不能凭typ×N|
|编译/XSIM/CPU回归|NOT_RUN|遵守先评审再验证要求|
|综合/STA/实物|NOT_RUN|未创建板级/PCB|

不动116源码/原PASS与旧staged38文件，不自动commit/tag或远程。根TASK工作树另记新任务，旧索引先不重置。

恢复：先读新提案第4/5/6节，确认N是待标定参数、运行控制交FPGA与否、存储服务重预算；只有方向明确后才做小型独立弧测试。不要运行run_m20_v24.sh，也不覆写116证据。未验证连线模板不能称非重叠已通过。
