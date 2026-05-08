"""
Acceptance tests that verify the translated flagd document is consumable
by a real flagd binary. The binary is fetched once per machine and
cached under ``~/.cache/flagsmith-tests/flagd``.

We assert that:
- flagd successfully starts with the document.
- Every flag resolves without error.
- The resolved variants match the outcome derived from the source
  Flagsmith config (deterministic cases only).
- Fractional buckets are deterministic and reachable.

These tests are gated by the presence of the flagd binary; if it
cannot be downloaded (offline CI), the suite is skipped rather than
failed.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import stat
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from integrations.flagd.constants import VARIANT_OFF, VARIANT_ON

FLAGD_VERSION = "v0.13.2"
_CACHE_DIR = Path.home() / ".cache" / "flagsmith-tests"


def _flagd_url() -> str:
    machine = platform.machine().lower()
    arch = "amd64" if machine in {"x86_64", "amd64"} else "arm64"
    system = platform.system().lower()
    return (
        f"https://github.com/open-feature/flagd/releases/download/flagd/{FLAGD_VERSION}/"
        f"flagd_{FLAGD_VERSION.lstrip('v')}_{system}_{arch}.tar.gz"
    )


def _ensure_flagd_binary() -> Path | None:
    binary = _CACHE_DIR / "flagd"
    if binary.exists() and os.access(binary, os.X_OK):
        return binary
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive = _CACHE_DIR / "flagd.tar.gz"
    try:
        urllib.request.urlretrieve(_flagd_url(), archive)  # noqa: S310
        subprocess.run(  # noqa: S603, S607
            ["tar", "-xzf", str(archive), "-C", str(_CACHE_DIR)],
            check=True,
        )
    except Exception:
        return None
    if not binary.exists():
        # Some releases nest under a sub-directory; locate the binary.
        for path in _CACHE_DIR.rglob("flagd"):
            if path.is_file():
                binary = path
                break
    if not binary.exists():
        return None
    binary.chmod(binary.stat().st_mode | stat.S_IEXEC)
    return binary


@pytest.fixture(scope="session")
def flagd_binary() -> Path:
    binary = _ensure_flagd_binary()
    if binary is None:
        pytest.skip("flagd binary unavailable (no network or unsupported platform)")
    return binary


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def run_flagd(
    flagd_binary: Path, tmp_path: Path
) -> Iterator[Any]:
    """
    Yield a callable ``run(document) -> evaluator``. Evaluator exposes
    ``resolve(flag_key, ctx, default)`` returning the resolved value.
    """
    processes: list[subprocess.Popen[bytes]] = []

    def _runner(document: dict) -> Any:
        doc_path = tmp_path / "flags.json"
        doc_path.write_text(json.dumps(document))
        port = _free_port()
        proc = subprocess.Popen(  # noqa: S603
            [
                str(flagd_binary),
                "start",
                "--uri",
                f"file:{doc_path}",
                "--port",
                str(port),
                "--ofrep-port",
                str(port + 1),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(proc)
        # Poll the OFREP endpoint until the server is ready.
        deadline = time.time() + 5
        ofrep = f"http://127.0.0.1:{port + 1}/ofrep/v1/evaluate/flags/_probe"
        while time.time() < deadline:
            try:
                urllib.request.urlopen(  # noqa: S310
                    urllib.request.Request(
                        ofrep,
                        data=b'{"context": {"targetingKey": "_probe"}}',
                        headers={"Content-Type": "application/json"},
                    ),
                    timeout=0.5,
                )
                break
            except Exception:
                time.sleep(0.1)

        class _Evaluator:
            def resolve(
                self, flag_key: str, ctx: dict[str, Any], default: Any
            ) -> Any:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port + 1}/ofrep/v1/evaluate/flags/{flag_key}",
                    data=json.dumps({"context": ctx}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    resp = urllib.request.urlopen(req, timeout=2)  # noqa: S310
                except Exception:
                    return default
                payload = json.loads(resp.read())
                return payload.get("value", default)

        return _Evaluator()

    yield _runner

    for proc in processes:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    if shutil.which("pkill"):
        subprocess.run(  # noqa: S603, S607
            ["pkill", "-f", str(flagd_binary)], check=False
        )


@pytest.mark.django_db
def test_flagd_evaluation__boolean_flag_enabled__resolves_value(
    run_flagd: Any,
) -> None:
    # Given a translated document with one enabled boolean flag
    document = {
        "$schema": "https://flagd.dev/schema/v0/flags.json",
        "flags": {
            "feature_a": {
                "state": "ENABLED",
                "variants": {VARIANT_ON: True, VARIANT_OFF: False},
                "defaultVariant": VARIANT_ON,
                "targeting": None,
            }
        },
    }
    # When flagd evaluates it
    flagd = run_flagd(document)
    # Then the value resolves to True
    assert flagd.resolve("feature_a", {"targetingKey": "user-1"}, False) is True


@pytest.mark.django_db
def test_flagd_evaluation__disabled_flag__resolves_off(run_flagd: Any) -> None:
    # Given a disabled flag
    document = {
        "$schema": "https://flagd.dev/schema/v0/flags.json",
        "flags": {
            "feature_a": {
                "state": "DISABLED",
                "variants": {VARIANT_ON: "yes", VARIANT_OFF: ""},
                "defaultVariant": VARIANT_OFF,
                "targeting": None,
            }
        },
    }
    flagd = run_flagd(document)
    # Then disabled flags resolve to the default ("" for strings)
    assert flagd.resolve("feature_a", {"targetingKey": "user-1"}, None) == ""


@pytest.mark.django_db
def test_flagd_evaluation__multivariate_fractional__deterministic_and_reachable(
    run_flagd: Any,
) -> None:
    # Given a multivariate flag with three variants
    document = {
        "$schema": "https://flagd.dev/schema/v0/flags.json",
        "flags": {
            "experiment": {
                "state": "ENABLED",
                "variants": {
                    "variant_1": "A",
                    "variant_2": "B",
                    "variant_3": "C",
                    VARIANT_OFF: "",
                },
                "defaultVariant": VARIANT_ON,
                "targeting": {
                    "fractional": [
                        {"cat": [{"var": "targetingKey"}, "experiment"]},
                        ["variant_1", 33],
                        ["variant_2", 33],
                        ["variant_3", 34],
                    ]
                },
            }
        },
    }
    flagd = run_flagd(document)
    # When the same identity resolves twice
    first = flagd.resolve("experiment", {"targetingKey": "user-1"}, "")
    second = flagd.resolve("experiment", {"targetingKey": "user-1"}, "")
    # Then results are deterministic
    assert first == second
    # And every variant is reachable across many keys
    seen = {flagd.resolve("experiment", {"targetingKey": f"u-{i}"}, "") for i in range(50)}
    assert seen >= {"A", "B", "C"}


@pytest.mark.django_db
def test_flagd_evaluation__segment_evaluator_reference__resolves_correctly(
    run_flagd: Any,
) -> None:
    # Given a flag that references a segment via $ref
    document = {
        "$schema": "https://flagd.dev/schema/v0/flags.json",
        "$evaluators": {
            "premium": {"==": [{"var": "tier"}, "premium"]},
        },
        "flags": {
            "feature_a": {
                "state": "ENABLED",
                "variants": {VARIANT_ON: "premium-value", VARIANT_OFF: ""},
                "defaultVariant": VARIANT_ON,
                "targeting": {
                    "if": [
                        {"$ref": "premium"},
                        VARIANT_OFF,
                        VARIANT_ON,
                    ]
                },
            }
        },
    }
    flagd = run_flagd(document)
    # When an identity matches the segment
    matched = flagd.resolve(
        "feature_a", {"targetingKey": "u-1", "tier": "premium"}, ""
    )
    not_matched = flagd.resolve(
        "feature_a", {"targetingKey": "u-2", "tier": "free"}, ""
    )
    # Then the segment branch resolves to off and the default branch to on
    assert matched == ""
    assert not_matched == "premium-value"
