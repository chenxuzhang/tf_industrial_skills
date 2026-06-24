---
name: query-industrial-stock-reconcile
description: Use when an agent needs to query hbip-scm stock reconciliation batch pages or pending reconciliation difference details in local, test, pre-release, or production environments.
---

# Query Industrial Stock Reconcile

## Purpose

Query stock reconciliation batches or pending difference details through the hbip-scm Agent stock API. Select one endpoint from the user's intent; do not automatically chain batch and detail queries.

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
| 查询对账批次列表、扫描进度、差异数量，或按批次开始时间筛选 | `/scm/inner/stock/agent-api/query-reconcile-batch` |
| 已知批次号，查询该批次待处理的库存差异和修复建议 | `/scm/inner/stock/agent-api/query-reconcile-detail` |

Do not call the detail endpoint without a batch number. Do not query batches first unless the user explicitly asks to locate a batch and then inspect its differences.

## Shared Request Rules

- Method: `POST`
- Content type: `application/json`
- Outer response: `Result<Paged<T>>`
- Send `pageNo`; the implementation fixes page size at 50 records.
- Do not promise that a supplied `pageSize` changes the result size.
- Omit the `Authorization` header when authentication is not required.

Paged responses contain page number, page size, total count, and `records`. Field names can follow the platform's serialized `Paged<T>` contract; summarize the metadata rather than assuming more pages exist.

## Query Reconciliation Batches

Use this endpoint for batch-level information.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `pageNo` | Yes | Page number |
| `startTimeFrom` | No | Inclusive lower bound for batch `startTime` |
| `startTimeTo` | No | Inclusive upper bound for batch `startTime` |

Use the project-configured local date-time format with second precision: `yyyy-MM-dd HH:mm:ss`.
The separator between date and time must be a space. Do not use the ISO `T` separator.

Example:

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"
ENDPOINT="<batch-endpoint-from-intent-routing>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
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

Use this endpoint only when a reconciliation batch number is known.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `pageNo` | Yes | Page number |
| `batchNo` | Yes | Reconciliation batch number |

Example:

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"
ENDPOINT="<detail-endpoint-from-intent-routing>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"pageNo":1,"batchNo":"RECONCILE_202606100001"}'
```

Validate that `batchNo` is non-blank before calling. The current business implementation returns a null result for a missing or blank batch number.

The endpoint returns only:

- rows for the supplied `batchNo`;
- non-deleted rows;
- pending rows with `handle_status=0`.

Shop and SKU names are enriched through internal services. A missing display name does not mean the reconciliation row is absent.

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

## Response Presentation

For batch pages:

| 批次号 | 状态 | 应扫描数 | 已扫描数 | 差异数 | 开始时间 | 结束时间 |
| --- | --- | --- | --- | --- | --- | --- |

For difference pages:

| 批次号 | 店铺 | SKU ID | SKU 名称 | DB库存（真实/冻结/可售） | Redis可售 | 差异 | 差异类型 | 修复目标 | 修复建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Format the DB stock cell as `真实: {dbRealStock} / 冻结: {dbFrozenStock} / 可售: {dbVirtualStock}`.
Do not display `dbExpectedVirtualStock` in the terminal table. Keep `redisVirtualStock` as its own column.

Then report:

- Pagination: current page, fixed page size 50, and total count.
- Environment: `local`, `test`, `pre`, or `prod`; do not print a sensitive host.
- Auth: whether authentication was required; never print the credential.
- Empty result: distinguish “no matching batch” from “no pending differences for this batch”.

## Common Mistakes

- Calling the detail endpoint without `batchNo`.
- Sending time-range fields to the detail endpoint.
- Sending `LocalDateTime` values with a `T` separator instead of `yyyy-MM-dd HH:mm:ss`.
- Expecting the detail endpoint to return already handled rows; it only returns `handle_status=0`.
- Assuming caller-supplied `pageSize` overrides the fixed size of 50.
- Automatically querying the batch list before details when the user already supplied `batchNo`.
- Treating missing `shopName` or `skuName` as proof that the difference row does not exist.
- Printing an auth token or sensitive production base URL.
