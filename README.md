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
