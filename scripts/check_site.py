#!/usr/bin/env python3
"""Offline static checks for the Ambient Core GitHub Pages site (stdlib only)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_HREFS = frozenset(
    {
        "https://www.ambientsystems.ai",
        "https://github.com/Ambient-Team/ambient-core",
    }
)

I18N_KEYS = (
    "hero.title",
    "hero.description",
    "banner.text",
    "banner.link",
    "cta.contribute",
    "cta.start",
    "switcher.label",
)

REQUIRED_LOCALES = (
    "en",
    "sr-Latn",
    "fr-CA",
    "zh-Hans",
    "zh-Hant-HK",
    "ko",
    "ja",
    "de",
    "es",
    "sv",
    "nb",
    "da",
    "el",
    "ru",
    "he",
)

SECRET_PATTERNS = (
    re.compile(r"BEGIN PRIVATE KEY"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{10,}"),
)

HTTP_URL_RE = re.compile(r"https?://[^\s\"')]+", re.IGNORECASE)
HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
IMPORT_URL_RE = re.compile(r"""@import\s+url\s*\(\s*['"]?https?://""", re.IGNORECASE)
FONT_URL_RE = re.compile(
    r"""url\s*\(\s*['"]?([^'")]+)['"]?\s*\)""", re.IGNORECASE
)


def _errors() -> list[str]:
    errors: list[str] = []
    html_files = sorted({p.resolve() for p in ROOT.rglob("*.html") if ".git" not in p.parts})
    if len(html_files) != 1 or html_files[0].name != "index.html":
        errors.append("expected exactly one HTML page at index.html")

    index = ROOT / "index.html"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        html_tag = re.search(r"<html\b[^>]*>", text, re.I)
        if not html_tag:
            errors.append("index.html missing <html> tag")
        else:
            tag = html_tag.group(0)
            if not re.search(r"""\blang\s*=\s*["']en["']""", tag, re.I):
                errors.append("index.html must default to lang=en on <html>")
            if not re.search(r"""\bdir\s*=\s*["']ltr["']""", tag, re.I):
                errors.append("index.html must default to dir=ltr on <html>")
        if re.search(r"""rel\s*=\s*["']alternate["']""", text, re.I) or "hreflang" in text.lower():
            errors.append("hreflang/alternate links are not allowed")
        anchor_hrefs: list[str] = []
        for match in re.finditer(r"<a\b[^>]*>", text, re.I):
            tag = match.group(0)
            href_match = HREF_RE.search(tag)
            if href_match:
                anchor_hrefs.append(href_match.group(1))
        if set(anchor_hrefs) != ALLOWED_HREFS:
            errors.append(
                f"anchor href set must be exactly {sorted(ALLOWED_HREFS)!r}, found {sorted(set(anchor_hrefs))!r}"
            )
        anchor_count = len(re.findall(r"<a\b", text, re.I))
        if anchor_count != 2:
            errors.append(f"expected exactly 2 <a> elements, found {anchor_count}")

    i18n_path = ROOT / "assets" / "i18n.js"
    if i18n_path.is_file():
        raw = i18n_path.read_text(encoding="utf-8")
        match = re.search(r"const I18N_DATA = (\{[\s\S]*?\n\});", raw)
        if not match:
            errors.append("could not parse I18N_DATA from assets/i18n.js")
        else:
            try:
                blob = match.group(1)
                blob = re.sub(r",(\s*[}\]])", r"\1", blob)
                data = json.loads(blob)
            except json.JSONDecodeError as exc:
                errors.append(f"I18N_DATA JSON invalid: {exc}")
                data = {}
            for locale in REQUIRED_LOCALES:
                if locale not in data:
                    errors.append(f"missing locale {locale!r} in I18N_DATA")
                    continue
                for key in I18N_KEYS:
                    value = data.get(locale, {}).get(key)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"locale {locale!r} missing or empty key {key!r}")

    for rel in ("assets/site.css", "assets/site.js", "assets/i18n.js"):
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        body = path.read_text(encoding="utf-8")
        if HTTP_URL_RE.search(body):
            errors.append(f"{rel} must not contain http(s) URLs")
        if IMPORT_URL_RE.search(body):
            errors.append(f"{rel} must not @import remote URLs")

    css_path = ROOT / "assets" / "site.css"
    if css_path.is_file():
        css = css_path.read_text(encoding="utf-8")
        for font_ref in FONT_URL_RE.findall(css):
            ref = font_ref.strip()
            if ref.startswith(("http://", "https://", "data:")):
                errors.append(f"remote/data font URL not allowed: {ref!r}")
                continue
            font_file = (css_path.parent / ref).resolve()
            try:
                font_file.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"font path escapes repo: {ref!r}")
                continue
            if not font_file.is_file():
                errors.append(f"font file missing for CSS url({ref!r})")

    scan_paths = [
        ROOT / "index.html",
        ROOT / "assets",
        ROOT / "fonts",
    ]
    for base in scan_paths:
        if not base.exists():
            continue
        paths = [base] if base.is_file() else base.rglob("*")
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix in {".woff2"}:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            for pattern in SECRET_PATTERNS:
                if pattern.search(content):
                    errors.append(f"secret pattern {pattern.pattern!r} in {path.relative_to(ROOT)}")

    return errors


def main() -> int:
    errors = _errors()
    if errors:
        for err in errors:
            print(f"CHECK_SITE: {err}", file=sys.stderr)
        return 1
    print("OK: site checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
