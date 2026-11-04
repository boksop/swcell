# SwCell 首次GitHub Private发布记录

2026-11-04，Asia/Shanghai。**当前状态：本地准备中；GitHub认证尚未完成，未创建远程仓库、未push。** 本页后续只记录真实执行结果，不预填URL/SHA。

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

GitHub CLI v2.103.3由[官方发行包](https://github.com/cli/cli/releases/tag/v2.103.3)安装，发行包SHA256与官方checksums一致，路径~/.local/bin/gh；当前未登录。用户使用浏览器gh auth login，不提供Token到聊天或代码。

Vivado/XSIM2026.1.1（V3）、历史M11的2022.1、厂商安装与许可需使用者提供；Python3.12及依赖快照在host/python。当前V3无外部XCI/未纳管IP/子模块/Git LFS依赖。大bit/原始完整波形只能按本机索引另行备份。

## 尚待执行

1. 本地分单元提交及干净恢复：网表字节/477+33、Python、XSIM和综合。
2. 创建明确FUNCTIONAL_STORAGE通过、STRICT_MUX未放行的V3 annotated Tag。
3. gh认证后确认owner/名称/无冲突origin，创建Private仓库，正常push main/正式tags。
4. 远程main/tag SHA、独立远程检出、README/关键文件/无缓存验证。

远程URL、main SHA、V3 commit/tag、最终跟踪数/仓库大小及恢复日志待实际完成后补充。当前不能声称已能通过GitHub连接器在线读取；Private库还需相应连接器/账号权限，未在本任务中验证该授权。

## 已知边界

FUNCTIONAL_STORAGE为477组合MUX＋33原生FF实机通过；STRICT_MUX有85 LUTLP-1/WNS−22.002ns，无bit/无硬件放行；实体157时序未签核。原545候选非法HALT缺陷、原603基线和V2.4失败反例保留。

旧M11七个原始数据文档链接在本机缺失，既有报告/源码不伪造恢复；这些不是本轮遗漏删除。Git fsck未报告损坏，存在先前stage产生的dangling对象，原位保留、不清理，不作为待push的可达历史。
