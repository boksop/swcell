# M20候选ISA v0.1

**未冻结。** 下面给出可据以设计后续RTL/参考模型的指令语义；并不表示已经有汇编器、程序或CPU。默认完整游戏配置含LR与全部IO。

## 1. 编码、状态和周期规则

- 指令流按8位字节寻址，PC12，首字节`opcode[7:4] | field[3:0]`；所有数值为无符号，A/B为4位，AR8，运算模16/模256/PC模4096。
- 除C/D/E/F族外均1字节。分支/调用第一字节低nibble是目标高4位，第二字节是目标低8位；例`JMP 0x123`编码`C1 23`。不使用当前页隐含地址。
- 指令开始PC指向opcode；取指后内部PC先递增1。普通指令退役时PC=起点+1；未取分支PC=起点+2；已取分支PC=目标。跨FFF按模4096处理。
- C对ADD/ADC为carry-out；SUB/SBC/CMP对减法表示**无借位**。`SBC: A + (~operand & 15) + C`。无N/V标志；有符号判断须软件另实现。
- ADD/SUB/ADC/SBC/CMP更新Z、C；LDI/LD/IN/AND/XOR更新Z、保留C；SHR更新Z、C=A旧bit0；其它指令保留Z/C。CMP不改A。
- 内部K/T可被取指和地址微操作改变，不能被软件当参数；A/B/AR/Z/C不得被普通取指破坏。特别禁止PC递增使用B作临时结果。
- 基础取指/PC递增/译码为`F=10+W_R`周期。W_R、W_D、W_W为控制器选定的**附加**ROM读/RAM读/RAM写等待0..3；基础SETUP/SAMPLE或PULSE/RELEASE已经计入。不得再统一加一个“平均CPI”。

状态缩写：F取指；E普通执行；RD/WR各3态；AI为AR两段ADD/WRITE四态；J=保存高段+扩展ROM三态+目标PC三段（7）；SK=保存高段+扩展ROM三态+跳过操作数PC递增六态（10）；LC=PC复制LR三态+LR递增六态；RT=LR写PC三态。详见architecture的63态分组。

## 2. 主编码族

|编码|汇编/操作数|功能|状态/周期|硬件|游戏用途|
|---|---|---|---|---|---|
|0n|LDI n|A←n；Z更新|F,E；11+W_R|IR低半字、PASS_R|常数、显示控制值|
|1n|ADDI n|A←A+n|F,E；11+W_R|加法、ZC|坐标/计数|
|2n|ADCI n|A←A+n+C|同上|加法、进位选择|8位数高段|
|3n|SUBI n|A←A−n|同上|反相操作数、cin=1|边界/减计数|
|4n|SBCI n|A←A−n−(1−C)|同上|cin=C|多nibble借位|
|5n|ANDI n|A←A AND n|同上|AND|掩码、位图|
|6n|XORI n|A←A XOR n|同上|共享XOR|方向/LFSR|
|7n|ARL n|AR[3:0]←n|同上，ZC不变|地址分组写|固定变量地址|
|8n|ARH n|AR[7:4]←n|同上，ZC不变|地址分组写|RAM区域选择|
|90/91|IN 0/1|A←六键低4/高2（高2位补0）；Z更新|F,E；11+W_R|键同步、银行选择|输入/消抖|
|9F|HALT|关闭存储器活动；进入HALT，GPIO保持|进入11+W_R；以后不退役|状态机保持|单测终点/诊断|
|A0/A1|OUT 0/1|GPO←A / RSTn←A[0]|F,E；11+W_R|公共写回、GPIO使能|软件SPI/屏复位|
|Bn|扩展操作|见下表|见下表|见下表|RAM与寄存器操作|
|Cn ll|JMP hll|PC←(n<<8) OR ll|F,J；17+2W_R|T、ROM扩展、PC写|循环/状态机|
|Dn ll|JZ hll|Z=1取分支|取17+2W_R；未取20+2W_R|同上+Z判定|相等/循环结束|
|En ll|JC hll|C=1取分支|同上|同上+C判定|进位/无借位比较|
|Fn ll|CALL hll|LR←起点+2；PC←目标|F,LC,J；26+2W_R|LR12、T/K、共享ALU|叶级SPI例程复用|

`92..9E`、`A2..AF`是非法IO编码，退役前进入TRAP、不产生IO写；9F是唯一HALT特例，不是读端口15。TRAP保持到复位，观察口报告opcode和取指地址；观察口存储属于FPGA辅助，不另加真实CPU故障寄存器。

## 3. B扩展族（全为单字节）

|编码|汇编|语义|状态/周期|资源|实际用途|
|---|---|---|---|---|---|
|B0|MOVB A|B←A，标志不变|F,E；11+W_R|A+0→写回|暂存/两倍运算|
|B1|LD A,[AR]|A←RAM[AR]；Z更新，C保持|F,RD；13+W_R+W_D|RAM读总线直接写A|游戏变量/数组|
|B2|ST [AR],A|RAM[AR]←A；不自动增AR|F,WR；13+W_R+W_W|地址保持/写脉冲|身体/位图更新|
|B3|LDB [AR]|B←RAM[AR]；ZC保持|同读周期|RAM读直接写B|算术/比较操作数|
|B4|ADD B|A←A+B|F,E；11+W_R|4位加法|位置/动态地址|
|B5|ADC B|A←A+B+C|同上|进位|8位地址高段|
|B6|SUB B|A←A−B|同上|减法|碰撞差值|
|B7|SBC B|A←A−B−(1−C)|同上|借位|多nibble比较|
|B8|AND B|A←A AND B；Z更新C保持|同上|AND|占用位图掩码|
|B9|XOR B|A←A XOR B；Z更新C保持|同上|XOR|软件随机/逻辑|
|BA|CMP B|按A−B设置Z/C，不改A|同上|减法/写使能屏蔽|边界/自身碰撞|
|BB|SHR A|A←A>>1；C←旧A[0]，Z更新|同上|连线、结果选择|拆字段/软件LFSR|
|BC|MOVARL A|AR低nibble←A，标志不变|同上|地址分组写|动态指针|
|BD|MOVARH A|AR高nibble←A，标志不变|同上|地址分组写|动态指针|
|BE|INCAR|AR←AR+1模256，ZC/B不变|F,AI；14+W_R|共享ALU、K/T|数组相邻nibble|
|BF|RET|PC←LR，LR不变|F,RT；13+W_R|LR三段→PC|返回叶例程|

LD A不使用B作为读缓冲，否则`LDB [rhs]; LD A,[lhs]; CMP B`会丢掉rhs。读数据经公共RAM写回源直接进入A/B；该选择在预算中计数。

## 4. 组合指令、调用约束

|需求|可用序列 / 限制|
|---|---|
|比较立即数8|`ADDI 8`可以取得原A≥8的C但会改变A；需保值时MOVB/内存保存，或装B后CMP|
|非零分支|`JZ skip; JMP target; skip:`，4字节；不虚构独立JNZ编码|
|左移1/乘2|`MOVB A; ADD B`，A模16左移，C为原高位|
|OR|`A OR B = (A XOR B) XOR (A AND B)`，用RAM暂存；没有隐藏OR硬件|
|8位加减|先低段ADD/SUB，ST/LD不破坏C，再高段ADC/SBC；多字节标志规则显式|
|软件栈|可用AR/RAM构造，但本版无硬件栈；LR不能自动压栈|
|NOP|用跳至下一地址的JMP伪指令，或明确无副作用的程序结构；没有免费未分配opcode|

CALL仅有一个LR，没有深度计数器或自动嵌套保护。推荐调用图深度≤1：游戏主循环直接调用叶SPI例程，叶例程内部不CALL；其余辅助例程内联。嵌套CALL会覆盖LR，必须由汇编器静态检查或程序自行保存；不承诺硬件TRAP。复位LR=0，所以首次CALL之前RET定义为返回000。调用约定中A/B/AR/ZC可被**例程**破坏；CALL/RET指令自身不改这些寄存器。

## 5. Snake动态数组访问证明（仅汇编记法示例）

以下宏记法必须在P3展开为上表机器指令，不是已存在的汇编器功能。变量`ptr_lo=04`、`ptr_hi=05`，保存一个RAM地址；目标可能为身体表中的任意nibble。

```text
ARH 0
ARL 5
LDB [AR]       ; B=ptr_hi
ARL 4
LD A,[AR]     ; A=ptr_lo，不能覆盖B
MOVARL A      ; AR低段=ptr_lo
LDI 0
ADD B         ; A=ptr_hi
MOVARH A      ; AR现在是完整动态地址
LD A,[AR]     ; 真正的数组读取
INCAR
ST [AR],A     ; 示例相邻nibble写入；实际程序先提供正确新值
```

`body_base+2*index`由两nibble加法和乘2序列求得，存入ptr变量；没有固定地址“假数组”。占用位图地址/掩码同样由CPU计算。P3要求对0..63全部index生成、执行、读回，并检查边界BF→C0不越界。

## 6. 必须执行的ISA测试（未来）

穷举A/B=0..15、C=0/1的算术与逻辑；检测SBC的无借位定义；检测所有编码/非法IO、PC跨FFF、AR跨FF、taken/not-taken、CALL目标高位保存、LR返回地址+2、RET、HALT只退役一次。独立ISA模型不得共享RTL ALU函数、微状态或期望寄存器。程序ROM中每个opcode均由可追溯二进制清单确认，本次没有执行上述测试。
