# M20 V3.1 Git定版与证据归档

2026-11-05。用户授权本地commit、annotated tag m20-v3.1-autonomous-fpga-verified、正常远程同步及GitHub Release归档；不重新进行硬件测试，不改V3/冻结ISA/CPU/固件功能。**源码/Tag已推送，Release已发布，独立远程克隆与附件下载校验全部通过。** 最终记录在本文件和v31_release_resources中。

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
|留本机|build/results原始目录、全部缓存/大波形/DCP/venv|原位保留，不删除；未上传缓存，未将旧失败改PASS|

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
- 已执行：源码commit、干净恢复、annotated tag、正常atomic push、Release创建、独立远程克隆和四附件下载校验，均PASS。

用户在发布恢复验证期间告知已自行删除未跟踪docs.zip；该文件从未进入本轮commit/Release，未执行恢复，ignore条款仅防未来同名备份误入库。

## 最终提交、Tag与远程验证

|项目|实际结果|
|---|---|
|源码提交|`d0df9f97893019687bb2d8c81473a13ac6a074fb`，155路径变更；全部正式V3.1源/ROM/工程/方法及65份精选证据|
|annotated Tag|`m20-v3.1-autonomous-fpga-verified`，对象`42c2b7f3539551d238512309ea4db3b200fcf71c`，目标为上述源码提交|
|源码树规模|910个跟踪文件；旧762文件保留，未删除原模块或改原RTL/ISA/游戏ROM|
|后续main|补充本轮恢复和远程下载核验的文档/JSON/日志记录；不移动Tag，source/tag目标保持不变|
|远程|`origin https://github.com/boksop/swcell.git`，Public；只有main和本次Tag正常推送，无force/rebase/amend|
|Release|[m20-v3.1-autonomous-fpga-verified](https://github.com/boksop/swcell/releases/tag/m20-v3.1-autonomous-fpga-verified)，2026-11-05T05:10:59Z发布，非draft/非prerelease|
|附件|bit1312962bytes；证据包2307369bytes；release manifest5186bytes；SHA256SUMS329bytes，全部下载读回通过|
|旧Tag|5个旧annotated对象及目标与发布前完全一致，未覆盖V2.3/V2.4/V3等版本|

干净detached检出独立执行181 Python、GPIO/BRAM/STOP/STEP/HALT/TRAP单元、2589535退役/9566SPI/373773写/最终256nibble、工程新综合477MUX，全部PASS。3个固件文件可逐字节重建，82来源/16实际bit构建输入/65归档证据SHA通过；旧V3的67源和10个生成文件也全部保持。此处未重跑P&R或硬件；原路由报告/实际用户验收bit与确认记录独立保留。

独立从GitHub按Tag浅克隆，确认source commit及annotated对象、ROM再生成/资源审计/证据校验PASS。再从Release下载四个附件，全部SHA通过，完整读回证据包73份文件、50566239字节，逐项大小与SHA一致。Release manifest的source commit/tag对象/源清单SHA与远程克隆对应；与普通Git无bit/cache的策略一致。

|校验文件|作用|
|---|---|
|[recovery_verification.json](v31_release_resources/recovery_verification.json)|实际干净恢复结果与原日志SHA；recovery/保留本次新检查的小日志|
|[release_asset_manifest.json](v31_release_resources/release_asset_manifest.json)|与上传的manifest字节相同，绑定source/tag/ROM/Tcl/bit/证据包|
|[download_verification.json](v31_release_resources/download_verification.json)|四附件读回及73份内层原文件校验|
|[remote_assets_source_audit.json](v31_release_resources/remote_assets_source_audit.json)|真正远程检出的82来源、3再生成、65证据及下载资产校验|
|[publication_verification.json](v31_release_resources/publication_verification.json)|发布时main/source与旧Tag/Release元数据；最终main可随文档补充前进，Tag不移动|

本轮未重新上板、不写Flash、不变更任何功能RTL/ISA/固件、不扩展STRICT_MUX或实体时序结论。`docs.zip`由用户自行删除，未进入Git或Release；原始build/results和失败记录保持。工作树收尾仅保留本轮发布记录，最终main精确SHA另存build/v31_release_20261105/final_receipt.json，避免文档嵌入其自身提交SHA的循环。
