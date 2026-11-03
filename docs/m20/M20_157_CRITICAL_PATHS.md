# M20：最长路径、最短路径与竞态

2026-11-02。拓扑/连接为VERIFIED；延迟为ESTIMATED；实物setup/hold/最差敏化路径为TBD。

## 图与复现

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20.physical \
  --traces build/m20_300/v21/regression_r3/games
```

工具先独立审计SV/JSON，再构建每个MUX的s/i0/i1→Y弧。Top50按带pin类别的最大场景排序，保存完整节点/组/端点；按FF/FPGA起点与FF/输出终点分类。直连的PC→ROM地址为0级，也保留。特定源族独立搜索，避免ROM的大量长路径掩盖RAM/reset路径。

|路径类别|最长拓扑|LVC85℃+0.15ns/级示例ns|
|---|---:|---:|
|ROM数据→状态D|29|149.35|
|FF→FF：C→Z|16|82.40|
|PC内部更新|15|77.25|
|AR内部递增|11|56.65|
|RAM数据→A|16|82.40|
|状态→RAM WE|9|46.35|
|reset→状态/数据D控制锥|6|30.90|

不应将29层当作所有FF→FF路径长度。详见[Top50](physical_resources/top50_paths.csv)、[分类](physical_resources/critical_categories.csv)、[端点](physical_resources/endpoint_paths.csv)。CPU取指存在PC-Q→FPGA ROM→ROM数据→D的跨器件环，内部FF16层不能覆盖这个环。

3000组固定种子静态赋值对Top50未找到同时满足全部pin旁路条件的见证，结果UNPROVEN；**这不是不可敏化证明**。没有SAT/形式时序可达性证明，也不能将这些路径标成“真实最坏功能路径”。同时输入变化/毛刺可能不同于稳定向量敏化，不能凭未找到见证忽略长路径。

## 最短路径与同边沿源更新

[最短FF路径CSV](physical_resources/shortest_ff_paths.csv)包括自反馈和跨寄存器路径；最小跨寄存器为A→GPO的2层，但OUT时A不更新，不能直接当作实际hold危险路径。

从实际Pong/Snake boot与连续64tick CSV重建旧状态、指令和读数据，核对图的D投影与实际退役一致后，检查源Q将在本边沿改变、该最短pin路径旁路条件成立，以及翻转源会改变目的D。找到79对逻辑风险见证：[co_launch_risks.csv](physical_resources/co_launch_risks.csv)。这是功能同边沿活动证据，不是已测保持违例。

|重点短路径|级数|实际见证|
|---|---:|---|
|PC0→PC1|4|Pong boot首条LDI，PC0→1使低位更新且高位D敏感|
|AR0→AR1|4|Snake boot的INCAR|
|A0→C|4|Pong连续执行SHR|
|A3→C|4|Pong的SUBI|
|AR进位链相邻位|5及以上|Snake清RAM循环|

若目的Master关闭比源Slave新Q发出更晚，以上路径可能把新值采入本应使用旧值的计算。self-hold两层路径也需验证其使能稳定，但不能把保持状态当作新数据发射。

## 约束形式

对未来已表征的DFF，setup形式为T≥tCQ,max+tCOMB,max+tPCB,max+tSU−skew+margin（skew=目的捕获−源发射）；保守预算用|skew|。hold形式为tCQ,min+tCD,min+tPCB,min≥skew+tH。当前tCD/真实tH缺失，任何频率均不能标hold PASS。

非重叠两相要求所有目标Master先关闭，之后才允许任一源Slave打开；下降交接时所有Slave先关闭，之后才允许Master透明。死区须覆盖分支差、器件pin时延差、边沿阈值差和抖动，并留裕量；不能只按PCB等长保证。
