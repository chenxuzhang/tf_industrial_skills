---
name: query-industrial-stock-reconcile
description: Use when an agent needs to query hbip-scm stock reconciliation batches or differences, or reconcile Redis and database sellable-stock flow records by SKU and time range, in local, test, pre-release, or production environments.
---

# Query Industrial Stock Reconcile

## Purpose

Use the hbip-scm Agent stock APIs for one of two distinct reconciliation concepts:

1. Query persisted stock-snapshot reconciliation batches and pending differences.
2. Run a read-only comparison of Redis and database sellable-stock flow records for specified SKUs and a time window.

Select one endpoint from the user's intent. Do not treat flow reconciliation as stock recalculation, stock balance comparison, repair, or inventory modification.

## Environment Selection

| Environment | Base URL source | Default |
| --- | --- | --- |
| `local` | Fixed local startup URL | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | Ask if missing |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | Ask if missing |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | Ask if missing |

Before querying `prod`, confirm that the user explicitly requested production. Do not infer production from ambiguous wording.

If authentication is required, read it from `SCM_AUTH_TOKEN`. Never print tokens, cookies, sensitive internal hosts, or real customer data.

## Intent Routing

Choose exactly one endpoint by default.

| User intent | Endpoint |
| --- | --- |
| 查询库存对账批次、扫描进度、差异数量，或按批次开始时间筛选 | `/scm/inner/stock/agent-api/query-reconcile-batch` |
| 已知批次号，查询库存快照差异、修复目标或修复建议 | `/scm/inner/stock/agent-api/query-reconcile-detail` |
| 按时间范围和 SKU 对账 Redis、数据库可售库存流水，排查单边缺失或变动数量不一致 | `/scm/inner/stock/agent-api/reconcile-sellable-stock-flow` |

Use these semantic boundaries:

| Concept | Compares | Input anchor | Output | Writes data |
| --- | --- | --- | --- | --- |
| Batch snapshot reconciliation | Redis current sellable stock and database stock snapshot | Batch or batch start time | Batch progress, stock differences, repair suggestions | No |
| Sellable-stock flow reconciliation | Redis sellable-stock flow records and database sellable-stock flow records | SKU IDs and time window | Flow anomalies only | No |

Important distinctions:

- “Redis 可售库存和数据库可售库存流水对账” means the flow endpoint.
- “当前 Redis 可售库存和 DB 可售库存是否一致” means snapshot reconciliation or a stock query, not the flow endpoint.
- “重算库存”, “修改库存”, “修复差异”, or “补流水” is not supported by these query endpoints.
- Raw or complete stock-flow browsing belongs to `query-industrial-stock-flow`; the flow reconciliation endpoint omits matched records.
- Do not call the batch-detail endpoint without a batch number.
- Do not query batches first unless the user explicitly asks to locate a batch and then inspect its differences.

## Shared Request Rules

- Method: `POST`
- Content type: `application/json`
- Omit the `Authorization` header when authentication is not required.
- Treat HTTP errors, authentication errors, timeouts, and a non-success outer `Result` as request failures.
- Do not automatically chain reconciliation endpoints.

## Query Reconciliation Batches

Use `/scm/inner/stock/agent-api/query-reconcile-batch` for batch-level stock-snapshot reconciliation information.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `pageNo` | Yes | Page number |
| `startTimeFrom` | No | Inclusive lower bound for batch `startTime` |
| `startTimeTo` | No | Inclusive upper bound for batch `startTime` |

Use `yyyy-MM-dd HH:mm:ss`. Do not use the ISO `T` separator.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/query-reconcile-batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"pageNo":1,"startTimeFrom":"2026-06-01 00:00:00","startTimeTo":"2026-06-10 23:59:59"}'
```

Behavior:

- Both time fields may be omitted to query all non-deleted batches.
- Either bound may be supplied independently.
- Both bounds are inclusive.
- Results are ordered by `startTime` descending.
- Always send a non-null JSON object containing `pageNo`.
- The implementation fixes page size at 50 records; do not promise that `pageSize` changes it.
- Outer response: `Result<Paged<AgentReconcileBatchRespDTO>>`.

Each record contains:

| Field | Meaning |
| --- | --- |
| `batchNo` | Reconciliation batch number |
| `status` | `0` running, `1` completed, `2` failed |
| `scanTotalCount` | Total records expected to be scanned |
| `totalCount` | Stock records scanned |
| `diffCount` | Difference count |
| `startTime` | Batch start time |
| `endTime` | Batch end time |

## Query Reconciliation Difference Details

Use `/scm/inner/stock/agent-api/query-reconcile-detail` only when a stock-snapshot reconciliation batch number is known.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `pageNo` | Yes | Page number |
| `batchNo` | Yes | Reconciliation batch number |

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/query-reconcile-detail" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"pageNo":1,"batchNo":"RECONCILE_202606100001"}'
```

Validate that `batchNo` is non-blank before calling. The current implementation returns a null result for a missing or blank batch number.

The endpoint returns only:

- rows for the supplied `batchNo`;
- non-deleted rows;
- pending rows with `handle_status=0`.

Shop and SKU names are enriched through internal services. A missing display name does not mean the reconciliation row is absent.

The implementation fixes page size at 50 records. Outer response: `Result<Paged<AgentReconcileDetailRespDTO>>`.

Each record contains:

| Field | Meaning |
| --- | --- |
| `batchNo` | Reconciliation batch number |
| `merchantId` | Merchant ID |
| `shopName` | Merchant shop name |
| `skuId` | SKU ID |
| `skuName` | SKU name |
| `dbRealStock` | Database real stock |
| `dbFrozenStock` | Database frozen stock |
| `dbVirtualStock` | Database sellable stock |
| `dbExpectedVirtualStock` | Expected sellable stock: real minus frozen |
| `redisVirtualStock` | Redis sellable stock |
| `diffQty` | Redis sellable stock minus DB sellable stock |
| `diffType` | Difference type code |
| `diffTypeValue` | Difference type description |
| `repairTarget` | Repair target: `REDIS` or `DB` |
| `repairRemark` | Repair recommendation |

Known `diffType` values include:

- `REDIS_KEY_MISSING`
- `REDIS_LESS_THAN_DB`
- `REDIS_GREATER_THAN_DB`
- `DB_VIRTUAL_DIFF`
- `DB_STOCK_INVALID`

## Reconcile Sellable-Stock Flows

Use `/scm/inner/stock/agent-api/reconcile-sellable-stock-flow` to compare Redis and database sellable-stock flow records.

This endpoint is read-only. It does not compare current stock balances, recalculate inventory, repair stock, modify stock, or insert missing flow records.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `startTime` | Yes | Inclusive start of the reconciliation window |
| `endTime` | Yes | Exclusive end of the reconciliation window |
| `skuIds` | Yes | SKU ID list; nulls are ignored and duplicates are removed |

Validation rules:

- `startTime` must be earlier than `endTime`.
- The time span must not exceed 24 hours.
- At least one non-null SKU ID is required.
- At most 10 distinct non-null SKU IDs are allowed.
- Only SKU IDs are accepted; do not send SKU codes or SPU identifiers.
- Use `yyyy-MM-dd HH:mm:ss`.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/reconcile-sellable-stock-flow" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{
    "startTime":"2026-06-15 09:00:00",
    "endTime":"2026-06-15 10:00:00",
    "skuIds":[10001,10002]
  }'
```

### Matching Semantics

- Resolve every valid SKU to its supplier before querying flows.
- Query Redis flow-window records by `operate_time` in `[startTime, endTime)`.
- Query database flow-window records by `create_time` in `[startTime, endTime)`.
- Use each side's window records to query the opposite side by candidate business number and SKU without a time restriction. This allows the counterpart to fall outside the window because of asynchronous processing delay.
- Match the current implementation by the exact business key `uniqueNo + merchantId + skuId + flowType`.
- Do not invent main-order/sub-order conversion during result interpretation. Report the `uniqueNo` returned by the API.
- Compare `redisChangeQty` and `mysqlChangeQty` only after the exact business key matches.
- Matched records with equal quantities are omitted from `data`.
- A requested valid supplier-SKU with no window flow on either side is returned as `SKU_FLOW_NOT_FOUND`.

Outer response: `Result<AgentStockFlowQueryResultDTO>`.

Business data:

```text
data: List<AgentSellableStockFlowReconcileDetailDTO>
errors: Set<String>
```

Each anomaly detail contains:

| Field | Meaning |
| --- | --- |
| `uniqueNo` | Business number associated with the anomalous flow |
| `merchantId` | Supplier ID |
| `skuId` | SKU ID |
| `flowType` | Sellable-stock flow type |
| `redisChangeQty` | Redis flow quantity; null when Redis flow is absent |
| `mysqlChangeQty` | Database flow quantity; null when DB flow is absent |
| `reconcileStatus` | Anomaly type |
| `errorMessage` | Full troubleshooting context |

Known `reconcileStatus` values:

| Status | Meaning |
| --- | --- |
| `REDIS_FLOW_ONLY` | Redis flow exists but the corresponding database flow is absent |
| `MYSQL_FLOW_ONLY` | Database flow exists but the corresponding Redis flow is absent |
| `CHANGE_QTY_MISMATCH` | Exact business key matches but change quantities differ |
| `SKU_FLOW_NOT_FOUND` | Neither side has a sellable-stock flow for the supplier-SKU in the requested window |

Interpret the response as follows:

- `data` empty and `errors` empty: no flow anomaly was found.
- `data` non-empty: flow anomalies were found; present every detail.
- Validation, SKU lookup, and reconciliation errors are returned in `errors`.
- `data` and `errors` describe business-level reconciliation results; they are not pagination fields.

## Response Presentation

For batch pages:

| 批次号 | 状态 | 应扫描数 | 已扫描数 | 差异数 | 开始时间 | 结束时间 |
| --- | --- | --- | --- | --- | --- | --- |

For snapshot difference pages:

| 批次号 | 店铺 | SKU ID | SKU 名称 | DB库存（真实/冻结/可售） | Redis可售 | 差异 | 差异类型 | 修复目标 | 修复建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Format DB stock as `真实: {dbRealStock} / 冻结: {dbFrozenStock} / 可售: {dbVirtualStock}`. Report current page, fixed page size 50, and total count.

For sellable-stock flow reconciliation:

| 状态 | 业务单号 | 供应商 ID | SKU ID | 流水类型 | Redis 变动 | DB 变动 | 异常说明 |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |

After the selected result:

- Report the environment as `local`, `test`, `pre`, or `prod`; do not print a sensitive host.
- Report whether authentication was required; never print the credential.
- Preserve returned business errors without hiding successful or anomalous detail rows.
- For flow reconciliation, explicitly state that the operation was read-only and did not repair or modify inventory.

## Common Mistakes

- Routing “可售库存流水对账” to batch snapshot reconciliation.
- Describing the flow endpoint as a current Redis-versus-DB stock balance comparison.
- Claiming the flow endpoint recalculates, repairs, modifies, or supplements inventory.
- Sending `batchNo` or pagination fields to the flow endpoint.
- Sending SKU codes or SPU identifiers instead of numeric SKU IDs.
- Using an inclusive end time; the flow window is `[startTime, endTime)`.
- Querying more than 10 distinct SKU IDs or more than 24 hours.
- Expecting matched flow records to appear in the response.
- Treating `SKU_FLOW_NOT_FOUND` as proof that the SKU itself does not exist.
- Inventing main-order/sub-order conversion instead of following the returned `uniqueNo`.
- Ignoring `errors` because the outer `Result` succeeded.
- Calling the batch-detail endpoint without `batchNo`.
- Expecting caller-supplied `pageSize` to override the fixed size of 50.
- Printing an auth token or sensitive production base URL.
