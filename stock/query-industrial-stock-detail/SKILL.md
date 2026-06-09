---
name: query-industrial-stock-detail
description: Use when an agent needs to query hbip-scm database stock details by SKU ID or SKU code, including real stock, frozen stock, and sellable stock, in local, test, pre-release, or production environments.
---

# Query Industrial Stock Detail

## Purpose

Query database stock details through the hbip-scm Agent stock API. This Skill is dedicated to SKU-level stock-table data and must not call or orchestrate other stock endpoints.

## Environment Selection

Endpoint path:

```text
/scm/inner/stock/agent-api/query-stock-detail
```

| Environment | Base URL source | Default |
| --- | --- | --- |
| `local` | Fixed local startup URL | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | Ask if missing |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | Ask if missing |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | Ask if missing |

Before querying `prod`, confirm that the user explicitly requested production. Do not infer production from ambiguous wording.

If authentication is required, read it from `SCM_AUTH_TOKEN`. Never print tokens, cookies, sensitive internal hosts, or real customer data.

## Input Classification

Build a `StockDetailQueryReqDTO` JSON object. At least one list should be non-empty.

| User input | Request field |
| --- | --- |
| Numeric value described as a SKU ID | `skuIds` |
| String SKU code, normally starting with `SKU` | `skuCodes` |

Mixed SKU IDs and SKU codes can be queried in one request. This endpoint does not accept SPU IDs or SPU codes.

If a numeric value is not clearly identified as a SKU ID, ask for clarification instead of treating it as another identifier type.

## Request

Use `POST` with `Content-Type: application/json`.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"
ENDPOINT="<endpoint-path-above>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"skuIds":[1,2],"skuCodes":["SKU26060300019000001"]}'
```

For local use, set `BASE_URL="http://localhost:8803"`. Omit the `Authorization` header when authentication is not required.

## Response Handling

The outer response is `Result<StockDetailQueryResultDTO>`.

- A successful outer response contains `data.data` and `data.errors`.
- HTTP errors, authentication errors, timeouts, dependency exceptions, and a non-success outer result are request failures.
- A null request or a request with both lists empty returns empty `data` and empty `errors`.

Each `data.data` row contains:

| Field | Meaning |
| --- | --- |
| `queryCondition` | Matched input, such as `skuId:1` or `skuCode:SKU...` |
| `shopName` | Merchant shop name |
| `skuId` | SKU primary key |
| `skuName` | SKU name |
| `realStock` | Database real stock |
| `frozenStock` | Database frozen stock |
| `virtualStock` | Database sellable stock |

This endpoint reads stock-table values. Do not label `virtualStock` as Redis stock.

## Matching And Deduplication

- Duplicate `skuIds` and duplicate `skuCodes` are removed while preserving first-seen order.
- Matched rows are deduplicated by `merchantId + skuId`.
- If the same SKU is supplied by both ID and code, only one row is returned and `queryCondition` prefers `skuId`.
- A matched SKU normally produces one result row.

Unmatched unique conditions are added to `data.errors`:

```text
skuId:{value} 未查询到数据
skuCode:{value} 未查询到数据
```

If SKU metadata exists but no corresponding stock-table row exists, the row is still returned with:

```text
realStock = 0
frozenStock = 0
virtualStock = 0
```

This zero-stock case is not added to `errors`.

## Result Status

Use these labels:

- Full success: `data.data` has rows and `data.errors` is empty.
- Partial success: `data.data` has rows and `data.errors` is not empty.
- All failed: `data.data` is empty and `data.errors` is not empty.
- Empty input: both collections are empty because no query condition was supplied.
- Request failed: HTTP, authentication, timeout, dependency, or outer-result failure.

## Final Answer Format

Return a concise table:

| 查询条件 | 店铺 | SKU ID | SKU 名称 | 真实库存 | 冻结库存 | 可售库存 |
| --- | --- | --- | --- | --- | --- | --- |

Then report:

- Status: one label from the preceding section.
- Unmatched: list `data.errors`, if any.
- Environment: `local`, `test`, `pre`, or `prod`; do not print a sensitive host.
- Auth: whether authentication was required; never print the credential.
- Zero stock: clarify that a returned all-zero row means the SKU matched but no stock-table values were found or all stored values are zero.

## Common Mistakes

- Sending a raw array instead of a JSON object with `skuIds` and/or `skuCodes`.
- Sending SPU identifiers to this SKU-only endpoint.
- Describing `virtualStock` as a cache or Redis value.
- Treating a returned zero-stock row as an unmatched SKU.
- Expecting duplicate ID/code inputs for the same SKU to produce duplicate rows.
- Exposing an authentication token or sensitive production base URL.
