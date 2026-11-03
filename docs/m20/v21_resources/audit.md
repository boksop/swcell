# M20 V2.1 独立资源审计

状态 VERIFIED；从SV逐pin/无条件FF-D解析，与生成器JSON交叉核对。

|口径|组合MUX|存储折算|总数|
|---|---:|---:|---:|
|完整验证接口|477|66|543|
|纯功能核心|476|66|542|

33功能状态，33个显式reset选择已包含组合；debug-only 1颗用于trap_event。
最大拓扑29，最大输入pin负载34；不是实物时序证明。

|组|组合MUX|
|---|---:|
|alu|55|
|ar|51|
|bus|17|
|control|47|
|decode|132|
|flags|23|
|pc|73|
|result|55|
|storage|24|

检查：实例/端口/每pin、33状态/FF-D/reset、已驱动源/多驱动/环路、功能与debug锥/死网；所有数值可重生成。
详见v21_resources/audit.json、nodes.csv、fanout.csv；nativeFF仍须真实双MUX DFF另验证。
