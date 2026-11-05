# M20 V3.1 Git定版与证据归档

2026-11-05。用户授权本地commit、annotated tag m20-v3.1-autonomous-fpga-verified、正常远程同步及GitHub Release归档；不重新进行硬件测试，不改V3/冻结ISA/CPU/固件功能。发布动作尚在执行，实际提交和远程结果将补充在本文件。

## 定版对象

- 固件M20-V31-0.2，4052/4096字ROM；源码、生成器、ASM/memh/软件manifest、FPGA工程Tcl/XDC依赖、测试入口、中文报告全部纳管。
- FUNCTIONAL_STORAGE：477组合MUX＋33原生FF，等价543；不是STRICT_MUX或实体66存储MUX时序验收。
- ROM SHA ae5be5055052c8ea9c8a5e4d00de5dcaf2dfe531e84a57fb9dec0b4feef71619；最终用户验收bit SHA181fb8844407a69f405594440245dc5ed1e50a24e81e103d194aa531835cfd0f。
- 源清单[v31_release_resources/source_manifest.json](v31_release_resources/source_manifest.json)覆盖82份来源及实际bit构建16份输入，连接固件0.2/ROM/Tcl/bit/证据归档。清单不含自身SHA，提交SHA在对象实际存在后由Release资产manifest记录，避免循环依赖。

## Git与Release分层

|层次|内容|核查方式|
|---|---|---|
|普通Git|所有正式代码/ROM/工程/测试/报告及65份精选证据，约1.07MiB|docs/evidence/m20_v31/manifest.json；源SHA/再生成/独立477/33/543审计|
|Release bit|swcell_m20_v3_1_fw0_2_xc7k325tffg900-2_FUNCTIONAL_STORAGE.bit，1312962bytes|SHA181fb884…；是原已上板字节，不用重建bit冒充原验收镜像|
|Release完整证据|m20-v3.1-verification-evidence.tar.gz，73份/50566239未压缩字节|内置ARCHIVE_MANIFEST.json逐原路径/大小/SHA；含最终42MiB vectors和4.9MiB OUT trace，含原失败|
|Release关联|m20-v3.1-release-manifest.json及SHA256SUMS.txt|实际source commit、annotated tag对象、ROM和bit/压缩包SHA；SHA文件不包含自身|
|留本机|build/results原始目录、全部缓存/大波形/DCP/venv、docs.zip|原位保留，不删除；未上传缓存，未将旧失败改PASS|

所有大文件来自本轮可核查原路径；[较大证据索引](v31_release_resources/large_evidence_index.csv)和[归档准备记录](v31_release_resources/archive_preparation.json)独立保留。未选择或添加开源许可证。Public仓库权限不等于替项目授予开源许可。

## 复现与校验

```bash
# 已安装Python依赖及Vivado后，在仓库根目录执行，输出须全新
build/venvs/python312/bin/python -B tools/git/v31_release_audit.py --output build/v31_audit_new.json
build/venvs/python312/bin/python -B tools/test/run_python_tests.py
bash sim/scripts/run_m20_v31_units.sh
bash sim/scripts/run_m20_v31.sh

# 新工程构建（不会自动下载/写Flash）
vivado -mode batch -source fpga/projects/m20/autonomous/scripts/build.tcl \
  -tclargs --rom software/m20_300/v31/m20_v31.memh --output build/fpga/m20/autonomous/rebuild_new
```

Release URL：[m20-v3.1-autonomous-fpga-verified](https://github.com/boksop/swcell/releases/tag/m20-v3.1-autonomous-fpga-verified)。下载后在资产目录执行sha256sum -c SHA256SUMS.txt。证据包可离线核查，无需重新上板；生成的新bit与历史bit不保证二进制相同，只有声明并核验的原bit SHA代表本次实物验收镜像。

## 执行检查点

- 本地起点main 4a7d1fd，与remote main一致；5个旧annotated tags对象/目标一致。暂存区原为空，docs.zip保留并加入明确本机备份忽略。
- 工作树82源/16构建输入、3个软件文件再生成、65份证据与bit/完整归档SHA通过；全历史及候选秘密/缓存/大小扫描PASS，模式检测不等于普遍保密或版权证明。
- 待执行：提交后干净恢复、当前Tag创建、正常push、Release下载比对。未发生的动作不标PASS。
