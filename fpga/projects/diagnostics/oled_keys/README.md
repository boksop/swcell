# 独立 OLED / 按键 / LED 引脚验证

这是swcell_k325t的独立诊断，不依赖M20/M11逻辑。输入RST_N也作为待测按键，不复位FPGA；KEY0～7低按下，对应LED0～7低点亮。共享时钟D27=50MHz，UART=W23/V20，115200。

上电约0.23s初始化SSD1306（SPI mode0/MSB/10MHz，SCK高40ns/低60ns），随后约8.15s依次显示黑、白、8像素棋盘、1像素棋盘（反显）、竖条、横条、边框/对角线、移动十字，然后进入8行按键状态页。任何按键按下立即请求实时页。RST_N短按切换正/反显；长按≥2s后释放重播图案。按键20ms逐位消抖，内容更新58.87485帧/s（默认参数XSIM周期计数，含SPI及16ms帧间隔），每帧用同一输入快照。LED一直跟随各KEY，不用自检灯效遮蔽输入。

SPI没有读回/ACK，初始化/数据已发送不等于屏幕确实显示。实际OLED与LED需目视确认；KEY0～7和RST_N应逐一按下/释放≥0.2s，也测试多键。具体引脚/测试与证据见[诊断说明](../../../../docs/diagnostics/oled_keys.md)。

```bash
bash sim/scripts/run_oled_keys.sh
vivado -mode batch -source fpga/projects/diagnostics/oled_keys/scripts/build.tcl
# 只有仿真/实现/STA/DRC通过后才显式JTAG；不操作Flash
vivado -mode batch -source fpga/common/tcl/program.tcl -tclargs build/fpga/diagnostics/oled_keys/swcell_oled_keys_top.bit xc7k325t_0
```

本工程使用独立io.xdc，不加载含旧LED_G/Y/R或M11端口的base_io。所有引脚由用户提供，参考board/oled_keys.json；未知的模块VBAT/上电状态不伪装成实测值。

当前版本OLEDKEYS04按板卡安装方向旋转180°：初始化A0/C0（原版A1/C8）；common驱动的ROTATE_180默认0，板级默认1。只在反显状态变化时发送A6/A7，SPI及内容更新率与屏幕内部行扫描频率分别记录。原1MHz实测基础引脚功能已获用户确认；白底整体明暗闪动仍需对比新版本，不能提前宣称解决。
