---
name: gitlab-pipeline-operations
description: Use when an agent needs to query GitLab CI pipeline execution records with glab, inspect a pipeline by pipeline ID, or create GitLab pipelines for test, pre-release, or production branches using glab pipeline run.
---

# GitLab Pipeline Operations

## Purpose

Use the GitLab CLI (`glab`) to query recent pipeline execution records or create a pipeline for a known deployment environment. Keep the workflow command-driven and do not invent GitLab API calls when the requested operation maps to the commands below.

## Platform And Safety

- Run commands from the target Git repository so `glab` resolves the correct GitLab project.
- Require `glab` and `jq` for pipeline-record queries; require `glab` for pipeline creation.
- Never print GitLab tokens, cookies, project secrets, masked variables, or sensitive job log content.
- Pipeline creation is a side-effecting operation. Only run it when the user explicitly asks to create, run, trigger, or start a pipeline.
- For production, require explicit wording such as `master`, `prod`, `production`, or `正式环境`. Do not infer production from ambiguous text such as "上线" without confirmation.

## Intent Routing

| User intent | Operation |
| --- | --- |
| 查询流水线执行记录、查看 pipeline 记录、看最近 CI 执行情况 | Query pipeline records list |
| 根据流水线记录 ID 查询详情、查看 pipeline ID 详情 | Query one pipeline detail by ID |
| 创建测试环境流水线、触发 test 流水线 | Run `test` branch pipeline |
| 创建预发布流水线、触发 pre 流水线 | Run `pre` branch pipeline |
| 创建正式环境流水线、触发生产流水线、触发 master 流水线 | Run `master` branch pipeline |

If the user asks for a pipeline creation but does not name `test`, `pre`, or `master`/production, ask which environment to use before running any creation command.

## Query Pipeline Records

Use this command to query recent pipeline execution records. This is the required list-query workflow: first get pipeline IDs from `glab pipeline list -F json`, then call `glab ci get` for each ID and show only the first 10 lines per pipeline record.

```bash
for id in $(glab pipeline list -F json | jq -r '.[].id'); do
  glab ci get --pipeline-id "$id" 2>/dev/null | head -10
  echo "---"
done
```

Display the records as a page table. The table data should be read from the `glab ci get --pipeline-id "$id" | head -10` blocks produced by the loop. The table must include these fields:

| Field | Rule |
| --- | --- |
| `id` | Show the pipeline record ID so the user can request details later. |
| `status` | Required. |
| `ref` | Required. |
| `sha` | Required; show only the first 8 characters when the SHA is longer than 8 characters. |
| `user` | Required; prefer username, then display name, then raw user value. |
| `created` | Required; use `created_at` when `created` is absent. |

Other fields from the first 10 lines of each pipeline record are optional and may be omitted from the list page. Do not replace this loop with a direct `glab pipeline list -F json | jq ...` table-only query unless the user explicitly asks for raw JSON/list output instead of pipeline execution records.

## Query Pipeline Detail By ID

When the user provides a pipeline record ID, query the complete detail with:

```bash
glab ci get --pipeline-id 1222
```

Replace `1222` with the requested pipeline ID. Display all returned detail data on the page. Do not pipe the command through `head`, `tail`, field filters, or summary-only formatting. Preserve all sections and rows returned by `glab`; redact only credentials, tokens, cookies, and secrets if they appear.

Before running it, check prerequisites if the environment is uncertain:

```bash
command -v glab
command -v jq
glab auth status
```

If `glab pipeline list -F json` fails because authentication, network access, or project context is missing, report that directly and do not retry with secrets printed in the command.
If `glab ci get --pipeline-id <id>` fails, report the failing pipeline ID and the `glab` error without guessing another ID.

## Create Pipelines

Map the requested environment to exactly one branch:

| Environment wording | Branch | Command |
| --- | --- | --- |
| `test`, `测试`, `测试环境` | `test` | `glab pipeline run -b test` |
| `pre`, `预发布`, `预发布环境` | `pre` | `glab pipeline run -b pre` |
| `master`, `prod`, `production`, `正式`, `正式环境`, `生产` | `master` | `glab pipeline run -b master` |

Run the command exactly from the repository root or the intended GitLab project directory:

```bash
glab pipeline run -b test
glab pipeline run -b pre
glab pipeline run -b master
```

If branch protection, permissions, variables, or manual inputs block pipeline creation, stop and report the `glab` error. Do not guess additional flags or pass secret variables unless the user explicitly provides safe, non-secret values.

## Response Presentation

For query results:

- For the list page, show a table with `id`, `status`, `ref`, `sha`, `user`, and `created`. Keep `sha` to 8 characters when longer.
- For a pipeline detail page, show all data returned by `glab ci get --pipeline-id <id>` instead of a summary.
- Preserve important error messages from `glab` without exposing credentials.

For pipeline creation:

- State the environment and branch used.
- Include the resulting pipeline URL or ID if `glab` prints it.
- If creation failed, state the failing command and the actionable error.

## Common Mistakes

- Running `glab pipeline run` without an explicit environment.
- Treating `pre` and `master` as interchangeable release targets.
- Creating a production pipeline from ambiguous wording.
- Running commands outside the target GitLab repository.
- Omitting `jq` for the pipeline-record loop.
- Using `head -10` for detail queries and hiding required data.
- Omitting required list fields: `status`, `ref`, `sha`, `user`, or `created`.
- Printing authentication tokens or masked CI/CD variables.
