# 公共Tcl

- repo_paths.tcl：从脚本位置向上定位仓库，不依赖当前工作目录和固定层数。
- program.tcl：显式JTAG下载，要求真实bit文件及精确设备名。
- flash_config.tcl：纯配置校验/镜像生成帮助。
- program_flash.tcl：只有显式调用才擦写/固化，延续原安全检查；目录整理不调用。

应用构建位于各project/scripts，板卡配置位于boards。不要在这里放M11/M20顶层或私有引脚。
