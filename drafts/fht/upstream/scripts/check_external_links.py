"""Scheduled/manual external link check for FHT-Specification (issue #14).

Fetches every http(s) URL cited by the repository's Markdown files and fails
on any URL that does not answer successfully. This lane runs ONLY on a
schedule and via manual dispatch (``.github/workflows/external-links.yml``);
it is deliberately not a pull-request check, because a transient remote
failure must not gate unrelated documentation or schema work. The PR signal
for links is the owned local-link/whitespace/conflict check
(``scripts/check_docs.py``).

Narrow exclusions live in ``scripts/external-links-exclusions.json``; every
entry needs a recorded justification (see docs/CI.md). Each URL is retried
once before it counts as a failure.

Local usage (network required; standard library only):

    python scripts/check_external_links.py            # check all cited URLs
    python scripts/check_external_links.py --list     # show the target list
    python scripts/check_external_links.py --url URL  # check one URL

Exit status is 0 when every non-excluded URL succeeds and 1 otherwise.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import check_docs  # same directory; used for Markdown/link discovery

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(__file__).resolve().parent / "external-links-exclusions.json"
USER_AGENT = "FAIR-bioHeaders-FHT-linkcheck/1.0 (+https://github.com/FAIR-bioHeaders/FHT-Specification)"
TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 5


def load_exclusions():
    record = json.loads(CONFIG.read_text(encoding="utf-8"))
    return record.get("exclusions", [])


def excluded(url, exclusions):
    for entry in exclusions:
        if entry.get("url") == url:
            return entry
        prefix = entry.get("prefix")
        if prefix and url.startswith(prefix):
            return entry
    return None


def fetch_once(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, None
    except urllib.error.HTTPError as error:
        return error.code, None
    except Exception as error:  # URLError, timeouts, TLS, DNS
        return None, f"{type(error).__name__}: {error}"


def check(url):
    """Return True when the URL answers 2xx/3xx, with one retry."""
    status, transport_error = fetch_once(url)
    if status is not None and status < 400:
        print(f"  {status} {url}")
        return True
    reason = f"HTTP {status}" if status is not None else transport_error
    time.sleep(RETRY_DELAY_SECONDS)
    status2, transport_error2 = fetch_once(url)
    if status2 is not None and status2 < 400:
        print(f"  {status2} {url} (after retry; first attempt: {reason})")
        return True
    reason2 = f"HTTP {status2}" if status2 is not None else transport_error2
    print(f"  FAIL {url} ({reason}; retry: {reason2})")
    return False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--list":
        for url in check_docs.external_urls():
            print(url)
        return 0
    if argv and argv[0] == "--url":
        if len(argv) != 2:
            print("usage: --url URL", file=sys.stderr)
            return 2
        return 0 if check(argv[1]) else 1
    if argv:
        print(__doc__, file=sys.stderr)
        return 2

    exclusions = load_exclusions()
    urls = check_docs.external_urls()
    failures = []
    skipped = 0
    print(f"Checking {len(urls)} external URL(s) "
          f"({len(exclusions)} exclusion record(s)):")
    for url in urls:
        entry = excluded(url, exclusions)
        if entry:
            skipped += 1
            print(f"  SKIP {url} "
                  f"(excluded since {entry.get('added', 'unknown')}: "
                  f"{entry.get('reason', 'no recorded reason')})")
            continue
        if not check(url):
            failures.append(url)
    if failures:
        print(
            f"\nExternal link check failed for {len(failures)} URL(s):",
            file=sys.stderr,
        )
        for url in failures:
            print(f"  {url}", file=sys.stderr)
        print(
            "Repair the citation or, if the endpoint is durably bot-hostile, "
            "add a narrow dated exclusion with evidence in "
            "scripts/external-links-exclusions.json (reviewed maintainer "
            "action; see docs/CI.md).",
            file=sys.stderr,
        )
        return 1
    print(
        f"\nExternal link check passed: {len(urls) - skipped} fetched, "
        f"{skipped} excluded."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
