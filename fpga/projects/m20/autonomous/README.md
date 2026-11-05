# M20 V3.1 自主软件计算机 FPGA 工程

独立于V3 `cpu_validation`，功能存储模式477组合MUX＋33原生FF。CPU连续执行统一4096×16 ROM；全部菜单/游戏/绘图/软件SPI由CPU完成。当前验收状态见[测试报告](../../../../docs/m20/M20_V31_TEST_REPORT.md)。

```bash
# 先重生成并比较；输出必须是全新目录
build/venvs/python312/bin/python -B tools/m20/v31/build_firmware.py --output build/m20_v31/reproduce_new
cmp software/m20_300/v31/m20_v31.memh build/m20_v31/reproduce_new/m20_v31.memh

bash sim/scripts/run_m20_v31_units.sh
bash sim/scripts/run_m20_v31.sh

vivado -mode batch -source fpga/projects/m20/autonomous/scripts/build.tcl \
  -tclargs --rom software/m20_300/v31/m20_v31.memh \
  --output build/fpga/m20/autonomous/run_new

# 仅有板卡连接且获得当次授权后JTAG；不写Flash
vivado -mode batch -source fpga/common/tcl/program.tcl \
  -tclargs build/fpga/m20/autonomous/run_new/swcell_m20_v31_top.bit xc7k325t_0

build/venvs/python312/bin/python -B host/python/swcell_m20_v31.py \
  --port /dev/ttyUSB1 --baud 115200 --seconds 60
```

50MHz系统单域、1MHz CPU微周期；SPI来自OUT，不能再称10MHz硬件SPI。OLED显示M20/PONG/SNAKE菜单，上下选择、A/KEY5进入，游戏A重开、B/KEY6返回，上下长按约3.36秒返回。KEY7仅调试暂停，RST_N复位CPU并由软件重新初始化OLED；KEY4禁用。六GPI只有2FF、无FPGA消抖/FIFO。

UART空格暂停/恢复、n单微周期、r系统复位；其余字符无游戏含义。遥测M20_V31_STATE包含PC、AR、A、GPO、微状态、六键、RUN/RESET/HALT/TRAP、64位微周期/退役/读写/错误。没有游戏RAM格式或帧地址。

构建脚本复用已经实机验证的OLED/按键板卡XDC，声明唯一20ns时钟、9个异步输入到各2FF第一级的例外，无CPU多周期/全局false_path。精确477个MUX在综合时检查；routed.dcp可用tools/m20/v31/route_audit.tcl审计33FF和OLED四路直接驱动。
