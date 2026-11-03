# Ubuntu 24.04：Python 3.12开发环境准备

日期：2026-10-28（Asia/Shanghai）。新环境已完成准备：**52项Python测试全部PASS、无跳过；P2B原始数据可重新生成一致统计及完整三张图**。没有执行Vivado、实物测试或Git提交。

## 环境与依赖

|项目|实际值|
|---|---|
|主机 / 系统|b760m / Ubuntu24.04；Python3.12.3|
|旧环境|`.venv`保持原样，不切换其链接、不安装包、不删除|
|新环境|`build/venvs/python312`；受现有`build/`忽略规则覆盖|
|安装依据|原`host/python/requirements-analysis.txt`包含`requirements.txt`；原文件未修改|
|pip / 核心依赖|pip26.2.2；pyserial3.5；numpy2.5.4；matplotlib3.11.2|
|已验证版本快照|[requirements-py312-ubuntu24.lock.txt](../host/python/requirements-py312-ubuntu24.lock.txt)|

系统没有ensurepip和pip，因此用`python3 -m venv --without-pip`创建新环境，再从官方PyPI下载pip wheel并按PyPI元数据的SHA256验证，仅在新环境引导pip。没有安装系统包或修改系统Python。引导来源记录为`build/env_setup_20261028/bootstrap/provenance.json`，完整安装日志为`pip_bootstrap.log`及`pip_install.log`。

依赖版本来自实际安装及验证。版本快照记录全部13项运行依赖，便于在Ubuntu24/Python3.12下重建；它不保证跨平台二进制相同，也不是含所有wheel哈希的严格供应链锁。

## 使用

不需要修改旧`.venv`或全局PATH；推荐显式使用新解释器：

```bash
cd /home/boksop/swcell
build/venvs/python312/bin/python --version
build/venvs/python312/bin/python -m pip check

# 也可只在当前shell激活；不会改变旧环境。
source build/venvs/python312/bin/activate
python --version
deactivate
```

安装/重建时，先准备一个新的3.12虚拟环境，再安装现有依赖声明，或安装本轮已验证版本快照。当前新环境位于build，清理build会一并移除它，清理前保留版本快照及环境准备日志；不需要将虚拟环境目录提交Git。

```bash
# 当前已安装，不必重复运行。
build/venvs/python312/bin/python -m pip install \
  -r host/python/requirements-analysis.txt
# 若需要重建相同版本集合：
build/venvs/python312/bin/python -m pip install \
  -r host/python/requirements-py312-ubuntu24.lock.txt
```

## 本次验证

|验证|结果|证据|
|---|---|---|
|依赖一致性|PASS，No broken requirements found|`build/env_setup_20261028/pip_check.log`|
|全部Python单元测试|PASS，52项，无跳过|`build/env_setup_20261028/python_tests.log`|
|测试范围|原协议/保存、伪终端串口/Ctrl+C、离线统计、窗口、门控、缓存校验及恢复/调度|已有测试，未修改测试源码|
|P2B统计重生成|PASS：96行phase、12行long；summary/CSV/report与历史版逐字节一致|`reanalysis_validation.json`|
|P2B图表重生成|PASS：Q相位、QM相位、频率结论三图均生成并通过PNG解码校验|新输出目录见下|
|旧环境/源码/历史结果保护|最终指纹核对见任务记录|`protected_before.json`及`protected_validation.json`|

本次测试命令：

```bash
PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/home/boksop/swcell/build/env_setup_20261028/matplotlib \
build/venvs/python312/bin/python -B -m unittest discover \
  -s host/python/tests -v
```

伪终端测试使用操作系统虚拟端口，不访问板卡UART；硬件编排相关测试使用mock，不生成或下载bitstream。日志中模拟测试出现SKIP/UNSUPPORTED是被测试场景，最终unittest结果没有skipped项。

## P2B离线结果

历史输入为`results/M11/phase2b_20261016_reset_sync/`。为了避免`--analyze`覆盖历史CSV/图表，本次先把raw、checkpoint及attempts复制到新的`build/env_setup_20261028/p2b_reanalysis/`，再对新目录运行分析：

```bash
PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/home/boksop/swcell/build/env_setup_20261028/matplotlib \
build/venvs/python312/bin/python -B host/python/swcell_phase2b.py \
  --analyze build/env_setup_20261028/p2b_reanalysis
```

可阅读[重新生成的图文结果](../build/env_setup_20261028/p2b_reanalysis/report.md)。输出含`summary.json`、`phase_scan.csv`、`long_run.csv`、`q_phase_scan.png`、`qm_phase_scan.png`、`frequency_summary.png`；原raw/checkpoint保持一致。

结论仍为75/100MHz `PASS_1E8_ZERO_ERRORS`、125MHz `MARGINAL_WINDOW`；最高可靠窗口亿次零错100MHz、最高观测125MHz。没有重新测量FPGA性能。新版matplotlib生成的PNG编码/字体可能与历史版不同，验证重点是数据/总结一致、图表有效，不能要求跨版本PNG哈希相同。

## Git与后续边界

纳管方案见[首次Git提交准备](git_tracking_plan.md)。新环境、安装日志和重生成结果均已被现有build/规则排除；根`.gitignore`没有修改。拟议补充规则单独保存在[gitignore.proposed](gitignore.proposed)，需用户确认后才合并。

本次未运行完整XSIM或Vivado，不代表Vivado2026.1兼容性通过。原回归Shell仍可能使用`.venv/bin/python`；本轮没有修改Shell/Tcl入口，未来运行RTL回归前应在独立适配任务中显式选择新解释器和工具版本，不能盲目使用旧venv。
