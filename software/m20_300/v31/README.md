# M20 V3.1 软件镜像

`m20_v31.asm`和`m20_v31.memh`由tools/m20/v31/build_firmware.py生成，源程序包括未改变的原Pong和V3乱序Snake变体。生成器对符号加P_/S_前缀，使用原汇编器统一解析地址；不拼接绝对机器码。manifest.json给出全部符号/软件返回ID/RAM布局及指纹。

当前4052/4096个16位字，剩44字（1.07%）；无Bank/额外ROM数据口/新指令。增加应用只涉及软件，但本镜像已经接近容量上限，第三游戏无法据此承诺放得下。原V3两个程序、旧ROM和Bitstream不覆盖。

差异：IN0/IN1在迁移后的游戏例程中读取软件消抖/方向暂存结果；系统真正IN0/IN1读取连续原始GPI。RETURN_ID由F0移到3F，Snake启动只清游戏区，保留菜单/驱动软件RAM。tick_done是软件跳转标签，FPGA完全不读取它。

共享例程无CALL/RET：普通RAM写返回ID＋静态JZ/JMP分派；非递归、不同例程独占返回槽。SPI有152个调用点，占两nibble返回编号；所有运行控制/字体/食物表都是CPU指令。

软件采样、图形和帧节奏见[架构](../../../docs/m20/M20_V31_ARCHITECTURE.md)和[性能](../../../docs/m20/M20_V31_SOFTWARE_PERFORMANCE.md)。

固件0.2修复Pong A重开后静止球拍缓存未失效的问题，并将球与食物由横条改为CPU软件逐列产生的加号。未改原游戏/V3/CPU/ISA；初始固件0.1的源和证据独立保留。
