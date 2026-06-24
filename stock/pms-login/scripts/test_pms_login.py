import json
import importlib.util
from pathlib import Path


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        payload = {
            "code": 0,
            "data": {
                "authorization": "mock.jwt.token",
                "token": "uuid-token-should-not-be-used",
            },
            "ok": True,
        }
        return json.dumps(payload).encode("utf-8")


def fake_urlopen(request, timeout):
    body = json.loads(request.data.decode("utf-8"))

    assert timeout == 20
    assert request.full_url == "https://pre.example.test/pms/admin/login"
    assert body == {"username": "pre-user", "password": "pre-secret"}
    assert request.headers.get("X-app-code") == "ADMIN"
    assert request.headers.get("X-client-type") == "PC"
    assert request.headers.get("Deviceid") == "pre-device"

    return FakeResponse()


def main():
    root = Path(__file__).resolve().parent
    input_file = root / "tmp_pms_login_input.json"
    script = root / "pms_login.py"

    try:
        input_file.write_text(
            json.dumps(
                {
                    "environments": {
                        "test": {
                            "base_url": "https://test.example.test/",
                            "username": "test-user",
                            "password": "test-secret",
                            "deviceid": "test-device",
                            "authorization": "old-test-token",
                        },
                        "pre": {
                            "base_url": "https://pre.example.test/",
                            "username": "pre-user",
                            "password": "pre-secret",
                            "deviceid": "pre-device",
                            "authorization": "old-pre-token",
                            "timeout_seconds": 20,
                        },
                        "prod": {
                            "base_url": "https://prod.example.test/",
                            "username": "prod-user",
                            "password": "prod-secret",
                            "authorization": "old-prod-token",
                        },
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        spec = importlib.util.spec_from_file_location("pms_login", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.DEFAULT_CONFIG_PATH == root.parent / "pms-login-config.json"
        assert module.DEFAULT_CONFIG_PATH.exists()

        output = module.main(["--input", str(input_file), "--env", "pre"], opener=fake_urlopen)
        assert "mock.jwt.token" not in output

        updated = json.loads(input_file.read_text(encoding="utf-8"))
        assert updated["environments"]["test"]["authorization"] == "old-test-token"
        assert updated["environments"]["pre"]["authorization"] == "mock.jwt.token"
        assert updated["environments"]["prod"]["authorization"] == "old-prod-token"
    finally:
        input_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
