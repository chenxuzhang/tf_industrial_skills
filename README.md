# Industrial Skills

## stock (库存)

### query-industrial-sellable-stock

**用途**: 查询工业品项目可售库存

**触发条件**: 当需要通过 SKU ID、SPU ID、SKU Code 或 SPU Code 查询 hbip-scm 工业品可售库存时使用。

**支持环境**: local、test、pre-release、production

**API 端点**: `/scm/inner/stock/agent-api/query-sellable-stock`

#### 对话使用示例

**示例 1: 查询本地环境**

```
用户: 帮我查询一下本地环境 skuId 为 1 和 2 的可售库存
```

**示例 2: 查询测试环境**

```
用户: 查询测试环境 SKU26060300019000001 的可售库存
```

**示例 3: 混合查询**

```
用户: 帮我查下 pre 环境 skuId 1、2 和 spuCode SPU26060300016000001 的库存
```

**示例 4: 查询生产环境**

```
用户: 查询生产环境 spuId 6 的可售库存
```

---

### query-industrial-stock-detail

**用途**: 查询数据库库存明细（真实库存、冻结库存、可售库存）

**触发条件**: 当需要通过 SKU ID 或 SKU Code 查询 hbip-scm 数据库库存明细时使用。

**支持环境**: local、test、pre-release、production

**API 端点**: `/scm/inner/stock/agent-api/query-stock-detail`

#### 对话使用示例

**示例 1: 通过 SKU ID 查询**

```
用户: 查询测试环境 skuId 1 和 2 的库存明细
```

**示例 2: 通过 SKU Code 查询**

```
用户: 查询本地环境 SKU26060300019000001 的库存明细
```

**示例 3: 混合查询**

```
用户: 查一下 pre 环境 skuId 1 和 skuCode SKU26060300019000001 的真实库存
```

---

### query-industrial-order-data

**用途**: 查询工业品订单数据（主订单、子订单、退款单、正向订单、逆向订单）

**触发条件**: 当需要判断订单类型或查询主订单、子订单、退款单、正向订单、逆向订单数据时使用。

**支持环境**: local、test、pre-release、production

**API 端点**:
- `/scm/inner/stock/agent-api/query-order-type` - 判断订单类型
- `/scm/inner/stock/agent-api/query-sub-order-nos` - 查询子订单号
- `/scm/inner/stock/agent-api/query-refund-nos` - 查询退款单号
- `/scm/inner/stock/agent-api/query-main-order-no` - 查询主订单号
- `/scm/inner/stock/agent-api/query-sub-order-by-refund-no` - 根据退款单查询子订单
- `/scm/inner/stock/agent-api/query-forward-order-data` - 查询正向订单详情
- `/scm/inner/stock/agent-api/query-reverse-order-data` - 查询退款单详情

#### 对话使用示例

**示例 1: 判断订单类型**

```
用户: 帮我判断一下 ORDER_1001 是什么类型的订单
```

**示例 2: 查询子订单**

```
用户: 查询主订单 MAIN_1001 下的所有子订单
```

**示例 3: 查询退款单**

```
用户: 查询子订单 SUB_1001 关联的退款单号
```

**示例 4: 查询正向订单详情**

```
用户: 查询测试环境主订单 MAIN_1001 的商品详情
```

**示例 5: 查询退款单详情**

```
用户: 查询退款单 RF_1001 的退款商品详情
```
