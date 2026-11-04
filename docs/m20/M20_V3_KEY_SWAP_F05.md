# M20 V3 F05：交换切换游戏与暂停按键

2026-11-04，Asia/Shanghai。用户明确要求仅互换现有两项控制，保留暂停功能。

|按键|F04历史镜像|F05|
|---|---|---|
|KEY5 / A / N19|暂停/继续|切换Pong/Snake并复位CPU|
|KEY7 / M27|切换Pong/Snake并复位CPU|暂停/继续|
|KEY6 / B / M19|重启当前游戏|不变|
|KEY2/0/3/1|上/下/左/右|不变|
|KEY4中键|无控制功能|不变|

切游戏保持原运行/暂停状态：暂停时切换后仍暂停，按KEY7恢复。持续按住一次不会反复切换；均沿用20ms消抖后的按下事件。六个CPU逻辑输入的位序、原IN1 A预留语义不变，不增加CPU输入、157或状态位。

改动仅在板级`select_request`与`run_toggle`按键来源，以及UART构建标识F05。UART `p/s/r/空格/n/1/2/3`仍保持原义。Python新增F05兼容，同时继续解析F01～F04。CPU477组合MUX、33位原生FF适配、ISA、两游戏代码和乱序表均不改；Pong10tick/s、Snake5tick/s、SPI10MHz、主动CPU微周期默认1MHz保持。

## 验证记录

|层级|状态|方法与证据|
|---|---|---|
|Python|PASS，164项|build/m20_v3_python_swapped_keys_r1.log|
|XSIM编译/elaboration/板级集成|PASS|build/sim/m20_v3/swapped_keys_r1/；实际引脚输入、两游戏SPI像素、3918 UART字节|
|互换断言|PASS|A切Snake不暂停；KEY7暂停不换游戏；暂停时A切回Pong仍暂停；KEY7恢复不换游戏；KEY4忽略、B及短按缓存继续检查|
|综合/实现/STA|PASS|build/fpga/m20/cpu_validation/snake_shuffled_keys_r1/；WNS+0.849ns、WHS+0.042ns、WPWS+9.232ns、DRC0|
|源指纹/引脚/路由实例|PASS|22份输入SHA、25个3.3V引脚、477 LUT3/33CPU FF/1BUFG；pre_program_verification.json|
|新镜像JTAG|PASS|21:00:11 startup HIGH、退出0；build/m20_v3_program_swapped_keys_r1.log|
|UART在线运行|PASS，60条有效记录，错误/输入溢出0|results/M20_V3/20261104_210020_swapped_keys_f05/；1条未识别启动行保留，不将UART运行替代实际按键确认|
|新实体按键体验|用户确认符合预期|用户另指出BOOT页仍需KEY7进入；该新增入口要求由F06独立处理|

本次使用此前通过的固定乱序食物ROM，完成断点313；默认无变体构建参数的工程仍使用原版Snake。此前F04/乱序实机证据不改写为F05结果。原回退镜像`build/fpga/m20/cpu_validation/snake_shuffled_r1/swcell_m20_v3_top.bit`保留，SHA256 `d58128b860ff512fd0bb36b6ae70afa35496844b098c39df6b27bf2e77eb3440`，KEY5暂停/KEY7切换。

F05已下载镜像：`build/fpga/m20/cpu_validation/snake_shuffled_keys_r1/swcell_m20_v3_top.bit`，SHA256 `8143bb2d4b1a38ebdd65b06ec15d9dcc65151dc03e8a746ccf22557413e16afe`。原始构建/仿真缓存和数据不提交，关键小型记录另保存在v3_resources/f05_*。

采集raw SHA256 `f7a472d18587f5bdab4948f2fe66a9209234ed71a1319de23dcb0b2b509b161a`；本次未发送UART控制命令，采集到Pong运行。物理新键位尚未收到用户确认。逐项核对旧F04源快照，除top两按键来源和版本字符串外，其余21个构建输入SHA未变；没有重新执行无改动CPU的87场景，复用原核心证据并新增本轮实际引脚驱动的板级互换断言。

后续用户明确确认F05互换符合预期；本页采集摘要及当时的NOT_VERIFIED字段不回写。新增“M20 CPU BOOT”页KEY5启动要求及新版本见[F06报告](M20_V3_BOOT_ENTRY_F06.md)。

```bash
vivado -mode batch -source fpga/common/tcl/program.tcl \
  -tclargs build/fpga/m20/cpu_validation/snake_shuffled_keys_r1/swcell_m20_v3_top.bit xc7k325t_0
```

## 复现

从仓库根目录执行，输出目录必须未存在：

```bash
M20V3_BOARD_SNAKE_FILE="$PWD/software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.memh" \
M20V3_BOARD_SNAKE_DONE=313 bash sim/scripts/run_m20_v3_board.sh
vivado -mode batch -source "$PWD/fpga/projects/m20/cpu_validation/scripts/build.tcl" \
  -tclargs --mode FUNCTIONAL_STORAGE --output build/fpga/m20/cpu_validation/swapped_new \
  --snake-rom software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.memh --snake-done 313
```

当前任务不commit、Tag、Flash或远程Git；严格双反馈MUX存储的历史DRC限制仍在，本次仅为FUNCTIONAL_STORAGE原型的板级键位调整。
