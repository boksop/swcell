# UART JSONL 协议（v1与兼容扩展v2）

UART_TX 单向输出，默认115200、8数据位、无校验、1停止位（8N1）、空闲高，LSB先发，无流控。PC 端不需要发送命令。每行是一个 ASCII JSON 对象，以单字节 LF (`0x0a`) 结束；无 CR、BOM 或额外调试文本。

以下TEST_消息为第一阶段v1协议，保持不变。每项测试顺序：TEST_START → 可选 FIRST_ERROR → TEST_RESULT。全部17项后输出一次 TEST_COMPLETE，然后保持空闲，重新配置FPGA可重跑。START 发送完毕才施加该测试序列；FIRST_ERROR 在测试全部检查结束后发送。下一项等待消息完成，UART 忙碌不会丢包。

所有64bit数值在FPGA线上为 **JSON字符串** `"0x"+16位小写十六进制`，避免FPGA十进制除法，也避免其他JSON消费者的浮点精度损失。快照向量为 `"0x"+1位十六进制`。Python 解析器也接受合法范围的 JSON 整数，以便离线工具使用；CSV 一律保存无符号十进制。

## TEST_START

```json
{"type":"TEST_START","module":"M11","test":"L01"}
```

`test` 为 L01–L08 或 F01–F09。RTL 内部 test_id 映射 L01–L08=`0x01..0x08`，F01–F09=`0x11..0x19`；序列化使用可读字符串。

## TEST_RESULT

```json
{"type":"TEST_RESULT","module":"M11","test":"F03","total_checks":"0x0000000000000060","error_checks":"0x0000000000000000","q_errors":"0x0000000000000000","qm_errors":"0x0000000000000000","status":"PASS"}
```

| 字段 | 含义 |
|---|---|
| total_checks | 本子测试已执行的有效采样/检查事件总数，不含准备步骤 |
| error_checks | 任一被使能输出出错的检查数；同一事件多位错只计一次 |
| q_errors | DL_Q 或 DFF_Q 出错的检查数，取决于当前测试 |
| qm_errors | DFF_QM 出错的检查数；Latch测试为0 |
| status | error_checks=0 为 PASS，否则 FAIL |

满足 `max(q_errors,qm_errors)<=error_checks<=min(total_checks,q_errors+qm_errors)`。上例为板级默认 F03 的96次检查。

## FIRST_ERROR

```json
{"type":"FIRST_ERROR","module":"M11","test":"F03","cycle":"0x0000000000012345","check":"0x0000000000000001","inputs":"0x8","actual":"0x6","expected":"0x0","mask":"0x6"}
```

首次错误在 logger 内锁住，后续错误只累加计数。`cycle` 是复位后系统周期编号（包含UART等待和准备时间），`check` 为本测试从1起的检查编号；不能把cycle解释为DFF外部时钟数。

| 向量 | 位定义（MSB→LSB） |
|---|---|
| inputs[3:0] | `{M11_DFF_CLK,M11_DFF_D,M11_DL_EN,M11_DL_D}` |
| actual[2:0] | 同步后的 `{M11_DFF_QM,M11_DFF_Q,M11_DL_Q}` |
| expected[2:0] | 参考模型的 `{QM,Q,DL_Q}` |
| mask[2:0] | Latch=001、DFF=110，1表示该位参与比较 |

输入与期望对应当前持有的步骤，实际值为同步流水线结果；长稳定窗口保证它们属于同一步骤。完整向量也包括本测试未比较的输出，分析错误时必须应用mask：`(actual ^ expected) & mask`。三个电路节点在整套测试前已初始化。该消息不替代最终 RESULT。

## TEST_COMPLETE

```json
{"type":"TEST_COMPLETE","module":"M11","tests":"0x0000000000000011","failed_tests":"0x0000000000000000","status":"PASS"}
```

`tests` 为完成的子测试数，M11为17；`failed_tests` 为失败子测试数，非总错误次数。任一子测试FAIL则整套FAIL。内部`suite_done`在本消息最后一个停止位发送后拉高。板上LED_Y熄灭，PASS点亮LED_G、FAIL点亮LED_R；状态保持至重新配置或断电重启。

## PC 保存和异常行为

`swcell_capture.py --port PORT --baud 115200` 在本地时区时间戳目录创建：

- raw.jsonl：原始字节原样保存，包括非法行、乱码、超长行、未结束片段。
- results.csv：列为 module,test,total_checks,error_checks,q_errors,qm_errors,status。
- metadata.json：时间、串口和波特率/回放源。
- capture_summary.json：有效消息数、RESULT数、非法行数、是否收到COMPLETE、是否有FAIL。

解析器支持跨读取/串口超时的分段行；行长超过8192字节会放弃解析至下一个LF，原始字节继续保留。重复JSON字段、越界数值、错误字段/状态和矛盾的计数会告警且不写CSV。串口断开或Ctrl+C时关闭文件；CSV每条结果flush，raw每块flush。未收到COMPLETE表示一次运行可能不完整；常见原因是监听晚于FPGA配置或连接中断。默认可连续采集多次重新配置，CSV有重复测试名时按原始START/COMPLETE边界区分运行。

退出码：0=采集/回放正常且已收到的测试无FAIL；1=有测试FAIL；2=打开/读取/解析错误，或离线回放缺少COMPLETE；130=用户Ctrl+C。`--stop-on-complete` 在收到首个完整COMPLETE后退出，默认持续监听。实际工作建议先打开串口再JTAG配置FPGA，避免丢失开头信息。未实现包序号、CRC或断点续传；回归检查完整顺序，但PC采集器本身只做行级协议校验，不保证检测所有整行丢包，应结合RESULT/COMPLETE数量复核。

## 协议v2：M11高速测试

v1消息不增加强制字段。检测到`protocol_version:2`才启用高速解析；UART物理格式仍为115200、8N1、ASCII JSONL。FPGA输出数值为`0x`加16位十六进制字符串，版本号和名义电压等编译常量可为普通JSON数值。Python校验后转为无符号整数。

每个静态镜像运行一次，顺序为`SWEEP_START → PHASE_RESULT或FREQ_RESULT → 可选ERROR_SNAPSHOT → SWEEP_COMPLETE`。高速引擎与UART独立运行，结果冻结后才传输；START发送过程中可以已经开始测量。SWEEP_COMPLETE只结束当前镜像/点，整轮多镜像扫频由主机汇总，不代表所有频率已经完成。

| 消息 | 含义 |
| --- | --- |
| SWEEP_START | 当前镜像配置，status=RUNNING；此时计数可能为0 |
| PHASE_RESULT | 短相位扫描点，Q/QM分别统计 |
| FREQ_RESULT | 所选采样组合的长测；失锁/超时也以本类型报告ABORTED |
| ERROR_SNAPSHOT | 首次错误的配置、lane、采样编号、PRBS状态及预期/实测 |
| SWEEP_COMPLETE | 当前镜像点结束，状态保持至下次配置 |

| 字段 | 定义与单位 |
| --- | --- |
| module、device、test、fpga_version | M11、74LVC1G157、测试名及固件标识；固定序列另由pattern区分 |
| frequency_hz | 配置的DFF CLK频率，不伪装为仪器实测 |
| d_phase、q_sample_phase、qm_sample_phase | 逻辑相位索引，单位为turn/16；Q/QM为0..15 |
| d_phase_mdeg、q_phase_mdeg、qm_phase_mdeg | 实际量化后的逻辑配置角度，单位毫度；不包含板外延迟 |
| pattern | 0=全0、1=全1、2=0101、3=0011、5=PRBS31 |
| requested_bits | 目标有效检查数 |
| total_bits、qm_total_bits | Q、QM实际检查数，正常完成时均等于requested_bits |
| q_errors、qm_errors | 各自错误次数，可同时发生，不直接相加当成错误周期数 |
| q_start_state、qm_start_state | 各自首个有效样本对应的31bit序列标签；记录预热后的实际起点 |
| q_first_error_cycle、qm_first_error_cycle | 各lane从1起算的有效样本编号；无错为0 |
| q_first_state、qm_first_state | 各路首次错误的序列状态 |
| first_error_cycle | 两路首次错误中较小的有效样本编号；不等于跨相位绝对时间戳 |
| first_error_lane | 0=无错误、1=Q、2=QM；编号相同优先Q |
| first_error_expected、first_error_actual | first_error_lane对应的单bit值，以64bit十六进制封装 |
| prbs_state | first_error_lane对应的序列状态 |
| voltage_v、temperature_c、pcb_delay_ns | 当前为null；允许有实测值时须给对应`*_source:measured`来源标记 |
| voltage_nominal_v | 名义测试条件3.3，非仪器读数 |
| idelay_tap | 当前未使用IDELAY，为null |
| status | RUNNING、PASS、CAPTURE_ERRORS、ABORTED；主机还可记录UNSUPPORTED、BUILD_ERROR、TRANSPORT_ERROR、NO_VALID_CAPTURE_WINDOW |

CAPTURE_ERRORS表示某个采样配置观测到错误，不能直接断言DUT失效。FPGA实现失败的配置不下载，主机在独立`host_events.jsonl`记录UNSUPPORTED/FPGA_TIMING，包含source=host；不往UART原始字节文件中插入伪FPGA消息。时钟失锁/运行超时记ABORTED，不能参与零错误频率判断。

扫描后未能选定Q/QM组合时，主机还写入`test:SCAN_SUMMARY`的FREQ_RESULT：全部被FPGA实现拒绝则为UNSUPPORTED，存在基础设施异常则保留对应状态，已测点不足以形成窗口则为NO_VALID_CAPTURE_WINDOW。此记录`selection_valid:false`、执行位数0，不是FPGA长测；CSV将未选定的采样相位留空。JSON为复用整数格式保留的相位0不可解释为实际选择。扫描汇总不重复计入配置点数量，完整逐点结果仍在phase_sweep.csv。

所有v2消息采用相同完整配置/计数字段，便于独立解析和追溯。ERROR_SNAPSHOT包含完整配置及上述首次错误字段；Q/QM采样相位不同，不能将两个lane的首次错误状态当成同一瞬间的并行波形。未来BRAM缓存可接每路error_event扩展。

`swcell_capture.py`收到v2结果时保留raw并生成phase_sweep.csv、frequency_sweep.csv、summary.json及图表；原v1的results.csv继续保留。单点使用`--stop-on-complete`会在该点SWEEP_COMPLETE后退出；多镜像请使用`swcell_sweep.py`，它对每点的START/RESULT/COMPLETE和配置标识做完整性核对。

### Phase 2B 独立首错扩展（固件 m11_hs_v2_2）

协议版本保持2；保留全部既有字段，额外输出四个64bit十六进制字符串字段：
`q_first_expected`、`q_first_actual`、`qm_first_expected`、`qm_first_actual`。
有效值为0或1，各自对应 `q_first_error_cycle` 和 `qm_first_error_cycle`。
某路错误计数为0时，该路首错字段不代表有效快照。原有合并首错字段继续表示两路本地检查序号较小的一次（相同则Q优先）；两路相位不同，因此本地序号不是一个已标定的共同物理时间戳。

新版 Python 接收旧 v2 时允许缺少这四项；Phase 2B 自动扫描要求新固件完整输出，防止把另一通道的快照误当作当前扫描轴的首错。独立扫描、恢复和数据文件见 [Phase 2B](phase2b.md)。
