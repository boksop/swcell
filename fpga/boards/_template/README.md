# 板卡资源接入

新板卡建 `fpga/boards/<board_id>/`，记录真实part、系统时钟/极性、共享IO、配置电压和资料来源。未知字段保留TODO，不猜引脚或速度等级。

board.tcl只保存物理板级参数；公共约束不包含M11/M20等模块私有连接。各工程独立生成create_clock并引用公共XDC，避免重复时钟定义。局部配置使用board.local.tcl（忽略），不得带入凭据/许可文件。
