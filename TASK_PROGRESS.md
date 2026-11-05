# SwCell 当前任务进度

## 最新任务 M20-V31-RELEASE-20261105

**COMPLETED，2026-11-05。** 用户授权本地定版及远程/Release归档已落实。源码提交`d0df9f97893019687bb2d8c81473a13ac6a074fb`；annotated tag `m20-v3.1-autonomous-fpga-verified`（对象42c2b7f…）目标为该提交，已正常推送。Public [Release](https://github.com/boksop/swcell/releases/tag/m20-v3.1-autonomous-fpga-verified)四附件已发布并独立下载校验。

干净源码恢复181 Python、2589535指令/9566SPI联合、GPIO/BRAM/调试单元、新工程综合PASS；82来源/16实际bit输入、3固件再生成、65份Git精选证据及Release内73文件/约50.6MB原始证据SHA通过。最终用户验收bit SHA181fb884…、ROM ae5be505…，CPU477/33/543不变；未重跑硬件、未改ISA/旧模块/旧Tag，未上传缓存或凭据。docs.zip由用户自行删除，从未入库。

[定版报告](docs/m20/M20_V31_LOCAL_GIT_REPORT.md)、[发布检查点](docs/tasks/m20-v31-release-20261105.md)。main会包含最后的恢复/下载元数据补充提交，Tag保持源码冻结点；实际最终main SHA在Git及build/v31_release_20261105/final_receipt.json核实，不自引用。若会话中断于元数据commit/push，先检查status和远程main，仅完成该记录同步，不重复Tag/Release创建。不自动开始下一阶段。

## 当前任务 M20-V31-AUTONOMOUS-20261105

**COMPLETED，2026-11-05，Asia/Shanghai。** 用户确认基本菜单/两游戏/长按/暂停/复位，并在修复后确认重复A重开球拍正常、Pong球与Snake食物均为加号。[正式报告](docs/reports/m20_phaseV3.1_20261105.md)、[完整检查点](docs/tasks/m20-v31-autonomous-20261105.md)。

最终固件M20-V31-0.2：4052/4096字ROM剩44，CPU自主输入/菜单/游戏/绘图/软件SPI；平台RTL/477网表/ISA/原V3不改。181 Python、2589535指令联合/V1/Python、9566SPI字节/全RAM通过；布局布线WNS1.972/WHS0.092ns，477MUX/33FF/4OLED直驱。原CPU87/57331及非法/数学/访存回归保留。

当前已加载build/fpga/m20/autonomous/restart_plus_r2/swcell_m20_v31_top.bit（SHA181fb884…）；45条新UART错误0，人工确认独立JSON在docs/m20/v31_resources。原r5重开/图案失败及首次修复测试失败原位保留，初始证据v31_initial_r5_resources，不改历史数据为PASS。

**恢复入口：**没有未完成实现/测试；下一项工作由用户决定。原始数据results/M20_V31需独立备份；ILA/STRICT_MUX/实体157/Flash/长期可靠性不在本次验收内。功能验收完成时尚未定版，现已由上述独立发布任务建立commit/Tag/Release；不重复发布或下载，原用户docs.zip后已自行删除。当前无后台采集依赖。

## 最新仓库设置（2026-11-05）

**SWCELL-GITHUB-PUBLIC-20261105：COMPLETED。** 用户明确要求将boksop/swcell改为Public，已通过GitHub CLI完成，并用无认证GitHub API确认可公开读取。仓库https://github.com/boksop/swcell；main仍4a7d1fd9377a3ed1f80a7dc010e3467811089de0，无代码/历史或Tag变更。本次仅改仓库设置并本地更新本进度，不执行新的commit/push；下方Private记录为2026-11-04首次发布的历史状态。新记录/home/boksop/swcell_github_visibility_20261105.json。未添加或选择开源许可证。

2026-11-04，Asia/Shanghai。main；当前任务 **SWCELL-GITHUB-PUBLISH-20261104：COMPLETED**。

## 已完成

- 用户授权本次本地commit/annotated Tag及首次Private GitHub发布，现已完成；后续发布不据此自动授权。
- 仓库 **https://github.com/boksop/swcell**，API确认Private，origin为同一HTTPS地址；main和5个正式Tag已推送。
- 旧V2.3/V2.4提交/Tag保持；本次外设b4081d3、V3 8fab9f6、恢复bbf229e、origin工具兼容365e543及最终报告元数据提交。V3Tag m20-v3-fpga-hardware-verified目标8fab9f6，不将原生FF冒充实体157。
- 168项本地隔离恢复通过；真实远程克隆先发现旧审计器reject-all-remote导致1项失败，保留失败并仅允许显式授权origin、增加两项反例后，新远程克隆**170项全部通过**。
- 67源SHA、10生成文件字节、477/33/543 CPU＋20发生器、74份原样证据SHA通过；实际干净XSIM核心87/57331、非法/算术/访存、板级SPI/6键/UART和Vivado新综合通过。
- 原561跟踪文件全部保留；最终762文件纳管，无缓存/bit/大波形/匹配凭据/超限大文件。全历史和当前候选已扫描，不能将模式扫描视作万能保密/版权证明。
- F06硬件本身不改，功能模式477组合MUX＋33原生FF。STRICT_MUX85 LUTLP-1无bit，实体157时序开放；既有原始失败不改写。

## 最终记录与恢复入口

[最终发布报告](docs/GITHUB_PUBLISH_REPORT.md)、[任务细节](docs/tasks/github-publish-20261104.md)、[V3阶段报告](docs/reports/m20_phaseV3_20261104.md)。报告的SHA是实际检查点；最终main精确SHA在完成元数据push后记录到工程外 **/home/boksop/swcell_github_publish_final.json**，避免提交内自引用；恢复时先核对git status/HEAD/origin/main。

当前已无待执行功能或发布动作；若会话恰好中断于最后元数据提交/push，先检查本地与远程SHA，不重复建仓库/Tag或改历史。通过工具v3_release_audit.py/github_publish_audit.py选新build输出只读核验。现有临时独立检出留在/tmp供核查，不依赖其长期存在，关键恢复摘要已纳管。

## 验收边界与剩余外部事项

- ChatGPT GitHub连接器仍须用户授予私有库访问，本次仅核验gh/API和独立克隆，不声称连接器已配置。
- 七个旧M11原始数据文档链接本机缺失，非本轮删除；既有原始build/results未移动，独立备份仍必要。
- 无项目开源许可证，不自动Public；Vivado安装/许可/凭据不发布。
- 不开始新CPU、PCB、Flash或实物测试，不自动后续commit/push。旧临时Vivado辅助txt仍原位、已ignore。

## 历史任务

[V3与F06交互](docs/tasks/m20-v3-fpga-20261104.md)、[外设诊断](docs/tasks/oled-keys-20261104.md)。本次发布任务的整体V3用户确认取代此前“等待整体验收”的检查点，不回写旧采集字段。
