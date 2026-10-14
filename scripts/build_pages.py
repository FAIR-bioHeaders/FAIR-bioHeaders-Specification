# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Build the GitHub Pages site that serves the JSON-LD files.

GitHub Pages serves ``.jsonld`` as ``application/ld+json`` and ``.ttl`` as
``text/turtle``, with ``Access-Control-Allow-Origin: *``, which raw GitHub does
not (specs/011-jsonld-mapping, maintainer decision 1). The site holds:

- ``terms/``: the vocabulary from the working tree, as ``index.html`` (rendered
  from ``docs/TERMS.md``), ``terms.ttl`` and ``terms.jsonld``. The w3id
  namespace ``https://w3id.org/fair-bioheaders/terms`` redirects here;
- ``fhr/main/jsonld/``: the working tree's JSON-LD files, as a preview;
- ``fhr/vX.Y.Z/jsonld/``: the same files from every release tag that has them.
  ``https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/...`` redirects here.

Usage: ``python scripts/build_pages.py SITE_DIR``. Release copies need the git
tags; a checkout without them builds only ``terms/`` and ``fhr/main/``. Only
the standard library is used, and nothing is fetched from the network.
"""

import argparse
import html
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
JSONLD_FILES = ("fhr.context.jsonld", "terms.ttl", "terms.jsonld")
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
BLOB = "https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/"
PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{links}<style>
body {{ font-family: system-ui, sans-serif; max-width: 50rem; margin: 2rem auto;
       padding: 0 1rem; line-height: 1.5; }}
code {{ background: #f3f3f3; padding: 0 .2em; overflow-wrap: anywhere; }}
h3 {{ margin-top: 2rem; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""
INLINE = re.compile(r"`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)")


def link_target(target, source):
    """Resolve a relative Markdown link in ``source`` (a repo path) to GitHub."""
    if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
        return target
    base = Path(source).parent
    parts = []
    for part in (base / target).as_posix().split("/"):
        if part == "..":
            parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return BLOB + "/".join(parts)


def inline(text, source):
    out, last = [], 0
    for match in INLINE.finditer(text):
        out.append(html.escape(text[last:match.start()]))
        if match.group(1) is not None:
            out.append(f"<code>{html.escape(match.group(1))}</code>")
        else:
            href = html.escape(link_target(match.group(3), source), quote=True)
            out.append(f'<a href="{href}">{html.escape(match.group(2))}</a>')
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def render_markdown(text, source):
    """Render the Markdown subset that ``docs/TERMS.md`` uses.

    That is ATX headings, paragraphs, ``-`` lists (with indented continuation
    lines), inline code, links and HTML comments. A level-3 heading's id is its
    exact text, so ``#seqcol_id`` works as on GitHub; anything else raises.
    """
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    blocks, current = [], []
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append(current)
            current = []
        elif line.startswith("#"):
            if current:
                blocks.append(current)
            blocks.append([line])
            current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    out = []
    for block in blocks:
        first = block[0]
        heading = re.fullmatch(r"(#{1,3}) (.+)", first)
        if heading:
            level, title = len(heading.group(1)), heading.group(2)
            anchor = title if level == 3 else slug(title)
            out.append(f'<h{level} id="{html.escape(anchor, quote=True)}">'
                       f"{inline(title, source)}</h{level}>")
        elif first.startswith("- "):
            items = []
            for line in block:
                if line.startswith("- "):
                    items.append(line[2:])
                elif line.startswith("  ") and items:
                    items[-1] += " " + line.strip()
                else:
                    raise ValueError(f"{source}: unsupported list line: {line!r}")
            out.append("<ul>\n" + "\n".join(f"<li>{inline(item, source)}</li>"
                                             for item in items) + "\n</ul>")
        elif first.startswith(("#", ">", "|", "```", "*", "1.")):
            raise ValueError(f"{source}: unsupported Markdown: {first!r}")
        else:
            out.append(f"<p>{inline(' '.join(line.strip() for line in block), source)}</p>")
    return "\n".join(out)


def terms_page():
    source = "docs/TERMS.md"
    body = render_markdown((ROOT / source).read_text(encoding="utf-8"), source)
    links = ('<link rel="alternate" type="text/turtle" href="terms.ttl">\n'
             '<link rel="alternate" type="application/ld+json" href="terms.jsonld">\n')
    return PAGE.format(title="FAIR-bioHeaders vocabulary", links=links, body=body)


def release_tags():
    try:
        result = subprocess.run(["git", "tag", "--list", "v*"], cwd=ROOT, check=True,
                                capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return []
    tags = [tag for tag in result.stdout.split() if TAG.fullmatch(tag)]
    return sorted(tags, key=lambda tag: tuple(int(n) for n in tag[1:].split(".")))


def tag_file(tag, name):
    result = subprocess.run(["git", "show", f"{tag}:jsonld/{name}"], cwd=ROOT,
                            capture_output=True)
    return result.stdout if result.returncode == 0 else None


def index_page(versions):
    items = "\n".join(
        f'<li><a href="fhr/{v}/jsonld/fhr.context.jsonld">{v}</a></li>' for v in versions)
    body = f"""<h1>FAIR-bioHeaders JSON-LD</h1>
<p>JSON-LD files of the <a href="https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification">FAIR-bioHeaders
specification</a>. Cite them through their persistent URLs:</p>
<ul>
<li>Vocabulary: <a href="terms/"><code>https://w3id.org/fair-bioheaders/terms</code></a>
(<a href="terms/terms.ttl">Turtle</a>, <a href="terms/terms.jsonld">JSON-LD</a>)</li>
<li>Context of a release:
<code>https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/fhr.context.jsonld</code></li>
</ul>
<p>Contexts by release (<code>main</code> is an unreleased preview and may change):</p>
<ul>
{items}
</ul>
<p>How records use them: <a href="{BLOB}docs/JSONLD.md">docs/JSONLD.md</a>.</p>"""
    return PAGE.format(title="FAIR-bioHeaders JSON-LD", links="", body=body)


def build(site):
    if site.exists():
        shutil.rmtree(site)
    (site / "terms").mkdir(parents=True)
    (site / ".nojekyll").write_bytes(b"")
    (site / "terms" / "index.html").write_text(terms_page(), encoding="utf-8")
    for name in ("terms.ttl", "terms.jsonld"):
        shutil.copyfile(ROOT / "jsonld" / name, site / "terms" / name)
    versions = []
    for tag in reversed(release_tags()):
        files = {name: tag_file(tag, name) for name in JSONLD_FILES}
        if files["fhr.context.jsonld"] is None:
            continue
        target = site / "fhr" / tag / "jsonld"
        target.mkdir(parents=True)
        for name, data in files.items():
            if data is not None:
                (target / name).write_bytes(data)
        versions.append(tag)
    target = site / "fhr" / "main" / "jsonld"
    target.mkdir(parents=True)
    for name in JSONLD_FILES:
        shutil.copyfile(ROOT / "jsonld" / name, target / name)
    versions.append("main")
    (site / "index.html").write_text(index_page(versions), encoding="utf-8")
    return versions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", type=Path, help="output directory (replaced if it exists)")
    args = parser.parse_args(argv)
    try:
        versions = build(args.site)
    except ValueError as error:
        print(f"build_pages: {error}", file=sys.stderr)
        return 1
    print(f"Built {args.site}: terms/ and fhr/{{{','.join(versions)}}}/jsonld/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
