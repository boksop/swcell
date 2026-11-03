# M20 FPGA功能原型规划

本文件只定义未来边界。本次未创建Vivado工程、RTL、XDC或程序文件，未运行综合/时序/下载。

## 1. L0–L6分层

|层|未来模块职责|真实CPU预算边界|
|---|---|---|
|L0|具体157电气单元、外部时钟/复位/负载模型|物理绑定；器件厂商/封装TBD|
|L1|`swc_ite2`等单路MUX组合原语（拟定名）|每实例1颗；当前库不存在，P1新建|
|L2|NOT/XOR/选择树、寄存器状态接口、DFF绑定|FF两MUX+CE/复位/写源另计|
|L3|4位ALU、分段寄存器、译码、等待/控制|全部显式进入CPU资源台账|
|L4|m20 CPU核心：ISA/微状态/总线相位|原型和最终CPU共用状态/控制定义|
|L5|CPU可见ROM/RAM、GPIO/键同步/写驱动控制|存储容量外置，但接口与同步/等待计入|
|L6|Pong/Snake机器码、软件回归、游戏检查|游戏逻辑由程序执行|
|AUX（不混入L0–L6预算）|FPGA时钟封装、装载器、UART、trace/比较器、OLED观察模型|只用于验证，单独网表层级/报告|

目录建议（**未来**）：通用MUX库置`rtl/common/ite/`；M20数据/控制在`rtl/modules/m20/`；独立模型`sim/models/m20/`；CPU TB/程序场景`sim/m20/`；新工程封装`fpga/xc7k325t/m20/`；软件工具`host/python/m20/`。不得为了CPU测试重写M11顶层或复用旧.xpr产生混合工程。

## 2. 两种状态绑定

|模式|组合逻辑|状态|目标|
|---|---|---|---|
|FPGA功能原型|结构化ITE网络，综合可映射LUT但保留可审计中间表示|原生posedge FF、统一enable/reset语义|验证ISA、微状态、总线及程序|
|真实MUX结构|同一组合网络|恢复2-MUX反馈主从DFF及显式CE/复位网络|独立时序/门级仿真、PCB实现和物理审计|

不把组合反馈环塞回FPGA fabric来“实现真实锁存器”；反馈结构用于外部模型/真实PCB。FPGA原生FF只是状态后端，不能顺手改变取指、分支、等待周期或加隐藏寄存器。绑定差异必须经过同程序退役状态/内存/IO等价检查，并保留物理模型允许的传播时间。

CPU只允许外部存储器模型占用BRAM。游戏数组、控制表、微码、寄存器若额外放BRAM，必须作为架构变更评审；不能在原生FF模式偷偷用寄存器堆/硬加法器代替计数台账内逻辑。

## 3. 已有模块复用边界

|现有文件/能力|可复用|必须注意|
|---|---|---|
|swc_uart_tx / swc_json_packet_tx|调试字节与包发送握手|不是CPU游戏外设；不能UART背压改变已运行程序的逻辑结果|
|swc_input_sync / swc_reset_sync|同步结构/属性方法|真实CPU的状态同步成本仍入预算；FPGA INIT不等于真实PCB复位|
|swc_test_logger|聚合统计/首次错误机制|需适配CPU宽状态，不截断为M11小向量|
|swc_snapshot_bridge|冻结后的快照握手|当前是保持done/payload至reset的一次性桥；持续逐指令trace需新请求/应答或FIFO，不能直接重复用|
|swc_prbs31|外部随机测试激励|仅AUX；不替游戏软件生成随机食物|
|Python JSONL/CSV经验|保存和离线分析模式|当前parse_record只接受M11/其测试名；未来增加M20解析器/协议版本，保留M11回归|

## 4. CPU时钟与控制

首版建议单50MHz系统域，CPU全部状态用统一`cpu_step`使能；计划有效微周期0.1/0.5/1/2/5MHz用于软件性能实验。它们是未来配置点，不是已支持或实测CPU频率。

STA默认仍按50MHz检查CPU路径，不能因step较慢而随意false-path。若难以闭合，另评审合法MMCM/BUFG低速域及CDC；不能新增无约束组合/Fabric时钟。实物CPU用真实时钟分配网络，不能把FPGA CE逻辑当免费实物时钟门。

单步只在受控微周期边界推进；暂停必须冻结同组CPU状态/等待计数和总线阶段，不留下无限WE低脉冲。建议运行态仅允许在指令边界、总线RELEASE后停机；微步调试若要暂停写周期，需专门定义物理安全策略，不能作为默认硬件暂停能力。

复位/加载ROM/RAM只在CPU保持复位/停止时进行。运行中主机写游戏数据不属于正常验收。启动后CPU自行从ROM000运行，不需要PC为每条指令服务。

## 5. 观察接口与证据

建议只读retire事件包含：序号、取指PC、opcode/扩展、next PC、A/B/AR/LR/Z/C、内存写地址/值、IO写、异常原因。取指PC可由AUX观察器在fetch阶段保存，不新增未计入真实CPU的“历史PC”寄存器。内部微状态波形可旁路抓取，但不能驱动期望CPU输出。

短程序允许每指令比对；游戏trace用AUX BRAM/FIFO、触发/摘要或离线仿真，不假设115200 UART可实时上传所有高速指令。FIFO满必须报告TRACE_OVERFLOW；不得丢轨迹后仍声称逐指令等价已完成，也不能为迁就UART把游戏核心偷偷切成每条指令由主机驱动。

OLED模型仅解码CPU发送的SPI，按控制器语义更新观察画面；六键由TB/host事件表驱动。参考游戏模型独立计算预期并比较，任何模型差异只报告，不能将预期帧回灌CPU。

未来M20 JSONL建议包含protocol/module/test/program_hash/isa_version/microarchitecture_version/clock_config/wait_config/retired/mismatches/status，另保存辅助层开关、MUX台账版本、bitstream/raw SHA和工具报告。未测电压/温度保持null，方案频率标为configured。

## 6. 新Vivado工程的未来门槛

从已确认part、系统输入条件新建独立M20构建入口；P6开始才运行`get_parts`及许可/器件支持检查。AMD的2026.1资源与许可说明不能代替本机实际安装器件包/许可证核验；本次不启动Vivado，也不声称2026.1.1已完成适配。

初次P6可只用已确认的时钟、复位逻辑和UART验证核心；外设未知时用AUX逻辑模型。真实OLED/六键外接前必须取得明确连接、电平及Bank兼容性，新增约束经过用户评审。不借用M11七个测点去猜CPU外设引脚。

未来报告须分列CPU、ROM/RAM模型、调试/时钟/AUX资源；逐配置保存综合、place/route、DRC、setup/hold/pulse、CDC和未约束路径。Vivado通过只证明该FPGA配置，不证明真实157 CPU时序。

资料：[AMD FDRE原生FF语义](https://docs.amd.com/r/en-US/ug953-vivado-7series-libraries/FDRE)、[AMD2026.1下载与许可变化](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2026-1.html)。这里仅引用原生FF/工具支持检查依据，没有执行或给出具体外设IO约束。
