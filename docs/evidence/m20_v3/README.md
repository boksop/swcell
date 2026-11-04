# M20 V3 原样精选证据

这是发布准备时从本机build/results复制的74份小型证据，共2340847字节。原文件均留原位，所有副本与来源SHA256相同，见[manifest.json](manifest.json)。manifest不包含自身SHA。

- `fpga_f06/`：最终F06真实路由STA、利用率、DRC/CDC/IO、CPU477实例/33FF映射、源指纹、JTAG日志。没有bitstream或DCP。
- `strict_mux_blocked/`：STRICT_MUX布局布线后85项LUTLP-1及失败STA，不标为通过。
- `early_functional_timing_failure/`：初次F模式外设除法WNS−7.059ns失败；原目录实际名为FUNCTIONAL_STORAGE，早期技术文档称functional_r1是运行标签，不是实际路径。
- `simulation/`：原49指令/38游戏差分及ISA/算术/非法/访存日志、最新F06启动/按键、系统完整RAM对照、乱序软件315场景；失败boot_entry_r1也保留。
- `hardware/`：10次V3小型UART采集/解析/诊断的原样数据，运行配置/人工确认须结合[总报告](../../reports/m20_phaseV3_20261104.md)及[技术报告](../../m20/M20_V3_HARDWARE_TEST_REPORT.md)，不能混同游戏、独立指令诊断、TRAP或等待页。

`.log`的精选副本明确改名为`.txt`以区别默认忽略的临时日志，字节未改变；manifest记录原始路径。原始采集中的启动未识别行、NOT_CONFIRMED、旧字段缺陷均保留，后续人工确认另存JSON，不回写旧数据。

来源仍在本机时，可用`tools/git/archive_v3_evidence.py --output 新目录`重建相同选择；干净检出只需校验副本，不应要求不存在的旧build/results。源码、ROM和Tcl足以重新执行验证；历史证据不是当前环境测试的替代品。

原始大波形、路由数据库、bitstream、全部旧M11采集仍按独立备份/哈希索引管理，不在本精选目录。工具输出带有AMD版权抬头，仅保留本项目运行报告，不包括Vivado软件、加密IP或第三方器件手册全文。当前未添加项目开源许可证，仓库仅按用户授权Private发布。
