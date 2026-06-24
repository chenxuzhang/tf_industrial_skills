#!/usr/bin/env python3
"""Login to PMS and write the authorization token back to the input JSON file."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "pms-login-config.json"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Login to PMS and write response data.authorization back to the input JSON file."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the JSON file containing environment-scoped PMS login settings.",
    )
    parser.add_argument(
        "--env",
        required=True,
        choices=("test", "pre", "prod"),
        help="Environment to log in to and update: test, pre, or prod.",
    )
    return parser.parse_args(argv)


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Input file is not valid JSON: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Input JSON must be an object.")
    return data


def require_string(config: dict[str, Any], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Input JSON must contain a non-empty string field: {key}")
    return value.strip()


def select_environment(config: dict[str, Any], env: str) -> dict[str, Any]:
    environments = config.get("environments")
    if not isinstance(environments, dict):
        raise SystemExit("Input JSON must contain an environments object.")

    env_config = environments.get(env)
    if not isinstance(env_config, dict):
        raise SystemExit(f"Input JSON must contain environments.{env} object.")

    return env_config


def resolve_base_url(config: dict[str, Any]) -> str:
    base_url = config.get("base_url") or config.get("domain")
    if not isinstance(base_url, str) or not base_url.strip():
        raise SystemExit("Input JSON must contain non-empty string field base_url or domain.")
    return base_url.strip().rstrip("/")


def build_login_url(config: dict[str, Any]) -> str:
    base_url = resolve_base_url(config)
    path = config.get("login_path", "/pms/admin/login")
    if not isinstance(path, str) or not path.strip():
        raise SystemExit("login_path must be a non-empty string when provided.")
    normalized_path = path.strip()
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    return f"{base_url}{normalized_path}"


def build_headers(config: dict[str, Any]) -> dict[str, str]:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "user-agent": str(config.get("user_agent") or DEFAULT_USER_AGENT),
        "x-app-code": str(config.get("x_app_code") or "ADMIN"),
        "x-client-type": str(config.get("x_client_type") or "PC"),
    }
    for key in ("deviceid", "origin", "referer"):
        value = config.get(key)
        if isinstance(value, str) and value.strip():
            headers[key] = value.strip().rstrip("/") if key == "origin" else value.strip()

    if "origin" in headers and "referer" not in headers:
        headers["referer"] = f"{headers['origin']}/"

    return headers


def perform_login(
    config: dict[str, Any],
    opener: Callable[..., Any] = urlopen,
) -> str:
    username = require_string(config, "username")
    password = require_string(config, "password")
    timeout = int(config.get("timeout_seconds") or 15)

    request_body = json.dumps(
        {"username": username, "password": password},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        build_login_url(config),
        data=request_body,
        headers=build_headers(config),
        method="POST",
    )

    try:
        with opener(request, timeout=timeout) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as exc:
        raise SystemExit(f"PMS login HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"PMS login request failed: {exc.reason}") from exc

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"PMS login response is not valid JSON: {exc}") from exc

    if payload.get("code") != 0 or payload.get("ok") is not True:
        message = payload.get("msg") or "unknown error"
        raise SystemExit(f"PMS login failed: code={payload.get('code')}, msg={message}")

    data = payload.get("data")
    authorization = data.get("authorization") if isinstance(data, dict) else None
    if not isinstance(authorization, str) or not authorization.strip():
        raise SystemExit("PMS login response does not contain data.authorization.")

    return authorization.strip()


def write_authorization(path: Path, config: dict[str, Any], env: str, authorization: str) -> None:
    updated = dict(config)
    environments = dict(updated["environments"])
    env_config = dict(environments[env])
    env_config["authorization"] = authorization
    environments[env] = env_config
    updated["environments"] = environments

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        json.dump(updated, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)

    tmp_path.replace(path)


def main(argv: list[str] | None = None, opener: Callable[..., Any] = urlopen) -> str:
    args = parse_args(argv)
    input_path = Path(args.input).expanduser().resolve()
    config = read_json(input_path)
    env_config = select_environment(config, args.env)
    authorization = perform_login(env_config, opener=opener)
    write_authorization(input_path, config, args.env, authorization)
    return f"PMS login succeeded for {args.env}; authorization written to {input_path}"


if __name__ == "__main__":
    try:
        print(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - last-resort CLI guard.
        print(f"PMS login failed: {exc}", file=sys.stderr)
        sys.exit(1)
