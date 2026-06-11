---
name: query-industrial-stock-flow
description: Use when an agent needs to query hbip-scm raw stock flow pages by SKU or aggregated stock changes by main order, sub-order, or refund number in local, test, pre-release, or production environments.
---

# Query Industrial Stock Flow

## Purpose

Query raw stock flow rows or business-stage stock changes through the hbip-scm Agent stock API. Select one endpoint from the user's intent; do not automatically chain the raw and aggregate queries.

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
| 按 SKU ID 或 SKU 编码查看原始库存流水、流水时间、库存类型、流水类型和变更前后数量 | `/scm/inner/stock/agent-api/query-stock-flow-page` |
| 按主订单号、子订单号或退款单号查看下单、取消/退款、出库阶段的聚合库存变更 | `/scm/inner/stock/agent-api/query-stock-flow` |

Do not call both endpoints unless the user explicitly asks for both raw database flows and business-stage aggregation.

## Shared Request Rules

- Method: `POST`
- Content type: `application/json`
- Outer response: `Result<AgentStockFlowQueryResultDTO>`
- Successful data and `errors` may coexist. Do not discard successful rows because `errors` is non-empty.
- Omit the `Authorization` header when authentication is not required.

## Query Raw Stock Flow Page

Use this endpoint to inspect chronological database stock-flow rows for one or more SKUs.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `pageNo` | Yes | Page number; non-positive values are treated as page 1 |
| `skuIds` | Conditional | SKU ID list; pure numeric values, e.g. `[10001, 10002]` |
| `skuCodes` | Conditional | SKU code list; values start with `SKU` prefix, e.g. `["SKU26060300019000001"]` |
| `stockTypes` | No | Stock-type filters |
| `flowTypes` | No | Flow-type filters |

At least one of `skuIds` or `skuCodes` must be non-empty. They may be supplied together. Resolved SKU records are deduplicated by `merchantId + skuId`.

- `skuId`: pure numeric identifier, e.g. `10001`
- `skuCode`: string starting with `SKU` prefix, e.g. `SKU26060300019000001`

Classify user-supplied SKU identifiers before building the request:

| Input format | Request field | JSON type | Example |
| --- | --- | --- | --- |
| Pure digits: `^[0-9]+$` | `skuIds` | Number | `26060300019000001` |
| Uppercase `SKU` followed by digits: `^SKU[0-9]+$` | `skuCodes` | String | `"SKU26060300019000001"` |

For mixed input, place every pure numeric value in `skuIds` and every `SKU`-prefixed value in `skuCodes`. Deduplicate each array while preserving the user's order.

Reject unsupported values before calling the endpoint. Do not treat `SKU-26060300019000001`, lowercase `sku26060300019000001`, or other alphanumeric text as valid SKU codes.

Supported stock types:

| Code | Description |
| --- | --- |
| `REAL_STOCK` | 真实库存 |
| `FROZEN_STOCK` | 冻结库存 |
| `VIRTUAL_STOCK` | 可售库存 |

Supported flow types:

| Code | Description |
| --- | --- |
| `REDUCE_SELLABLE_STOCK` | 减少可售库存 |
| `ADD_FROZEN_STOCK` | 增加冻结库存 |
| `ADD_SELLABLE_STOCK` | 增加可售库存 |
| `REDUCE_FROZEN_STOCK` | 减少冻结库存 |
| `REDUCE_REAL_STOCK` | 减少真实库存 |
| `MANUAL_INCREASE` | 手动增加 |
| `MANUAL_DECREASE` | 手动减少 |

Although the controller comment says stock and flow types should be specified, the current implementation treats both filter lists as optional. Omit them when the user asks for all flows for the selected SKUs.

Example:

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"
ENDPOINT="<raw-flow-endpoint-from-intent-routing>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{
    "pageNo": 1,
    "skuIds": [26060300019000001],
    "skuCodes": ["SKU26060300019000001"],
    "stockTypes": ["VIRTUAL_STOCK", "FROZEN_STOCK"],
    "flowTypes": ["REDUCE_SELLABLE_STOCK", "ADD_FROZEN_STOCK"]
  }'
```

Behavior:

- Only non-deleted rows are queried.
- Records are ordered by `createTime` descending.
- Page size is fixed at 50; do not promise that caller-supplied `pageSize` changes it.
- Missing SKU conditions and an empty flow result are reported in `errors`.
- Shop and SKU names are enriched through internal services.

Each record contains:

| Field | Meaning |
| --- | --- |
| `uniqueNo` | Business number associated with the flow |
| `merchantId` | Merchant ID |
| `shopName` | Merchant shop name |
| `skuId` | SKU ID |
| `skuName` | SKU name |
| `stockType` / `stockTypeDesc` | Stock type code and description |
| `flowType` / `flowTypeDesc` | Flow type code and description |
| `changeQty` | Changed quantity; positive increases and negative decreases |
| `beforeQty` | Quantity before the change |
| `afterQty` | Quantity after the change |
| `createUser` | Operator |
| `createTime` | Flow creation time |

## Query Aggregated Flow By Business Number

Use this endpoint when the user provides a main order number, sub-order number, or refund number and wants stock changes grouped by business stage.

Request fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `uniqueNo` | Yes | Main order, sub-order, or `RF_` refund number; maximum 64 characters |

Trim surrounding whitespace before calling. Reject a blank value or a value longer than 64 characters.

Example:

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"
ENDPOINT="<aggregate-flow-endpoint-from-intent-routing>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"uniqueNo":"ORDER_OR_RF_NUMBER"}'
```

Number recognition:

1. An `RF_` prefix, case-insensitive, is queried as a refund.
2. Other numbers are queried as main orders first.
3. If no main order is found, the number is queried as a sub-order.

Query scope:

- Main order: applicable main-order flows, child-order flows, and related refund flows.
- Sub-order: applicable main-order flows, the current child-order flows, and its related refund flows.
- Refund: only the current refund number's flows; do not include the full order lifecycle.

Results are grouped by sub-order number, `merchantId`, and `skuId`. `relatedOrderNos` contains the associated `mainOrderNo` and deduplicated `refundNos`.

Stock actions are classified only from complete combinations within the same flow number, merchant, and SKU group:

| Action | Virtual/sellable stock | Frozen stock | Real stock |
| --- | --- | --- | --- |
| `orderChange` | `VIRTUAL_STOCK + REDUCE_SELLABLE_STOCK` | `FROZEN_STOCK + ADD_FROZEN_STOCK` | Not applicable |
| `cancelOrRefundChange` | `VIRTUAL_STOCK + ADD_SELLABLE_STOCK` | `FROZEN_STOCK + REDUCE_FROZEN_STOCK` | Not applicable |
| `outboundChange` | Not applicable | `FROZEN_STOCK + REDUCE_FROZEN_STOCK` | `REAL_STOCK + REDUCE_REAL_STOCK` |

Do not classify `REDUCE_FROZEN_STOCK` by itself. Its companion `ADD_SELLABLE_STOCK` or `REDUCE_REAL_STOCK` determines whether it belongs to cancellation/refund or outbound.

Manual changes, incomplete pairs, unsupported combinations, ambiguous main-order-to-child-order mappings, missing documents, and internal-call failures are reported in `errors` without invalidating successfully aggregated rows.

Each aggregate record contains:

| Field | Meaning |
| --- | --- |
| `uniqueNo` | Display sub-order number |
| `merchantId` / `shopName` | Merchant and shop |
| `skuId` / `skuName` | SKU ID and name |
| `relatedOrderNos.mainOrderNo` | Associated main order |
| `relatedOrderNos.refundNos` | Associated refund numbers |
| `orderChange` | Sellable, frozen, and real quantity changes caused by ordering |
| `cancelOrRefundChange` | Quantity changes caused by cancellation, timeout, or refund |
| `outboundChange` | Quantity changes caused by outbound processing |

## Response Presentation

For raw flow pages:

| 业务单号 | 店铺 | SKU ID | SKU 名称 | 库存类型 | 流水类型 | 变更数量 | 变更前 | 变更后 | 创建人 | 创建时间 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use the description fields for stock and flow types, optionally retaining the code in parentheses. Then report current page, fixed page size 50, and total count.

For business-number aggregation:

| 子订单号 | 店铺 | SKU ID | SKU 名称 | 关联主单 | 关联退款单 | 下单变更（可售/冻结/真实） | 取消或退款变更（可售/冻结/真实） | 出库变更（可售/冻结/真实） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Format each action cell as `可售: {virtualStockChangeQty} / 冻结: {frozenStockChangeQty} / 真实: {realStockChangeQty}`. Display `-` for a null component and join multiple refund numbers with commas.

After either table:

- List `errors` separately and preserve their returned order.
- State that successful data remains usable when partial errors exist.
- Report the environment name without printing a sensitive host.
- Report whether authentication was required without printing credentials.
- Distinguish an empty result from a failed request.

## Common Mistakes

- Calling both endpoints when the user requested only raw rows or only business-stage aggregation.
- Sending neither `skuIds` nor `skuCodes` to the page endpoint.
- Sending a numeric SKU ID as a quoted string instead of a JSON number.
- Sending a SKU code without the uppercase `SKU` prefix, or using a hyphen such as `SKU-26060300019000001`.
- Assuming `stockTypes` and `flowTypes` are mandatory despite the current implementation treating them as optional.
- Expecting caller-supplied `pageSize` to override the fixed size of 50.
- Treating an `RF_` query as the complete order lifecycle; it returns only that refund's flows.
- Classifying an isolated `REDUCE_FROZEN_STOCK` without checking its companion flow.
- Hiding successful rows because the response also contains `errors`.
- Printing an auth token or sensitive production base URL.
