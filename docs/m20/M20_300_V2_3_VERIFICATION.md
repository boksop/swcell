# M20 V2.3：自动联合回归与证据方法

## 一条命令

```bash
# 必须新输出目录，重复路径会拒绝，保护失败与历史证据。
M20V23_OUTPUT_DIR="$PWD/build/m20_300/v23/my_new_run" sim/scripts/run_m20_v23.sh
# Python自测，与原有全部测试一并执行
PYTHONPATH=host/python build/venvs/python312/bin/python -B -m unittest discover -s host/python/tests -v
```

压力测试入口`sim/scripts/run_m20_v23_stress.sh`运行同一完整回归（保留功能保护，不跳过原87场景）。

绘图沿用现有`host/python/requirements-analysis.txt`中的matplotlib/numpy依赖；可在选定虚拟环境执行`python -m pip install -r host/python/requirements-analysis.txt`安装。原requirements不修改。

默认Vivado工具路径为`$HOME/AMDDesignTools/2026.1.1/Vivado/bin`，可由`M20_VIVADO_BIN`覆盖；Python由`SWCELL_PYTHON`覆盖。本轮不做Vivado版本移植或板级工程。XSIM负向fatal可能仍返回进程0，脚本逐项检查PASS标记；预期负测必须匹配指定fatal，不能把任意编译错误视为负测通过。

## 五个独立比较参与者

V1行为RTL、冻结V2.1原生FF结构RTL、V2.3原生FF切换分支、V2.3真实双反馈MUX状态，分别拥有独立同步ROM/RAM数组和事务处理；原Python解释器产生期望，保持旧编码、机器码和2/5周期。

每个微周期M关闭前比较旧33位状态、总线/退役载荷、RAM读写值及2/5元数据，并检查Master已稳定。S观察点再次比较完整新状态。每个事件写四份独立CSV；最终各自写256项RAM文件，Python再逐字段/全部RAM与独立期望比较。不是让其他CPU共享两相DUT的计算结果。非事件期间RAM写计数与静止终态也检查。

## 覆盖矩阵

|层级|覆盖|判定|
|---|---|---|
|结构|477逐pin、33 D/Q/QM、66反馈MUX|独立审计，拒绝额外逻辑/隐藏FF；临时目录重生成字节一致|
|调度|独立3/5 tick不对称死区；5次单步；四阶段发起停钟|阶段长度、互斥、停钟两端关闭，无额外提交|
|CPU单步|LDI/ST/HALT及终态再单步|2/5指令微周期、每次停钟33位保持、ST只写一次|
|功能|49指令+38游戏=87；57331事件|四RTL+Python；含连续64tick、PC/AR回绕、HALT/TRAP|
|非法|65536字分类，50521非法实际执行至TRAP并复位执行NOP|每字保持30位数据、无写、终态7及恢复|
|存储/复位|7组|pending写取消、已写不回滚、同步读/OUT/HALT、重复执行、不清RAM、TRAP/未加载FFFF及恢复|
|延迟|完整87再次执行；指定5短路径场景按多配置执行|原游戏码、完整RAM/退役周期不改；各有效位互斥|
|负测|M晚关、S早开导致实际重叠|先观察Q错误穿透，再独立开启fatal确认检测|

5个定向短路径来自V2.2 `physical_resources/co_launch_risks.csv`：PC0→PC1、AR0→AR1、A0→C（SHR7100）、A3→C（SUBI3001）、FSM访存退出。它们是活动向量，不把拓扑路径的所有节点都称作已证明可敏化；全游戏对照仍覆盖原来的79组同边沿见证来源。

## 压力配置

sys_clk=20ns；数据/选择传播为数字输入路径延迟，节点序号奇偶交替min/max，33位分支按i%3分配偏斜。

|配置|M/D1/S/D2 tick|组合D min/max ns|组合S min/max ns|锁存D/S ns|Master偏移/Slave偏移/步进偏斜 ns|
|---|---|---|---|---|---|
|zero|12/4/12/4|0/0|0/0|0/0|0/0/0|
|delayed|64/8/64/8|0.2/0.8|0.3/1.0|0.4/0.5|1/0.5/0.3|
|reduced|64/1/64/1|同delayed|同delayed|同delayed|同delayed|
|max_delay|64/8/64/8|1.6/2.5|2/3|1.5/2|3/1/2|
|master_late|64/8/64/8|同delayed|同delayed|同delayed|35/0.5/2|
|slave_early|64/3/64/8|同delayed|同delayed|同delayed|1/0/0.3|

负向单bit模型数据延迟1ns、选择0.5ns，Master分支12ns、Slave分支0ns；两原始控制同时翻转后3ns改变D，观察原应保持0的Q变1。另一次运行使能互斥fatal。另有两项存储负测：人为增加RAM输出延迟至200ns，必须触发V23_RAM_RESPONSE_SETUP；ROM延迟300ns，必须触发V23_ROM_CHANGED_MASTER_OPEN。不是仅修改理想单时钟的频率。min/max配置没有来自已测器件的统计分布意义；未模拟噪声/负载/亚稳态，不能作实体Hold签核。

## 输出与保护

每轮独立输出`build/m20_300/v23/<run>/`：

- `source_sha256.json`、`input_sha256.json`：仿真前快照，结束校验，不允许改期望造PASS。
- `resource_audit.json`；各profile/suite原始四CSV、独立最终RAM、Python比较JSON。
- `xsim/*.log`和WDB；`timing_trace.csv`为前1600系统边沿，`penetration.csv`记录实际有效相位/QM/Q事件。
- `regression_summary.csv`及`verification.json`：只有全部指定标记/四方比较/哈希一致才生成PASS。

小型摘要/关键波形图与哈希索引可纳入`docs/m20/v23_resources/`；原始大量CSV、WDB、编译库留在build，不提交。历史V1/V2/V21数据、ROM及标签不移动。生成器、原语、适配器、脚本、TB和小型报告纳入现有Git审阅流程；没有本轮明确提交授权时不自动commit。
