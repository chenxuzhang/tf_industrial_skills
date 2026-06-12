---
name: query-industrial-stock-redis
description: Use when an agent needs to inspect hbip-scm stock Redis datasource configuration, discover supported stock Redis key patterns, or query complete Redis keys for values, data types, and TTLs in local, test, pre-release, or production environments.
---

# Query Industrial Stock Redis

## Purpose

Query the read-only hbip-scm stock Redis Agent APIs. Select one endpoint from the user's intent; discover key patterns before querying values only when the user has not supplied a complete key.

## Platform And Security

- Use the available HTTP or shell tool; prefer `curl` when no HTTP client is available.
- These endpoints are read-only, but production access still requires explicit user intent.
- Never print authentication credentials, cookies, `passwordMasked`, or sensitive internal Redis/application addresses.
- For configuration results, summarize datasource names, database indexes, timeouts, and serializers. Redact addresses by default and always redact them in production; show a non-production address only when the user explicitly requests it and it is safe to disclose.
- Redis values may contain customer, order, inventory, or idempotency data. Return only the fields needed to answer the request and avoid echoing unrelated payload content.

## Environment Selection

| Environment | Base URL source | Default |
| --- | --- | --- |
| `local` | Fixed local startup URL | `http://localhost:8803` |
| `test` | `SCM_STOCK_TEST_BASE_URL` | Ask if missing |
| `pre` / `pre-release` | `SCM_STOCK_PRE_BASE_URL` | Ask if missing |
| `prod` / `production` | `SCM_STOCK_PROD_BASE_URL` | Ask if missing |

Do not infer production from ambiguous wording. If authentication is required, read it from `SCM_AUTH_TOKEN`; do not ask the user to paste a token unless no safer option exists.

All endpoint paths include the application context path `/scm`.

## Intent Routing

Choose exactly one endpoint by default.

| User intent | Endpoint |
| --- | --- |
| 查看 stock 模块 Redis 数据源、DB 索引、超时或序列化配置 | `/scm/inner/stock/agent-api/query-redis-config` |
| 查看当前 Agent 接口公开的库存 Redis key 模式和占位符 | `/scm/inner/stock/agent-api/query-redis-keys` |
| 已知完整 Redis key，查询值、类型和 TTL | `/scm/inner/stock/agent-api/query-redis-value` |

If the user asks for a Redis value but supplies only an order number, refund number, or other placeholder value, call `query-redis-keys` first or ask which key pattern they intend. Do not guess a complete key.

## Shared Request Rules

- Method: `POST`
- Outer response: `Result<T>`
- Treat HTTP errors, authentication errors, timeouts, and a non-success outer result as request failures.
- Omit the `Authorization` header when authentication is not required.
- Successful value-query data and business-level errors may coexist.

## Query Redis Configuration

This endpoint has no request body.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/query-redis-config" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}"
```

Response data:

| Field | Meaning |
| --- | --- |
| `primary` | Primary Redis datasource name |
| `globalSerializer` | Default serializers for string, hash, list, set, and zset |
| `datasources[].name` | Datasource name |
| `datasources[].primary` | Whether this is the primary datasource |
| `datasources[].address` | Redis `host:port`; redact in user-facing output |
| `datasources[].database` | Redis database index |
| `datasources[].timeout` | Connection timeout in milliseconds |
| `datasources[].passwordMasked` | Masked password; do not print it |
| `datasources[].serializer` | Datasource override; null means use `globalSerializer` |

Serializer values can include `STRING`, `FASTJSON`, `JACKSON`, and `JDK`. Hash configuration uses `key`, `hashKey`, and `hashValue`; other structures use `key` and `value`.

## Query Redis Key Patterns

This endpoint requires an empty JSON object because the controller binds `@RequestBody AgentRedisKeyQueryReqDTO`.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/query-redis-keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{}'
```

The current implementation returns only these active patterns:

| Pattern | Placeholder 1 | Purpose |
| --- | --- | --- |
| `hbip-scm:scm-stock:scm-stock-service:stock:freeze:idempotent:%s` | Main order number | Main-order stock-freeze idempotency check |
| `hbip-scm:scm-stock:scm-stock-service:stock:unfreeze:idempotent:%s` | Sub-order number or `RF_` refund number | Stock-unfreeze idempotency check |

Important:

- The request object currently has no fields.
- The current implementation does not return every constant in `RedisKeyEnum`.
- The merchant sellable-stock pattern and stock-deduct pattern are not exposed by this endpoint.
- Returned `dataSource` can be null because the implementation does not populate it; interpret that as no explicit datasource metadata, not as proof that the key is absent.

Replace `%s` with the complete placeholder value without adding quotes or braces. Do not call the value endpoint with the literal `%s`.

## Query Redis Values

Send a JSON object containing `keys`. Each entry requires a complete key and can independently select a datasource.

```bash
BASE_URL="${SCM_STOCK_TEST_BASE_URL}"

curl -sS -X POST \
  "${BASE_URL}/scm/inner/stock/agent-api/query-redis-value" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SCM_AUTH_TOKEN}" \
  -d '{
    "keys": [
      {
        "key": "hbip-scm:scm-stock:scm-stock-service:stock:freeze:idempotent:MAIN_ORDER_NO",
        "dataSource": "<datasource-name-from-query-redis-config>"
      },
      {
        "key": "hbip-scm:scm-stock:scm-stock-service:stock:unfreeze:idempotent:RF_1001"
      }
    ]
  }'
```

Rules:

- `keys` must be non-empty; otherwise `errors` contains `keys 不能为空`.
- `key` is trimmed and must be non-blank.
- Omit `dataSource` or send `""` to use the configured primary datasource.
- When specifying `dataSource`, use a name returned by `query-redis-config`; do not assume that the primary datasource is named `main`.
- Do not send whitespace as `dataSource`; it is treated as a literal datasource name.
- Supported Redis types are `string`, `hash`, `list`, `set`, and `zset`.
- String values are returned as strings. Hash, list, set, and zset values are returned as JSON text inside the `value` string.
- An existing empty collection can have `value = null`; use TTL and type to distinguish it from a missing key.
- A missing key returns `ttlSeconds = -2` and `value = null`; its type is normally `none`.
- `ttlSeconds = -1` means the key exists without an expiration.
- Invalid datasource and per-key query exceptions are added to `errors` without discarding successful rows.
- Errors are deduplicated while preserving first-seen order.
- A value read/deserialization failure can appear as a `value` string beginning with `读取失败:` rather than in `errors`; report it as a per-key read failure.

The response data is:

```text
dataSource = "按 key 独立指定"
data[{key, value, ttlSeconds, type}]
errors[string]
```

Successful rows preserve the successful input order, but failed entries are omitted. Individual rows do not include the datasource name, so do not claim which datasource produced a row when multiple datasources were queried unless it can be mapped unambiguously from the request.

## Response Presentation

For configuration:

| 数据源 | 主数据源 | DB | 超时(ms) | 序列化覆盖 |
| --- | --- | ---: | ---: | --- |

State the primary datasource and summarize the global serializers separately. Redact addresses and password fields.

For key patterns:

| Key 模式 | 占位符 | 用途 |
| --- | --- | --- |

For values:

| Key | 类型 | TTL(秒) | 值 |
| --- | --- | ---: | --- |

Truncate long values and describe their structure unless the user explicitly asks for raw JSON or the full value. Then report:

- Status: full success, partial success, all failed, or request failed.
- Errors: preserve the returned order.
- Environment: `local`, `test`, `pre`, or `prod`, without printing a sensitive host.
- Auth: whether authentication was required, without exposing credentials.

## Common Mistakes

- Omitting `/scm` from the endpoint path.
- Sending no body to `query-redis-keys` instead of `{}`.
- Sending a raw key array instead of `{"keys":[...]}` to `query-redis-value`.
- Passing a key pattern containing `%s` instead of a complete key.
- Assuming `query-redis-keys` exposes every `RedisKeyEnum` constant.
- Treating a null key-pattern `dataSource` as a missing datasource.
- Treating `ttlSeconds = -1` as missing instead of persistent.
- Treating an existing empty collection with `value = null` as definitely missing.
- Assuming each value row identifies its datasource.
- Ignoring successful value rows because `errors` is non-empty.
- Printing masked passwords, internal addresses, credentials, or unnecessary sensitive Redis values.
