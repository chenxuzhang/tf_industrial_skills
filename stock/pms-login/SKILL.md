---
name: pms-login
description: Use when an agent needs to log in to PMS admin through the pms/admin/login API with separate test pre prod domains accounts and authorization tokens stored in a local JSON file.
---

# PMS Login

## Purpose

Login to PMS admin for one selected environment. The Python script reads `pms-login-config.json` and writes the response `data.authorization` value back to that environment as `authorization`.

## Security Rules

- Never print `password`, `authorization`, cookies, or full JWT values in the final response.
- Never read, open, cat, sed, grep, summarize, or display `pms-login-config.json` in the agent context. It contains environment domains, accounts, passwords, and tokens.
- Only `scripts/pms_login.py` may read or write `pms-login-config.json`.
- Require an explicit environment: `test`, `pre`, or `prod`.
- Do not infer production from ambiguous wording; only run `prod` when the user or command explicitly selects `--env prod`.
- Treat `data.authorization` as the token. Do not use `data.token`, because that field is the UUID-style token from the response.
- Keep environment domains, usernames, passwords, and authorization tokens in `pms-login-config.json`; do not hardcode them in the script.

## Config File

The default parameter file is:

```text
./pms-login-config.json
```

Do not inspect this file with agent tools. It must contain an `environments` object with `test`, `pre`, and `prod` environment objects. Each environment object stores that environment's gateway domain, PMS username, PMS password, optional request metadata, and `authorization` token.

Run with one selected environment:

| Command env | Config object | Token writeback |
| --- | --- | --- |
| `--env test` | `environments.test` | `environments.test.authorization` |
| `--env pre` | `environments.pre` | `environments.pre.authorization` |
| `--env prod` | `environments.prod` | `environments.prod.authorization` |

Required fields inside the selected environment object:

| Field | Meaning |
| --- | --- |
| `base_url` or `domain` | Gateway domain, without requiring the `/pms/admin/login` path. |
| `username` | PMS login username. |
| `password` | PMS login password. |

Optional fields inside each environment object:

| Field | Default |
| --- | --- |
| `login_path` | `/pms/admin/login` |
| `deviceid` | omitted if not configured |
| `origin` | omitted if not configured |
| `referer` | `${origin}/` |
| `timeout_seconds` | `15` |

After a successful login, the script overwrites only the selected environment's `authorization` in this same JSON file. Other environments' tokens are left unchanged.

## Run

Run from this skill directory and always use `uvx` to execute the script.

```bash
uvx --isolated --python 3.14 python scripts/pms_login.py --env test
```

Use `--input` only when you need a different config file:

```bash
uvx --isolated --python 3.14 python scripts/pms_login.py --input /path/to/pms-login-config.json --env pre
```

## Request Contract

The script calls:

```text
POST {base_url}/pms/admin/login
Content-Type: application/json
x-app-code: ADMIN
x-client-type: PC
```

Request body:

```json
{"username":"<username>","password":"<password>"}
```

The script also sends browser-compatible headers from the captured PMS curl, including `accept`, `accept-language`, `deviceid`, `origin`, `referer`, and `user-agent`.

## Response Handling

Expected success response:

```json
{
  "code": 0,
  "data": {
    "authorization": "..."
  },
  "ok": true
}
```

Success rules:

- `code` must be `0`.
- `ok` must be `true`.
- `data.authorization` must be a non-empty string.

On success, report only that the token was written to the input file. Do not print the token.

## Common Mistakes

- Omitting `--env`; the script requires `test`, `pre`, or `prod`.
- Reading or displaying `pms-login-config.json` before running the script.
- Using any runner other than `uvx`.
- Putting `base_url`, `username`, or `password` at the top level instead of inside `environments.<env>`.
- Adding a new domain or account in the script instead of `pms-login-config.json`.
- Passing the full login URL as `base_url` and also keeping the default `login_path`; `base_url` should be only the gateway domain.
- Reading `data.token` instead of `data.authorization`.
- Printing the JWT in chat or terminal summaries.
- Reusing a token from another environment; always read and write the token under the selected environment object.
- Hardcoding username and password in the skill body or script; keep current credentials in the input JSON file.
