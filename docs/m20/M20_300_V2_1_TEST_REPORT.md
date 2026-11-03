# M20 V2.1：正式结构级测试结果

日期2026-11-02。**V2.1本轮自动验收条件全部通过；等待用户确认阶段验收。** 物理实现仍为V2.2分析，不能把本报告当实物通过。现接受500+规模，300不再是验收门槛。

本轮参数口径：

|参数|配置/含义|
|---|---|
|环境|Ubuntu24.04、Python3.12、XSIM2026.1.1|
|普通CPU回归时钟|10ns周期，100MHz理想RTL仿真激励；不含真实157延迟，不能作为实物主频|
|FPGA接口模型|sys_clk50MHz、外部CPU模型1MHz，固定相位服务|
|真实CPU电源/初始频率建议|目标3.3V、先100kHz；尚未上电/测量|
|存储空间|ROM4096×16、RAM256×4，由FPGA提供|
|UART|本轮没有UART采集；真实原始证据为XSIM/CSV/JSON|

|验收项|结果|本轮证据，根build/m20_300/v21/|
|---|---|---|
|确定性生成与独立pin审计|VERIFIED：477组合/33状态；完整543、纯功能542|session_20261102/reproduction.json；docs/m20/v21_resources/audit.json|
|所有编码合法性|PASS：65536，15015合法、50521非法|regression_r3/xsim/illegal.log|
|所有非法CPU实际终态/恢复|PASS：50521逐一进入TRAP7、保持且复位执行NOP|同上，recovery=50521|
|数学数据通路|PASS：正式CPU27840向量；原V1 ALU32768|regression_r3/xsim/datapath.log、isa_v1.log|
|X/Z观察/复位恢复|PASS：3组|datapath.log|
|指令差分|PASS：49case，22223事件|regression_r3/instructions/three_way_comparison.json|
|游戏差分|PASS：38case，35108事件，含连续64tick|regression_r3/games/three_way_comparison.json|
|RAM事务/所有最终RAM|PASS：全部87场景，每场景256nibble|各case CSV和两核最终RAM|
|内存及复位|PASS：7组|regression_r3/xsim/memory.log|
|Python全部|PASS：110项，10.163s|session_20261102/python_tests_final.log|
|8态next-D断言与逐周期V1锁步|PASS|指令锁步51340周期，游戏115651周期|
|V1/603/ISA/游戏/索引保护|VERIFIED：见最终SHA核对|session_20261102/final_receipt.json|
|综合/实现/STA/bitstream/实物|NOT_RUN|本轮不执行|

总差分57331事件=57314正常退役+17异常事件，保留原2/5profile；没有因双核把一次指令重复计数。全部非法穷举为另外的专项，不混入57331事件中。

Pong ROM168字，Snake368字，二进制SHA与冻结规范一致；实际游戏周期沿用本轮CSV：Pong定向最大观察tick308周期，Snake食物63探测13419周期，Snake boot4531周期。它们不是全输入数学最坏界。

首轮仿真及Python测试自身问题、修复与保留位置见[验证方法](M20_300_V2_1_VERIFICATION.md)。本轮通过证据是regression_r3，不能直接沿用旧候选PASS。

后续结论：采用543结构具备数字功能/可审计基础；可以围绕时钟、电源、走线和接口推进实物小样验证。**尚不具备全CPU PCB投板放行条件**，主要缺口是真实双MUX DFF的setup/hold/主从交接、min-delay、加载与板级接口参数。
