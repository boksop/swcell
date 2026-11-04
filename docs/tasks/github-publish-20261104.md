# SWCELL-GITHUB-PUBLISH-20261104

状态IN_PROGRESS，2026-11-04，main，起始HEAD70daf6f。用户明确授权本次本地提交、V3 annotated Tag、创建Private GitHub仓库swcell及正常push。此前“仅本地、不远程”的会话限制由本次授权取代；不延伸为未来自动发布/Public权限。

## 已核实 / 已完成

- [x] 现有12提交、4个annotated tags；V2.3 aecf570及Tag、V2.4 4a95665/48564b5及Tag均存在，不重写。
- [x] main无remote、无旧暂存；561个既有跟踪文件，V3/外设诊断未提交。初始status/index/diff保存于build/github_publish_20261104/。
- [x] 首轮全部可达对象扫描：786 blob/266 tree/12 commit/4 tag，未发现匹配的凭据、历史缓存或>50MiB对象；最大blob2045358字节。该模式扫描不等于万能保密/版权证明。
- [x] 官方GitHub CLI v2.103.3安装至~/.local/bin/gh，发行包SHA256验证。用户已完成浏览器登录，gh核对活动账号boksop；未索取或存储Token到代码。
- [x] .gitignore补充Vivado辅助报告、缓存及本地凭据模式；不删除原文件。

## 待完成（按顺序）

- [x] 固定V3核心/板级/软件/源SHA及实机证据，保存小型可用于Private仓库的原样副本和哈希；大缓存/bit/波形留本地。
- [x] 更新README、V3整体正式报告、版本边界/来源/第三方依赖和可复现入口；不选择许可证。
- [x] 全部待纳管文件和全历史再次扫描；明确清单暂存/本地提交；不得误入clockInfo/tight_setup_hold_pins。
- [x] 干净隔离检出验证：Python164项、网表逐字节再生成/477+33计数、V3关键XSIM及可用的Vivado综合。
- [x] 创建m20-v3-fpga-hardware-verified annotated Tag：仅FUNCTIONAL_STORAGE上板通过，STRICT_MUX反馈存储未放行，实体157时序开放。
- [ ] gh认证成功后确认活动账号/owner、swcell名称、无冲突origin；创建Private仓库、push main和正式标签，不force。
- [ ] 隔离远程检出，检查main/标签SHA、关键文件/README/无缓存，保存最终发布报告并push文档。

## 依赖与风险

认证已完成：个人账号boksop，swcell查询404，当前无origin。仓库owner以成功登录的活动个人账号为默认；如多账号/已存在同名仓库/冲突origin，先报告，不覆盖。

旧M11报告有7个原始数据链接本机缺失，是既有问题；不伪造补全，不影响现有源码纳管。M0～M19非M11独立源码/实际PCB原理图在当前树未找到，不创建虚假资源。部分历史目录是估算/提案，正式验收以版本报告为准。

所有功能RTL/ISA/机器码不修改；不重新做实物测试，不写Flash。实体157最小延迟无保证、STRICT_MUX 85 LUTLP-1等失败证据保留。现有4标签对象保持字节不变。

## 恢复入口

先读根TASK、本文、git status及build/github_publish_20261104/审计。gh路径/home/boksop/.local/bin/gh；检查gh auth status，不输出token。认证未完成时继续剩余本地项，不创建假URL/远程结果。使用tools/git/github_publish_audit.py复核当前全部候选及历史；所有输出选新目录。已有提交或Tag须先核对，不重复创建，不reset/rebase/amend/force。

本地已完成：b4081d3诊断、8fab9f6 V3，Tag目标8fab9f6；干净恢复详见docs/evidence/m20_v3_recovery_20261104.json。下一步远程创建及推送，当前尚未执行。不重复创建Tag。

## 远程发布与工具修正检查点

Private https://github.com/boksop/swcell已创建并push main bbf229e及5正式tags。独立远程克隆、759文件逐blob、README API及远程Tag对象/目标均匹配；记录docs/evidence/github_initial_remote_verification_20261104.json。

真实新失败：远程克隆Python168项中1项test_audit_is_read_only_for_git_index失败，原因旧审计器拒绝所有remote；CPU不受影响。原失败build/github_publish_20261104/remote_python.txt保留。修正只读工具认可用户明确授权的origin URL，新增config/git_publication.json及两项正反测试，旧manifest/Tag不改。当前本机170项通过，待提交修复并从新远程克隆验证；V3源67项仍须相同，不能把工具修正当成新硬件验证。
