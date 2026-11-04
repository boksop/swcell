# 逻辑源码

common用于可复用UART/PRBS/CDC/计数等；新模块放modules/<模块>，板级顶层与引脚放fpga/projects，不进入逻辑目录。既有rtl/m20各CPU版本是冻结参考位置，保留不搬迁，不把其不同版本一起递归编译。

M11：modules/m11；M20：m20。详细索引见docs/m11和docs/m20。
