---
name: nacos-query
description: Use when querying Nacos configurations, namespaces, registered services, service instances, SCM IPs, scm ip, SCM addresses, or hbip-scm nodes.
---

# Nacos Query

使用本目录中的 Python CLI 查询 Nacos 配置和服务。所有命令均在本技能目录下通过 `uvx --from .` 执行。

## SCM IP 快捷查询

当用户表达以下任一意图时，直接执行固定命令，不再询问环境、服务名、分组或命名空间：

- `scm ip`
- `查询 scm ip`
- `查 scm ip`
- `测试环境 scm 项目 ip`
- 查询 `hbip-scm` 的 IP、地址、实例或节点

固定查询目标：

| 参数 | 固定值 |
| --- | --- |
| 环境 | `test` |
| 服务名 | `hbip-scm` |
| 分组 | `DEFAULT_GROUP` |
| 命名空间 | `industrial-test` |

立即执行：

```bash
uvx --from . nacos-get-service-detail --env test --service-name hbip-scm --group DEFAULT_GROUP --namespace industrial-test
```

从返回结果中提取并展示实例 IP、端口、健康状态和启用状态。没有实例或查询失败时，直接说明脚本返回的错误。

## 执行规则

- 用户已表达查询意图时立即执行脚本，不要只回复命令，也不要再次请求确认。
- 脚本自动从 `~/.nacos/config.json` 或 `NACOS_{ENV}_ADDR`、`NACOS_{ENV}_USERNAME`、`NACOS_{ENV}_PASSWORD` 读取连接信息。
- 可直接读取已有 Nacos 凭据，不要求用户再次提供或审批。
- 不在回复、日志摘要或错误说明中展示用户名、密码、认证头或完整凭据文件内容。
- 只有用户明确指定其他环境、服务、分组或命名空间时，才覆盖 SCM IP 快捷查询的固定值。

## Commands

| 命令 | 功能 | 必需参数 | 可选参数 |
| --- | --- | --- | --- |
| `nacos-get-namespaces` | 获取命名空间列表 | `--env` | `--config` |
| `nacos-get-config-list` | 获取配置列表 | `--env` | `--namespace`, `--config` |
| `nacos-get-config-content` | 获取配置内容 | `--env`, `--data-id` | `--group`, `--namespace`, `--config` |
| `nacos-get-services` | 获取服务列表 | `--env` | `--namespace`, `--group`, `--page-no`, `--page-size`, `--config` |
| `nacos-get-service-detail` | 获取服务实例详情 | `--env`, `--service-name` | `--group`, `--namespace`, `--config` |

支持环境：`test`、`staging`、`prod`。

## Examples

```bash
uvx --from . nacos-get-namespaces --env test
uvx --from . nacos-get-config-list --env test --namespace industrial-test
uvx --from . nacos-get-config-content --env test --data-id application.yml
uvx --from . nacos-get-services --env test --namespace industrial-test
uvx --from . nacos-get-service-detail --env test --service-name hbip-scm --group DEFAULT_GROUP --namespace industrial-test
```

## Output

脚本输出 JSON，退出码 `0` 表示成功，`1` 表示失败。

成功示例：

```json
{"code": 200, "data": {}}
```

失败示例：

```json
{"error": "错误信息"}
```

返回给用户时只保留查询结果和必要错误信息，不回显敏感配置。
