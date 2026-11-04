# SwCell 当前任务进度

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
