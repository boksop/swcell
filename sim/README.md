# 仿真与回归

模块TB/独立外部模型放模块目录，公共启动入口放scripts。M11的m11/models/phase2及M20历史m20*路径有意保留；各脚本只选需要的源，新增模块按sim/<模块>组织。

新M11输出在build/sim/m11，新模块仿真按build/sim/<模块>/<套件>；旧证据不搬迁。XSIM明确PASS标记＋进程退出码共同判断，Python套件使用tools/test/run_python_tests.py；仿真不等于STA或实物验证。
