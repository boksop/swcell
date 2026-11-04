# Snake 固定乱序食物 v0.1

这是独立的软件变体；原 `software/m20_300/snake.asm` 及原参考 ROM 不变。

- 16×8 棋盘的128格各出现一次；顺序固定，循环使用，不是运行时随机数。
- 初始食物为(10,3)；吃到后依次考虑(2,6)、(13,1)、(5,5)、(1,0)等。
- CPU读取身体占用位图，候选在蛇身上就继续查下一项。索引127之后回到0。
- 保留原64格身体环及满员处理；最多检查65个候选，异常位图仍走原错误处理。
- RAM 0x22/0x23保存表索引，CPU状态仍33位，ISA和477组合MUX均不变。

当前ISA没有ROM数据加载指令，因此位置表通过CPU条件分支及立即数编码，不能简单将FPGA数组输出代替CPU计算。程序占1295/4096个16位ROM字，原版为368字；`tick_done=313`，必须通过构建参数传入，不能沿用原版316。

`food_table.json`是可读表；`snake_shuffled.asm`和填充4096字的`.memh`为生成文件，来源为[生成器](../../../../tools/m20/v3_snake_shuffled.py)。重新生成必须使用新目录：

```bash
build/venvs/python312/bin/python tools/m20/v3_snake_shuffled.py --output build/snake_shuffled_reproduced
bash sim/scripts/run_m20_v3_snake_shuffled.sh
```

命令从仓库根目录执行。具体仿真、硬件结果及构建/回退方法见[验证说明](../../../../docs/m20/M20_V3_SNAKE_SHUFFLED.md)。
