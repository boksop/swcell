# M20：157器件和时序模型

日期2026-11-02。数据表摘录条件为VERIFIED文档事实；网表应用为ESTIMATED；实物测量为TBD。

## 原厂来源

|候选|手册与版本|3.3V对应条件|数据/选择最大ns|
|---|---|---|---|
|74LVC1G157GW,125|[Nexperia Rev12，2023-08-15](https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf)|3.0–3.6V，50pF/500Ω，−40…85℃|5.0 / 5.0|
|NC7SV157P6X|[onsemi Rev3，2024-01](https://www.onsemi.com/download/data-sheet/pdf/nc7sv157-d.pdf)|2.7–3.6V，30pF/500Ω，−40…85℃|3.6 / 3.6|
|NC7SZ157P6X|[onsemi Rev7，2024-08](https://www.onsemi.com/download/data-sheet/pdf/nc7sz157-d.pdf)|3.3±0.3V，50pF/500Ω，−40…85℃|5.0 / 5.2|

SV与其它两项负载不同，不能直接按3.6/5.0作速度排名。SZ另有15pF条件，库中单独保留。推荐先以单一厂商LVC批次作保守小样，不混料；最终选型须连同DFF和负载验证决定。GW与P6X的pin功能一致并不自动保证焊盘/外形完全可替换。

完整电压、VIH/VIL、输出测试电流、Cin/Cpd/ICC、温度、封装、引脚及最小/典型/最大条件保存在`config/m20/157_timing_models.json`和[参数CSV](physical_resources/device_parameters.csv)。LVC125℃最大6.3ns应单列，不混入85℃场景。最小tpd不是经过表征的污染延迟tCD；onsemi两型号的最小tpd为空，不能补成典型值。

这些MUX手册均未提供“反馈主从DFF”的setup、hold、CLK→Q或最小高低脉宽，库中全部为null。典型Cin没有max保证，因此负载总量也只能估算。无SPICE晶体管模型/仿真结果；未使用FDRE时序代替真实器件。

资料核对通过浏览工具读取原厂PDF正文与关键表格；命令行下载三份PDF均返回403，未生成伪造的本地PDF或SHA，记录在build/m20_300/v21/datasheets/sources.json。后续归档请人工从原厂取得相同版本。时钟缓冲器目前只核对产品资料，完整选型/负载参数尚未闭合。

## 估算与可配置边界

physical.py逐pin选取data或select的最大tpd，再加显式每级走线假设0.15ns。默认LVC85℃、Cin典型2.5pF、每网PCB10pF、FPGA输入每pin5pF；超出测试负载的网络会被标记，不外推为已保证时序。没有建立任意负载线性延迟定律。

频率场景另假定CLK→Q10ns、setup10ns、skew5ns、固定PCB10ns、裕量20ns、FPGA ROM服务160ns。该10ns CQ示例未纳入首样建议的100ns两相死区，采用两相后需相应增大CQ预算。均为可编辑工程假设，不是DFF或FPGA实测值；任何频率的hold和最终合格状态都保留TBD。参数变化后重新运行工具生成CSV。

## 主从模型与风险

连接：Master Y=master_hold?QM:D；Slave Y=slave_open?QM:Q。单clock是master_hold=slave_open=CLK；透明相位互补，但器件内部与PCB延迟可令两级同时透明。

`sim/m20_physical/swc_mux157_timed.sv`采用独立输入pin延迟和反馈接线，仅是数字示例，不含模拟阈值、惯性滤波精确模型、亚稳态或PVT相关性。本轮XSIM：4bit/16向量在10ns死区示例通过；Master关闭8ns、Slave开启1ns的失配示例捕获到新D穿透。这个故障被预期捕获，不能说芯片实际必然发生同样7ns重叠。

```bash
sim/scripts/run_m20_physical_models.sh
```

P1需实测：Master关闭/Slave打开相对窗口；D双向setup/hold；CLK→QM/Q；高低脉宽；负载、供电、温度、占空比与双边沿skew扫描；初始化/反馈保持。每个测量保存厂商/批号/探头负载/仪器时间基准。M11已有100MHz单DFF记录不能证明33位CPU同频可行。
