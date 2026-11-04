# 新模块验证工程模板

复制project.example.json的字段到 `fpga/projects/<模块>/<测试>/project.json`；替换MODULE/TEST，提供README和实际引用。模板本身不是有效工程，不被catalog扫描。不为尚未实现的模块批量创建空目录。

板卡共享资源引用 `fpga/boards/<板卡>/`；模块外部连接放该模块constraints，构建/顶层/项目参数放工程内。逻辑放 `rtl/modules/<模块>/`，仿真放 `sim/<模块>/`，Python按 `host/python/<模块>/` 分包，软件放 `software/<模块>/`，文档放 `docs/<模块>/`。`rtl/m20`等既有冻结路径是明确保留的例外。

所有构建输出写 `build/fpga/<模块>/<测试>/`，模拟输出写 `build/sim/<模块>/<套件>/`；原始实测写 `results/<模块>/<时间>/`。真实引脚未知时保留PLANNED/TODO，不复用M11引脚，不用UCIO/NSTD降级绕过约束。

在仓库根执行 `python3 tools/fpga/project_catalog.py check`；再按真实验证结果分开记录编译、仿真、综合、实现、STA和硬件。不要把目录存在或catalog检查通过记为功能验收。
