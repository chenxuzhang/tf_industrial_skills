---
name: query-industrial-sellable-stock
description: Use when an agent needs to query hbip-scm industrial sellable stock by SKU ID, SPU ID, SKU code, or SPU code through PMS-authenticated test pre prod environments.
---

# Query Industrial Sellable Stock

## Purpose

Query 工业品项目可售库存 through the PMS-authenticated SCM admin API. Keep the workflow simple: identify environment, classify query values, call the API, then summarize Redis and DB sellable stock.

## Security Rules

- Never read, open, cat, sed, grep, summarize, or display the PMS login config file in the agent context. It contains domains, accounts, passwords, and authorization tokens.
- Use the PMS login skill's `scripts/read_pms_env.py` helper to read runtime values into variables. Do not print those variables.
- Always execute Python helpers through `uvx --isolated --python 3.14 python ...`.
- Never print authorization tokens, passwords, cookies, or sensitive production hosts.
- Only query `prod` when the user explicitly selects production.

## Endpoint

Use the admin endpoint:

```text
POST {base_url}/scm/admin/stock/query/query-sellable-stock
authorization: {authorization}
content-type: application/json
x-app-code: ADMIN
x-client-type: PC
```

`base_url` and `authorization` must come from the selected environment in the PMS login config file. Do not pass `Bearer`; the header value is the raw authorization token.

## Input Classification

Build an `AgentStockQueryReqDTO` JSON body. At least one list must be non-empty.

| User input | Request field |
| --- | --- |
| Pure number | `skuIds` by default |
| Number explicitly described as SPU ID | `spuIds` |
| String starting with `SKU` | `skuCodes` |
| String starting with `SPU` | `spuCodes` |

When the user provides mixed values, group them into the matching arrays. If a numeric value may be an SPU ID but the user did not say so, ask a brief clarification or default to `skuIds` and state that assumption.

## Request Flow

Run commands from this skill directory. Use shell variables so secrets are not printed.

```bash
ENV_NAME="test"
DATA_RAW='{"skuIds":[1],"spuIds":[6]}'
PMS_CONFIG="../pms-login/pms-login-config.json"

BASE_URL="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field base_url)"
AUTHORIZATION="$(uvx --isolated --python 3.14 python ../pms-login/scripts/read_pms_env.py --input "${PMS_CONFIG}" --env "${ENV_NAME}" --field authorization)"

curl -sS "${BASE_URL}/scm/admin/stock/query/query-sellable-stock" \
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

## Response Handling

The outer response uses `Result<AgentStockQueryResultDTO>`.

- Successful business data is under `data.data`.
- Unmatched conditions are under `data.errors`.
- `virtualStock`: Redis cached sellable stock, 6 decimal precision.
- `dbVirtualStock`: database sellable stock.
- `queryCondition`: matched input condition, such as `skuId:1`; empty usually means SKU ID query.

Match expectations:

| Query type | Success rule | Error text |
| --- | --- | --- |
| `skuId` | exactly one row | `skuId:{value} 未查询到数据` |
| `skuCode` | exactly one row | `skuCode:{value} 未查询到数据` |
| `spuId` | at least one row | `spuId:{value} 未查询到数据` |
| `spuCode` | at least one row | `spuCode:{value} 未查询到数据` |

If `virtualStock` and `dbVirtualStock` differ, call out the difference because Redis and DB are not aligned for that SKU.

## Final Answer Format

Return a concise table:

| 查询条件 | 店铺 | SKU ID | SKU 名称 | Redis 可售 | DB 可售 |
| --- | --- | --- | --- | --- | --- |

Then add:

- Status: Full success, Partial success, All failed, or Request failed.
- Token refreshed: `yes` only if the first request returned 401 and PMS login was rerun; never print the token.
- Unmatched: list `data.errors`, if any.
- Environment: `test`, `pre`, or `prod`; do not print a sensitive host.

## Common Mistakes

- Reading or displaying the PMS login config file before running the command.
- Using ad hoc inline Python instead of `../pms-login/scripts/read_pms_env.py`.
- Using any runner other than `uvx`.
- Manually copying a token into chat or the final answer.
- Using the legacy inner agent endpoint instead of the PMS admin endpoint.
- Prefixing the authorization header with `Bearer`.
- Retrying login more than once after repeated 401 responses.
- Sending a raw array instead of a JSON object.
- Printing an auth token or a sensitive production base URL.
