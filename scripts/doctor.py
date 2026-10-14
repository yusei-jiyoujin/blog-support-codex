"""Check shared workflow files and dependencies without modifying user data."""

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path


RULE_FILES = (
    "AGENTS.md", "ARTICLE_RULES.md", "WORKFLOW_CONFIG.json", "SITE_PROFILE.md",
    "AUTO_CONTENT.md", "OUTPUT_FORMAT.md", "QUALITY_GATE.md", "IMAGE_RULES.md",
    "AFFILIATE_RESEARCH.md", "AFFILIATE_LINKING.md", "ARTICLE_LOGGING.md",
    "CONTENT_STRATEGY.md", "CATEGORY_RULES.md", "KEYWORD_PLAN.md",
    "requirements.txt", "scripts/setup.sh", "scripts/doctor.py",
    "scripts/check_article_length.py",
)
STATE_FILES = {
    "ARTICLE_INDEX.json": "articles",
    "ARTICLE_BATCH.json": "batches",
    "ARTICLE_LOG.json": "events",
    "AFFILIATE_CATALOG.json": "programs",
}


def inspect(root, image_generation="unknown"):
    root = root.resolve()
    errors = []
    warnings = []
    digest = hashlib.sha256()
    for name in RULE_FILES:
        path = root / name
        try:
            data = path.read_bytes()
            digest.update(name.encode() + b"\0" + data + b"\0")
        except OSError:
            errors.append(f"Missing shared file: {name}")
    entry = root / "AGENTS.md"
    if entry.exists() and entry.stat().st_size > 8192:
        errors.append("AGENTS.md must stay below the project's 8 KiB entry budget")
    config = None
    try:
        config = json.loads((root / "WORKFLOW_CONFIG.json").read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("configuration must be an object")
        expected = {
            "version": 1, "site_url": "https://jiyoujin.com/", "language": "ja",
            "timezone": "Asia/Tokyo", "article_count": 5,
            "minimum_body_characters": 5000, "eyecatch_count": 1,
            "inline_image_count": 1, "delivery_mode": "per_article",
            "require_delivery_before_next": True,
            "missing_image_policy": "pause_after_current_article",
        }
        for key, value in expected.items():
            if type(config.get(key)) is not type(value) or config.get(key) != value:
                errors.append(f"Shared configuration mismatch: {key}")
        categories = ["副業ライフ", "ノマドライフ", "暮らしの工夫", "自己投資", "ブログラボ"]
        if config.get("categories") != categories:
            errors.append("Shared configuration mismatch: categories")
    except (OSError, ValueError, UnicodeError) as error:
        errors.append(f"Cannot load WORKFLOW_CONFIG.json: {error}")
    for name, key in STATE_FILES.items():
        try:
            state = json.loads((root / name).read_text(encoding="utf-8"))
            if not isinstance(state, dict) or not isinstance(state.get(key), list):
                errors.append(f"Invalid state array: {name}.{key}")
        except (OSError, ValueError, UnicodeError) as error:
            errors.append(f"Cannot read state file {name}: {error}")
    for package, version in (("markdown-it-py", "4.0.0"), ("mdurl", "0.1.2")):
        try:
            if importlib.metadata.version(package) != version:
                errors.append(f"Dependency version mismatch: {package} requires {version}")
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"Missing dependency: {package}; run bash scripts/setup.sh")
    if sys.version_info < (3, 10):
        errors.append("Python 3.10+ is required")
    if image_generation == "unknown":
        warnings.append("Image generation requires checking Codex's tool list; Python cannot detect it")
    elif image_generation == "unavailable":
        warnings.append("Article text can start; delivery pauses before article 2 until images are available or explicitly skipped")
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {
        "ready_for_text": not errors, "root": str(root), "commit": commit,
        "workflow_fingerprint": digest.hexdigest(), "config": config,
        "image_generation": image_generation, "errors": errors, "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--image-generation", choices=("unknown", "available", "unavailable"), default="unknown")
    args = parser.parse_args()
    report = inspect(args.root, args.image_generation)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready_for_text"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
