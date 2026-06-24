---
name: query-industrial-order-data
description: Use when an agent needs to identify order types or query main-order, sub-order, refund-order, forward-order, or reverse-order data through PMS-authenticated hbip-scm admin stock query endpoints.
---

# Query Industrial Order Data

## Purpose

Call one of the seven PMS-authenticated SCM admin order-query APIs according to the user's stated intent. Select one endpoint by default; do not automatically trace the complete main-order, sub-order, and refund-order relationship.

## Security Rules

- Never read, open, cat, sed, grep, summarize, or display the PMS login config file in the agent context. It contains domains, accounts, passwords, and authorization tokens.
- Use the PMS login skill's `scripts/read_pms_env.py` helper to read runtime values into variables. Do not print those variables.
- Always execute Python helpers through `uvx --isolated --python 3.14 python ...`.
- Never print authorization tokens, passwords, cookies, or sensitive production hosts.
- Only query `prod` when the user explicitly selects production.

## Intent Routing

Choose exactly one row unless the user explicitly requests multiple independent results or cross-document tracing.

| User intent | Endpoint |
| --- | --- |
| 判断单号是主订单、子订单还是退单 | `/scm/admin/stock/query/query-order-type` |
| 查询主订单下所有子订单，或判断传入单号是否为子订单 | `/scm/admin/stock/query/query-sub-order-nos` |
| 根据正向单号查询关联的退款单号，不查询退款商品详情 | `/scm/admin/stock/query/query-refund-nos` |
| 根据子订单查询主订单，或判断单号本身是否为主订单 | `/scm/admin/stock/query/query-main-order-no` |
| 根据 `RF_` 退款单号查询关联的子订单号 | `/scm/admin/stock/query/query-sub-order-by-refund-no` |
| 查询主订单或子订单的正向订单及商品详情 | `/scm/admin/stock/query/query-forward-order-data` |
| 查询 `RF_` 退款单及退款商品详情 | `/scm/admin/stock/query/query-reverse-order-data` |

Important distinctions:

- “主订单下有哪些子订单” uses `query-sub-order-nos`.
- “退款单对应哪个子订单” uses `query-sub-order-by-refund-no`.
- “有哪些退款单号” uses `query-refund-nos`.
- “退款单有哪些商品” uses `query-reverse-order-data`.
- If the user only says “查询订单关系”, ask which relationship they need instead of calling several endpoints.

## Request Flow

All seven APIs use `POST`, `content-type: application/json`, and a raw JSON string array. Do not wrap the array in an object such as `{"orderNos":[...]}`.

Run commands from this skill directory. Use shell variables so secrets are not printed.

```bash
ENV_NAME="test"
ENDPOINT="/scm/admin/stock/query/query-order-type"
DATA_RAW='["ORDER_NO_1","RF_1001"]'
PMS_CONFIG="../pms-login/pms-login-config.json"

BASE_URL="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field base_url)"
AUTHORIZATION="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field authorization)"

curl -sS "${BASE_URL}${ENDPOINT}" \
  -H "authorization: ${AUTHORIZATION}" \
  -H "content-type: application/json" \
  -H "x-app-code: ADMIN" \
  -H "x-client-type: PC" \
  --data-raw "${DATA_RAW}"
```

Do not echo `BASE_URL` or `AUTHORIZATION`. The final answer should show only the environment name, not the sensitive host or token.

## Token Refresh

If the business API returns:

```json
{"msg":"无权限","code":401,"ok":false}
```

refresh the PMS token once for the same environment:

```bash
uvx --isolated --python 3.14 python ../pms-login/scripts/pms_login.py --env "${ENV_NAME}"
```

Then reload `BASE_URL` and `AUTHORIZATION` with `../pms-login/scripts/read_pms_env.py` and retry the request once. If the retry still returns `code=401`, stop. Do not refresh again.

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

### 3. Query Refund Numbers

- Use to find refund numbers related to forward order numbers.
- Body example: `["MAIN_1001","SUB_1001","RF_1001"]`
- Returns `List<String>` positionally aligned with input.
- An `RF_` input is reported as already being a refund order.

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

### 6. Query Forward Order Data

- Use for detailed forward-order and goods data from main-order or sub-order numbers.
- Body example: `["MAIN_1001","SUB_1002"]`
- Returns `AgentForwardOrderQueryResultDTO` inside the outer `Result.data`.
- Successful detail rows are read from `data.data`, and per-item errors are read from `data.errors`.

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
- Blank values, non-`RF_` values, unmatched refund orders, and caught exceptions are written to `data.errors`.

`AgentReverseOrderDTO`:

```text
refundNo
orderNo
orderStatus (0-待付款, 1-待发货, 2-待收货, 3-已完成, 4-已取消)
goodsList[{skuId, skuName, num}]
```

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

- Environment name only: `test`, `pre`, or `prod`.
- Token refreshed: `yes` only if the first request returned 401 and PMS login was rerun; never print the token.
- For forward/reverse DTO endpoints, present all entries from the business-level `data.errors` list after the successful data table.

## Common Mistakes

- Reading or displaying the PMS login config file before running the command.
- Using ad hoc inline Python instead of `../pms-login/scripts/read_pms_env.py`.
- Using any runner other than `uvx`.
- Manually copying a token into chat or the final answer.
- Using legacy inner agent endpoints instead of the PMS admin endpoints.
- Prefixing the authorization header with `Bearer`.
- Retrying login more than once after repeated 401 responses.
- Sending a JSON object instead of a raw JSON string array.
- Automatically chaining endpoints when the user asked for one relationship.
