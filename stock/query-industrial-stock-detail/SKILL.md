---
name: query-industrial-stock-detail
description: Use when an agent needs to query hbip-scm admin stock details by SKU ID or SKU code through PMS-authenticated test pre prod environments.
---

# Query Industrial Stock Detail

## Purpose

Query SKU-level stock details through the PMS-authenticated SCM admin API. This skill is instruction-only; do not create a new stock-detail script for it.

## Security Rules

- Never read, open, cat, sed, grep, summarize, or display the PMS login config file in the agent context. It contains domains, accounts, passwords, and authorization tokens.
- Use the PMS login skill's `scripts/read_pms_env.py` helper to read runtime values into variables. Do not print those variables.
- Always execute Python helpers through `uvx --isolated --python 3.14 python ...`.
- Never print authorization tokens, passwords, cookies, or sensitive production hosts.
- Only query `prod` when the user explicitly selects production.

## Endpoint

Use the admin endpoint:

```text
POST {base_url}/scm/admin/stock/query/query-stock-detail
authorization: {authorization}
content-type: application/json
x-app-code: ADMIN
x-client-type: PC
```

`base_url` and `authorization` must come from the selected environment in the PMS login config file. Do not pass `Bearer`; the header value is the raw authorization token.

## Request Body

Build a JSON object matching the admin API request body:

| User input | Request field |
| --- | --- |
| Numeric SKU IDs | `skuIds` |
| SKU code strings | `skuCodes` |

Examples:

```json
{"skuIds":[1231,123]}
```

```json
{"skuCodes":["SKU26060300019000001"]}
```

Mixed SKU IDs and SKU codes can be queried in one request. This endpoint does not accept SPU IDs or SPU codes.

If a numeric value is not clearly a SKU ID, ask for clarification instead of guessing another identifier type.

## Request Flow

Run commands from this skill directory. Use a subshell so secrets stay in shell variables and are not printed.

```bash
ENV_NAME="test"
DATA_RAW='{"skuIds":[1231,123]}'
PMS_CONFIG="../pms-login/pms-login-config.json"

BASE_URL="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field base_url)"
AUTHORIZATION="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field authorization)"

curl -sS "${BASE_URL}/scm/admin/stock/query/query-stock-detail" \
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

refresh the PMS token once for the same environment by running the existing PMS login skill script:

```bash
uvx --isolated --python 3.14 python ../pms-login/scripts/pms_login.py --env "${ENV_NAME}"
```

Then rerun the stock-detail request once, reloading `BASE_URL` and `AUTHORIZATION` with `../pms-login/scripts/read_pms_env.py`.

If the retry still returns `code=401`, stop. Do not refresh again.

## Response Handling

The API response is expected to contain stock rows under `data.data` and unmatched conditions under `data.errors`.

Each `data.data` row contains:

| Field | Meaning |
| --- | --- |
| `queryCondition` | Matched input, such as `skuId:1231` or `skuCode:SKU...` |
| `shopName` | Merchant shop name |
| `skuId` | SKU primary key |
| `skuName` | SKU name |
| `realStock` | Database real stock |
| `frozenStock` | Database frozen stock |
| `virtualStock` | Database sellable stock |

This endpoint reads stock-table values. Do not label `virtualStock` as Redis stock.

## Result Status

Use these labels:

- Full success: `data.data` has rows and `data.errors` is empty.
- Partial success: `data.data` has rows and `data.errors` is not empty.
- All failed: `data.data` is empty and `data.errors` is not empty.
- Empty result: both collections are empty.
- Request failed: HTTP error, timeout, repeated 401, or non-success outer result.

## Final Answer Format

Return a concise table:

| 查询条件 | 店铺 | SKU ID | SKU 名称 | 真实库存 | 冻结库存 | 可售库存 |
| --- | --- | --- | --- | --- | --- | --- |

Then report:

- Status: one label from the preceding section.
- Token refreshed: `yes` only if the first request returned 401 and PMS login was rerun; never print the token.
- Unmatched: list `data.errors`, if any.
- Environment: `test`, `pre`, or `prod`; do not print a sensitive host.
- Zero stock: clarify that a returned all-zero row means the SKU matched but no stock-table values were found or all stored values are zero.

## Common Mistakes

- Creating a new stock-detail script for this skill.
- Reading or displaying the PMS login config file before running the command.
- Using ad hoc inline Python instead of `../pms-login/scripts/read_pms_env.py`.
- Using any runner other than `uvx`.
- Manually copying a token into chat or the final answer.
- Using the old `/scm/inner/stock/agent-api/query-stock-detail` endpoint.
- Prefixing the authorization header with `Bearer`.
- Retrying login more than once after repeated 401 responses.
- Sending a raw array instead of a JSON object with `skuIds` and/or `skuCodes`.
- Sending SPU identifiers to this SKU-only endpoint.
- Describing `virtualStock` as a cache or Redis value.
- Exposing an authentication token or sensitive production base URL.
