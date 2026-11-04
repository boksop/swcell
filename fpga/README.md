# SwCell FPGA工程

`boards`归属硬件身份，`projects/<模块>/<测试>`归属验证应用，`common/tcl`归属可复用构建/下载帮助。实际工程由各自project.json登记；`_template`不计作工程。

```bash
python3 tools/fpga/project_catalog.py list
python3 tools/fpga/project_catalog.py check
```

命令只读，不调用Vivado或硬件。M11两套验证、UART/OLED独立诊断及M20/cpu_validation功能存储原型均已实现；M20严格反馈存储未放行。查看[工程目录规范](../docs/repository_layout.md)，不要把PLANNED条目当可构建项目。
