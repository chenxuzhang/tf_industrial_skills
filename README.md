# Industrial Skills

hbip-scm 工业品 Agent 技能集合，用于查询库存和订单数据。

## 环境配置

| 环境 | 环境变量 | 默认地址 |
| --- | --- | --- |
| `local` | - | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | 需用户配置 |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | 需用户配置 |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | 需用户配置 |

认证令牌通过 `SCM_AUTH_TOKEN` 环境变量读取。

---

## Skills 概览

| Skill | 用途 | 支持的查询类型 |
| --- | --- | --- |
| [query-industrial-sellable-stock](#query-industrial-sellable-stock) | 查询可售库存 | SKU ID / SPU ID / SKU Code / SPU Code |
| [query-industrial-stock-detail](#query-industrial-stock-detail) | 查询库存明细 | SKU ID / SKU Code |
| [query-industrial-stock-flow](#query-industrial-stock-flow) | 查询库存流水 | SKU ID / SKU Code / 订单号 |
| [query-industrial-stock-reconcile](#query-industrial-stock-reconcile) | 查询库存对账 | 批次号 / 时间范围 |
| [query-industrial-order-data](#query-industrial-order-data) | 查询订单数据 | 订单号 |

---

## query-industrial-sellable-stock

**用途**: 查询工业品项目可售库存（Redis 缓存 + 数据库）

**API 端点**: `POST /scm/inner/stock/agent-api/query-sellable-stock`

### 支持的查询类型

| 输入类型 | 请求字段 | 示例 |
| --- | --- | --- |
| 纯数字（默认 SKU ID） | `skuIds` | `[1, 2]` |
| 明确为 SPU ID | `spuIds` | `[6]` |
| `SKU` 开头字符串 | `skuCodes` | `["SKU26060300019000001"]` |
| `SPU` 开头字符串 | `spuCodes` | `["SPU26060300016000001"]` |

### 响应字段

| 字段 | 含义 |
| --- | --- |
| `virtualStock` | Redis 缓存可售库存（6 位小数精度） |
| `dbVirtualStock` | 数据库可售库存 |
| `queryCondition` | 匹配的查询条件 |

### 对话示例

```
用户: 帮我查询一下本地环境 skuId 为 1 和 2 的可售库存
用户: 查询测试环境 SKU26060300019000001 的可售库存
用户: 帮我查下 pre 环境 skuId 1、2 和 spuCode SPU26060300016000001 的库存
用户: 查询生产环境 spuId 6 的可售库存
```

### 结果展示格式

| 查询条件 | 店铺 | SKU ID | SKU 名称 | Redis 可售 | DB 可售 |
| --- | --- | --- | --- | --- | --- |
| skuId:1 | xx店 | 1 | 商品A | 100 | 100 |

---

## query-industrial-stock-detail

**用途**: 查询数据库库存明细（真实库存、冻结库存、可售库存）

**API 端点**: `POST /scm/inner/stock/agent-api/query-stock-detail`

### 支持的查询类型

| 输入类型 | 请求字段 | 示例 |
| --- | --- | --- |
| SKU ID | `skuIds` | `[1, 2]` |
| SKU Code | `skuCodes` | `["SKU26060300019000001"]` |

> 注意：此端点仅支持 SKU 级别查询，不支持 SPU ID/Code。

### 响应字段

| 字段 | 含义 |
| --- | --- |
| `realStock` | 数据库真实库存 |
| `frozenStock` | 数据库冻结库存 |
| `virtualStock` | 数据库可售库存 |

### 对话示例

```
用户: 查询测试环境 skuId 1 和 2 的库存明细
用户: 查询本地环境 SKU26060300019000001 的库存明细
用户: 查一下 pre 环境 skuId 1 和 skuCode SKU26060300019000001 的真实库存
```

### 结果展示格式

| 查询条件 | 店铺 | SKU ID | SKU 名称 | 真实库存 | 冻结库存 | 可售库存 |
| --- | --- | --- | --- | --- | --- | --- |
| skuId:1 | xx店 | 1 | 商品A | 150 | 50 | 100 |

---

## query-industrial-stock-flow

**用途**: 查询库存流水（原始流水记录 或 按订单聚合的库存变更）

**API 端点**:
- `POST /scm/inner/stock/agent-api/query-stock-flow-page` - 按 SKU 查询原始库存流水
- `POST /scm/inner/stock/agent-api/query-stock-flow` - 按订单号查询聚合库存变更

### 原始库存流水查询

按 SKU ID 或 SKU Code 查询分页的库存流水记录。

**请求字段**:

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `pageNo` | 是 | 页码 |
| `skuIds` | 条件必填 | SKU ID 列表 |
| `skuCodes` | 条件必填 | SKU Code 列表 |
| `stockTypes` | 否 | 库存类型筛选 |
| `flowTypes` | 否 | 流水类型筛选 |

**支持的库存类型**: `REAL_STOCK`（真实库存）、`FROZEN_STOCK`（冻结库存）、`VIRTUAL_STOCK`（可售库存）

**支持的流水类型**: `REDUCE_SELLABLE_STOCK`、`ADD_FROZEN_STOCK`、`ADD_SELLABLE_STOCK`、`REDUCE_FROZEN_STOCK`、`REDUCE_REAL_STOCK`、`MANUAL_INCREASE`、`MANUAL_DECREASE`

### 聚合库存变更查询

按主订单号、子订单号或退款单号查询下单、取消/退款、出库阶段的聚合库存变更。

**请求字段**:

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `uniqueNo` | 是 | 主订单号、子订单号或退款单号 |

### 对话示例

```
用户: 查询测试环境 skuId 1 的库存流水
用户: 查询 SKU26060300019000001 的可售库存变更记录
用户: 查询主订单 MAIN_1001 的库存变更情况
用户: 查询退款单 RF_1001 的库存变更
```

### 结果展示格式

**原始流水**:

| 业务单号 | 店铺 | SKU ID | SKU 名称 | 库存类型 | 流水类型 | 变更数量 | 变更前 | 变更后 | 创建人 | 创建时间 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

**聚合变更**:

| 子订单号 | 店铺 | SKU ID | SKU 名称 | 关联主单 | 关联退款单 | 下单变更 | 取消/退款变更 | 出库变更 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

---

## query-industrial-stock-reconcile

**用途**: 查询库存对账批次和待处理差异明细

**API 端点**:
- `POST /scm/inner/stock/agent-api/query-reconcile-batch` - 查询对账批次列表
- `POST /scm/inner/stock/agent-api/query-reconcile-detail` - 查询批次差异明细

### 对账批次查询

查询对账批次列表，支持按时间范围筛选。

**请求字段**:

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `pageNo` | 是 | 页码 |
| `startTimeFrom` | 否 | 批次开始时间下限（含） |
| `startTimeTo` | 否 | 批次开始时间上限（含） |

时间格式: `yyyy-MM-dd HH:mm:ss`

### 差异明细查询

查询指定批次的待处理库存差异和修复建议。

**请求字段**:

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `pageNo` | 是 | 页码 |
| `batchNo` | 是 | 对账批次号 |

### 对话示例

```
用户: 查询最近的对账批次
用户: 查询 2026-06-01 到 2026-06-10 的对账批次
用户: 查询批次 RECONCILE_202606100001 的差异明细
```

### 结果展示格式

**批次列表**:

| 批次号 | 状态 | 应扫描数 | 已扫描数 | 差异数 | 开始时间 | 结束时间 |
| --- | --- | --- | --- | --- | --- | --- |

**差异明细**:

| 批次号 | 店铺 | SKU ID | SKU 名称 | DB库存（真实/冻结/可售） | Redis可售 | 差异 | 差异类型 | 修复目标 | 修复建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

---

## query-industrial-order-data

**用途**: 查询工业品订单数据（主订单、子订单、退款单、正向订单、逆向订单）

### API 端点列表

| 用户意图 | API 端点 |
| --- | --- |
| 判断单号类型（主订单/子订单/退单） | `/scm/inner/stock/agent-api/query-order-type` |
| 查询主订单下所有子订单 | `/scm/inner/stock/agent-api/query-sub-order-nos` |
| 根据正向单号查询关联退款单号 | `/scm/inner/stock/agent-api/query-refund-nos` |
| 根据子订单查询主订单 | `/scm/inner/stock/agent-api/query-main-order-no` |
| 根据退款单号查询关联子订单 | `/scm/inner/stock/agent-api/query-sub-order-by-refund-no` |
| 查询正向订单及商品详情 | `/scm/inner/stock/agent-api/query-forward-order-data` |
| 查询退款单及退款商品详情 | `/scm/inner/stock/agent-api/query-reverse-order-data` |

### 请求格式

所有 API 均使用 `POST`，请求体为 JSON 字符串数组：

```json
["ORDER_NO_1", "RF_1001"]
```

### 对话示例

```
用户: 帮我判断一下 ORDER_1001 是什么类型的订单
用户: 查询主订单 MAIN_1001 下的所有子订单
用户: 查询子订单 SUB_1001 关联的退款单号
用户: 查询测试环境主订单 MAIN_1001 的商品详情
用户: 查询退款单 RF_1001 的退款商品详情
```

### 结果展示格式

**订单类型/关系查询**:

| 输入单号 | 查询结果 |
| --- | --- |
| ORDER_1001 | 子订单 |

**正向订单详情**:

| 主订单号 | 子订单号 | 店铺 | SKU ID | SKU 名称 | 下单数量 |
| --- | --- | --- | --- | --- | --- |
| MAIN_1001 | SUB_1001 | xx店 | 1 | 商品A | 2 |

**退款单详情**:

| 退款单号 | 子订单号 | SKU ID | SKU 名称 | 退款数量 |
| --- | --- | --- | --- | --- |
| RF_1001 | SUB_1001 | 1 | 商品A | 1 |
