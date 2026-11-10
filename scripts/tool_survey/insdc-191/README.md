# `tool_survey/insdc-191` — INSDC submission-validator harness

Validation-only evidence for
[FAIR-bioHeaders-Specification#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191):
how NCBI, ENA and DDBJ submission tools handle FAIR-bioHeaders `;~` / `#~` header
blocks. Synthetic data only. Nothing is submitted; no account is created and no
credential is used.

This directory is self-contained and does not import the existing
`make_inputs.py` / `run_survey.py` machinery (those target the local tool survey
on Linux/conda; this one targets three submission vendors on one macOS host).

## Layout

*The recorded run wrote transcripts under an ephemeral working directory; the
absolute prefix in committed logs is masked as `$WORKAREA`. File contents, exit
codes and byte comparisons are otherwise verbatim, and `run-evidence.sh`
reproduces every arm from a clean checkout (regenerated outputs land under the
new run's own paths).*

| File | Role |
| --- | --- |
| `run-evidence.sh` | The harness. Downloads tools, builds fixtures, runs every arm, records exit codes. |
| `fixtures/gen_sequences.py` | Seeded PRNG ⇒ the plain (control) FASTA and GFF3. Deterministic. |
| `fixtures/gen_r11_fixture.py` | Valid FHR file with a raw `>` in a value (the FORMAT.md R11 hazard); recomputes the checksum. |
| `fixtures/gen_controls.py` | Stale-checksum controls: exactly one character of the checksum value changed, so only R3/R4 fail, not R5. |
| `fixtures/template.sbt` | NCBI submission template, sanitised from NCBI's shipped sample (its real names, e-mail and BioProject removed). |
| `fixtures/ddbj_sample.ann` | DDBJ annotation companion (their `.ann` format), held fixed across DDBJ arms so the FASTA is the only variable. |
| `results-191.md` | Results tables, environment limits, and the "what this does and does not prove" section. |
| `PROVENANCE.txt` | sha256 of every downloaded binary and built fixture. |
| `evidence.log`, `jobs.tsv` | Full transcript and per-arm classification table of the recorded run (2026-11-10). |
| `runs/` | Inputs, outputs and exit codes of every recorded arm; byte-pinned via `PROVENANCE.txt`. |

`run-evidence.sh` writes the headered fixtures (`fhr_header.fsa`,
`fhgff3_header.gff`, `fhr_meta.json`, `fhgff3_meta.json`) and everything under
`runs/`, `venv/`, `venv-ddbj/`, `bin/`. Checksums are recomputed by
`bioheaders combine`, so the fixture bytes are reproducible even though the
metadata JSON is regenerated in place.

## Running

```bash
mkdir survey && cd survey
cp /path/to/run-evidence.sh . && mkdir fixtures
cp /path/to/fixtures/{gen_sequences,gen_r11_fixture,gen_controls}.py \
   /path/to/fixtures/template.sbt /path/to/fixtures/ddbj_sample.ann fixtures/
./run-evidence.sh                       # add TOOLDIR=/path/to/cache to reuse downloads
```

Requirements: macOS on Apple silicon (the NCBI builds used are `arm64`),
Python 3.x with `venv`, `curl`, `gzip`, `unzip`, `shasum`, and a JRE for
Webin-CLI (`java`; on this host `/opt/homebrew/opt/openjdk/bin`). The tool pins
and expected versions are at the top of the script; digests are verified on
download where NCBI does not publish one.

Outputs: `evidence.log` (full transcript), `jobs.tsv` (tool, case, exit code),
`runs/<tool>/<case>/` (every input and output of every arm).

## What the arms are

Each tool gets a **control** arm (no header) and a **test** arm (same bytes plus
an FH block), and the outputs are compared with `cmp`. Two extra arms per tool
are the reason the positive results mean anything:

- `*-corrupt` — the same file with one character of the checksum changed. If the
  tool's output is byte-identical to the *valid* headered arm, the tool never
  looked at the header.
- `*-r11` — a valid FHR file whose header contains a raw `>`, the character
  FORMAT.md R11 tells writers to escape.
- DDBJ additionally gets `c1-semicolon` (one ordinary `;` comment line) and
  `c3-semicolon-block` (the whole header re-marked as plain `;` comments), which
  show its failure is generic leading-comment intolerance, not a reaction to `~`.

## Do not extend this to submission

`-submit` is never passed to any tool. Webin-CLI needs a Webin account for
`-validate` and stops at `ERROR: Missing required option: '-userName=USER'`
(exit 2); that is recorded, not worked around. If someone with a test account
continues, keep `-validate` and stay off `-submit`.
