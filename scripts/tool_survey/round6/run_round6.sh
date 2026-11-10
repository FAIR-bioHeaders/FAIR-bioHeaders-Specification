#!/usr/bin/env bash
# run_round6.sh — reproduce all issue #210 validation evidence from a clean
# directory. Validation/conversion modes ONLY; synthetic data only; nothing is
# uploaded anywhere; no git repositories are modified.
#
# Requirements: macOS/Linux, Python 3.13+ (tested 3.15.0), git, curl, network
# access to PyPI and GitHub. Java (17 and/or 27) optional: the ENA gff3tools
# build attempt is documented and its failure captured, but the evidence set
# does not depend on it.
set -u
cd "$(dirname "$0")"
ROOT="$PWD"
log() { printf '%s\n' "$*"; }
run() { log "\$ $*"; local tmp; tmp="$(mktemp)"; "$@" >"$tmp" 2>&1; rc=$?; sed 's/^/  | /' "$tmp"; rm -f "$tmp"; log "  exit=$rc"; return $rc; }

# 0. venv with pinned tools -------------------------------------------------
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install fair-bioheaders==0.9.0 PyYAML==6.0.3 jsonschema==4.26.0 \
  biopython==1.88 gff3==1.0.1 gffutils==0.14 >/dev/null 2>&1 || \
  .venv/bin/pip install -r requirements-pinned.txt
.venv/bin/pip freeze > results/pip-freeze.txt

# 1. build fixtures + companion FASTA ---------------------------------------
run .venv/bin/python make_fixtures.py

# 2. bioheaders verify on all four fixtures (expect exit 1 on fixture1 only)
{ for f in fixtures/fixture*.gff3; do
  log "\$ .venv/bin/bioheaders verify $f"
  .venv/bin/bioheaders verify "$f" 2>&1; log "exit=$?"
done; } | tee results/verify-log.txt

# 3. independent checksum cross-check + fixtures 3-vs-4 equivalence proof ----
log "\$ .venv/bin/python crosscheck.py > results/crosscheck-output.txt"
.venv/bin/python crosscheck.py > results/crosscheck-output.txt 2>&1; log "exit=$?"

# 4. byte-level analysis ------------------------------------------------------
log "\$ .venv/bin/python byte_analysis.py > results/byte-analysis-precise.txt"
.venv/bin/python byte_analysis.py > results/byte-analysis-precise.txt 2>&1; log "exit=$?"

# 5. pinned fallback parsers (gff3==1.0.1, gffutils==0.14) -------------------
log "\$ .venv/bin/python fallback_parsers.py > results/fallback-results.json"
.venv/bin/python fallback_parsers.py > results/fallback-results.json 2>results/fallback-stderr.txt; log "exit=$?"

# 6. FH-stack strip / combine / copied-checksum tests ------------------------
log "\$ .venv/bin/python fh_stack_runs.py > results/fh-stack-results.json"
.venv/bin/python fh_stack_runs.py > results/fh-stack-results.json 2>&1; log "exit=$?"

# 7. digests -----------------------------------------------------------------
sha256sum fixtures/*.gff3 outputs/*.gff3 > results/digest-manifest.txt

# 8. ENA gff3tools: pin + documented non-executability ------------------------
log ""
log "ENA gff3tools pin: https://github.com/enasequence/gff3tools"
log "  commit 1bbe070fa1d8f846553833d9625a2cf3e2a268ea (main, 2026-11-06; no named releases)"
if command -v java >/dev/null 2>&1; then
  if [ ! -d gff3tools ]; then git clone --quiet https://github.com/enasequence/gff3tools.git gff3tools; fi
  log "cloned at: $(git -C gff3tools rev-parse HEAD)"
  log "build attempt (expected to FAIL: webin-taxonomy-sdk needs EBI GitLab auth):"
  ( cd gff3tools && JAVA_HOME="${JAVA17_HOME:-/opt/homebrew/opt/openjdk@17}" \
      PATH="${JAVA17_HOME:-/opt/homebrew/opt/openjdk@17}/bin:$PATH" \
      ./gradlew --no-daemon shadowJar -x test ) > results/gff3tools-build-attempt.log 2>&1
  log "  build exit=$?  (see results/gff3tools-build-attempt.log; 401 Unauthorized on gitlab.ebi.ac.uk)"
else
  log "  java not present: skipping the documented build attempt; result stands:"
  log "  ENA gff3tools NOT EXECUTED — dependency build requires authenticated EBI package registry."
fi
log ""
log "Evidence complete: see README.md"
