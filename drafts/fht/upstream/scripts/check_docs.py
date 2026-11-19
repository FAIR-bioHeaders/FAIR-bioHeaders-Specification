"""Owned documentation checks for FHT-Specification (issue #14).

Zero-dependency (standard library only) checks that run on every push and pull
request under ``.github/workflows/docs-checks.yml`` and act as the PR signal
for documentation-only changes:

1. Git conflict markers (``<<<<<<<`` / ``=======`` / ``>>>>>>>`` lines).
2. Whitespace hygiene: trailing whitespace, carriage returns and a missing
   single final newline.
3. Local relative links in Markdown: the target path (file or directory) must
   exist, and ``#fragment`` anchors must match a GitHub-style heading slug in
   the target (or the same) Markdown file.

External (http/https) links are deliberately NOT fetched here: transient
remote failures must not be the PR signal. They are checked on a schedule and
on demand by ``scripts/check_external_links.py``. Markdownlint itself runs as
a separate pinned step (``npx -y markdownlint-cli2@0.24.0``) with the reviewed
local configuration ``.markdownlint-cli2.jsonc``.

Local usage (repository root or anywhere):

    python scripts/check_docs.py            # check every tracked Markdown file
    python scripts/check_docs.py README.md  # check specific files
    python scripts/check_docs.py --list-external

Exit status is 0 when all checks pass and 1 otherwise. All findings are
reported before the script exits, so one run shows every problem.

Scope notes: link extraction skips fenced code blocks; inline code spans
containing Markdown link syntax are not modelled and reference-style links
(``[text][ref]``) are not followed (limitations, not failures; all current
Markdown uses inline links). HTML ``<a href>`` links inside Markdown are not
checked here.
"""

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIR_PARTS = {".git", "node_modules", ".venv", "venv", "__pycache__"}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+[\"'][^)]*[\"'])?\s*\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
ANGLE_RE = re.compile(r"<(https?://[^<>\s]+)>")
CONFLICT_START_RE = re.compile(r"^<{7}(?:\s|$)")
CONFLICT_END_RE = re.compile(r"^>{7}(?:\s|$)")
CONFLICT_MID_RE = re.compile(r"^={7}$")
FENCE_RE = re.compile(r"^ {0,3}(```+|~~~+)")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def markdown_files(paths):
    """Yield Markdown files under the given paths (default: whole repository)."""
    if not paths:
        paths = [ROOT]
    seen = []
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(path.rglob("*.md"))
        else:
            yield None, f"{raw}: no such file or directory"
            continue
        for candidate in candidates:
            if SKIP_DIR_PARTS.intersection(candidate.parts):
                continue
            seen.append(candidate)
    for candidate in seen:
        yield candidate, None


def strip_fences(lines):
    """Yield (number, text, in_code) with fenced code blocks marked."""
    fence = None
    for number, text in enumerate(lines, start=1):
        match = FENCE_RE.match(text)
        if fence is None and match:
            fence = match.group(1)
            yield number, text, True
            continue
        if (
            fence is not None
            and match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
            and not text[match.end():].strip(" \t")
        ):
            fence = None
            yield number, text, True
            continue
        yield number, text, fence is not None


def slugify(heading):
    """Approximate GitHub's heading anchor slug."""
    text = heading.strip().lower()
    text = re.sub(r"`", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    out = []
    for char in text:
        if char in " \t":
            out.append("-")
        elif char == "-" or char == "_":
            out.append(char)
        elif unicodedata.category(char)[0] in ("L", "N", "M"):
            out.append(char)
    return "".join(out)


def heading_slugs(text):
    """Return the set of GitHub-style anchor slugs for a Markdown document."""
    slugs = set()
    counts = {}
    for _, line, in_code in strip_fences(text.splitlines()):
        if in_code:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = slugify(match.group(2))
        if not slug:
            continue
        if slug in counts:
            counts[slug] += 1
            slug = f"{slug}-{counts[slug]}"
        else:
            counts[slug] = 0
        slugs.add(slug)
    return slugs


def check_hygiene(rel, text):
    failures = []
    lines = text.splitlines()
    markers = [
        number
        for number, line, _ in strip_fences(lines)
        if CONFLICT_START_RE.match(line)
        or CONFLICT_END_RE.match(line)
        or CONFLICT_MID_RE.match(line)
    ]
    for number in markers:
        failures.append(f"{rel}:{number}: git conflict marker line")
    for number, line, _ in strip_fences(lines):
        if line != line.rstrip(" \t"):
            failures.append(f"{rel}:{number}: trailing whitespace")
    for number, raw in enumerate(text.split("\n"), start=1):
        if raw.endswith("\r"):
            failures.append(f"{rel}:{number}: carriage return")
    return failures


def check_file_final_newline(rel, text, failures):
    if text and not text.endswith("\n"):
        failures.append(f"{rel}: missing final newline")
    if text.endswith("\n\n"):
        failures.append(f"{rel}: more than one blank line at end of file")


def check_links(rel, path, text, slug_cache, failures):
    """Validate local relative links in one Markdown document."""
    slugs = slug_cache.get(path)
    if slugs is None:
        slugs = heading_slugs(text)
        slug_cache[path] = slugs
    in_link_targets = set()
    for number, line, in_code in strip_fences(text.splitlines()):
        if in_code:
            continue
        for match in LINK_RE.finditer(line):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            in_link_targets.add((number, target))
    for number, target in sorted(in_link_targets):
        if not target:
            failures.append(f"{rel}:{number}: empty link target")
            continue
        if SCHEME_RE.match(target):
            continue  # external or mailto: the scheduled lane owns these
        if target.startswith("#"):
            if target[1:] not in slugs:
                failures.append(
                    f"{rel}:{number}: anchor {target!r} matches no heading"
                )
            continue
        file_part, _, fragment = target.partition("#")
        if "%" in file_part:  # percent-encoding: decode for the filesystem
            file_part = unquote(file_part)
        resolved = (path.parent / file_part).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            failures.append(
                f"{rel}:{number}: link {target!r} escapes the repository"
            )
            continue
        if file_part.endswith("/") or file_part == "":
            if not resolved.is_dir():
                failures.append(f"{rel}:{number}: missing directory {file_part!r}")
            continue
        if not resolved.exists():
            failures.append(f"{rel}:{number}: missing local link target {file_part!r}")
            continue
        if fragment and resolved.suffix.lower() == ".md":
            target_text = resolved.read_text(encoding="utf-8")
            target_slugs = slug_cache.get(resolved)
            if target_slugs is None:
                target_slugs = heading_slugs(target_text)
                slug_cache[resolved] = target_slugs
            if fragment not in target_slugs:
                failures.append(
                    f"{rel}:{number}: anchor {fragment!r} matches no heading "
                    f"in {file_part!r}"
                )


def external_urls(paths=None):
    """Return the sorted unique external URLs cited as links by Markdown files.

    Scope: inline link targets ``[text](url)`` and angle autolinks ``<url>``.
    URLs that appear only as inline code or bare prose (schema dialect
    strings, URL templates) are deliberately not treated as fetch targets.
    """
    urls = set()
    for path, error in markdown_files(paths):
        if error:
            continue
        text = path.read_text(encoding="utf-8")
        for _, line, in_code in strip_fences(text.splitlines()):
            if in_code:
                continue
            for match in LINK_RE.finditer(line):
                target = match.group(1).strip("<>")
                if re.match(r"^https?://", target):
                    urls.add(target)
            for match in ANGLE_RE.finditer(line):
                urls.add(match.group(1))
    return sorted(urls)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--list-external":
        for url in external_urls(argv[1:]):
            print(url)
        return 0
    paths = [Path(a).resolve() for a in argv]
    failures = []
    slug_cache = {}
    count = 0
    for path, error in markdown_files(paths):
        if error:
            failures.append(error)
            continue
        count += 1
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        # newline="" preserves CRLF/CR bytes so the hygiene check can see them.
        text = path.read_text(encoding="utf-8", newline="")
        failures.extend(check_hygiene(rel, text))
        check_file_final_newline(rel, text, failures)
        check_links(rel, path, text, slug_cache, failures)
    if failures:
        print(f"Documentation checks failed ({len(failures)} finding(s)):",
              file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            "Fix the findings above or, for a preserved historical artifact, "
            "record a reviewed exception in docs/CI.md and "
            ".markdownlint-cli2.jsonc.",
            file=sys.stderr,
        )
        return 1
    external = external_urls(paths or None)
    print(
        f"Documentation checks passed: {count} Markdown file(s); "
        f"{len(external)} external URL(s) noted for the scheduled lane "
        "(not fetched here)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
