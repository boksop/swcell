# M20-300 ISA v0.1 正式冻结规范

冻结日期：2026-10-28（Asia/Shanghai）。**ISA ID：`M20-300-ISA-0.1`**。

本规范冻结已通过 V0 验证的程序可见语义，不改变既有机器码。历史来源标识为 `M20-300-ISA-0.1-software`，在 Python 的 `LEGACY_ISA_VERSION` 中保留；[V0 工具文档](M20_300_isa_v0_1.md)、[V0 验证记录](M20_300_software_validation_v0_1.md)及历史证据中的旧标识仍表示当时生成的记录，不能改写历史数据来统一版本名。

配套机器规则：[isa_v0_1.json](isa_v0_1.json)，schema 版本 1。冻结编码、算术、标志、访存、退役、复位、HALT/TRAP；**不冻结微架构、状态编码或执行周期**。当前 V1 使用独立的 `M20-300-V1-TIMING-0.1` 性能验证契约。后续变更 ISA 语义必须明确评审并版本化；仅改微架构也必须更新受影响的时序/性能契约、测试和报告，不能沿用已失效的周期预算。

## 1. 状态、地址与存储器

|程序可见状态|宽度|含义|
|---|---:|---|
|PC|12 bit|指令字地址，正常顺序更新按模 4096 回绕|
|AR|8 bit|间接 RAM 地址；INCAR 按模 256 回绕|
|A|4 bit|累加器，算术写回低 4 位|
|Z|1 bit|最后一次明确更新 Z 的结果是否为 0；不是随时反映 A|
|C|1 bit|加法进位、减法无借位或移位移出位；由指令明确更新|
|GPO|4 bit|OUT 写入的逻辑输出值|

程序可见状态共 **30 bit**。当前 V1 另预算 3 bit `uSTATE`，核心状态边界共 **33 bit**；`uSTATE` 的位宽及资源属于实现审计，具体 8 状态编码不是 ISA 的一部分。HALTED/TRAP 可由控制状态表示，不添加隐藏的核心状态位。B/T/IR/LR、硬件栈、硬件 CALL/RET、8-bit ALU、游戏加速器均不在本架构内。验证计数器、trace、ROM 有效范围和调试捕获寄存器属于测试层，不得偷偷并入 CPU 核心或用来帮助执行指令。

- ROM 逻辑空间 `4096 × 16 bit`，每条指令恰好一个 word；PC、跳转目标和 `.org` 都以 word 寻址，不能按字节解释。
- RAM 逻辑空间 `256 × 4 bit`；每地址一个 nibble，不做隐含的打包读改写。直接地址来自指令低 8 位，间接地址来自 AR。
- `.bin` 每 word 低字节在前；`B123` 对应字节 `23 B1`。`.memh` 每行四个十六进制字符，首行为 PC=0。
- CPU 复位不初始化外部 RAM。软件夹具或测试平台初始化不构成免费硬件清 RAM。
- 在当前无 IR 实现中，PC 在执行整个指令/RAM 事务期间保持，提交时才更新。ROM 数据稳定及总线边沿必须另由 RTL/存储器模型验证，不能由原子 Python 指令执行证明。

## 2. 完整合法编码

`s=word[11:8]`，`n=word[3:0]`，`aa=word[7:0]`，`xxx=word[11:0]`。以下写为 0 的保留字段必须全 0；不允许截断或忽略非零保留位。

### 2.1 立即数和 AUX

|编码|指令|操作|Z|C|
|---|---|---|---|---|
|000n|LDI n|A←n|结果为 0|保持|
|100n|ADDI n|A←A+n|结果为 0|加法进位|
|200n|ADCI n|A←A+n+旧 C|结果为 0|加法进位|
|300n|SUBI n|A←A−n|结果为 0|无借位|
|400n|SBCI n|A←A−n−(1−旧 C)|结果为 0|无借位|
|500n|ANDI n|A←A AND n|结果为 0|保持|
|600n|XORI n|A←A XOR n|结果为 0|保持|
|7000|SHL|A←(旧 A<<1) AND 15|结果为 0|旧 A[3]|
|7100|SHR|A←旧 A>>1，最高位补 0|结果为 0|旧 A[0]|
|7200|NOT|A←旧 A XOR 15|结果为 0|保持|

立即数 major 0..6 的 bits[11:4] 必须为 0；AUX 的 low8 必须为 0，子操作 3..F 保留。移位只有单步逻辑移位，无隐含 rotate-through-carry。

### 2.2 RAM：直接 `8saa`，间接 `9s00`

间接编码的 low8 必须为 0，不提供位移，不自动修改 AR。

|s|指令|操作|A 写回|Z|C|RAM 事务|
|---|---|---|---|---|---|---|
|0|LD|A←RAM[address]|是|结果为 0|保持|读一次|
|1|ST|RAM[address]←A|否|保持|保持|写一次|
|2|ADD|A←A+RAM[address]|是|结果为 0|加法进位|读一次|
|3|ADC|A←A+RAM[address]+旧 C|是|结果为 0|加法进位|读一次|
|4|SUB|A←A−RAM[address]|是|结果为 0|无借位|读一次|
|5|SBC|A←A−RAM[address]−(1−旧 C)|是|结果为 0|无借位|读一次|
|6|CMP|按 A−RAM[address] 设置标志|**否**|差的低 4 位为 0|无借位|读一次|
|7|AND|A←A AND RAM[address]|是|结果为 0|保持|读一次|
|8|XOR|A←A XOR RAM[address]|是|结果为 0|保持|读一次|
|9|OR|A←A OR RAM[address]|是|结果为 0|保持|读一次|

子操作 A..F 保留。ST 不隐含一次 RAM 读；trace 中的 `previous` 只是测试平台观察，不应计入读事务或要求真实 SRAM 执行读改写。所有 RAM 指令保持 AR。RAM/ROM 后端是外部资源，不能修改退役语义或代替 CPU 执行游戏操作。

### 2.3 AR、跳转、IO、系统

|编码|指令|操作|Z/C|
|---|---|---|---|
|A00n|ARL n|AR[3:0]←n|保持|
|A10n|ARH n|AR[7:4]←n|保持|
|A200|MOVARL A|AR[3:0]←A|保持|
|A300|MOVARH A|AR[7:4]←A|保持|
|A400|MOVA ARL|A←AR[3:0]|保持|
|A500|MOVA ARH|A←AR[7:4]|保持|
|A600|INCAR|AR←AR+1，模 256|保持|
|Bxxx|JMP target|PC←target|保持|
|Cxxx|JZ target|Z=1 时 PC←target，否则 PC+1|保持|
|Dxxx|JC target|C=1 时 PC←target，否则 PC+1|保持|
|E000|IN0|A←逻辑六键掩码的 bits[3:0]|保持|
|E100|IN1|A←逻辑六键掩码的 bits[5:4]，高 2 位补 0|保持|
|E200|OUT|GPO←A|保持|
|F000|NOP|无数据状态修改，PC+1|保持|
|F100|HALT|正常提交一次，PC+1，进入停止执行|保持|

ARL/ARH 的 bits[7:4] 必须为 0；其余 AR 指令 low8 必须为 0。AR 子操作 7..F、IO 子操作 3..F、SYS 子操作 2..F 全部保留；合法 IO/SYS 指令 low8 必须为 0。

除列出的写目标外，指令保留其它数据状态。**IN0/IN1 和 MOVA ARL/ARH 即使改变 A，也保持旧 Z/C**。输入极性、异步同步、机械消抖和采样边沿属于板级/实现契约，不在 ISA 中假定某种最终 PCB 引脚。GPO 仅定义 4 位逻辑值，外设连线由板级文档另定。

合法编码共 **15015**：立即数 112、AUX 3、RAM 直接 2560、RAM 间接 10、AR 37、跳转 12288、IO 3、SYS 2；其余 **50521** 个 word 全部 TRAP。未提供 DECAR、ORI、JNZ/JNC、CALL/RET 或隐含扩展字。不能为保留码添加快捷行为。

## 3. 算术和标志的精确定义

算术使用**未截断整数**判断进借位，再将结果取模 16。所有操作数和旧 A 均为 0..15，旧 C 为 0/1。

```text
ADD/ADDI: carry_in = 0
ADC/ADCI: carry_in = old_C
SUM = old_A + operand + carry_in
A_next = SUM mod 16
C_next = (SUM >= 16)
Z_next = (A_next == 0)

SUB/SUBI/CMP: borrow_in = 0
SBC/SBCI: borrow_in = 1 - old_C
DIFF = old_A - operand - borrow_in
result = DIFF mod 16
C_next = (DIFF >= 0)          # 1 表示无借位
Z_next = (result == 0)
A_next = old_A for CMP else result
```

LDI/LD/ANDI/AND/XORI/XOR/OR/NOT 仅更新 Z，保持 C；SHL/SHR 按第 2 节更新 Z 和移出位 C。ST、全部 AR_CTRL、跳转、IO、NOP/HALT 均保持 Z/C。A/Z/C 的写使能彼此独立，不能因 A 写回而无条件更新 Z，也不能因 CMP 不写 A 而跳过标志更新。

## 4. PC、提交与停止语义

- 正常退役只发生在指令全部效果完成的提交边界，一条合法执行的指令只退役一次。退役记录观察当前指令的 PC/word、提交后状态和 `next_pc`，不能在 PC 更新后误采样下一条 ROM 数据。
- 非跳转和未取分支的下一 PC 为 `(old_PC+1) AND 0xFFF`；已取分支为 12-bit 绝对 word 地址。PC=FFF 的普通指令下一地址为 000。
- RAM 指令提交包含与其对应的唯一一次读/写事务；PC 在 RAM 事务结束前不提前更新。不允许重复 ST、读写冲突、非法字发起写或复位期间写 RAM。
- HALT 退役一次，下一 PC 正常递增，A/AR/Z/C/GPO 和 RAM 保持；随后不再取指、退役或发起 RAM 事务，直到复位。HALT **保持 GPO**，不强制把当前值改成复位值。
- 非法/保留 word 进入 TRAP，不退役，PC/A/AR/Z/C/GPO/RAM 均保持，禁止 RAM 事务并停止正常执行，直到复位。TRAP 的控制状态变化不是一次普通指令退役。
- 指令、复位、HALT/TRAP 的具体时钟边沿和控制状态编码属于微架构设计，不由本节额外冻结。

## 5. 复位

|状态|复位值|
|---|---|
|PC|000|
|AR|00|
|A|0|
|Z|1|
|C|0|
|GPO|8|

复位不退役、不访问或清除外部 RAM，并从 HALT/TRAP 恢复到可以执行的状态；数据初始值必须与上表一致。正常硬件入口为 PC=0。Python 的 `pc=` 非零构造参数仅是验证入口，`reset(clear_ram=True)` 仅是夹具操作，不扩展核心复位能力。复位有效极性、同步/异步实现、保持时间与离开复位的稳定周期由实现文档规定。

## 6. FAULT/UNMAPPED_ROM 的范围

**FAULT 不是新增的 CPU 状态、指令或硬件接口。** Python 为有限长度镜像保存了“地址是否已加载”的元数据：访问镜像长度外的地址时停止解释，标记 `FAULT/UNMAPPED_ROM`；PC 和数据状态不变、不退役。RTL 仿真可由 ROM 模型/外部检查器的有效范围 sideband 识别同类配置错误，由测试平台停止并报告，不能把 sideband 引入执行数据通路来增加核心状态。

真实 ROM/NOR 或常规 FPGA ROM 通常只在有效的 12-bit 地址上返回数据字；CPU 核心根据该 word 译码。已加载的 `16'hFFFF`、`.org` 的 FFFF 空洞、未加载区被仿真填成 FFFF 时，核心看到的始终是非法编码并 **TRAP**，不能因数值 FFFF 伪造 FAULT。若检查器开启映射范围检查，它可在消费填充值前先报告环境层 UNMAPPED_ROM；必须在差分配置中明确选择相同模式。

后续若要添加硬件总线异常、访问有效信号或核心 FAULT 状态，需要单独评审接口、状态位和资源成本；本次没有批准或实现这些新增硬件。

## 7. 当前 V1 时序验证 profile（不属于冻结 ISA）

Profile ID：`M20-300-V1-TIMING-0.1`，与 V0 当前解释器计费兼容。

|类别|基础模型微周期|口径|
|---|---:|---|
|普通合法指令|2|含 taken/not-taken 分支及一次 HALT|
|RAM 合法指令|5|FETCH_WAIT、EXEC、MEM_SETUP、MEM_ACCESS、MEM_RELEASE|
|非法 TRAP|2|计执行成本，不退役|
|UNMAPPED_ROM|2|仅软件/仿真异常的模型成本，不要求新增核心状态|
|RESET|1|单独记录的复位入口，不混入执行指令成本|

正常指令路径满足 `cycles=2*retired+3*(ram_reads+ram_writes)`；异常成本另加，`total_cycles=reset_cycles+cycles`。`rom_reads` 每次取指尝试计一次，包含解释器的非法/未映射尝试，不等于真实异步 ROM 的电平读取次数。ST 的调试 previous-value 查询不算 RAM 读。

当前建议 8 状态 RESET/FETCH_WAIT/EXEC/MEM_SETUP/MEM_ACCESS/MEM_RELEASE/HALT/TRAP，控制位预算 3；**状态数量、编码和具体微架构不是 ISA 冻结项**。本轮 V1 必须验证所选 profile 的 2/5 契约；若未来改为其它执行周期或加入 WAIT，需要独立版本化性能/总线契约并重新计量程序预算，不能默改计数来通过差分测试。profile 不代表物理 SRAM/NOR 的 tACC/tWE 已满足，也不证明 FPGA 或 157 的工作频率。

## 8. 机器规则表与独立验证

`isa_v0_1.json` 为工具可读取的规则表；45 个 `encoding_rules` 按 `(word & mask)==value` 匹配，不匹配即非法，规则互不重叠。mask/value/operand_mask 为 `0x` 前缀字符串，operand_shift 固定 0，枚举含义由表中的 `rule_fields` 说明。`mnemonic` 使用 Python 解码内部名称，例如 MOVA_ARL；`assembly` 给人读语法。`v1_cycles` 明确仅属于第 7 节 profile。

编码常量和声明性规则允许测试工具共享；ALU 的结果计算、标志和外部存储器事务检查必须保持独立，不得把同一待测 ALU 当作其自身 oracle。Python 执行器继续使用原 V0 实现，不通过 JSON 新增快捷行为；规则表由独立位掩码判定遍历 65536 个 word 验证，合法总数保持 15015。

V0 原始 Pong/Snake `.asm` 和机器镜像必须保持以下值；仅 ISA ID 变化不应改变二进制、逐指令状态、RAM 或动态周期：

|文件|SHA256|
|---|---|
|Pong `.asm`|`1b43020e4cdebac150041796e3898aeaac489efaf911496b39fc0dc5fe66933c`|
|Pong `.bin`|`e1029928d763ab5b0d21fe347687f52b326f545e9072f4c04365597439eead8c`|
|Snake `.asm`|`9d905bd0b8d567ae8d6f54250e220f85bdb72734324ba6025b3259e07b08dd13`|
|Snake `.bin`|`466cb149c8e5d6914d0b78dc8a3ec5074c77020edf880cedbd520b41b3376b98`|
|原 V0 `machine.py`|`421aa1526a21ad063de40a951eb9544e7f85f67f4163f30953013dcc997172e4`|

冻结本身只确定 ISA 契约；V1 RTL、总线边沿、差分、游戏 ROM 和资源审计必须另以实际测试记录验收，不能把本文件或 V0 Python PASS 当作 RTL PASS。
