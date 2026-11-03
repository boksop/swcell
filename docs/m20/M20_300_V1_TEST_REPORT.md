# M20-300 V1.0–V1.3 RTL 功能验证结果

日期：2026-10-29（Asia/Shanghai）。**本轮自动化验证通过到 V1.3：原 Pong/Snake 机器码已由真正的 M20 CPU RTL 执行，并与 Python 指令模型逐条一致。** 这是 RTL 仿真结果，尚非 FPGA/157 实物正式验收。

## 1. 验收范围与结论

|阶段|实际结果|证据|
|---|---|---|
|V1.0 ISA冻结|PASS，正式ID和45条机器规则；编码/标志/软件状态不变|[冻结规范](M20_300_ISA_FROZEN.md)、[规则JSON](isa_v0_1.json)、冻结测试|
|V1.1 CPU功能RTL|PASS，7份RTL、33个功能FF状态位，非工程编译/elaboration通过|[设计文档](M20_300_V1_RTL_DESIGN.md)、`xsim/compile.log`及3份elaborate日志|
|V1.2 指令与差分|PASS，完整编码/ALU单元、内存/复位、49个CPU指令场景|`xsim/{isa,memory,instructions}.log`、`instructions/comparison.json`|
|V1.3 游戏ROM|PASS，38场景，含boot、关键边界、连续64tick和内存适配|`xsim/games.log`、`games/comparison.json`及全部CSV/最终RAM|

ISA冻结不冻结微架构。本轮采用8状态和普通2/RAM5周期便于建立可信功能参考；以后可改变内部逻辑及周期，但必须保持ISA效果，并同步版本化周期profile、模型与测试。没有为300颗目标提前做复杂MUX共享，也没有宣称328颗预算已落实。

## 2. 环境、版本和运行命令

|项目|实际使用/来源|
|---|---|
|系统/工作区|Ubuntu24.04，`/home/boksop/swcell`|
|工具|Vivado Simulator **2026.1.1**，用户2026.1系列的补丁版；实际xvlog/xelab/xsim|
|工具目录|`/home/boksop/AMDDesignTools/2026.1.1/Vivado/bin`|
|Python|现有`build/venvs/python312/bin/python`；旧`.venv`未动|
|ISA ID|`M20-300-ISA-0.1`；历史来源`M20-300-ISA-0.1-software`保留|
|周期profile|`M20-300-V1-TIMING-0.1`，普通2/RAM5/reset1单列|
|TB时钟/精度|周期10ns，分辨率1ps；仅测试时基，不是实测CPU最高主频|
|Git|main尚无首个commit；本轮未暂存/commit/push或改分支|

实际完整入口：

```bash
sim/scripts/run_m20.sh
```

实际退出码0，末尾标记：

```text
RTL_DIFF_PASS instructions: 49 cases, 22223 events
RTL_DIFF_PASS games: 38 cases, 35108 events
M20_EVIDENCE_PASS sources=32 rules=45 python_tests=86
M20_V1_REGRESSION_PASS output=/home/boksop/swcell/build/m20_300/v1
```

运行方法/失败定位/数据协议详见[验证说明](M20_300_V1_VERIFICATION.md)。所有相对证据路径以下均以`build/m20_300/v1/`为根。

## 3. 文件和状态位核对

|RTL模块|作用|功能状态位|
|---|---|---:|
|`m20_pkg.sv`|内部常量|0|
|`m20_decoder.sv`|严格保留字段检查及操作类别|0|
|`m20_alu.sv`|四位算术/逻辑，独立A/Z/C写使能|0|
|`m20_pc.sv`|PC12、退役更新|12|
|`m20_ar.sv`|AR8、退役更新|8|
|`m20_control.sv`|当前uSTATE3|3|
|`m20_cpu_core.sv`|A4、Z1、C1、GPO4；组合总线/retire|10|
|**合计**|没有IR/B/T/LR、硬件栈或游戏加速状态|**33**|

另新增`sim/m20/`的ROM/RAM模型、共用fixture、三个TB和Tcl，`sim/scripts/run_m20.sh`，Python的`rtl_regression.py`及冻结/比较器测试。软件解释器和原Pong/Snake核心算法不改；ISA Python仅正式版本标识/历史来源元数据调整。

33位是当前行为RTL源码中功能时序状态的精确核对；retire/debug是组合导线，TB计数器/捕获寄存器不是CPU功能硬件。未执行综合，因此不以综合FF/LUT报告冒充结构证明。

## 4. 实际测试结果

|测试项|规模/覆盖|结果|证据|
|---|---|---|---|
|全部Python回归|86项：原77＋冻结6＋差分工具3；5.541s|PASS|`python_tests.log`|
|RTL编码合法性|65536 word；15015合法/50521非法|PASS|`xsim/isa.log`|
|RTL ALU独立数学oracle|64内部操作值×16A×16operand×2C=32768向量|PASS|`xsim/isa.log`|
|运行中复位与内存|7组检查：active-WE阻断、已写不回滚、RAM保持、延迟读、HALT/TRAP恢复、映射元数据|PASS|`xsim/memory.log`|
|CPU指令差分|49场景，22223事件，51193执行微周期|PASS|`instructions/comparison.json`|
|游戏CPU差分|38场景，35108事件，115651执行微周期|PASS|`games/comparison.json`|
|总计差分|87场景，57331事件：57314正常退役＋17 TRAP|PASS|两个comparison及`verification.json`|
|实际指令规则覆盖|45/45，包含所有立即数/直接/间接/AR/分支/IO/SYS类别|PASS|`coverage.json`|
|最终RAM|所有87场景均比较全部256个nibble，包括scratch与未访问地址|PASS|每场景`expected_ram.memh`与`ram.final.memh`|
|原文件保护|308个既有文件＋V0解释器/汇编器/游戏/架构＋Git index指纹一致|PASS|`baseline.json`、`verification.json`|
|综合/布局布线/STA/硬件|本次明确不执行|NOT_RUN|没有新bitstream或板级工程|

指令套件包括：分段装入ROM的全部4-bit立即数A/n/旧C组合，RAM十种子操作的直接/间接边界，全256地址，初始Z/C四组合下全部64按键，AR回绕/动态装入，PC FFF→000，taken/not-taken分支，16种代表性非法字及物理未加载FFFF、16个固定种子随机程序，异步延迟和同步RAM适配。全非法字的RTL覆盖是译码穷举；CPU进入TRAP的差分执行为17个代表场景，不把它夸大为50521次完整CPU异常运行。

独立A/Z/C使能已覆盖全部八种“值改变/不改变”组合：例如A变而Z/C保持12274次，A保持但Z/C同时变27次，A保持且Z变/C保持872次；它们是观测值变化统计，不等同于硬件写使能次数。CMP和IN/MOVA的写使能另由ALU单元逐向量检查。

## 5. 每类指令的实际RTL微周期

以下所有指令都在真实CPU轨迹中执行，监视器独立累计边沿数，并逐条与参考模型比较；45条编码规则的直接/间接形式均已覆盖。

|指令（完整列举）|实际执行微周期|退役/写回|
|---|---:|---|
|LDI、ADDI、ADCI、SUBI、SBCI、ANDI、XORI|2|EXEC边沿提交|
|SHL、SHR、NOT|2|EXEC边沿提交|
|ARL、ARH、MOVARL、MOVARH、MOVA ARL、MOVA ARH、INCAR|2|EXEC边沿提交；AR/IO类保持标志|
|JMP、JZ、JC（taken/not-taken）|2|EXEC边沿更新PC|
|IN0、IN1、OUT|2|EXEC提交，Z/C保持|
|NOP、HALT|2|HALT只正常退役一次，PC递增后停止|
|LD、ST、ADD、ADC、SUB、SBC、CMP、AND、XOR、OR（直接）|5|MEM_RELEASE退役；ST真实写在前一MEM_ACCESS边沿|
|同上十种RAM操作（`[AR]`间接）|5|同上；地址无自动递增|
|非法字TRAP事件|2|不正常退役，保持PC与软件数据状态，无RAM事务|
|离开reset的初始化状态|1，单列|RESET→FETCH_WAIT，不计入上述执行周期|

普通指令没有额外pipeline退役周期。RAM读OE覆盖SETUP/ACCESS/RELEASE，统一在RELEASE写A/Z/C，因此没有RAM结果临时寄存器；无IR时PC/ROM和数据状态在整次事务内保持。所有正常轨迹符合`cycles=2×retired+3×RAM事务数`，TRAP事件另计2。

## 6. Pong/Snake的真实RTL执行结果

ROM容量4096×16，各游戏单独装载；源文件/机器码保持V0版本：

|程序|ROM word/有效字节|占容量|本轮关键RTL场景|
|---|---:|---:|---|
|Pong|168 / 336|4.10%|boot、墙/球拍、得分/进位/回绕、双球拍输入、64tick连续、内存延迟|
|Snake|368 / 736|8.98%|CPU清RAM、身体环/位图、尾格、自撞、增长、63探测、64封顶、重启、64tick连续、内存延迟|

|真实RTL场景|指令/事件|RAM读|RAM写|执行微周期|结果|
|---|---:|---:|---:|---:|---|
|Pong boot到首次tick入口|19|0|15|83|PASS|
|Pong 普通tick|65|15|9|202|PASS|
|Pong 墙反弹＋双球拍移动＋分数进位|94|21|19|308|PASS|
|Pong boot＋连续64tick|4252|924|649|13223|PASS|
|Snake 完整清RAM及boot|1862|0|269|4531|PASS|
|Snake 普通tick|256|82|56|926|PASS|
|Snake 合法进入旧尾|274|86|57|977|PASS|
|Snake 长度64封顶|225|73|51|822|PASS|
|Snake 重启（含重新清RAM）|1869|0|271|4551|PASS|
|Snake 62→63节，63次食物探测|4152|1021|684|13419|PASS|
|Snake boot＋连续64tick|18778|5266|3957|65225|PASS|

单tick从tick入口到tick_done前，不含其后NOP/JMP的4周期；连续记录包含实际boot和循环开销，不能拿V0“排除boot”的512tick统计直接相减。连续模式仅提供按键，TB没有推进球/蛇、调用食物算法或修正RAM。所有指令后PC、机器字、next_pc、A/AR/Z/C/GPO、RAM事务、单条与累计周期一致，结束时完整RAM也一致。

63探测例沿用V0连通身体夹具；真实RTL执行4152条指令后，在(0,4)找到空格，长度62→63、分数FF→00，全部与Python相同。以上是核心算法测试，没有OLED输出或完整游戏帧率结论。

## 7. 内存时序和异常边界

本轮通过的模型组合为：零延迟基准、ROM异步1.5ns/RAM异步2ns，以及RAM注册读适配（内存单元含2ns返回延迟）。没有WAIT；同步ROM/最终BRAM IP未验证。真实外部SRAM/NOR的访问时间、WE最小脉宽、建立保持、三态、电平、PCB延迟尚未验证。10ns仿真时钟只用于检查数字执行关系，不能称为157 CPU的100MHz性能测试。

CPU只接ROM word，FFFF是实际TRAP。Python短镜像FAULT仍为软件范围诊断；仿真ROM用mapped sideband区分范围，但没有给CPU偷偷增加FAULT位/状态。复位前已发生的外部ST写无法回滚；本轮只保证尚未到写边沿的请求被reset阻断，RAM不会因CPU复位被清零。

## 8. 证据与校验

|对象|SHA256|
|---|---|
|冻结规范MD|`d908221a5fe52a7f315e8b73a6c0ce4a70bc4fd104c42f2f561d0c8e712ef99d`|
|机器规则JSON|`3d22bbcb03d0714020627d72a3ea93c44aebe7cf796bb1c2d3a2ef263059cdaa`|
|正式ISA Python源|`362fbf4dc25604328ecc2676edb86469f4be6c312922ea45c0573037f6dc16a4`|
|Pong机器镜像（小端、未填充）|`e1029928d763ab5b0d21fe347687f52b326f545e9072f4c04365597439eead8c`|
|Snake机器镜像（小端、未填充）|`466cb149c8e5d6914d0b78dc8a3ec5074c77020edf880cedbd520b41b3376b98`|

`inputs_manifest.json`与`verification.json`保留32份RTL/TB/工具/参考源文件指纹，确认编译前后未变；每case metadata关联ROM哈希。完整原始CSV/预期JSONL/夹具/最终RAM，以及`isa.wdb`、`memory.wdb`、`instructions.wdb`、`games.wdb`均在build输出目录，Git忽略。源码/文档与可再生证据分离，长期审计应额外归档该目录。

本机xelab提示`LIBRARY_PATH`环境变量可能影响C编译器；实际3份snapshot构建及XSIM全部成功，没有工具错误。该提示不被当成RTL失效，也没有为消除提示而改变全局环境。一次早期语法检查产生的M20根目录缓存经核实后已移入build保留，原旧`.Xil`未动；正式脚本全部在build编译。

## 9. 资源结论与下一步

原预算仍为328：66颗storage等价MUX＋262颗组合/保持/使能估算。V1只确认33个功能状态位，普通DFF暂按2颗157时基础storage为66；ALU40、PC/AR选择和增量、复位12、译码/控制70等仍未结构化准确计数，可能有明显偏差。不能用LUT数换算，不宣称完整PCB为328颗。

FPGA/仿真ROM/RAM、监视/trace/计数/断言属于验证辅助；真实存储器、SRAM方向/三态驱动、时钟/复位/按键同步及PCB辅助应另列BOM。六键同步24＋复位同步4的157等价也不隐藏到核心预算外作为免费物理能力。详表见设计文档资源节。

V1现在可作为后续结构化/共享优化的功能参照；后续优化应继续对照Python与本RTL退役效果。下一阶段须另行完成MUX结构网表/逐项计数、同步ROM/BRAM与物理存储器适配、OLED/SPI/消抖/tick计时，以及之后独立的FPGA工程/STA/板级验证。本轮终点已达V1.3，不提前展开这些工作。
