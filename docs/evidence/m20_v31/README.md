# V3.1 精选原样证据

65份证据，manifest.json逐一记录原路径、归档路径、字节数及SHA256。只将.log明确改名为.txt，不改文件内容。包含最终固件0.2的真实编译/仿真/路由/JTAG/45条UART、原CPU回归、旧平台调试及失败反例。

initial_r5_source保存未修复的固件0.1源码/ROM快照；Python代码以.py.txt归档，供隔离还原原路径核查，不在证据目录直接运行。旧球拍消失和横条图案属于已知失败版本，不标为正式可用固件。negative包含第一版修复断言失败及源码变化保护失败。

完整cpu_out.csv和vectors.hex较大，只放GitHub Release压缩证据附件，普通Git通过manifest/SHA索引关联；不打包xsim.dir、WDB/DCP、虚拟环境或用户docs.zip。实际下载使用Release的FUNCTIONAL_STORAGE bit。

[版本绑定与恢复方法](../../m20/M20_V31_LOCAL_GIT_REPORT.md)。原始build/results保持不变，发布归档不替代独立备份。
