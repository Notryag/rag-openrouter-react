#!/usr/bin/env python3
"""Architecture guardrails for repo structure and file growth."""

from __future__ import annotations

from pathlib import Path
import sys
import os


ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "node_modules", "dist", "__pycache__"}


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def iter_files(base: Path, suffixes: set[str]):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in files:
            path = Path(root) / name
            if path.suffix in suffixes:
                yield path


def main() -> int:
    failures: list[str] = []

    backend_dir = ROOT / "backend"
    frontend_src_dir = ROOT / "frontend" / "src"

    # 1) Placement checks
    allowed_backend_roots = {
        ROOT / "backend" / "app.py",
    }
    allowed_backend_dirs = [
        ROOT / "backend" / "scripts",
        ROOT / "backend" / "core",
        ROOT / "backend" / "routers",
        ROOT / "backend" / "services",
        ROOT / "backend" / "repositories",
        ROOT / "backend" / "schemas",
    ]

    for path in iter_files(backend_dir, {".py"}):
        if path.name == "__init__.py":
            continue
        if path in allowed_backend_roots:
            continue
        if any(is_within(path, allowed_dir) for allowed_dir in allowed_backend_dirs):
            continue
        failures.append(
            f"[placement] {relative(path)} should be moved under backend/core|routers|services|repositories|schemas|scripts"
        )

    allowed_frontend_root_files = {
        ROOT / "frontend" / "src" / "App.jsx",
        ROOT / "frontend" / "src" / "main.jsx",
        ROOT / "frontend" / "src" / "api.js",
    }
    allowed_frontend_dirs = [
        ROOT / "frontend" / "src" / "components",
        ROOT / "frontend" / "src" / "hooks",
        ROOT / "frontend" / "src" / "services",
        ROOT / "frontend" / "src" / "state",
    ]

    for path in iter_files(frontend_src_dir, {".js", ".jsx"}):
        if path in allowed_frontend_root_files:
            continue
        if any(is_within(path, allowed_dir) for allowed_dir in allowed_frontend_dirs):
            continue
        failures.append(
            f"[placement] {relative(path)} should be under src/components|hooks|services|state"
        )

    # 2) Size checks (transitional guardrails)
    caps = {
        ROOT / "backend" / "app.py": 740,
        ROOT / "frontend" / "src" / "App.jsx": 330,
    }

    for file_path, cap in caps.items():
        if file_path.exists():
            lines = count_lines(file_path)
            if lines > cap:
                failures.append(
                    f"[size] {relative(file_path)} has {lines} lines (cap {cap})"
                )

    for path in iter_files(backend_dir, {".py"}):
        if path.name == "__init__.py":
            continue
        if path == ROOT / "backend" / "app.py":
            continue
        lines = count_lines(path)
        if lines > 260:
            failures.append(
                f"[size] {relative(path)} has {lines} lines (cap 260 for non-app backend python)"
            )

    for path in iter_files(frontend_src_dir, {".js", ".jsx"}):
        if path == ROOT / "frontend" / "src" / "App.jsx":
            continue
        lines = count_lines(path)
        if lines > 220:
            failures.append(
                f"[size] {relative(path)} has {lines} lines (cap 220 for non-App frontend js/jsx)"
            )

    # 3) Basic boundary checks for future split layers
    for path in iter_files(ROOT / "frontend" / "src" / "components", {".jsx"}):
        content = path.read_text(encoding="utf-8")
        if "./api" in content or "../api" in content:
            failures.append(
                f"[boundary] {relative(path)} should not import api.js directly; use src/services layer"
            )

    for path in iter_files(ROOT / "backend" / "routers", {".py"}):
        content = path.read_text(encoding="utf-8")
        if "import sqlite3" in content:
            failures.append(
                f"[boundary] {relative(path)} should not import sqlite3 directly; use repositories layer"
            )

    if failures:
        print("Architecture check failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
