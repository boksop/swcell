# SwCell 首次GitHub Private发布记录

2026-11-04，Asia/Shanghai。**当前状态：本地V3定版及干净恢复完成，已认证boksop；尚未创建远程仓库、未push。** 本页后续只记录真实执行结果，不预填URL/SHA。

## 初始核查

- main起始70daf6f，12个历史提交、561个跟踪文件，无旧stage/remote。
- V2.3 aecf570＋后续5e601a9，Tag m20-v2.3-two-phase-sim-verified原对象保留。
- V2.4 4a95665＋80593a1＋48564b5，Tag m20-v2.4-digital-verified保留。
- V3与独立外设诊断尚未提交，现按用户授权整理；不重新初始化、重写历史或修改通过的功能。
- 初始全部可达历史扫描786blob/266tree/12commit/4tag，无已匹配凭据/缓存/超50MiB文件，最大2045358字节；不等于万能保密/版权证明。后续最终审计另列。

## 纳管与排除

纳管所有现存正式RTL/生成器/结构SV/连接JSON、ISA/汇编/ROM、Tcl/XDC、TB/回归、Python/依赖、物理预算/接口契约、历史正负例与小型统计、README/AGENTS/任务。M0～M10/M12～M19独立源码和实际PCB原理图在当前目录未找到，不虚构已实现内容。

V3原样精选证据74份、2340847字节及来源SHA见[清单](evidence/m20_v3/manifest.json)；包括最终路由报告、STRICT_MUX/早期STA失败、CPU/游戏差分日志及实际UART。原文件保留build/results原位置。

排除build/.venv/Vivado缓存、WDB/VCD/FSDB等大波形、DCP/bit/LTX、旧重复ZIP、许可/密码/密钥、本机覆盖及辅助clockInfo/tight_setup_hold_pins。既有2KB V2.3负向VCD有明确例外，冻结小ROM .bin/.memh纳管；不按后缀一刀切。GitHub普通Git文件>100MiB会被拒绝，50MiB以上有警告，来源：[官方限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。

没有新增许可证；本次仅Private。无纳管Vivado安装/加密IP/厂商数据手册全文。AMD运行报告原抬头保留；候选设计资料来自既有用户附件，未据此承诺公开再许可。实际公开发布前需进一步确认权利范围。

## 工具与依赖

GitHub CLI v2.103.3由[官方发行包](https://github.com/cli/cli/releases/tag/v2.103.3)安装，发行包SHA256与官方checksums一致，路径~/.local/bin/gh；已认证活动个人账号boksop，repos/boksop/swcell查询404、origin为空。用户使用浏览器gh auth login，不提供Token到聊天或代码。

Vivado/XSIM2026.1.1（V3）、历史M11的2022.1、厂商安装与许可需使用者提供；Python3.12及依赖快照在host/python。当前V3无外部XCI/未纳管IP/子模块/Git LFS依赖。大bit/原始完整波形只能按本机索引另行备份。

## 已完成本地定版与恢复

- 外设诊断commit：b4081d31d79c1b477a44627ffd8be9cd50ec8d57，31文件。
- V3 commit：8fab9f6ad142e0b0fb3f8655411f5c538312f529，180文件独立变更；既有历史不改。
- V3 annotated Tag：m20-v3-fpga-hardware-verified，目标8fab9f6，Tag对象d47fe2b32114136ac7cc46ea3bbc1a6c13f4cd25。
- [干净恢复记录](evidence/m20_v3_recovery_20261104.json)：67份源SHA、10份生成文件字节相同、477/33/543 CPU及20发生器审计、74份精选证据SHA；Python168项、核心87/57331、50521非法终态/恢复、27840算术、7访存、板级5877字节UART及SPI/键位通过；Vivado全新综合477MUX通过。
- 隔离检出未复制原build/results。创建全新Python3.12无pip环境后，通过已有pip --python安装版本快照13依赖；系统缺ensurepip已在README注明，未修改系统Python。
- 本轮没有新P&R/bit/JTAG或实物测试，实际硬件结论来自已存F06路由/下载/用户确认。
- 现有V2.1/V2.2/V2.3/V2.4四Tag对象未变。完整历史及当前候选模式扫描PASS，未匹配凭据/超限文件；厂商版权抬头均位于项目运行报告，人工保留来源，不包含软件/IP全文。
- 手写源/文档whitespace检查通过；原样报告空格及CSV的CRLF按证据字节保留，不为diff检查而归一化。

## 远程待办

创建Private https://github.com/boksop/swcell，推送main及5个正式tags；再校验远程main/tag对象、README、全部文件哈希及独立浅克隆。未实际完成前不宣称远程PASS。

在线审查入口已具备源码和复现结构；ChatGPT Work需安装有权限的源码插件，Codex Cloud需连接并选择仓库，账号必须有仓库访问权，见[OpenAI官方Code review](https://learn.chatgpt.com/docs/code-review?surface=app)及[Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments)。本机gh登录不等于ChatGPT连接器已授权，本次不代替用户配置连接器。

## 已知边界

FUNCTIONAL_STORAGE为477组合MUX＋33原生FF实机通过；STRICT_MUX有85 LUTLP-1/WNS−22.002ns，无bit/无硬件放行；实体157时序未签核。原545候选非法HALT缺陷、原603基线和V2.4失败反例保留。

旧M11七个原始数据文档链接在本机缺失，既有报告/源码不伪造恢复；这些不是本轮遗漏删除。Git fsck未报告损坏，存在先前stage产生的dangling对象，原位保留、不清理，不作为待push的可达历史。
