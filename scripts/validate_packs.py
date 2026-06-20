from __future__ import annotations

import argparse
import compileall
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_PACK_FILES = (
    "README.md",
    "pyproject.toml",
    "doc/agents.md",
    "doc/architecture.md",
    "doc/runbook.md",
    "doc/security.md",
)


@dataclass(frozen=True)
class PackCheckResult:
    name: str
    ok: bool
    messages: list[str]


def discover_packs(repo_root: Path) -> list[Path]:
    packs: list[Path] = []
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "__")):
            continue
        if (child / "pyproject.toml").is_file() and (child / "README.md").is_file():
            packs.append(child)
    return packs


def check_required_files(pack_dir: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_PACK_FILES:
        if not (pack_dir / relative_path).exists():
            missing.append(relative_path)
    return missing


def compile_python(pack_dir: Path) -> tuple[bool, str]:
    ok = compileall.compile_dir(str(pack_dir), quiet=1, force=False)
    if ok:
        return True, "Python sources compiled successfully."
    return False, "Python source compilation failed."


def docker_available() -> bool:
    return shutil.which("docker") is not None


def check_docker_compose(pack_dir: Path) -> tuple[bool, str]:
    compose_file = pack_dir / "docker-compose.yml"
    if not compose_file.exists():
        return True, "No docker-compose.yml file present; Docker validation skipped."

    if not docker_available():
        return True, "Docker executable not available; Docker validation skipped."

    command = ["docker", "compose", "-f", str(compose_file), "config"]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=repo_root_for(pack_dir))
    if completed.returncode == 0:
        return True, "docker compose config succeeded."
    message = completed.stderr.strip() or completed.stdout.strip() or "docker compose config failed."
    return False, message


def repo_root_for(pack_dir: Path) -> Path:
    return pack_dir.parent


def validate_pack(pack_dir: Path, check_docker: bool) -> PackCheckResult:
    messages: list[str] = []
    ok = True

    missing = check_required_files(pack_dir)
    if missing:
        ok = False
        messages.append(f"Missing required files: {', '.join(missing)}")
    else:
        messages.append("Required files present.")

    compiled_ok, compiled_message = compile_python(pack_dir)
    ok = ok and compiled_ok
    messages.append(compiled_message)

    if check_docker:
        docker_ok, docker_message = check_docker_compose(pack_dir)
        ok = ok and docker_ok
        messages.append(docker_message)

    return PackCheckResult(name=pack_dir.name, ok=ok, messages=messages)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate multi-agent packs in the workspace.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--pack",
        action="append",
        default=[],
        help="Specific pack name to validate. Can be passed multiple times.",
    )
    parser.add_argument(
        "--check-docker",
        action="store_true",
        help="Run docker compose config for packs that provide docker-compose.yml.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    discovered = discover_packs(repo_root)
    if args.pack:
        selected = [pack for pack in discovered if pack.name in set(args.pack)]
        missing_packs = sorted(set(args.pack) - {pack.name for pack in selected})
        if missing_packs:
            for name in missing_packs:
                print(f"[error] Unknown pack: {name}")
            return 1
        packs = selected
    else:
        packs = discovered

    if not packs:
        print("[error] No pack folders discovered.")
        return 1

    overall_ok = True
    for pack_dir in packs:
        result = validate_pack(pack_dir, check_docker=args.check_docker)
        status = "ok" if result.ok else "fail"
        print(f"[{status}] {result.name}")
        for message in result.messages:
            print(f"  - {message}")
        overall_ok = overall_ok and result.ok

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())