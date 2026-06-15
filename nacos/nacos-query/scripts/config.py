import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class NacosConfig:
    """Nacos connection configuration."""

    server_addr: str
    username: str
    password: str
    connection_timeout: int = 5000
    read_timeout: int = 10000
    max_retries: int = 3
    retry_backoff: int = 1000

    @classmethod
    def from_env(cls, env: str) -> "NacosConfig":
        """Load configuration from environment variables.

        Args:
            env: Environment name (test, staging, prod)

        Returns:
            NacosConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        config = cls._load_from_env(env)
        return cls(**config)

    @classmethod
    def from_file(cls, env: str, config_path: Optional[str] = None) -> "NacosConfig":
        """Load configuration from JSON file.

        Args:
            env: Environment name
            config_path: Path to config file (default: ~/.nacos/config.json)

        Returns:
            NacosConfig instance

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If environment not found in config
        """
        config = cls._load_from_file(env, config_path)
        return cls(**config)

    @classmethod
    def load(cls, env: str, config_path: Optional[str] = None) -> "NacosConfig":
        """Load configuration from file or environment variables.

        Tries file first, falls back to environment variables.

        Args:
            env: Environment name
            config_path: Optional path to config file

        Returns:
            NacosConfig instance
        """
        try:
            return cls.from_file(env, config_path)
        except (FileNotFoundError, ValueError):
            return cls.from_env(env)

    @classmethod
    def _load_from_env(cls, env: str) -> dict:
        """Load configuration from environment variables.

        Args:
            env: Environment name

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If required environment variables are missing
        """
        env = env.upper()
        server_addr = os.getenv(f"NACOS_{env}_ADDR")
        username = os.getenv(f"NACOS_{env}_USERNAME")
        password = os.getenv(f"NACOS_{env}_PASSWORD")

        missing = []
        if not server_addr:
            missing.append(f"NACOS_{env}_ADDR")
        if not username:
            missing.append(f"NACOS_{env}_USERNAME")
        if not password:
            missing.append(f"NACOS_{env}_PASSWORD")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return {
            "server_addr": server_addr,
            "username": username,
            "password": password,
        }

    @classmethod
    def _load_from_file(cls, env: str, config_path: Optional[str] = None) -> dict:
        """Load configuration from JSON file.

        Args:
            env: Environment name
            config_path: Path to config file (default: ~/.nacos/config.json)

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If environment not found in config
        """
        if config_path is None:
            config_path = str(Path.home() / ".nacos" / "config.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            config_data = json.load(f)

        if env not in config_data:
            raise ValueError(f"Environment '{env}' not found in config file")

        return config_data[env]
