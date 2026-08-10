#!/usr/bin/env python3
"""Audit a Firebase + Cloudflare web app and optionally run project scripts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".next",
    ".nuxt",
    ".output",
    ".svelte-kit",
    ".wrangler",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
}
TEXT_SUFFIXES = {
    ".cjs",
    ".css",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsonc",
    ".jsx",
    ".mjs",
    ".rules",
    ".svelte",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
}
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
SERVICE_ACCOUNT = re.compile(r'"type"\s*:\s*"service_account"')
ALLOW_ALL = re.compile(r"allow\s+(?:read\s*,\s*write|write\s*,\s*read)\s*:\s*if\s+true\s*;", re.I)
CLASSROOM_PUBLIC_RULE = re.compile(
    r"allow\s+(?:read|write|create|update|delete)"
    r"(?:\s*,\s*(?:read|write|create|update|delete))*"
    r"\s*(?::\s*if\s+true)?\s*;",
    re.I,
)
PUBLIC_SERVER_SECRET = re.compile(
    r"(?:VITE_|NEXT_PUBLIC_|PUBLIC_|REACT_APP_|NUXT_PUBLIC_).*(?:PRIVATE_KEY|SERVICE_ACCOUNT|ADMIN_|API_TOKEN|CLIENT_SECRET)",
    re.I,
)


def files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.startswith(".env") or path.name == ".dev.vars" or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def ignored(root: Path, filename: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", filename],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc.returncode == 0
    except OSError:
        return False


def package_details(root: Path) -> tuple[dict, str | None, str | None]:
    path = root / "package.json"
    if not path.exists():
        return {}, None, "package.json is missing"
    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, None, f"package.json cannot be parsed: {exc}"
    declared = package.get("packageManager", "")
    if isinstance(declared, str) and declared:
        manager = declared.split("@", 1)[0]
    elif (root / "pnpm-lock.yaml").exists():
        manager = "pnpm"
    elif (root / "yarn.lock").exists():
        manager = "yarn"
    elif (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        manager = "bun"
    else:
        manager = "npm"
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict) or "build" not in scripts:
        return package, manager, "package.json has no build script"
    return package, manager, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--rules-test", action="store_true", help="run the project's test:rules script")
    parser.add_argument(
        "--execute-project-scripts",
        action="store_true",
        help="confirm execution is occurring inside an isolated, credential-free environment",
    )
    parser.add_argument("--product", action="store_true", help="check launchable starter-product requirements")
    parser.add_argument(
        "--classroom",
        action="store_true",
        help="check the signed-in, deny-by-default classroom baseline",
    )
    args = parser.parse_args()
    if (args.build or args.rules_test) and not args.execute_project_scripts:
        parser.error(
            "--build and --rules-test execute project-defined scripts; rerun only inside an "
            "isolated, credential-free environment with --execute-project-scripts"
        )
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    errors: list[str] = []
    warnings: list[str] = []
    package, manager, package_error = package_details(root)
    if package_error:
        errors.append(package_error)
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}
    lifecycle_scripts = [
        name
        for name in ("preinstall", "install", "postinstall", "prepare", "prebuild", "postbuild")
        if name in scripts
    ]
    if lifecycle_scripts:
        warnings.append(
            "Project-defined lifecycle scripts require review before execution: "
            + ", ".join(lifecycle_scripts)
        )

    all_text: list[tuple[Path, str]] = []
    for path in files(root):
        text = read_text(path)
        all_text.append((path, text))
        relative = path.relative_to(root)
        if PRIVATE_KEY.search(text) or SERVICE_ACCOUNT.search(text):
            errors.append(f"private key or service-account material found in {relative}")
        if path.suffix == ".rules" and ALLOW_ALL.search(text):
            errors.append(f"unconditional allow-all rule found in {relative}")
        if args.classroom and path.suffix == ".rules" and CLASSROOM_PUBLIC_RULE.search(text):
            errors.append(f"public classroom rule found in {relative}")
        for line_number, line in enumerate(text.splitlines(), 1):
            if PUBLIC_SERVER_SECRET.search(line):
                errors.append(f"server-secret-like name uses a public prefix in {relative}:{line_number}")

    project_text = [
        (path, text)
        for path, text in all_text
        if path.name not in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"}
    ]

    deps = {}
    for field in ("dependencies", "devDependencies"):
        value = package.get(field, {})
        if isinstance(value, dict):
            deps.update(value)
    has_firebase_usage = any(
        "firebase/app" in text or "initializeApp(" in text for _, text in project_text
    )
    has_firebase_config = any(
        root.joinpath(name).exists()
        for name in ("firebase.json", ".firebaserc", "firestore.rules", "storage.rules")
    )
    if (has_firebase_usage or has_firebase_config) and "firebase" not in deps:
        warnings.append("Firebase configuration or usage exists but the Web SDK is not listed in package dependencies")
    if "firebase" in deps and not has_firebase_usage:
        warnings.append("Firebase dependency exists but no browser initialization was detected")

    cloudflare_configs = [
        name
        for name in ("wrangler.json", "wrangler.jsonc", "wrangler.toml")
        if (root / name).exists()
    ]
    has_pages_script = any(
        "wrangler pages deploy" in str(command)
        for command in package.get("scripts", {}).values()
    ) if isinstance(package.get("scripts", {}), dict) else False
    if not cloudflare_configs and not has_pages_script:
        warnings.append("No Wrangler config or Pages deploy script was detected")

    for env_file in (".env", ".env.local", ".env.production", ".dev.vars"):
        if (root / env_file).exists() and not ignored(root, env_file):
            errors.append(f"{env_file} exists but is not ignored by git")

    environment_keys = {
        match.group(1)
        for _, text in all_text
        for match in re.finditer(r"(?:import\.meta\.env\.|process\.env\.)([A-Z][A-Z0-9_]*)", text)
    }
    environment_keys.difference_update({"CI", "NODE_ENV", "PORT"})
    has_environment_usage = bool(environment_keys) or any("$env/" in text for _, text in all_text)
    if has_environment_usage and not (root / ".env.example").exists():
        warnings.append("No .env.example file was found")

    if args.product or args.classroom:
        combined = "\n".join(text for _, text in project_text)
        for required_script in ("dev", "build"):
            if required_script not in scripts:
                warnings.append(f"package.json has no {required_script} script")
        if not any(name in scripts for name in ("preview", "deploy")):
            warnings.append("package.json has neither a preview nor deploy script")

        uses_firestore = bool(re.search(r"firebase/firestore|\bgetFirestore\s*\(", combined, re.I))
        uses_storage = bool(re.search(r"firebase/storage|\bgetStorage\s*\(|\buploadBytes", combined, re.I))
        uses_auth = bool(re.search(r"firebase/auth|\bgetAuth\s*\(|\bsignIn", combined, re.I))
        if args.classroom:
            rules_tests = [
                path
                for path, text in all_text
                if ("rule" in path.name.lower() and re.search(r"(?:test|spec)", path.name, re.I))
                or "@firebase/rules-unit-testing" in text
            ]
            if not (root / "firestore.rules").exists():
                errors.append("classroom mode requires firestore.rules")
            if not (root / "firebase.json").exists():
                errors.append("classroom mode requires firebase.json")
            if not rules_tests:
                errors.append("classroom mode requires Firestore rules tests")
            if "test:rules" not in scripts:
                errors.append("classroom mode requires a test:rules script")
            if "@firebase/rules-unit-testing" not in deps:
                errors.append("classroom rules tests require @firebase/rules-unit-testing")
            if not uses_auth:
                warnings.append("No classroom sign-in flow was detected")
            elif not re.search(r"signInWithPopup|signInWithRedirect", combined, re.I):
                warnings.append("Authentication exists but no browser sign-in action was detected")
        if uses_firestore and not (root / "firestore.rules").exists():
            errors.append("Firestore usage was detected but firestore.rules is missing")
        if uses_storage and not (root / "storage.rules").exists():
            errors.append("Firebase Storage usage was detected but storage.rules is missing")
        if (uses_firestore or uses_storage) and not (root / "firebase.json").exists():
            errors.append("Firebase data services are used but firebase.json is missing")
        if uses_storage and not args.classroom:
            warnings.append("Firebase Storage requires Blaze plan approval before production use")

        source_only = "\n".join(
            text
            for path, text in all_text
            if any(part in {"src", "app", "pages", "components"} for part in path.parts)
        )
        for state, pattern in (
            ("loading", r"loading|pending|skeleton"),
            ("empty", r"empty|no\s+(?:items|results|data|uploads)|nothing\s+here"),
            ("error", r"error|failed|try\s+again"),
        ):
            if source_only and not re.search(pattern, source_only, re.I):
                warnings.append(f"No obvious {state} UI state was detected")
        if uses_auth and not re.search(r"signOut|log\s*out|sign\s*out", source_only, re.I):
            warnings.append("Authentication is used but no sign-out surface was detected")
        if not re.search(r"<title|document(?:Title|\.title)|metadata\s*=|title\s*:", combined, re.I):
            warnings.append("No obvious document title or framework metadata was detected")

    rules_status = "not requested"
    if args.rules_test:
        if package_error or not manager:
            rules_status = "not run"
        elif "test:rules" not in scripts:
            rules_status = "failed (missing script)"
            errors.append("rules test requested but package.json has no test:rules script")
        else:
            command = [manager, "run", "test:rules"]
            proc = subprocess.run(command, cwd=root, check=False)
            rules_status = "passed" if proc.returncode == 0 else f"failed ({proc.returncode})"
            if proc.returncode != 0:
                errors.append(f"rules tests failed: {' '.join(command)}")

    build_status = "not requested"
    if args.build and not package_error and manager:
        command = [manager, "run", "build"]
        proc = subprocess.run(command, cwd=root, check=False)
        build_status = "passed" if proc.returncode == 0 else f"failed ({proc.returncode})"
        if proc.returncode != 0:
            errors.append(f"build failed: {' '.join(command)}")

    print(f"Project: {root}")
    print(f"Rules tests: {rules_status}")
    print(f"Build: {build_status}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    print(f"Result: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
