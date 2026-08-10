#!/usr/bin/env python3
"""Inspect a web project without reading or printing environment values."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


FRAMEWORKS = [
    ("next", {"next"}),
    ("nuxt", {"nuxt"}),
    ("sveltekit", {"@sveltejs/kit"}),
    ("astro", {"astro"}),
    ("react-router", {"@react-router/dev", "@remix-run/dev"}),
    ("vite", {"vite"}),
    ("create-react-app", {"react-scripts"}),
]

OUTPUTS = {
    "static-html": ["dist", "public"],
    "vite": ["dist"],
    "create-react-app": ["build"],
    "astro": ["dist"],
    "next": ["out", ".next"],
}


def load_package_json(root: Path) -> tuple[dict[str, Any], str | None]:
    path = root / "package.json"
    if not path.exists():
        return {}, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return {}, str(exc)


def package_manager(root: Path, package: dict[str, Any]) -> str | None:
    declared = package.get("packageManager")
    if isinstance(declared, str) and declared:
        return declared.split("@", 1)[0]
    for filename, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
        ("package-lock.json", "npm"),
    ):
        if (root.joinpath(filename).exists()):
            return manager
    return "npm" if package else None


def framework(package: dict[str, Any]) -> str | None:
    deps: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(field, {})
        if isinstance(values, dict):
            deps.update(values)
    for name, markers in FRAMEWORKS:
        if deps.intersection(markers):
            return name
    return None


def build_command(manager: str | None, package: dict[str, Any]) -> str | None:
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict) or "build" not in scripts or not manager:
        return None
    return "npm run build" if manager == "npm" else f"{manager} run build"


def present(root: Path, names: list[str]) -> list[str]:
    return [name for name in names if root.joinpath(name).exists()]


def firebase_dependency(package: dict[str, Any]) -> bool:
    for field in ("dependencies", "devDependencies"):
        values = package.get(field, {})
        if isinstance(values, dict) and "firebase" in values:
            return True
    return False


def source_signals(root: Path) -> dict[str, bool]:
    patterns = {
        "authentication": re.compile(r"firebase/auth|\bgetAuth\s*\(|\bsignIn", re.I),
        "firestore": re.compile(r"firebase/firestore|\bgetFirestore\s*\(", re.I),
        "runtime_upload": re.compile(r"firebase/storage|\bgetStorage\s*\(|type=[\"']file[\"']|\buploadBytes", re.I),
        "server_code": re.compile(r"firebase-functions|export\s+default\s*\{\s*async\s+fetch|\bonRequest\s*\(", re.I),
    }
    matches = {name: False for name in patterns}
    skipped = {".git", ".next", ".nuxt", ".output", ".svelte-kit", "build", "dist", "node_modules", "out"}
    suffixes = {".html", ".js", ".jsx", ".mjs", ".svelte", ".ts", ".tsx", ".vue"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes or any(part in skipped for part in path.parts):
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, pattern in patterns.items():
            matches[name] = matches[name] or bool(pattern.search(text))
        if all(matches.values()):
            break
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    package, package_error = load_package_json(root)
    manager = package_manager(root, package)
    detected_framework = framework(package)
    if detected_framework is None and root.joinpath("index.html").exists():
        detected_framework = "static-html"
    output_candidates = OUTPUTS.get(detected_framework or "", [])

    result = {
        "root": str(root),
        "package_json": (root / "package.json").exists(),
        "package_json_error": package_error,
        "package_manager": manager,
        "framework": detected_framework,
        "scripts": sorted(package.get("scripts", {}).keys())
        if isinstance(package.get("scripts", {}), dict)
        else [],
        "build_command": build_command(manager, package),
        "build_output_candidates": output_candidates,
        "existing_build_outputs": present(root, output_candidates),
        "firebase": {
            "sdk_dependency": firebase_dependency(package),
            "config_files": present(
                root,
                ["firebase.json", ".firebaserc", "firestore.rules", "storage.rules"],
            ),
            "cli_available": bool(shutil.which("firebase")),
        },
        "cloudflare": {
            "config_files": present(
                root,
                ["wrangler.json", "wrangler.jsonc", "wrangler.toml", "_headers", "_redirects"],
            ),
            "wrangler_dependency": any(
                isinstance(package.get(field, {}), dict)
                and "wrangler" in package.get(field, {})
                for field in ("dependencies", "devDependencies")
            ),
            "cli_available": bool(shutil.which("wrangler")),
        },
        "environment_files": present(
            root,
            [
                ".env",
                ".env.local",
                ".env.development",
                ".env.production",
                ".dev.vars",
                ".env.example",
            ],
        ),
        "gitignore": (root / ".gitignore").exists(),
        "product_signals": source_signals(root),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if package_error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
