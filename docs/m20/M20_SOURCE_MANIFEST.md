# M20 当前源码与生成物清单

机器清单为[M20_SOURCE_MANIFEST.json](M20_SOURCE_MANIFEST.json)。列出的均为可恢复的源码、必要配置/机器码和验证工具，不依赖ignored build；SHA256对原始字节计算。清单不包含自身，也不包含本文或未来提交SHA，避免自引用。

冻结ISA JSON、ISA实现、Pong/Snake汇编及小型未填充参考ROM均有SHA；ROM来自原汇编只读组装，必须与早已冻结的binary SHA一致，不修改旧日志/ROM来适配新结果。正式V2-603和V2.1-543生成SV/连接JSON可逐字节重生成。

`software/m20_300/reference/v1_source_paths.json`保留原V1的32个来源路径及当时SHA；新回归读取这份纳管路径定义并计算当前源码SHA，历史SHA不冒充当前测试通过。原build/m20_300/v1/inputs_manifest.json保持不变。

只读审计命令：

```bash
python3 -B tools/git/local_release_audit.py --output build/local_release_audit_NEW
```

程序仅运行本地Git查询、读取来源、在私有临时目录重生成并进行独立计数；只写新审计输出和私有scratch，不修改源文件/索引/commit、不清理历史、不使用网络。报告会列commit、tags、脏状态、逐文件SHA、14份网表再生、ISA/ROM、477组合/33状态/543总与603参照。Python单元测试和XSIM需另行运行并关联真实日志，不由工具假造PASS。

新增/修改源码后，应在新的版本中明确更新机器清单；不能改旧证据/旧清单来匹配预期SHA。旧v21_resources/source_manifest.json及历史Git提案保留生成当时的内容，不作为本次恢复工具的可变输入。
