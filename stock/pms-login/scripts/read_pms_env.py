#!/usr/bin/env python3
"""Read one PMS environment value for shell command substitution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "pms-login-config.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read one PMS environment field.")
    parser.add_argument("--input", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--env", required=True, choices=("test", "pre", "prod"))
    parser.add_argument("--field", required=True, choices=("base_url", "authorization"))
    return parser.parse_args(argv)


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"PMS config file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"PMS config file is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("PMS config JSON must be an object.")
    return data


def select_environment(config: dict[str, Any], env: str) -> dict[str, Any]:
    environments = config.get("environments")
    if not isinstance(environments, dict):
        raise SystemExit("PMS config must contain an environments object.")

    env_config = environments.get(env)
    if not isinstance(env_config, dict):
        raise SystemExit(f"PMS config must contain environments.{env} object.")
    return env_config


def read_field(env_config: dict[str, Any], field: str) -> str:
    if field == "base_url":
        value = env_config.get("base_url") or env_config.get("domain")
        if isinstance(value, str) and value.strip():
            return value.strip().rstrip("/")
        raise SystemExit("Selected PMS environment must contain base_url or domain.")

    value = env_config.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise SystemExit(f"Selected PMS environment must contain non-empty {field}.")


def main(argv: list[str] | None = None) -> str:
    args = parse_args(argv)
    config = read_json(Path(args.input).expanduser().resolve())
    env_config = select_environment(config, args.env)
    return read_field(env_config, args.field)


if __name__ == "__main__":
    print(main())
