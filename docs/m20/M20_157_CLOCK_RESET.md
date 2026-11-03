# M20：时钟与复位物理规格初稿

2026-11-02。逻辑连接VERIFIED；电气预算ESTIMATED；实际skew、setup/hold与死区下限TBD。

物理相位草案ID：`M20-157-PHASE-DRAFT-0.1`；未冻结实测deadtime/skew，不等同于已放行硬件时钟规格。

## 时钟负载与建议

33位不是33个clock pin：两MUX每位各一个S，合计66个。LVC典型Cin2.5pF时仅pin电容即165pF，尚未含PCB/连接器/探头，不能由一个普通FPGA输出直接承担全部负载并宣称时序合格。

建议P1/P3优先评估非重叠两相，master_hold与slave_open各33个负载。每相分6支、每支5–6个S，典型12.5–15pF，再加走线。逻辑周期仍一个CPU微周期；死区在周期内，不增加指令状态。

|交接|master_hold|slave_open|动作|
|---|---:|---:|---|
|低相|0|0|Master透明、Slave保持|
|上升交接第一步|1|0|所有Master关闭|
|等待死区后|1|1|Slave打开，更新Q|
|下降交接第一步|1|0|所有Slave关闭|
|等待死区后|0|0|Master再打开|

初始100kHz小样可先研究100ns级死区，属于ESTIMATED调试设定，需按实测收敛，不是器件保证或本轮10ns模型值的放大证明。保持master_hold/slave_open的极性，不额外给每位插入不受控反相器。

## 缓冲与BOM

两相至少需要12路分支驱动能力；暂按两颗8路缓冲器规划，或两颗六路专用时钟扇出器研究。候选[TI CDCLVC1106产品资料](https://www.ti.com/product/CDCLVC1106)支持3.3V和6输出，但发布前必须核对其实际负载、跨片skew、脉宽/启停和低频/静态使用条件，不能把等负载单片输出skew套用到两个器件/整板。

reset另分4支，初稿一颗缓冲；电源良好监视器可另需一颗。此为新增辅助BOM，未加入543，不是已定型料号。分支端应预留源端串阻位置，值由IBIS/示波测量决定；不靠降低CPU频率消除快边沿反射。

## 同步复位与上电

所有33位D顶层都有rst选择，因此在原生FF模型中同步复位正确。但真实反馈回路上电未知，不能依赖GSR/initial。

启动顺序：电源稳定→FPGA配置并输出已知ROM/rst=1→slave_open=0且master_hold=0，等待D/QM确定→master_hold=1→死区→slave_open=1使Q确定→保持rst至少两个完整安全周期→在约定相位撤销reset→从RESET/FETCH进入PC0。复位不清RAM。

reset扇出34而非仅33（还驱动控制反相节点），典型加10pF走线估算95pF，需分区缓冲。断电/FPGA未配置时要确保相位、reset的默认电平和CPU/FPGA供电次序；拉电阻及监视器值TBD。rst单独保持而clock停在高相并不能完成真实同步初始化。

运行中rst应立即禁止FPGA待提交RAM写，CPU状态按下一安全边沿复位；已经发生的写不回滚。相关数字契约已由CPU与接口模型验证，真实复位走线及瞬态需P3测量。
