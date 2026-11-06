#!/usr/bin/env python3
"""Check the community repo's issue templates and Markdown links.

- Every issue form in .github/ISSUE_TEMPLATE/ parses as YAML and has a name, a
  description and a body; each body field has a type, input fields have a
  label, and field ids are unique.
- config.yml's contact links each have a name, an https URL and an "about".
- Relative links in the top-level Markdown files point at files that exist.

Usage: python3 .github/scripts/check_repo.py   (from the repo root)
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)")


def check_form(path: Path, errors: list[str]) -> None:
    form = yaml.safe_load(path.read_text())
    for key in ("name", "description", "body"):
        if not form.get(key):
            errors.append(f"{path.name}: missing '{key}'")
    ids = set()
    for i, field in enumerate(form.get("body") or []):
        where = f"{path.name}: body[{i}]"
        if "type" not in field:
            errors.append(f"{where}: missing 'type'")
            continue
        if field["type"] != "markdown" and not (field.get("attributes") or {}).get("label"):
            errors.append(f"{where}: {field['type']} field has no label")
        if fid := field.get("id"):
            if fid in ids:
                errors.append(f"{where}: duplicate id '{fid}'")
            ids.add(fid)


def check_config(path: Path, errors: list[str]) -> None:
    config = yaml.safe_load(path.read_text())
    if not isinstance(config.get("blank_issues_enabled"), bool):
        errors.append(f"{path.name}: 'blank_issues_enabled' must be true or false")
    for i, link in enumerate(config.get("contact_links") or []):
        for key in ("name", "url", "about"):
            if not link.get(key):
                errors.append(f"{path.name}: contact_links[{i}] missing '{key}'")
        if not str(link.get("url", "")).startswith("https://"):
            errors.append(f"{path.name}: contact_links[{i}] url must be https (GitHub rejects others)")


def check_links(path: Path, errors: list[str]) -> None:
    for n, line in enumerate(path.read_text().splitlines(), 1):
        for target in LINK.findall(line):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                errors.append(f"{path.name}:{n}: links to {target}, which doesn't exist")


def main() -> int:
    errors: list[str] = []
    forms = sorted(p for p in TEMPLATES.glob("*.yml") if p.name != "config.yml")
    if not forms:
        errors.append("no issue forms in .github/ISSUE_TEMPLATE/")
    for form in forms:
        check_form(form, errors)
    if (TEMPLATES / "config.yml").exists():
        check_config(TEMPLATES / "config.yml", errors)
    for md in sorted(ROOT.glob("*.md")):
        check_links(md, errors)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1
    print(f"OK: {len(forms)} issue forms, config.yml, and links in {len(list(ROOT.glob('*.md')))} Markdown files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
