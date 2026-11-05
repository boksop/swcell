# M20 V3.1 验证方法与边界

所有新输出在build/sim/m20_v31、build/fpga/m20/autonomous和results/M20_V31；旧V3工程、ROM、bit与失败证据不改。新平台只用FUNCTIONAL_STORAGE，不重启STRICT_MUX工作。

## 自动化入口

```bash
build/venvs/python312/bin/python -B tools/test/run_python_tests.py
bash sim/scripts/run_m20_v3_core.sh
bash sim/scripts/run_m20_v31_units.sh
bash sim/scripts/run_m20_v31.sh
build/venvs/python312/bin/python -B tools/m20/v31/verify_relocation.py --output build/m20_v31/relocation_new.json
```

普通Python套件含原170项和V3.1的9项；验证冻结指纹、可重复生成、跳转/软件返回ID边界、脏RAM启动、抖动/单次触发/松开/长按、游戏重定位规则、SPI反例和UART范围。旧V3核心回归不改夹具/期望，覆盖65536译码、50521非法TRAP及恢复、ALU、PC/AR边界、49指令＋38游戏场景、访存/运行复位。

unit入口逐一执行：

- 六个GPIO单系统拍脉冲仍按正确2FF位序出现，16组GPO直连；没有FPGA消抖/事件缓存。KEY4不在CPU输入端口，KEY7仅调试。
- 同步ROM地址采样/保持，RAM读延时、写数据锁存、写使能多拍只持久写一次、cancel及复位不清RAM。
- pending ST期间STOP、停止不增加写、STEP一微周期、HALT/TRAP、停止复位和恢复，硬件不靠游戏PC。

完整联合TB实例化真实板级top、2FF、同步BRAM适配、477MUX CPU和独立SSD1306接收器。每个CE与V1行为RTL比较完整33位状态/总线，每次指令退役和预生成Python64bit期望比较PC/word/PCnext/AR/A/Z/C/GPO；最终全部256nibble RAM相同。输入通过实体KEY引脚驱动，不强制CPU内部状态；包含菜单防抖/单次选择、两游戏及B返回。另用真实UART RX发n/空格验证单步/恢复。

每个GPO变化必须由OUT退役或明确复位产生，OLED四输出必须等于GPO；外部模型检查8bit、CS/DC、建立/高低宽度/周期、page地址、AF前清屏。CPU OUT轨迹cpu_out.csv、字节spi_bytes.csv、实际TX解码uart.jsonl可回溯。FPGA图形/游戏路径不进入源清单；路由审计进一步确认四路OLED OBUF的唯一leaf driver是CPU GPO FDRE/Q。

两个检查器的作用不同：全系统Golden trace来自Python；V1行为RTL计算独立；外部SSD模型不使用游戏状态生成实际输出。Python图像oracle读取CPU游戏RAM验证收到的GDDRAM位置，不能代替CPU规则差分。重定位规则另有177 Pong/315 Snake的软件三方核查（原程序/新程序/独立游戏oracle），不冒充所有492场景均由新平台RTL执行。

## 时序与硬件

Vivado脚本必须用新输出、同一50MHz时钟、仅异步输入到2FF第一拍的false path；无CPU多周期例外或全局false_path。综合检查477MUX，路由审计33FF、唯一BUFG和OLED4直接驱动。单次STA只证明当前FPGA实现满足声明约束，不证明NC7SZ157物理时序。

板上确认清单：菜单上下/A/B、Pong双球拍/反弹/比分、Snake方向/拒绝反向/食物/死亡/A重开/B返回、上下长按、KEY7暂停、RST_N重进菜单。UART不能代替肉眼显示验收。使用等价UART调试，本轮没有加入ILA core，因此ILA实测是NOT_RUN，不声称已经有ILA波形。

仿真结束可能截断最后一条UART行，离线解析保留raw并提示；只有完整JSON计为有效记录，不将末行截断当作通过的完整消息。工作记录中区分这类采集边界与UART framing/计数错误。

本轮已保留早期失败：joint_r1的32位超时常量溢出在0时刻终止；units_r1的TB漏连接导致elaboration失败；implementation_r1的同步器筛选误含POR释放寄存器。分别修复常量宽度、显式端口和精确层级筛选，没有关闭产品断言或替换期望；旧输出原位保留。
