---
name: query-industrial-sellable-stock
description: Use when an agent needs to query hbip-scm industrial sellable stock by SKU ID, SPU ID, SKU code, or SPU code in local, test, pre-release, or production environments.
---

# Query Industrial Sellable Stock

## Purpose

Query 工业品项目可售库存 through the hbip-scm Agent stock API. Keep the workflow simple: identify environment, classify query values, call the API, then summarize Redis and DB sellable stock.

## Platform Notes

This skill is agent-platform neutral.

- Claude Code: use the available shell tool or HTTP tool.
- Codex / opencode: use the available shell command tool; prefer `curl` when no dedicated HTTP client is available.
- Gemini or other agents: use the equivalent command execution tool.
- Never expose tokens, cookies, internal production hosts, or real customer data in the final response.

## Environment Selection

Endpoint path:

```text
/scm/inner/stock/agent-api/query-sellable-stock
```

Resolve the base URL like this:

| Environment | Base URL source | Default |
| --- | --- | --- |
| `local` | fixed local startup URL | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | ask user if missing |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | ask user if missing |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | ask user if missing |

Before querying `prod`, explicitly confirm that the user requested production. Do not infer production from ambiguous wording.

If auth is required, read it from an environment variable such as `SCM_AUTH_TOKEN`. Do not ask the user to paste secrets into chat unless there is no safer option.

## Input Classification

Build an `AgentStockQueryReqDTO` JSON body. At least one list must be non-empty.

| User input | Request field |
| --- | --- |
| Pure number | `skuIds` by default |
| Number explicitly described as SPU ID | `spuIds` |
| String starting with `SKU` | `skuCodes` |
| String starting with `SPU` | `spuCodes` |

When the user provides mixed values, group them into the matching arrays. If a numeric value may be an SPU ID but the user did not say so, ask a brief clarification or default to `skuIds` and state that assumption.

## Request

Use `POST` with `Content-Type: application/json`.

Local example:

```bash
curl -sS -X POST "http://localhost:8803/scm/inner/stock/agent-api/query-sellable-stock" \
  -H "Content-Type: application/json" \
  -d '{"skuIds":[1,2],"skuCodes":["SKU26060300019000001"],"spuCodes":["SPU26060300016000001"]}'
```

Environment example:

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST "${BASE_URL}/scm/inner/stock/agent-api/query-sellable-stock" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{"skuIds":[1],"spuIds":[6]}'
```

If no token is needed, omit the `Authorization` header.

## Response Handling

The outer response uses `Result<AgentStockQueryResultDTO>`.

- `code == 200`: API call succeeded; inspect business data.
- `data.data`: matched stock rows.
- `data.errors`: conditions that did not match data.
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

- Unmatched: list `data.errors`, if any.
- Environment: name only (`test`, `pre`, `prod`, or `local`), not the full host if it is sensitive.
- Auth: say whether auth was required, but never print the token.

Use these labels:

- Full success: rows exist and `errors` is empty.
- Partial success: rows exist and `errors` is not empty.
- All failed: rows are empty and `errors` is not empty.
- Request failed: HTTP error, auth error, timeout, or non-200 `code`.
