#!/usr/bin/env python3
"""
Basic public-repo sanitization scanner.

This is not a full secrets scanner. Use it as an additional safety check
before publishing or merging changes.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")

SKIP_DIRS = {".git", ".venv", "__pycache__"}
SKIP_FILES = {"sanitize_check.py"}

PATTERNS = {
    "uuid_like_value": re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    "azure_callback_sig": re.compile(r"sig=", re.IGNORECASE),
    "azurewebsites_hostname": re.compile(r"\b(?!privatelink\.)[a-zA-Z0-9-]+\.azurewebsites\.net\b"),
    "possible_secret_key": re.compile(r"(clientSecret|functionKey|sharedKey|apiKey|connectionString|token)\s*[:=]", re.IGNORECASE),
}

ALLOWLIST_FILES = {
    "networking-private-design.md",
    "sanitization-checklist.md",
    "security-design.md",
    "README.md",
    "function_app.py",
    "parent-agent-loop-sanitized.json",
    "child-sentinel-health-query-tool-sanitized.json",
    "pep-request-deny-forbidden-kql.json",
}

def should_skip(path: pathlib.Path) -> bool:
    return path.name in SKIP_FILES or any(part in SKIP_DIRS for part in path.parts)

def main() -> int:
    findings = []

    for path in ROOT.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                if path.name in ALLOWLIST_FILES and name == "possible_secret_key":
                    continue
                findings.append((str(path), name, match.group(0)))

    if findings:
        print("Potential sensitive values found:")
        for file_path, pattern_name, value in findings:
            print(f"- {file_path}: {pattern_name}: {value}")
        return 1

    print("No obvious sensitive values found by basic scanner.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
