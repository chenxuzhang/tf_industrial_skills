# Industrial Skills

hbip-scm 工业品 Agent 技能集合，涵盖库存查询、订单查询、Redis 查询、Nacos 配置查询、GitLab CI 流水线操作和 PMS 登录功能。

## 项目简介

本项目为 hbip-scm 工业品系统提供了一系列 Agent 技能，用于自动化执行常见的运维和查询任务。这些技能可以帮助开发人员和运维人员快速查询库存信息、订单数据、配置信息，以及管理 CI/CD 流水线。

## 快速开始

### 常见使用场景

#### 查询库存
- 查询可售库存：`帮我查询一下本地环境 skuId 为 1 和 2 的可售库存`
- 查询库存明细：`查询测试环境 skuId 1 和 2 的库存明细`
- 查询库存流水：`查询测试环境 skuId 1 的库存流水`

#### 查询订单
- 判断订单类型：`帮我判断一下 ORDER_1001 是什么类型的订单`
- 查询订单详情：`查询测试环境主订单 MAIN_1001 的商品详情`
- 查询退款单：`查询退款单 RF_1001 的退款商品详情`

#### 管理配置
- 查询命名空间：`查询测试环境的命名空间列表`
- 查询配置内容：`查看测试环境 application.yml 的配置内容`
- 查询服务实例：`查询测试环境 hbip-scm 服务的实例列表`

#### CI/CD 操作
- 查询流水线：`查看最近的流水线执行记录`
- 创建流水线：`创建测试环境流水线`

#### PMS 登录
- 登录测试环境：`登录测试环境 PMS`
- 登录预发布环境：`登录预发布环境 PMS`

### 环境配置快速参考

#### 库存/订单服务

| 环境 | 环境变量 | 默认地址 |
| --- | --- | --- |
| `local` | - | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | 需用户配置 |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | 需用户配置 |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | 需用户配置 |

认证令牌通过 `SCM_AUTH_TOKEN` 环境变量读取。

#### Nacos 服务

连接信息从 `~/.nacos/config.json` 或环境变量 `NACOS_{ENV}_ADDR`、`NACOS_{ENV}_USERNAME`、`NACOS_{ENV}_PASSWORD` 读取。支持环境：`test`、`staging`、`prod`。

#### GitLab CI

需在目标 Git 仓库目录下执行，依赖 `glab` 和 `jq` CLI 工具。

---

## 目录结构

```
tf_industrial_skills/
├── gitlab/
│   └── gitlab-pipeline-operations/    # GitLab CI 流水线操作
├── nacos/
│   └── nacos-query/                   # Nacos 配置与服务查询
└── stock/
    ├── pms-login/                     # PMS 管理后台登录
    ├── query-industrial-order-data/       # 订单数据查询
    ├── query-industrial-sellable-stock/   # 可售库存查询
    ├── query-industrial-stock-detail/     # 库存明细查询
    ├── query-industrial-stock-flow/       # 库存流水查询
    ├── query-industrial-stock-reconcile/  # 库存对账查询
    └── query-industrial-stock-redis/      # 库存 Redis 查询
```

## 环境配置

### 库存 / 订单服务

| 环境 | 环境变量 | 默认地址 |
| --- | --- | --- |
| `local` | - | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | 需用户配置 |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | 需用户配置 |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | 需用户配置 |

认证令牌通过 `SCM_AUTH_TOKEN` 环境变量读取。

### Nacos 服务

连接信息从 `~/.nacos/config.json` 或环境变量 `NACOS_{ENV}_ADDR`、`NACOS_{ENV}_USERNAME`、`NACOS_{ENV}_PASSWORD` 读取。支持环境：`test`、`staging`、`prod`。

### GitLab CI

需在目标 Git 仓库目录下执行，依赖 `glab` 和 `jq` CLI 工具。

---

## Skills 概览

| Skill | 用途 | 关键能力 |
| --- | --- | --- |
| [query-industrial-sellable-stock](#query-industrial-sellable-stock) | 查询可售库存 | SKU ID / SPU ID / SKU Code / SPU Code，Redis + DB 双源 |
| [query-industrial-stock-detail](#query-industrial-stock-detail) | 查询库存明细 | SKU ID / SKU Code，真实/冻结/可售库存 |
| [query-industrial-stock-flow](#query-industrial-stock-flow) | 查询库存流水 | 原始流水 / 按订单聚合变更 |
| [query-industrial-stock-redis](#query-industrial-stock-redis) | 查询库存 Redis | 数据源配置 / Key 模式 / Key 值查询 |
| [query-industrial-stock-reconcile](#query-industrial-stock-reconcile) | 查询库存对账 | 批次快照对账 / 可售库存流水对账 |
| [query-industrial-order-data](#query-industrial-order-data) | 查询订单数据 | 订单类型判断 / 正向&退款订单详情 |
| [nacos-query](#nacos-query) | 查询 Nacos 配置 | 命名空间 / 配置 / 服务实例 / SCM IP |
| [gitlab-pipeline-operations](#gitlab-pipeline-operations) | GitLab CI 流水线 | 查询记录 / 按 ID 查详情 / 创建流水线 |
| [pms-login](#pms-login) | PMS 管理后台登录 | 环境选择 / 安全登录 / 令牌管理 |

---

## query-industrial-sellable-stock

**用途**: 查询工业品项目可售库存（Redis 缓存 + 数据库）

**API 端点**: `POST /scm/admin/stock/query/query-sellable-stock`

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
用户: 查询本地环境所有 SKU 的可售库存
用户: 查询测试环境 SKU26060300019000001 和 SPU26060300016000001 的库存对比
```

### 结果展示格式

| 查询条件 | 店铺 | SKU ID | SKU 名称 | Redis 可售 | DB 可售 |
| --- | --- | --- | --- | --- | --- |
| skuId:1 | xx店 | 1 | 商品A | 100 | 100 |

---

## query-industrial-stock-detail

**用途**: 查询数据库库存明细（真实库存、冻结库存、可售库存）

**API 端点**: `POST /scm/admin/stock/query/query-stock-detail`

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
用户: 查询生产环境所有 SKU 的库存明细
用户: 查询测试环境冻结库存大于 0 的 SKU
```

### 结果展示格式

| 查询条件 | 店铺 | SKU ID | SKU 名称 | 真实库存 | 冻结库存 | 可售库存 |
| --- | --- | --- | --- | --- | --- | --- |
| skuId:1 | xx店 | 1 | 商品A | 150 | 50 | 100 |

---

## query-industrial-stock-flow

**用途**: 查询库存流水（原始流水记录 或 按订单聚合的库存变更）

**API 端点**:
- `POST /scm/admin/stock/query/query-stock-flow-page` - 按 SKU 查询原始库存流水
- `POST /scm/admin/stock/query/query-stock-flow` - 按订单号查询聚合库存变更

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

**支持的流水类型**: `REDUCE_SELLABLE_STOCK`、`ADD_FROZEN_STOCK`、`ADD_SELLABLE_STOCK`、`REDUCE_FROZEN_STOCK`、`REDUCE_REAL_STOCK`、`ADD_REAL_STOCK`、`MANUAL_INCREASE`、`MANUAL_DECREASE`

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
用户: 查询本地环境 skuId 1 最近 10 条库存流水
用户: 查询测试环境所有 REAL_STOCK 类型的库存流水
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
- `POST /scm/admin/stock/query/query-reconcile-batch` - 查询对账批次列表
- `POST /scm/admin/stock/query/query-reconcile-detail` - 查询批次差异明细
- `POST /scm/admin/stock/query/reconcile-sellable-stock-flow` - 按时间范围和 SKU 对账 Redis、数据库可售库存流水

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
用户: 查询最近 7 天的对账批次
用户: 查询有差异的对账批次
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
| 判断单号类型（主订单/子订单/退单） | `/scm/admin/stock/query/query-order-type` |
| 查询主订单下所有子订单 | `/scm/admin/stock/query/query-sub-order-nos` |
| 根据正向单号查询关联退款单号 | `/scm/admin/stock/query/query-refund-nos` |
| 根据子订单查询主订单 | `/scm/admin/stock/query/query-main-order-no` |
| 根据退款单号查询关联子订单 | `/scm/admin/stock/query/query-sub-order-by-refund-no` |
| 查询正向订单及商品详情 | `/scm/admin/stock/query/query-forward-order-data` |
| 查询退款单及退款商品详情 | `/scm/admin/stock/query/query-reverse-order-data` |

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
用户: 查询本地环境子订单 SUB_1001 的订单详情
用户: 查询测试环境所有退款单的详情
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

| 退款单号 | 子订单号 | 订单状态 | SKU ID | SKU 名称 | 退款数量 |
| --- | --- | --- | --- | --- | --- |
| RF_1001 | SUB_1001 | 已完成 | 1 | 商品A | 1 |

---

## query-industrial-stock-redis

**用途**: 查询 hbip-scm 库存 Redis 数据源配置、Key 模式和 Key 值

**API 端点**:
- `POST /scm/admin/stock/redis/query-redis-config` - 查询 Redis 数据源配置
- `POST /scm/admin/stock/redis/query-redis-keys` - 查询支持的 Redis Key 模式
- `POST /scm/admin/stock/redis/query-redis-value` - 查询指定 Key 的值、类型和 TTL

### 查询 Redis 配置

无需请求体，返回数据源列表（名称、DB 索引、超时、序列化器）。

### 查询 Redis Key 模式

请求体为 `{}`，当前支持的模式：

| Key 模式 | 占位符 | 用途 |
| --- | --- | --- |
| `hbip-scm:scm-stock:scm-stock-service:stock:freeze:idempotent:%s` | 主订单号 | 下单库存冻结幂等 |
| `hbip-scm:scm-stock:scm-stock-service:stock:unfreeze:idempotent:%s` | 子订单号 / 退款单号 | 库存解冻幂等 |

### 查询 Redis 值

```json
{
  "keys": [
    {"key": "hbip-scm:scm-stock:scm-stock-service:stock:freeze:idempotent:MAIN_ORDER_NO", "dataSource": "可选数据源名"},
    {"key": "hbip-scm:scm-stock:scm-stock-service:stock:unfreeze:idempotent:RF_1001"}
  ]
}
```

### 对话示例

```
用户: 查看测试环境 stock Redis 数据源配置
用户: 查看当前支持哪些 Redis Key 模式
用户: 查询 key hbip-scm:scm-stock:scm-stock-service:stock:freeze:idempotent:ORDER_1001 的值
用户: 查询本地环境 Redis 数据源配置
用户: 查询测试环境所有 Redis Key 模式
用户: 查询 key hbip-scm:scm-stock:scm-stock-service:stock:unfreeze:idempotent:RF_1001 的值
```

### 结果展示格式

**配置**:

| 数据源 | 主数据源 | DB | 超时(ms) | 序列化覆盖 |
| --- | --- | --- | --- | --- |
| primary | 是 | 0 | 2000 | - |

**Key 值**:

| Key | 类型 | TTL(秒) | 值 |
| --- | --- | --- | --- |
| ... | string | -1 | {"status":1} |

---

## nacos-query

**用途**: 查询 Nacos 配置中心的命名空间、配置列表、配置内容、服务列表和服务实例详情

**执行方式**: 在技能目录下通过 `uvx --from .` 执行 Python CLI

### SCM IP 快捷查询

当用户查询 SCM IP / hbip-scm 节点时，直接执行：

```bash
uvx --from . nacos-get-service-detail --env test --service-name hbip-scm --group DEFAULT_GROUP --namespace industrial-test
```

### 命令列表

| 命令 | 功能 | 必需参数 | 可选参数 |
| --- | --- | --- | --- |
| `nacos-get-namespaces` | 获取命名空间列表 | `--env` | `--config` |
| `nacos-get-config-list` | 获取配置列表 | `--env` | `--namespace`, `--config` |
| `nacos-get-config-content` | 获取配置内容 | `--env`, `--data-id` | `--group`, `--namespace`, `--config` |
| `nacos-get-services` | 获取服务列表 | `--env` | `--namespace`, `--group`, `--page-no`, `--page-size`, `--config` |
| `nacos-get-service-detail` | 获取服务实例详情 | `--env`, `--service-name` | `--group`, `--namespace`, `--config` |

### 对话示例

```
用户: 查询测试环境的命名空间列表
用户: 查询 industrial-test 命名空间下的配置列表
用户: 查看测试环境 application.yml 的配置内容
用户: 查询测试环境 hbip-scm 服务的实例列表
用户: 查询预发布环境的命名空间列表
用户: 查询生产环境 application.properties 的配置内容
用户: 查询测试环境所有服务的实例列表
```

---

## pms-login

**用途**: 登录 PMS 管理后台，获取授权令牌

**执行方式**: 在技能目录下通过 `uvx --from .` 执行 Python CLI

### 配置文件结构

配置文件 `pms-login-config.json` 包含环境配置：

```json
{
  "environments": {
    "test": {
      "base_url": "https://test-pms.example.com",
      "username": "test_user",
      "password": "test_password",
      "authorization": ""
    },
    "pre": {
      "base_url": "https://pre-pms.example.com",
      "username": "pre_user",
      "password": "pre_password",
      "authorization": ""
    },
    "prod": {
      "base_url": "https://pms.example.com",
      "username": "prod_user",
      "password": "prod_password",
      "authorization": ""
    }
  }
}
```

### 安全规则

- 不要打印密码、authorization、cookies 或完整 JWT 值
- 不要读取、打开、cat、sed、grep、总结或显示 `pms-login-config.json`
- 只有 `scripts/pms_login.py` 可以读取或写入 `pms-login-config.json`
- 需要明确指定环境：`test`、`pre` 或 `prod`
- 不要从模糊的措辞中推断生产环境；只在用户明确选择 `--env prod` 时运行 `prod`
- 将 `data.authorization` 视为令牌；不要使用 `data.token`
- 将环境域名、用户名、密码和授权令牌保存在 `pms-login-config.json` 中；不要在脚本中硬编码

### 使用步骤

1. 配置 `pms-login-config.json` 文件
2. 运行登录命令
3. 获取授权令牌

### 命令示例

```bash
# 登录测试环境
uvx --isolated --python 3.14 python scripts/pms_login.py --env test

# 登录预发布环境
uvx --isolated --python 3.14 python scripts/pms_login.py --env pre

# 登录生产环境
uvx --isolated --python 3.14 python scripts/pms_login.py --env prod
```

### 对话示例

```
用户: 登录测试环境 PMS
用户: 登录预发布环境 PMS
用户: 登录生产环境 PMS
```

### 结果展示格式

| 环境 | 状态 | 令牌写入位置 |
| --- | --- | --- |
| test | 成功 | pms-login-config.json -> environments.test.authorization |

---

## gitlab-pipeline-operations

**用途**: 使用 `glab` CLI 查询 GitLab CI 流水线执行记录、按 ID 查看详情、或创建指定环境的流水线

### 意图路由

| 用户意图 | 操作 |
| --- | --- |
| 查询流水线执行记录、查看 pipeline 记录 | 查询流水线列表 |
| 根据流水线 ID 查询详情 | 查询单个流水线详情 |
| 创建测试环境流水线 | `glab pipeline run -b test` |
| 创建预发布流水线 | `glab pipeline run -b pre` |
| 创建正式环境流水线 | `glab pipeline run -b master` |

### 查询流水线列表

```bash
for id in $(glab pipeline list -F json | jq -r '.[].id'); do
  glab ci get --pipeline-id "$id" 2>/dev/null | head -10
  echo "---"
done
```

### 结果展示格式

| ID | Status | Ref | SHA | User | Created |
| --- | --- | --- | --- | --- | --- |
| 1234 | success | test | a1b2c3d4 | user1 | 2026-06-20 |

### 对话示例

```
用户: 查看最近的流水线执行记录
用户: 查询流水线 ID 1234 的详情
用户: 创建测试环境流水线
用户: 触发正式环境流水线
用户: 查看最近 5 条流水线执行记录
用户: 查询流水线 ID 5678 的详细状态
用户: 创建预发布环境流水线
```

### 安全规则

- 不打印 GitLab token、cookies、项目密钥或敏感 CI/CD 变量
- 创建流水线为副作用操作，仅在用户明确要求时执行
- 生产环境需用户明确指定 `master`/`prod`/`production`/`正式环境`

---

## 最佳实践

### 安全注意事项

1. **不要打印敏感信息**
   - 不要在日志或输出中打印密码、令牌、cookies 或完整 JWT 值
   - 不要读取、打开、cat、sed、grep、总结或显示包含敏感信息的配置文件
   - 只有指定的脚本可以读取或写入包含敏感信息的文件

2. **正确处理环境变量**
   - 不要在代码中硬编码敏感信息
   - 使用环境变量或配置文件存储敏感信息
   - 定期更新授权令牌和密码

3. **使用安全的连接方式**
   - 优先使用 HTTPS 连接
   - 验证 SSL 证书
   - 使用安全的认证方式

4. **环境隔离**
   - 明确指定环境：test、pre 或 prod
   - 不要从模糊的措辞中推断生产环境
   - 只在用户明确选择时运行生产环境

### 性能优化建议

1. **使用批量查询**
   - 尽量使用批量查询减少 API 调用次数
   - 例如：一次查询多个 SKU 的库存，而不是逐个查询

2. **合理使用缓存**
   - 避免重复查询相同的数据
   - 使用 Redis 缓存提高查询性能

3. **查询时指定必要的字段**
   - 只查询需要的字段，减少数据传输量
   - 避免查询不必要的字段

4. **使用分页查询**
   - 处理大量数据时使用分页查询
   - 设置合理的每页数量

### 错误处理指南

1. **网络错误处理**
   - 检查网络连接是否正常
   - 重试失败的请求
   - 设置合理的超时时间

2. **权限错误处理**
   - 检查认证令牌是否有效
   - 确认用户是否有权限执行操作
   - 重新登录获取新的令牌

3. **参数错误处理**
   - 验证查询参数是否有效
   - 检查参数格式是否正确
   - 提供清晰的错误信息

4. **环境不存在处理**
   - 检查环境变量是否配置正确
   - 确认环境名称是否正确
   - 提供可用的环境列表

5. **超时和重试**
   - 设置合理的超时时间
   - 实现重试机制
   - 记录重试次数和结果
