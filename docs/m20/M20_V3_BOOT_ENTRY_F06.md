# M20 V3 F06：KEY5启动页入口

2026-11-04，Asia/Shanghai。用户确认F05切换/暂停互换符合预期，进一步要求“M20 CPU”页面也用KEY5进入游戏。

## 定位与行为

修改前先只读采集：`results/M20_V3/20261104_boot_entry_diagnosis_r1/`，8条有效、1条未识别启动行，实际版本F05；`frame_valid=0`、`run=0`、PC0/FETCH，计数不动、错误0。raw SHA256 `c64a460300650fa20c7689805e39b318573d7a654b5514bf0a5f393d43f9146e`。

“M20 CPU BOOT”不是另一套菜单；它代表尚无有效游戏快照。暂停状态下复位或切ROM会出现该页，旧实现须恢复RUN才能由CPU执行到第一个tick。未将用户描述直接认定为断电或旧Flash；本次未操作Flash。

|状态|KEY5 / A|KEY7|
|---|---|---|
|BOOT页：无有效游戏快照|启动当前游戏，不切ROM；已经运行时不打断初始化|不启动、不切换|
|已有游戏画面|切换另一游戏并复位，保留RUN/暂停状态|暂停/继续当前游戏|
|暂停后切换导致BOOT页|再按KEY5启动刚选中的游戏|无需用KEY7进入|

OLED BOOT第二行增加`KEY5: START`。默认配置后的自动运行不变，不引入新的强制等待菜单。KEY6/B、RST_N、方向、20ms消抖、方向FIFO、Pong10/Snake5tick/s及UART命令不变。UART空格在BOOT页仍可控制RUN，保留调试入口。

复用现有`frame_valid/run_requested`作板级状态判断，不增加CPU状态位，不修改477组合MUX、ISA、机器码、乱序食物表或2/5微周期。所有CPU计算和RAM更新仍由CPU执行。

## 验证

|项目|状态/证据|
|---|---|
|Python|PASS，164项：build/m20_v3_python_boot_entry_r1.log|
|板级初次测试boot_entry_r1|FAIL保留：旧测试在Snake初始化未完成时按KEY7，却仍期待暂停；新约定该阶段KEY7不启动/暂停。失败时间27.049340ms。未放宽产品断言，测试增加等待真实游戏快照后再验证暂停|
|板级boot_entry_r2|PASS；2帧Pong、1帧Snake、1帧BOOT提示、5877 UART字节；覆盖暂停复位BOOT、KEY7不启动、KEY5进入当前ROM、提示实际SPI像素、游戏选择/暂停/短按缓存|
|综合/实现/STA|PASS：snake_shuffled_boot_r1，WNS+0.982ns/WHS+0.062ns/WPWS+9.232ns，DRC0；8774LUT/5986FF、4RAMB36/1RAMB18/4LUTRAM/DSP0|
|源SHA/引脚/路由结构|PASS，22个输入文件、25个3.3V引脚、477逻辑LUT3/33CPU FF/1BUFG|
|JTAG|PASS，21:27:31 startup HIGH、退出0，build/m20_v3_program_boot_entry_r1.log|
|新UART|PASS，75条有效/1条未识别启动行，错误/输入溢出0；显式暂停/复位复现BOOT页：results/M20_V3/20261104_212750_boot_entry_f06/|
|新的启动页人工确认|用户确认通过：“已经完全正常了”；另明确问题发生于本次JTAG下载后或切换游戏后|

原F05 bit/源快照/60条采集及通过记录不覆盖，参见[F05报告](M20_V3_KEY_SWAP_F05.md)。F06继续使用乱序食物ROM和313断点，接收程序兼容F01～F06。当前阶段不创建Git提交或Tag，不做实体157时序签核。

当前已下载bit：`build/fpga/m20/cpu_validation/snake_shuffled_boot_r1/swcell_m20_v3_top.bit`；SHA256 `972d8ebc5378c244ce5f530be9c8f0b0c9b04853c6c56576c82f96e995d79c49`。

F06 raw SHA256 `0b89238f60ea046d27febdc2baae0336523ec5c70f777a5b8f34b699a1801f63`。只改top启动条件/版本和显示BOOT提示，其余20个构建输入与F05 SHA一致；CPU及软件未改，不重复运行其无改动87场景。小型记录及逐文件哈希见v3_resources/f06_*。采集中仅UART发送空格及r以停住/复位，没有记录到实体KEY5按下，因此新入口人工实机确认仍开放，不能将等待页75条快照说成已经按键进入游戏。

后续人工确认已完成：用户明确回复“已经完全正常了”，且说明场景为本次JTAG下载后或切换游戏后。该确认独立保存至[f06_user_acceptance.json](v3_resources/f06_user_acceptance.json)，不回写上段原75条UART或原验证摘要的NOT_VERIFIED字段。F06入口/键位子阶段COMPLETED；[正式验收报告](../reports/m20_phaseV3-F06_20261104.md)已保存。

```bash
vivado -mode batch -source fpga/common/tcl/program.tcl \
  -tclargs build/fpga/m20/cpu_validation/snake_shuffled_boot_r1/swcell_m20_v3_top.bit xc7k325t_0
```
