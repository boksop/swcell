# M20 V2.1：验证方法

2026-11-02。VERIFIED范围为本轮数字契约与结构审计，不是形式全状态等价、物理STA或实物性能。

## 一条命令

```bash
M20V21_OUTPUT_DIR=build/m20_300/v21/new_run sim/scripts/run_m20_v21.sh
```

工具默认XSIM2026.1.1、build/venvs/python312/bin/python；可设M20_VIVADO_BIN和SWCELL_PYTHON。输出目录禁止指向旧V1/V2或候选评审证据；已有verification.json时必须换目录。失败退出非零，XSIM还必须出现显式PASS标记。没有生成bitstream。

## 分层检查

|层级|实际方法|
|---|---|
|V1译码/ALU基准|原tb_m20_isa，65536编码和32768内部op向量|
|正式结构CPU数据通路|tb_m20v21_datapath，27648组立即数/直接/间接全A/B/C/Z数学向量，192组移位/NOT，共27840；不将不存在的64-op内部接口强加给候选|
|全部非法终态|tb_m20v21_illegal，65536合法性；50521非法逐一经过FETCH、EXEC及实际TRAP时钟边沿，三次保持检查，并逐一复位后执行NOP|
|异常副作用|非法不退役、无CE/OE/WE、PC及A/AR/Z/C/GPO保持；FSM next-D与8状态独立真值契约一致|
|X/Z|ROM全X、全Z和有效RAM读返回X可观察，复位恢复确定状态；这是环境错误检测，不承诺未知电压会被硬件可靠译成TRAP|
|内存/复位|原7组：pending ST reset阻断、写后reset不回滚、HALT/TRAP及恢复、同步/延迟RAM、ROM映射元数据|
|完整CPU|原49指令+38游戏，逐周期V1/结构状态及关键总线、真实CSV和独立Python、所有256-nibble最终RAM|
|Python|原98项加9结构审计及3路径/参数边界测试，共110项|

全非法测试在FETCH前通过仿真后门设置非零数据状态和PC123，此为覆盖夹具，不是CPU端口或新增状态。每个非法字都实际clock进入7，而不是只测组合trap_event。对正常游戏连续64tick，运行期间不由主机修改CPU/RAM状态。

## 来源和失败记录

v21_verify.py绑定正式源码、既有V1源码及输入/期望SHA；compare复用原字段与RAM比较器，不修改预期。sim/m20_v21拥有本轮夹具与8态断言，原V1/V2未改。

首轮regression_20261102：datapath手动时钟宏泄漏至后续编译单元，memory时钟停止而watchdog失败。已在该TB结尾undef，另目录regression_r2通过；随后加强独立审计输入/复位常量检查后，在regression_r3全套重新通过。首轮证据保留，不能改记PASS。Python首轮负向测试误把某pin设成原值，测试自身FAIL；改成真正不同的pin后python_tests_final.log全部通过。

全Python命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m unittest discover -s host/python/tests -v
```

## 独立结构审计

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20.v21_audit --output build/m20_300/v21/new_audit
```

独立解析每个实例与pin、端口和别名、无条件FF-D，拒绝隐藏操作/CE、重复驱动、浮空源、组合环、死网和额外状态。区分功能与debug锥，检查33个reset选择。审计负向测试覆盖错pin、伪计数、隐藏运算/FF控制、多驱动、环。CSV包括完整nodes和fanout，不能用LUT数折算。

独立辅助验证：[双MUX时序/FPGA适配模型](M20_FPGA_INTERFACE.md)，不计作真实157性能通过。
