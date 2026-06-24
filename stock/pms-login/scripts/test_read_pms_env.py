import importlib.util
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    config_file = root / "tmp_read_pms_env_config.json"
    script = root / "read_pms_env.py"

    try:
        config_file.write_text(
            json.dumps(
                {
                    "environments": {
                        "test": {
                            "base_url": "https://test.example.test/",
                            "authorization": "test-token",
                        },
                        "pre": {
                            "domain": "https://pre.example.test/",
                            "authorization": "pre-token",
                        },
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        spec = importlib.util.spec_from_file_location("read_pms_env", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert (
            module.main(["--input", str(config_file), "--env", "test", "--field", "base_url"])
            == "https://test.example.test"
        )
        assert (
            module.main(["--input", str(config_file), "--env", "pre", "--field", "base_url"])
            == "https://pre.example.test"
        )
        assert (
            module.main(["--input", str(config_file), "--env", "test", "--field", "authorization"])
            == "test-token"
        )
    finally:
        config_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
