# PC端工具

python中保留既有采集/离线分析CLI及m20包，避免破坏用户调用和冻结模型。后续模块按python/<模块>分包，共享协议与采集明确复用，不复制串口保存逻辑。

M11扫频当前从fpga/projects/m11/performance构建、从fpga/common/tcl/program.tcl进行显式JTAG下载。离线分析不依赖硬件；使用说明见docs/m11，环境见docs/environment_python312.md。
