# SwCell 当前任务进度

> 本文件是任务状态权威入口；实际源码、Git、原始日志和校验值用于核实。开始先读本文件及任务详情，遵守[AGENTS.md](AGENTS.md)。

## 1. 当前任务

|项目|内容|
|---|---|
|Task ID / Name|M11-PHASE2B-20261016 / 75、100、125MHz独立采样窗口与分级可靠性验证|
|目标|Q/QM各16点独立扫描；全部候选窗、模式对齐、百万→门控亿次、可恢复JTAG/UART采集及离线图表|
|范围 / 非目标|保留Phase1/2，静态MMCM/ODDR/IOB；不操作Flash、不做完整setup/hold、温压、GUI或其它模块|
|状态|**COMPLETED：实现、回归、实物采集与分析完成；等待用户正式验收**。125MHz保留MARGINAL，不是全频率PASS|
|分支|`main`，尚无首个commit；用户只授权初始化及暂存四份进度文档，其它源码尚未跟踪|
|最近核实时间|2026-10-17 06:35:03 +0800|
|详细记录|[主任务](docs/tasks/m11-phase2b-20261016.md)、[图文验证总结](docs/phase2b_validation.md)、[操作与文件清单](docs/phase2b.md)|

## 2. 已完成工作：已修改、已验证

- [x] 独立双轴/全窗口/事务边界/分级门控/恢复和离线分析；RTL本域启动同步及独立首错；协议向后兼容。
- [x] 全部XSIM回归PASS（SWCELL_ALL_REGRESSIONS_PASS）；最新Python52项PASS，收尾已重跑。
- [x] 三频率96个轴测点全部实采，每点每路10000；12个对齐/长测job全部完成。108有效job、105个独立镜像，各自实现/STA/DRC核验通过。
- [x] 每频率0101、0011、PRBS1e6与1e8两路零错误；按窗口宽度区分最终频率结论，见下表。
- [x] 离线重新生成96行phase CSV、12行long CSV、summary、3图和report；108个job原始消息/计数/源码/镜像SHA和聚合字节偏移核验通过。
- [x] 已更新验证总结、README、少量文档插图与任务记录；第一阶段正式报告不变。
- [x] 生成可上传证据包（约5.4MiB），包含原始数据、源码、实现报告及三份亿次镜像；逐成员SHA读回复核通过。
- [x] 长期进度机制已建立；Git main初始化及四文档暂存获授权；没有commit/push。

**已修改、未验证：没有当前已知功能修改。** 外部时序标定和用户正式验收仍未执行，不属于已验证事实。

## 3. 最终实物检查点

|DUT频率|Q零错索引 / 点数|QM零错索引 / 点数|所选Q / QM|最终分类|
|---:|---|---|---|---|
|75MHz|9,10,11,12,13,14,15 / 7点|1,2,3,4,5,6,7 / 7点|12 / 4|`PASS_1E8_ZERO_ERRORS`|
|100MHz|12,13,14,15 / 4点|4,5,6,7 / 4点|13 / 5|`PASS_1E8_ZERO_ERRORS`|
|125MHz|15 / 1点|7 / 1点|15 / 7|`MARGINAL_WINDOW`|

75MHz选Q12/QM4；100MHz选Q13/QM5；125MHz选Q15/QM7。三组各路均为0 errors / 100000000 checks。125MHz仅一个网格点零错，不能升级为可靠窗口PASS。按至少3连续点判据，最高已验证100MHz；最高观测亿次零错125MHz；均不是器件保证Fmax或理论BER=0。

runner于`2026-10-17T02:22:00.486885+08:00`正常结束。收尾已核实PID509248退出、无遗留控制器。111条历史尝试含2 INTERRUPTED、1旧STARTED，均已有后续完成记录；latest_jobs108项全MEASURED，**没有未完成硬件job**。不删除历史或按旧STARTED重复执行。

## 4. 待完成 / 后续入口

|优先级|动作|完成条件/边界|
|---|---|---|
|本轮|实现、回归、完整实采、最终离线分析和证据核验|全部完成，checklist已关闭|
|评审|用户阅读验证总结并确认正式阶段验收|收到明确确认后按模板生成docs/reports正式报告；目前不自称已获用户验收|
|可选新任务|125MHz更细相位、邻点重复及外部仪器标定|另定义范围和新结果目录，本轮仍MARGINAL|
|Git后续|完整源码纳管和首个commit|等待用户授权；不自动提交或无差别git add|

## 5. 关键设计决策

- Q/QM由MMCM CLKOUT2/2B和3/3B独立采样，静态16点、多bitstream，每次JTAG重配重新初始化；无运行时Fabric时钟MUX或IDELAY。
- D于nT+T/4发射b[n]；Q目标b[n−1]，QM0..7为b[n−1]、8..15为b[n]。Q15→0、QM7→8不合窗；QM15→0可合。不能任意挪动参考一拍制造PASS。
- 两路64bit本域统计、冻结256bit快照后握手CDC；PRBS停机不乱推进。可靠窗口至少3连续点，窄窗观测与可靠频率结论分开。
- 时序例外限未知外部pad→IOB、首级控制同步器及复位同步器PRE；内部数据路径保留STA。外部IO时序尚未标定，电压/温度为null。
- jobs2、只预构建当前频率、单一JTAG/UART控制器，避免OOM/重复占用；未来恢复仍须核对实际进程。

## 6. 测试与证据

|层次 / 测试|结果|命令 / 证据|
|---|---|---|
|SV语法/elaboration / XSIM|PASS|`sim/scripts/run_all_regressions.sh`；`build/phase2b/regressions.console.log`|
|Python52项|PASS|`.venv/bin/python -m unittest discover -s host/python/tests -v`；`build/phase2b/python_tests_final.log`|
|综合 / 布局布线 / 内部STA / DRC|PASS，105镜像|各build目录报告；`build/phase2b/final_timing_audit.csv`，外部IO未标定|
|实物功能/裕量|75/100 PASS；125 MARGINAL|当前目录checkpoint/CSV/raw，详见验证总结|
|最终离线分析 / 完整性核验|PASS|`build/phase2b/final_offline_analysis.log`、`final_evidence_audit.log`；[审计摘要](docs/assets/m11_phase2b_20261017/evidence_audit.json)|
|外部绝对时序 / 电气标定|NOT_RUN|需示波器、PCB/负载/电源测量；不冒充已测|
|用户正式验收|NOT_RUN|尚待用户确认，当前不是正式阶段报告|

- 结果目录：`results/M11/phase2b_20261016_reset_sync/`，398条JSON、531730字节；全部原始记录保留。
- 证据包：[m11_phase2b_20261017_evidence.tar.gz](results/M11/m11_phase2b_20261017_evidence.tar.gz)，包外`.sha256`、包内`PACKAGE_SHA256.json`；不包含大型DCP/波形。
- 当前FPGA源指纹：`b0209deae54271113fb461148b4a794d467ba2612ed6996ff19f13c1d16fb79b`。
- raw SHA256：`bcbcc762a6b4eaed474da83274722a0414112dd39d908ae42b2b14c4e25b4a56`。
- checkpoint SHA256：`2816eb0f2ef4a7705104e7feb12f4f15d88421c311085cd1bb0b20d77853cb10`；各长测raw/bit SHA和完整参数见验证总结。
- FPGA归档：`build/phase2b/source_b0209deae542.tar.gz`，SHA256 `ff5a3c3410c94a313fbbd33c9338d33eca04130e2a1358cf7796e0629a13e35c`。

## 7. 已知风险与恢复操作

1. **无需恢复扫描**：本任务已完成，先打开主任务详情、验证总结与summary。下次新会话只做事实核对或处理新指示，不能重复下载/重测亿次。
2. 若要离线复核，从根目录运行（不访问硬件）：

```bash
MPLCONFIGDIR=/tmp/swcell-mpl .venv/bin/python host/python/swcell_phase2b.py \
  --analyze results/M11/phase2b_20261016_reset_sync
.venv/bin/python build/phase2b/final_audit.py
```

3. 无当前已知已落盘未测试功能修改。用户正式确认后才新增报告；125MHz细扫/外部测量需新任务，不篡改raw或旧结果。
4. 历史闪退曾使RUNNING状态滞后；以后必须核对实际进程/源码/日志。22:29内核OOM杀Chrome的事实不证明VS Code直接崩溃原因；并行减至2后本轮完整结束。
5. CDC存在结构已审查的外部采样、复位、冻结总线项，不能宣称零告警或外部IO时序关闭。125MHz1点窗、有限样本/环境不代表可靠Fmax。
6. 旧88e约束诊断、历史25/50MHz和Phase1记录独立保留，不合并本轮统计。build/results受Git忽略，清理前必须保留证据；仅暂存四文档不是完整源码历史或异机备份。
7. 禁止未经授权commit/push/切分支、无差别add、reset/clean、写Flash、重做第一阶段或改模型掩盖错误。无可引用Git commit。

## 任务索引

|任务|状态|详情|
|---|---|---|
|M11-PHASE2B-20261016|COMPLETED（开发与实测完成，待用户正式验收）|[主任务](docs/tasks/m11-phase2b-20261016.md)|
|SWC-PROGRESS-PERSISTENCE-20261016|COMPLETED（机制和授权初始化已核验）|[持久化机制](docs/tasks/progress-persistence-20261016.md)|
