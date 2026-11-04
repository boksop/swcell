# SwCell 当前任务进度

2026-11-04，Asia/Shanghai。main；起始HEAD70daf6f。当前主要任务 **SWCELL-GITHUB-PUBLISH-20261104：IN_PROGRESS**。

## 目标与授权

保留全部本地历史/4个正式标签，将既有V3 FPGA功能原型和历史SwCell源码/小型证据定版，创建Private GitHub仓库swcell并正常推送main与正式Tag。用户本次已明确授权commit/tag/远程创建/push，取代此前任务的仅本地限制。不改RTL/ISA/游戏功能，不Public、不改历史、不force、不写Flash。

详情：[发布任务](docs/tasks/github-publish-20261104.md)。

## 已确认

- 本地12提交、561跟踪文件；V2.3/V2.4已提交并有annotated Tag，原对象须保持。
- V3/独立OLED诊断已分单元提交b4081d3/8fab9f6，无旧stage丢失；不覆盖任何用户修改。初始status/index/diff已保存在build/github_publish_20261104。
- 全历史首轮扫描PASS：786blob/266tree/12commit/4tag；无匹配凭据/历史缓存/超50MiB文件，最大2045358字节。仍需最终候选复扫/版权范围说明。
- GitHub CLI v2.103.3已安装且官方包SHA验证；用户已完成浏览器登录，活动个人账号boksop、swcell查询404、origin为空。
- V3实际为477组合MUX＋33原生FF FUNCTIONAL_STORAGE；实机Pong/Snake/输入/OLED已获用户确认。STRICT_MUX85 LUTLP-1无bit，实体157时序不纳入验收。当前F06 bit及证据不修改。

## 下一步

1. 读发布任务；补充小型原样实机/路由/失败证据和来源SHA清单，完善README/正式V3报告/许可边界。
2. 最终全历史/候选审计后分单元暂存提交；干净隔离恢复验证Python/网表/XSIM/综合，创建明确边界的V3Tag。
3. `/home/boksop/.local/bin/gh auth status`；用户认证完成后验证活动owner/swcell名称/无冲突origin，创建Private仓库与正常push。认证未完成时只停远程动作，继续本地工作。
4. 验证远程main/正式标签SHA、独立检出、关键源码和README，写真实发布报告。不能在认证/推送未完成时编造URL或远程PASS。

## 历史入口与限制

- [V3详细任务](docs/tasks/m20-v3-fpga-20261104.md)、[F06交互验收](docs/reports/m20_phaseV3-F06_20261104.md)、[外设诊断](docs/tasks/oled-keys-20261104.md)。
- 旧M11有7个原始数据链接本机缺失，属既有问题，不伪造；现存原始build/results不删除、不移动。
- clockInfo.txt/tight_setup_hold_pins.txt已确认Vivado辅助输出，新增ignore，不删除。大波形、bitstream、环境/凭据不发布。
- 未来功能/PCB/CPU优化不在本任务范围。当前只完成版本管理与首次Private发布。

最新检查点：隔离检出8fab9f6全部恢复检查PASS：Python168、核心87/57331、非法/算术/访存、板级SPI/键/UART、10生成文件字节、67源SHA/74证据SHA、477/33/543及20发生器、Vivado新综合。V3 annotated Tag已建立且目标8fab9f6，旧4Tag对象不变。准备创建Private远程并push，尚未执行远程发布。
