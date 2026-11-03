# M20-300 V1 验证方法与复现入口

更新：2026-10-29（Asia/Shanghai）。本轮终点是 V1.3：原 Pong/Snake ROM 在真正的 CPU RTL 中执行，与独立 Python 指令模型逐条一致。结果见 [测试报告](M20_300_V1_TEST_REPORT.md)，架构边沿见 [RTL 设计](M20_300_V1_RTL_DESIGN.md)。

## 1. 约束和版本

- 冻结 ISA：[`M20-300-ISA-0.1`](M20_300_ISA_FROZEN.md)，机器表为 [isa_v0_1.json](isa_v0_1.json)。编码、软件状态和指令效果冻结，不新增指令。
- 周期 profile：`M20-300-V1-TIMING-0.1`，当前普通 2/RAM 5/reset 单列 1；微架构不是 ISA。改变内部周期时必须同步参考模型、profile 和测试，不能静默重用旧预算。
- 本轮为行为功能 RTL，不做 MUX 结构优化、不综合/实现、不生成板级工程/引脚约束/bitstream，不进行硬件测试。
- 保留 V0 Python 算术/解释执行与游戏源码；Python 不调用 RTL ALU，TB 不执行游戏算法。共享编码规则用于分类，不共享参考计算过程。

## 2. 一条命令运行

从工程根目录执行：

```bash
sim/scripts/run_m20.sh
```

默认 Python 为 `build/venvs/python312/bin/python`；默认工具优先取显式配置、当前环境或 `~/AMDDesignTools/2026.1.1/Vivado/bin`。脚本核实所选 XSIM 属于用户指定的 2026.1 系列；本机实际是 **2026.1.1** 补丁版，无需新安装。

可显式指定工具和独立输出目录：

```bash
M20_VIVADO_BIN=/home/boksop/AMDDesignTools/2026.1.1/Vivado/bin \
SWCELL_PYTHON=/home/boksop/swcell/build/venvs/python312/bin/python \
M20_OUTPUT_DIR=/home/boksop/swcell/build/m20_300/v1_recheck \
sim/scripts/run_m20.sh
```

脚本在输出目录的 `xsim/` 编译/elaborate；不调用 Vivado 综合、实现或硬件管理。不要多个进程同时使用同一输出目录。默认结果在 `build/m20_300/v1/`，后续重验建议更换目录保留前次证据。

执行顺序：Python/冻结检查 → 生成输入和独立预期 → xvlog/xelab → 译码/ALU单元 → 内存/复位单元 → 指令差分 → 游戏差分 → 源码和证据汇总。全部成功返回 0，并输出 `M20_V1_REGRESSION_PASS`；任何阶段失败返回非零。XSIM 有时会在 HDL fatal 后仍返回 0，因此脚本还要求每个 TB 的显式 PASS 标记；差分错误不会被这种工具退出行为掩盖。

## 3. 分层验证

|层级|文件/方法|独立检查内容|
|---|---|---|
|冻结规则|`test_m20_frozen.py`、JSON|65536 编码唯一匹配、15015/50521计数、全部字段/版本/游戏哈希|
|RTL译码|`tb_m20_isa.sv`|独立 bit mask oracle，遍历全部 word，严格检查保留位和内存控制|
|RTL ALU|同上|64 个内部操作值×16 A×16 operand×2 C，共32768向量；数学整数运算和独立 A/Z/C 写使能|
|存储/复位|`tb_m20_memory.sv`|WE高时复位阻断、已完成写不回滚、RAM不清零、延迟读、HALT/TRAP静止和复位恢复|
|CPU指令差分|`tb_m20_cpu.sv` + `rtl_regression.py`|完整CPU执行、逐指令效果/总线事务/实际微周期、最终256-nibble RAM|
|游戏差分|同一通用TB|原汇编镜像的boot、定向边界、连续64tick、异步延迟和同步RAM读适配|
|比较器负向测试|`test_m20_rtl_tools.py`|缺失输出、少/多事件、X/Z、逐字段改错、未访问地址RAM改错均失败|

ALU 单元穷举四位操作数与旧进位；CPU 差分另外验证译码、操作数选择、写使能和提交路径，不以组合 ALU PASS 代替 CPU PASS。所有 45 条编码规则均在真实 CPU 轨迹中执行到。

## 4. 输入与差分协议

`host/python/m20/rtl_regression.py prepare --output DIR` 只生成输入和 **EXPECTED_ONLY_NOT_RTL_PASS** 预期。它不生成 `.rtl.csv`；这些文件只能由 XSIM TB 生成。

每套 `instructions/`、`games/` 包含 `metadata.json`、`cases.txt` 和每场景文件。`cases.txt` 每行14字段，除 case_id 外均为十进制：

```text
case_id rom_words entry_pc init_a init_ar init_z init_c init_gpo keys event_limit cycle_limit memory_mode rom_delay_ps ram_delay_ps
```

|文件|来源和含义|
|---|---|
|`NAME.rom.memh`|Python汇编/生成，4096个16-bit word；未装载区域FFFF|
|`NAME.ram.memh`|启动前256个nibble夹具；默认非零A，避免默认清零假象|
|`NAME.keys.txt`|每个指令事件的稳定逻辑按键0..63，不包含同步/消抖模型|
|`NAME.expected.jsonl`、`expected_ram.memh`|独立Python指令模型的预期，不是RTL结果|
|`NAME.rtl.csv`|真实XSIM采集的事件，所有字段十进制|
|`NAME.ram.final.memh`|真实XSIM结束时完整RAM，含scratch及未修改地址|
|`comparison.json`、`compare.log`|离线逐字段和最终RAM比较，仅实际输出匹配后PASS|

CSV字段：`sequence,pc,word,next_pc,a,ar,z,c,gpo,ram_kind,ram_addr,ram_data,cycles,cumulative_cycles,event,halted,trapped`。sequence从0；ram_kind=0无/1读/2写；event=0正常退役/1 TRAP。无事务时不要求无效地址/数据的值；有事务时地址和数据均精确比较。ST 的调试 previous-value 不作为硬件读事务。

TRAP 是独立异常事件，不产生 `retire_valid`；HALT 正常退役一次。FAULT 仍限 Python 短镜像范围/仿真元数据诊断；本轮物理CPU只有16位ROM输入，看到FFFF实际进入TRAP。ROM模型的有效范围sideband在内存单元中单独核实，不伪装成CPU硬件FAULT。

## 5. 退役采集与独立时序断言

核心组合 retire 接口在提交边沿之前描述旧PC、旧指令和提交后值。TB在posedge active区先保存这些值，NBA更新后再比较真实debug状态；不会等PC改变后才读取下一条ROM指令。

TB从FETCH_WAIT开始实际逐边沿计数，普通提交须恰2、RAM提交须恰5；累计周期也与Python相等。它不只相信核心给出的2/5声明常量。

每条指令同时检查：

- 未退役时PC/ROM保持；RAM setup/access/release期间地址、A/AR/Z/C保持。
- ST在ACCESS仅一个真实写边沿；读指令无写，非法指令无RAM请求。
- CE/OE/WE互斥关系正确；复位立即屏蔽请求；正常状态、ROM和读采样无X/Z。
- 组合retire预测和实际提交后的架构状态一致；HALT/TRAP之后继续若干时钟仍无事务/退役。
- 启动和运行中复位符合定义，RAM不随CPU reset清零。

每case只在reset启动边界装载ROM/RAM和CPU寄存器夹具。正常boot使用标准复位值；连续游戏由CPU执行全部初始化和后续循环，TB运行期间只改变外部keys，不修改游戏RAM或CPU状态。

## 6. 内存模型的有效范围

仿真微时钟周期10ns；测试ROM异步延迟1.5ns、RAM异步延迟2ns，以及RAM注册读适配。读取OE覆盖SETUP/ACCESS/RELEASE，RAM在RELEASE采样；持续OE仍只记一个ISA读事务。同步模型允许先在前一个MEM边沿取数，数据保持到提交。

内存单元特意覆盖：WE已经高、尚未到写边沿时复位，禁止该次写；以及写边沿已发生后、退役前复位，已有RAM写不会回滚。后者不是失败或原子回滚承诺。

这些是逻辑模型测试。**没有验证同步ROM/最终BRAM IP、物理SRAM/NOR tACC/WE脉宽、PCB/电平/三态换向或绝对时间裕量**；没有WAIT支持。超过当前数据稳定窗口的模型延迟不能宣称受支持。10ns仿真时钟不等于FPGA STA通过或157 CPU达到100MHz。

## 7. 失败证据和恢复

每次运行保留输入、预期、实际CSV、最终RAM、compile/elaboration/simulation日志和四个WDB，失败时也不自动删除。寄存器/事务/周期不一致时，比较器另写 `first_mismatch.json`，含测试名、序号、PC、机器字、expected/actual和输入路径；输出缺失或RAM错误在compare.log报告。

可以离线重新比较：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20.rtl_regression compare \
  --directory build/m20_300/v1/games
```

`inputs_manifest.json`固定编译前32份相关源文件指纹；最终`summarize`确认运行期间未变化、四个TB标记和Python/差分均通过，生成`verification.json`与`coverage.json`。默认历史输出另有本轮保护基线，检查原308文件、V0解释器/汇编器/游戏/架构与Git index未改；新独立目录无旧基线时明确记录，不伪称执行过该检查。

build中的轨迹/波形可再生，Git忽略；应保存本次证据归档以便长期审计。Git仍无首个commit，源码SHA是当前关联依据；不把提交或软件预期当作RTL执行证据。
