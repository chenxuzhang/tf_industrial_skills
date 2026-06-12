---
name: query-industrial-order-data
description: Use when an agent needs to identify order types or query main-order, sub-order, refund-order, forward-order, or reverse-order data through hbip-scm StockAgentApiController endpoints in local, test, pre-release, or production environments.
---

# Query Industrial Order Data

## Purpose

Call one of the seven hbip-scm Agent order-query APIs according to the user's stated intent. Select one endpoint by default; do not automatically trace the complete main-order, sub-order, and refund-order relationship.

## Platform And Security

- Use the available HTTP tool or shell tool; prefer `curl` when no HTTP client is available.
- Never print tokens, cookies, sensitive internal hosts, or real customer data.
- These endpoints are read-only, but production queries still require explicit user intent.

## Environment Selection

| Environment | Base URL source | Default |
| --- | --- | --- |
| `local` | Fixed local startup URL | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | Ask if missing |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | Ask if missing |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | Ask if missing |

Do not infer production from ambiguous wording. If authentication is required, read it from `SCM_AUTH_TOKEN`; never ask the user to paste a token unless no safer option exists.

## Intent Routing

Choose exactly one row unless the user explicitly requests multiple independent results or cross-document tracing.

| User intent | Endpoint |
| --- | --- |
| 判断单号是主订单、子订单还是退单 | `/scm/inner/stock/agent-api/query-order-type` |
| 查询主订单下所有子订单，或判断传入单号是否为子订单 | `/scm/inner/stock/agent-api/query-sub-order-nos` |
| 根据正向单号查询关联的退款单号，不查询退款商品详情 | `/scm/inner/stock/agent-api/query-refund-nos` |
| 根据子订单查询主订单，或判断单号本身是否为主订单 | `/scm/inner/stock/agent-api/query-main-order-no` |
| 根据 `RF_` 退款单号查询关联的子订单号 | `/scm/inner/stock/agent-api/query-sub-order-by-refund-no` |
| 查询主订单或子订单的正向订单及商品详情 | `/scm/inner/stock/agent-api/query-forward-order-data` |
| 查询 `RF_` 退款单及退款商品详情 | `/scm/inner/stock/agent-api/query-reverse-order-data` |

Important distinctions:

- “主订单下有哪些子订单” uses `query-sub-order-nos`.
- “退款单对应哪个子订单” uses `query-sub-order-by-refund-no`.
- “有哪些退款单号” uses `query-refund-nos`.
- “退款单有哪些商品” uses `query-reverse-order-data`.
- If the user only says “查询订单关系”, ask which relationship they need instead of calling several endpoints.

## Request Contract

All seven APIs use `POST`, `Content-Type: application/json`, and a raw JSON string array. Do not wrap the array in an object such as `{"orderNos":[...]}`.

```bash
BASE_URL="http://localhost:8803"
ENDPOINT="<selected-path-from-intent-routing>"

curl -sS -X POST "${BASE_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '["ORDER_NO_1","RF_1001"]'
```

Omit the `Authorization` header when it is not required.

The outer response is `Result<T>`. Treat HTTP errors, authentication errors, timeouts, and a non-success outer result as request failures. A successful outer response can still contain business descriptions such as “未查询到”, “不处理”, or “查询异常”.

## Endpoint Usage

### 1. Determine Order Type

- Use for mixed main-order, sub-order, and refund-order numbers.
- Body example: `["MAIN_1001","SUB_1001","RF_1001",""]`
- Returns `List<String>` in the same order and length as the input list.
- `RF_` is matched case-insensitively before calling order services.
- Blank, unmatched, and caught-exception items return description strings instead of being omitted.

### 2. Query Sub-Order Numbers

- Use to expand a main order into all of its sub-order numbers.
- It also identifies when an input is already a sub-order or refund order.
- Body example: `["MAIN_1001","SUB_1001","RF_1001"]`
- Returns `List<String>` positionally aligned with input.
- A main order can produce one description containing several comma-separated sub-order numbers.

### 3. Query Refund Numbers

- Use to find refund numbers related to forward order numbers.
- Body example: `["MAIN_1001","SUB_1001","RF_1001"]`
- Returns `List<String>` positionally aligned with input.
- An `RF_` input is reported as already being a refund order.
- No-match and caught-exception cases remain in the result as descriptions.

### 4. Query Main Order Number

- Use to find the main order associated with a sub-order or verify that an input is already a main order.
- Body example: `["SUB_1001","MAIN_1001","RF_1001"]`
- Returns `List<String>` positionally aligned with input.
- An `RF_` refund order is reported as unable to directly associate with a main order.

### 5. Query Sub-Order By Refund Number

- Use only when the relationship starts from a refund number.
- Body example: `["RF_1001","ORDER_1002",""]`
- Returns `List<String>` positionally aligned with input.
- Non-`RF_` values return a “非退款单, 不处理” description.
- Missing refund details, missing associated sub-orders, and caught exceptions return descriptions.

### 6. Query Forward Order Data

- Use for detailed forward-order and goods data from main-order or sub-order numbers.
- Body example: `["MAIN_1001","SUB_1002"]`
- Returns `AgentForwardOrderQueryResultDTO` inside the outer `Result.data`.
- The business result contains `data: List<AgentForwardOrderDTO>` and `errors: List<String>`.
- A sub-order input returns that sub-order; a main-order input expands to all sub-orders.
- Results are deduplicated by sub-order number.
- Blank order numbers, unmatched orders, and caught exceptions are written to `errors` without discarding successful data.
- The successful `data` list is expanded by sub-order and is not positionally aligned one-to-one with the input.

`AgentForwardOrderQueryResultDTO`:

```text
data[AgentForwardOrderDTO]
errors[string]
```

`AgentForwardOrderDTO`:

```text
mainOrderNo
orderNo
shopName
goodsList[{skuId, skuName, num}]
```

### 7. Query Reverse Order Data

- Use for refund-order details and refund goods.
- Body example: `["RF_1001","ORDER_1002",""]`
- Returns `AgentReverseOrderQueryResultDTO` inside the outer `Result.data`.
- The business result contains `data: List<AgentReverseOrderDTO>` and `errors: List<String>`.
- Blank values, non-`RF_` values, unmatched refund orders, and caught exceptions are written to `errors` without discarding successful data.
- The successful `data` list contains one element per queried refund order and is not positionally aligned one-to-one with the input when errors occur.

`AgentReverseOrderQueryResultDTO`:

```text
data[AgentReverseOrderDTO]
errors[string]
```

`AgentReverseOrderDTO`:

```text
refundNo
orderNo
orderStatus (0-待付款, 1-待发货, 2-待收货, 3-已完成, 4-已取消)
goodsList[{skuId, skuName, num}]
```

`orderStatus` is the associated order status. Preserve the numeric value from the API and present its Chinese meaning using the mapping above. If the value is null or outside `0-4`, report it as unknown instead of guessing.

## Response Presentation

For the first five endpoints, preserve input order:

| 输入单号 | 查询结果 |
| --- | --- |
| `...` | `...` |

For forward-order data:

| 主订单号 | 子订单号 | 店铺 | SKU ID | SKU 名称 | 下单数量 |
| --- | --- | --- | --- | --- | --- |

For reverse-order data:

| 退款单号 | 子订单号 | 订单状态 | SKU ID | SKU 名称 | 退款数量 |
| --- | --- | --- | --- | --- | --- |

Also report:

- Environment name only: `local`, `test`, `pre`, or `prod`.
- Whether authentication was required, without exposing credentials.
- For forward/reverse DTO endpoints, present all entries from the business-level `errors` list after the successful data table.
- Do not confuse outer `Result.data` with the inner business-level `data` list: successful detail rows are read from `response.data.data`, while per-item errors are read from `response.data.errors`.

## Common Mistakes

- Sending a JSON object instead of a raw JSON string array.
- Calling `query-sub-order-nos` when starting from an `RF_` refund number.
- Calling `query-refund-nos` when the user asked for refund goods details.
- Assuming forward/reverse DTO results align one-to-one with inputs.
- Reading forward/reverse rows from `response.data` instead of `response.data.data`.
- Ignoring the business-level `response.data.errors` list because the outer result succeeded.
- Automatically chaining endpoints when the user asked for one relationship.
- Treating a business “未查询到” description as an HTTP failure.
- Printing an auth token or a sensitive production base URL.
