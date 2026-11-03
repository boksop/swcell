# M20-300 游戏机器指令原型

2026-10-29补充：ISA已正式冻结为 [M20-300-ISA-0.1](../../docs/m20/M20_300_ISA_FROZEN.md)。以下两份游戏源码/机器码保持V0不变，已通过[V1.3真实RTL差分验证](../../docs/m20/M20_300_V1_TEST_REPORT.md)；执行`sim/scripts/run_m20.sh`可复现CPU仿真。旧软件标识和V0预算作为历史保留。

依据 [M20-300 架构候选](../../docs/m20/M20_300_architecture_v0_1.md) 的 V0：4-bit A、8-bit AR、12-bit word PC、16-bit 指令；RAM 是 256 个 nibble，ROM 是 4096 个 word。程序各自生成独立镜像。

|文件|用途|
|---|---|
|[pong.asm](pong.asm)|球拍、球运动、墙/球拍碰撞、每方两个 nibble 组成的 8-bit 分数、软件共享函数|
|[snake.asm](snake.asm)|身体环、占用位图、方向、碰撞、增长、食物探测、封顶和重启|
|[pong_program.md](pong_program.md)|Pong 的 RAM/输入/返回 ABI 和规则|
|[snake_program.md](snake_program.md)|Snake 的 RAM/输入/返回 ABI 和规则|
|[ISA 约定](../../docs/m20/M20_300_isa_v0_1.md)|全部编码、标志、汇编语法、异常及工具接口|
|[验证与预算](../../docs/m20/M20_300_software_validation_v0_1.md)|本轮可复现结果、真实指令计数、模型周期及能力复核|

两游戏的更新完全由 CPU 机器指令完成。Python 数学游戏模型仅作旁路核对；解释器没有 Pong/Snake 专用操作。场景测试允许在启动前装载 RAM 夹具，连续运行测试在 boot 后只改变外部按键输入，不回写游戏 RAM。

## 一条命令复现预算

从工程根目录执行，使用现有 Python 3.12 环境；M20 工具本身只依赖标准库。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20.benchmarks \
  --output build/m20_300/software_v0_1 --random-cases 1000
```

返回 0 表示所有场景、独立参考比较、RAM 不变量和连续运行均通过；错误会以非零码中止。建议修改程序后换一个输出目录保留前次证据。输出在被 Git 忽略的 `build/`，可随时从源码重建：

- `summary.json`：ROM/镜像与源文件 SHA256、逐类结果、boot/连续执行统计。
- `case_metrics.csv`：每个场景的动态指令、逻辑取指、RAM 读写、执行周期及循环开销。
- `clock_budget.csv`：100kHz/1MHz/2MHz/5MHz **假设微周期时钟**下的时间换算，包含来源及范围标记。
- `fixtures.jsonl`：全部场景的启动 RAM 与按键；用于复现，运行期间不作为 RAM 更新源。
- `pong/`、`snake/`：`.bin` 小端镜像、`.memh`、`.lst`、符号/JSON listing、最大观测场景的输入和完整 retire trace。

## 汇编与逐指令执行

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20 assemble \
  software/m20_300/pong.asm --output-dir build/m20_300/pong

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
build/venvs/python312/bin/python -B -m m20 run \
  build/m20_300/pong/pong.bin --max-instructions 10000 \
  --trace build/m20_300/pong/trace.jsonl \
  --summary build/m20_300/pong/run_summary.json
```

游戏包含持续循环，所以第二条命令通常以 `INSTRUCTION_LIMIT`、退出码 **2** 结束；0 只用于真正 HALT。`--format memh` 可运行文本镜像。解释器默认全零 RAM 是测试夹具，游戏 boot 的初始化另由机器指令执行；正式基准从非零 RAM 验证 boot。

## 回归

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \
MPLCONFIGDIR=/home/boksop/swcell/build/m20_300/matplotlib \
build/venvs/python312/bin/python -B -m unittest discover -s host/python/tests -v
```

包含既有 M11 的 Python 回归；不会烧写 FPGA。只测 M20 时可追加 `-p 'test_m20*.py'`。

本轮不含 OLED/SPI、软件按键消抖、实际 tick 定时或存储器 WAIT；不是完整可玩固件。普通 2/RAM 5 微周期是解释器的候选模型，不能据此宣称已实现 328 颗 MUX、实物主频或完整游戏帧率。
