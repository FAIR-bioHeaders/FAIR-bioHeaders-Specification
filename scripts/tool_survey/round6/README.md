# Issue #210 validation evidence — FHGFF3 UTF-8 header vs INSDC GFF3 draft ASCII rule

Status: **local validation-only evidence, run 2026-11-10**. Nothing was
uploaded, submitted, or published to any archive. All data are synthetic.
Home: `scripts/tool_survey/round6` in this repository. Inputs are generated
deterministically by `make_fixtures.py` (SHA-256 pinned in
`results/digest-manifest.txt`); rerun everything with `./run_round6.sh`.
Format authority: `FAIR-bioHeaders-Specification` `origin/main` @ `9db66060b0d835be56cd94c783ac28459935c32b`
(`docs/FORMAT.md` rules R1–R15, `docs/FHGFF3.md`; FHGFF3 contract `schemaVersion` "1.1", spec release v0.5.0).

---

## 1. Tool pins

| Tool | Pin | How pinned | Ran here? |
| --- | --- | --- | --- |
| fair-bioheaders (bioheaders CLI) | **0.9.0** (PyPI) | `pip install fair-bioheaders==0.9.0`; PyYAML 6.0.3, jsonschema 4.26.0; Python 3.15.0 | yes |
| ENA gff3tools | `https://github.com/enasequence/gff3tools` @ commit **`1bbe070fa1d8f846553833d9625a2cf3e2a268ea`** (main, committed 2026-11-06T16:23:38Z; project version 5.6.4 in `build.gradle`; **no named git releases exist** — `gh release list` empty) | checked out at exact commit before build | **no — not executable here** (see §5) |
| gff3 ("simple-gff3", PyPI, hotdogee/gff3-py) | **1.0.1** | pip | yes |
| gffutils | **0.14** | pip | yes |
| BioPython | 1.88 | pip | **GFF parser not testable** — `Bio.GFF` does not exist in 1.88 (verified absent from 1.79/1.83/1.84/1.85 sdists and the 1.88 wheel); fallback parsers above used instead |
| Java | OpenJDK 27.0.1.0.3 (Homebrew, `/opt/homebrew/opt/openjdk`); OpenJDK 17.0.21.0.3 installed to attempt the Gradle build | `java -version` | build attempts only |

## 2. Fixture byte table

All four fixtures share **byte-identical** directive lines, one ordinary ASCII
comment line (`# ordinary ASCII comment: this line must survive downstream tools`),
five feature lines, and a `##FASTA` section. Fixtures 2–4 additionally share an
identical 15-line `#~` header except line 4 (`#~annotation:`) and line 17
(`#~checksum:`). Genome link: asserted accession+SeqCol form with **synthetic
identifiers only** (`GCA_900000015.1` is the INSDC reserved test accession; the
`S`-only SeqCol digest is the spec examples' placeholder). All metadata parses,
validates, and round-trips as FHGFF3 1.1 (`schema: https://w3id.org/fair-bioheaders/fhgff3/v0.5.0`).

| # | File | Bytes | SHA-256 | FH checksum (recorded = verified) | Header annotation scalar | Serialized bytes of é |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `fixture1-plain.gff3` | 518 | `5e22dab04bdf52a91790a42bd7460a2df5fee7c0b5afb0db9ff9d89afea90b43` | n/a (no header) | — | — |
| 2 | `fixture2-ascii-header.gff3` | 1038 | `feb3a7c8c3e163585ba40fa5a5236323e6614ff87fc00b4ed815a11a794e7a2b` | `GAM2M53yPorYxX1vDK2JHQzBKMQ7hhvkSAlYHW6F4BI=` | `#~annotation: Synthetic annotation` (plain scalar) | none (pure ASCII) |
| 3 | `fixture3-raw-utf8.gff3` | 1036 | `de6c140d6f1b0893c8ad687c4fcdf3d8d6826e0089477412ef0c05b0881ee524` | `TsG/eToVe5vEdviwXhTTe6un7TFnMVl2xp02C14bh/g=` | `#~annotation: "Café annotation"` | `C3 A9` at file offsets **114–115** (line 4) |
| 4 | `fixture4-escaped.gff3` | 1040 | `ba2fb80cb4f7fbc68cd592a5d22b021e86dcfc4757355488eac0e9b6501c5fc1` | `zbxtFqkogcI6pLCtLH/+kRTkCYbdlFzz2j7RAOY0f5k=` | `#~annotation: "Caf\u00E9 annotation"` | none (pure ASCII; bytes `5C 75 30 30 45 39`) |

xxd excerpt, line 4 of fixtures 3 and 4 (the only byte difference between them):

```
fixture3: 00000060: 237e 616e 6e6f 7461 7469 6f6e 3a20 2243  #~annotation: "C
          00000070: 6166 c3a9 2061 6e6e 6f74 6174 696f 6e22  af.. annotation"
fixture4: 00000060: 237e 616e 6e6f 7461 7469 6f6e 3a20 2243  #~annotation: "C
          00000070: 6166 5c75 3030 4539 2061 6e6e 6f74 6174  af\u00E9 annotat
```

Byte scan result: **fixture 3 is the only fixture containing a byte ≥ 0x80**
(exactly two bytes, `0xC3 0xA9`); fixtures 1, 2, 4 are pure ASCII at file level.
(Full line-offset maps: `byte-analysis-precise.txt`; raw excerpts:
`byte-layout-excerpts.txt`.)

## 3. Checksum verification table (R1–R4)

The FH checksum was computed **independently** (own R1–R4 implementation in
`make_fixtures.py`: read as bytes; line ends at LF/CRLF/lone-CR with terminator;
exclude the one root `#~checksum:` line and its terminator; SHA-512/256 over
every other byte; padded standard base64) and by the pinned 0.9.0 library
(`bioheaders.cli.SequenceScan.checksum()`), then compared to the recorded header value:

| Fixture | independent (Python hashlib `sha512_256`) | bioheaders 0.9.0 | recorded in header | agree |
| --- | --- | --- | --- | --- |
| 2 | `GAM2M53yPorYxX1vDK2JHQzBKMQ7hhvkSAlYHW6F4BI=` | same | same | ✅ |
| 3 | `TsG/eToVe5vEdviwXhTTe6un7TFnMVl2xp02C14bh/g=` | same | same | ✅ |
| 4 | `zbxtFqkogcI6pLCtLH/+kRTkCYbdlFzz2j7RAOY0f5k=` | same | same | ✅ |

Canonicality (R4): the character before `=` is `I`, `g`, `k` respectively — all
in the canonical set `AEIMQUYcgkosw048`. ✅

`bioheaders verify` (commands and exit codes in `verify-log.txt`): fixtures 2–4
exit 0 "Checksum verified."; fixture 1 exits 1 ("No #~ FHR metadata header
found" — expected, it is deliberately headerless).

## 4. Decoded-value equivalence proof, fixtures 3 vs 4

Via the FH-aware reader path (`bioheaders.gff3.header_report` + the library's
own header loader, PyYAML 6.0.3):

| | fixture 3 (raw) | fixture 4 (escaped) |
| --- | --- | --- |
| `#~` lines serialized bytes | `… "Caf C3 A9 annotation"` | `… "Caf 5C 75 30 30 45 39 annotation"` |
| decoded `annotation` | `Café annotation` | `Café annotation` |
| codepoints | `U+0043 U+0061 U+0066 U+00E9 U+0020 …` | identical list |
| header_report yaml/checksum/schema/genome_link | ok/ok/ok/ok | ok/ok/ok/ok |

`equal_decoded_values: True`; `matches_expected_literal: True` (both equal the
Python literal `"Caf\u00e9 annotation"`). Full cross-check output:
`crosscheck-output.txt`.

Round-trip: re-serializing the decoded value ASCII-only with PyYAML
(`allow_unicode=False`) yields `"Caf\xE9 annotation"` (bytes
`…5C 78 45 39…`) which re-decodes to the identical string — proving the value
survives ASCII-only serialization in both `\xNN` and `\uNNNN` YAML
double-quoted escapes, while the **file bytes of fixture 4 themselves are pure
ASCII** (verified by full-file scan), so the escape does survive serialization
as literal bytes.

## 5. ENA gff3tools — **not executed** (reason documented); proxy evidence below

### 5.1 Why it could not run (arm64 macOS, 2026-11-10)

1. No named releases (`gh release list` → empty); pinned at `main` commit
   `1bbe070fa1d8f846553833d9625a2cf3e2a268ea`.
2. Repo ships **no prebuilt jar** (only `gradle/wrapper/gradle-wrapper.jar`).
3. `mvn`/`gradle` not installed; the project's own wrapper (Gradle 8.5) starts
   on JVM 27 but its Groovy script compiler fails: `BUG! … Unsupported class
   file major version 71` (exit 1; captured in
   `gff3tools-build-attempt-java27-groovy.log`).
4. With `openjdk@17` installed, the wrapper's build reaches dependency
   resolution and fails: `uk.ac.ebi.ena.taxonomy:webin-taxonomy-sdk:1.+` (via
   `uk.ac.ebi.ena.sequence:sequencetools:2.36.0`) resolves only from
   `https://gitlab.ebi.ac.uk/api/v4/groups/enasequence/-/packages/maven`, which
   returns **HTTP 401 Unauthorized** without a `gitlab_private_token`. The
   `uk.ac.ebi.ena.*` artifacts are **not on Maven Central** (404s recorded).
   Anonymous GitLab package download endpoints probed: metadata readable,
   artifact paths 404. Full failure log: `gff3tools-build-attempt.log` (exit 1).

**Conclusion: ENA gff3tools: not executed (no authenticated EBI package access
for its build dependencies).** Results below are (a) pinned-source static
analysis and (b) proxy runs with pinned parsers.

### 5.2 Pinned-source analysis (commit `1bbe070`, paths/lines exact)

* `GFF3FileReader.java` L45: `COMMENT = Pattern.compile("^#.*$")` — matches
  ordinary comments **and** `#~` FH lines. L142–144 (feature section):
  `else if (COMMENT.matcher(line).matches()) { // Skip comment  continue; }` —
  all comment lines are skipped during parsing.
* `readHeader()`: returns `new GFF3Header(version)` **only**; any non-comment,
  non-version header line is an `InvalidGFF3HeaderException`. `GFF3Header` is
  `record GFF3Header(String version)` whose `writeGFF3String` emits exactly
  `##gff-version <version>` (default constant `3.1.26`). So unrecognized `##`
  directives and all `#~` lines cannot survive a re-serialization.
* Write path (`GFF3File.writeGFF3String`): emits header version line, species,
  parsed annotations, and a merged `##FASTA` section — **no ordinary comments,
  no `#~` lines**. The `validation` command with an output file re-writes the
  GFF3 this way → header and comments dropped.
* `grep -rn '#~' src/` → **zero hits**: no FH-aware handling of the embedded
  header exists at this commit.
* Character handling: `AbstractCommand` uses `StandardCharsets.UTF_8` for stdin
  and file pipes; attribute percent-decoding uses UTF-8. There is no ASCII-only
  restriction on comment bytes in the reader, and a raw `#~annotation: "Café …"`
  byte sequence would never even be tokenized as a feature line (it is a
  comment) — **no source-observable reason for the raw UTF-8 header to be
  rejected by this tool's parser**.
* Adjacent signal: `FastaHeaderNormalisationFix` ("FASTA_HEADER_VALUE_NORMALISATION")
  **folds FASTA description-line values to ASCII7** (removes diacritics) in the
  pipeline that produces ENA submission headers — evidence that at least ENA's
  normalization path for GFF3-adjacent text actively destroys non-ASCII values.
  This applies to FASTA headers, not GFF3 comments (source scope is explicit).

### 5.3 Per-fixture results, **simple-gff3 `gff3==1.0.1`** (parse + inspect; kept distinct)

| Check | f1 plain | f2 ascii | f3 raw UTF-8 | f4 escaped |
| --- | --- | --- | --- | --- |
| parser accepts | ✅ | ✅ | ✅ | ✅ |
| feature lines parsed / expected | 5/5 | 5/5 | 5/5 | 5/5 |
| line errors reported | 0 | 0 | 0 | 0 |
| ordinary `#` comment kept in parse tree (raw) | ✅ | ✅ | ✅ | ✅ |
| `#~` lines kept in parse tree as `comment` | n/a | 16/16 incl. checksum line | 16/16 | 16/16 |
| non-ASCII in kept comment bytes | — | — | `U+00E9` **preserved raw** | — (escape preserved literally `Caf\u00E9`) |

### 5.4 Per-fixture results, **gffutils 0.14** (iterate = validation-equivalent; `create_db` + `GFFWriter` = conversion-equivalent)

| Check | f1 | f2 | f3 | f4 |
| --- | --- | --- | --- | --- |
| `DataIterator` accepts | ✅ | ✅ | ✅ | ✅ |
| features (ID sets) match input | ✅ | ✅ | ✅ | ✅ |
| export accepts, feature lines byte-identical | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 | ✅ 5/5 |
| ordinary `#` comment in export | ❌ dropped | ❌ dropped | ❌ dropped | ❌ dropped |
| `#~` lines in export | n/a | ❌ 0 survive | ❌ 0 survive | ❌ 0 survive |
| `##gff-version` / `##sequence-region` / `#!genome-build` in export | ❌ all dropped (only `#GFF3 file (created by gffutils (v0.14) …)` line) | ❌ | ❌ | ❌ |
| non-ASCII bytes in export | none | none | none (header dropped) | none |
| output `#~checksum` claim vs recomputation | n/a — **no checksum claim survives**, and recompute over export ≠ any copied claim; the export would be plain (unverifiable) GFF3 | same | same | same |

(`db.dialect`/`db.directives` retained only `gff-version 3` and
`sequence-region ctg1 1 48` internally; the `#!genome-build` line and every
`#~`/`# ` line never entered the model.)

### 5.5 Per-fixture results, **fair-bioheaders 0.9.0** (FH-aware; verify / strip / combine)

| Check | f1 | f2 | f3 | f4 |
| --- | --- | --- | --- | --- |
| `bioheaders verify` | exit 1, "No #~ FHR metadata header found" (by design) | exit 0 "Checksum verified." | exit 0 "Checksum verified." | exit 0 "Checksum verified." |
| `bioheaders strip` → payload | n/a | exit 0; output **byte-identical to the plain payload**; ordinary comment kept; 0 `#~` lines remain | same | same |
| `bioheaders combine` (f4 metadata + payload → new file) | — | — | — | exit 0; **verify passes**, but output is NOT byte-identical: canonical re-serialization rewrote the escaped scalar to the **raw** `Café` plain scalar (`C3 A9` present), so the ASCII-only serialization did not survive the tool round-trip; new correct checksum `SPKolM3cUKeyzoWEZGpfDQOuqg8ckMmFKtGDOvaTbRI=` |

### 5.6 Stale-checksum test (issue's final checklist item)

Constructed `outputs/fixture4-with-stale-fixture3-checksum.gff3`: fixture 4's
bytes are preserved except that fixture 3's checksum claim replaces fixture 4's
checksum line.

* stale claim from fixture 3: `TsG/eToVe5vEdviwXhTTe6un7TFnMVl2xp02C14bh/g=`
* recomputed over the unchanged fixture 4 bytes: `zbxtFqkogcI6pLCtLH/+kRTkCYbdlFzz2j7RAOY0f5k=`
* `bioheaders verify` → **exit 1, "FHR: Checksum verification failed"** — a
  stale checksum does not validate the fixture bytes. ✅ (consistent with
  FORMAT.md R3 and FHGFF3.md's "nothing repairs it" statement)

### 5.7 Follow-up same day: ENA's **bundled** engine (gff3tools 5.5.1 inside webin-cli-11.0.0.jar) on the four fixtures

The #191 harness (`../../insdc-191/`) located a runnable copy of ENA's GFF3
engine — `gff3tools-5.5.1.jar` ships inside the public Webin-CLI 11.0.0 jar —
and it was then run against these fixtures. Full transcript:
`results/gff3tools-bundled-5.5.1.txt`. Summary: report mode accepted all four
serializations with **zero encoding-related findings** and one identical
feature-level finding on every arm including the plain control
(`CDS_LENGTH`, the 63-bp synthetic CDS); rewrite mode emits nothing while any
error exists, so comment-level byte behavior was not observable here — the
#191 rewrite run on CDS_LENGTH-clean fixtures shows the engine drops `#~` and
ordinary comments when it does write. The standalone v5.6.4 pin of §5.1
remains unexecuted.

## 6. What remains unknown

1. **Standalone ENA gff3tools v5.6.4 runtime behavior** — partially closed the
   same day by §5.7 (bundled 5.5.1). Acceptance of all four encodings was
   observed on 5.5.1; the v5.6.4 source analysis of §5.2 is unchanged. A run
   with EBI-registry credentials is still needed for the current version, and
   rewrite-mode comment census on these fixtures is gated by the engine's own
   error policy.
2. **The INSDC draft's intent** — whether the v0.5.1-draft ASCII common rule
   (p. 6, lines 145–150) constrains (a) all file bytes, (b) only feature-section
   bytes, (c) ordinary comments, and/or (d) embedded `#~` metadata, and whether
   it speaks to serialized bytes or decoded values. No failure has been
   reproduced in any INSDC validator; none was observed here either.
3. **Webin-CLI end to end** — `-validate` refuses to run without an account
   (recorded in #191); table2asn and DDBJ results are in `../../insdc-191/`.
4. Whether future gff3tools versions add `#~` passthrough — as of the pinned
   commit the string `#~` appears nowhere in its source.

## 7. Artifact inventory

```
make_fixtures.py            # fixture builder + independent R1-R4 checksum implementation
                            #   (writes fixtures/: fixture[1-4]-*.gff3, payload.gff3, companion.fasta)
byte_analysis.py            # byte-level analysis         -> results/byte-analysis-precise.txt
                            #                             -> results/byte-layout-excerpts.txt
crosscheck.py               # checksum 3-way agreement + fixtures 3-vs-4 equivalence proof
                            #                             -> results/crosscheck-output.txt
fallback_parsers.py         # gff3 1.0.1 + gffutils 0.14  -> results/fallback-results.json
                            #                             -> results/fallback-stderr.txt, outputs/
fh_stack_runs.py            # verify/strip/combine/stale-checksum tests
                            #                             -> results/fh-stack-results.json, outputs/
run_round6.sh               # end-to-end reproduction from this directory
results/verify-log.txt, results/digest-manifest.txt       # commands + exit codes; SHA-256 pins
results/gff3tools-build-attempt.log,
results/gff3tools-build-attempt-java27-groovy.log         # pinned ENA gff3tools clone @1bbe070…
                            # unbuildable here (Groovy/classfile-71 on JVM 27; 401 on JVM 17 resolve)
question-for-upstream.md    # DRAFT question for the INSDC GFF3 draft feedback thread (unposted)
requirements-pinned.txt     # env pins
```
