# Issue #191 — FAIR-bioHeaders headers in INSDC submission validators

Validation-only evidence for
[#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191)
("Test FAIR-bioHeaders headers with INSDC submission validators").
Run date: **2026-11-10**. Nothing was submitted to NCBI, ENA or DDBJ; no account
was created and no credential was used. All data are synthetic.

Recorded run: 2026-11-10 in this directory; rerun with `./run-evidence.sh` (regenerates `runs/`, `evidence.log`, `jobs.tsv`).
Harness: [`run-evidence.sh`](run-evidence.sh) (reproduces every row from a clean
directory; self-tested 2026-11-10 — see [Reproduction](#reproduction)).
Full transcripts: [`evidence-harness.log`](evidence-harness.log) and
[`jobs-harness.tsv`](jobs-harness.tsv) (the clean re-run, 45 arms), plus the
interactive `runs/` trees; layout explained in
[`EVIDENCE-README.txt`](EVIDENCE-README.txt).
Digests of everything downloaded and built: [`PROVENANCE.txt`](PROVENANCE.txt).

## Headline

| Tool | Verdict | What happens to the FH header |
| --- | --- | --- |
| NCBI `table2asn` 1.29.324 | **a — tolerated, silently dropped** | `;~` and `#~` lines vanish. Every output (`.sqn`, `.gbf`, `.dr`, and `.val`/`.stats` where the mode writes them) is byte-identical to the header-free control. |
| NCBI `asnvalidate` 3.29.324 | **n/a for headers** | Reads only ASN.1. It rejects a plain `.fsa` too, so it never sees FASTA/GFF3 comments at all. |
| ENA Webin-CLI 11.0.0 (`-validate`) | **unknown — not runnable offline** | Refuses to start without a Webin account (`exit 2`). |
| ENA `gff3tools` 5.5.1 (the GFF3 engine bundled inside that jar, run directly) | **a — tolerated, dropped on rewrite** | Report-only: passes both arms. Rewrite: the `#~` block is dropped, like every other comment line. |
| DDBJ `ddbj-validator` 1.0.94 | **c — rejected** | Hard errors `SEQ0080` + `SEQ0090`; its auto-fix then rewrites the header block into a bogus sequence record. |

**One correction to the issue's premise:** DDBJ *does* now ship a public offline
validator ([ddbj/ddbj-validator](https://github.com/ddbj/ddbj-validator),
announced 2026-10-23), so "not tested" is no longer the right cell — and it is
the one tool here that **fails** on an FHR header.

## Provenance

| Tool | Version string (as printed) | URL | sha256 |
| --- | --- | --- | --- |
| table2asn (macOS) | `mac: 1.29.324`, build `Sep 16 2025 14:55:21`, `GitBranch: stable/29.0`, `Revision: 205bed9d5a`, `APPLE_CLANG_1600-ReleaseMT64--arm64-Darwin23.6.0` | `https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/mac.table2asn.gz` | `94f276a1283be339f10272f71963bce22053a8463987bac3c1ed55a7078583c1` (decompressed) |
| asnvalidate (macOS) | `mac: 3.29.324`, same build/revision | `https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/asnvalidate/mac.asnvalidate.gz` | `f669d61ba2c0fcda33537144f2a1d39f9426dce80f5d75a390a8cfae8ff3e6cf` |
| table2asn sample template | — | `.../table2asn/DOCUMENTATION/SubmissionTemplate.sbt` | `a9182167d04fc58bc69f51ffad1bde10481b911bde4cc479a92a27c646628b24` |
| NCBI toolkit version list | `table2asn: 1.29.324`, `asnvalidate: 3.29.324` | `.../table2asn/DOCUMENTATION/VERSIONS` | `80d6c271d19498cdfd0bf50318a4a9fb351bc280e5db6df1f11eeea2ccdf4806` |
| table2asn README | — | `.../table2asn/DOCUMENTATION/table2asn_readme.txt` | `5592a0936cb3bd7f98095875a01b7295a9b95b01c824fd862d8797c9d5add0dc` |
| ENA Webin-CLI | `Implementation-Version: 11.0.0`, built `Fri Oct 30 16:27:23 GMT 2026` | `https://github.com/enasequence/webin-cli/releases/download/11.0.0/webin-cli-11.0.0.jar` | `2202cd76cda299c05ee831811c210c574f2fe7f53b28a2824ff2c3532aea48b8` (sha512 `4516d8ac…f3aa`) |
| gff3tools (inside that jar) | 5.5.1 | `BOOT-INF/lib/gff3tools-5.5.1.jar` | `722b23c530447623597b58f5d3a929bcffe953062480ff3d2fddd6fc864c66cc` |
| DDBJ ddbj-validator | report line `Version: 1.0.94`; pip metadata `ddbj-validator 1.0.94` | `git+https://github.com/ddbj/ddbj-validator.git@f3d359969da65d2f755b6a9357eba2f3bc093484` (commit dated 2026-11-10T03:52:58Z) | installed in a throwaway venv |
| fair-bioheaders (fixtures) | `0.9.0` | PyPI `fair_bioheaders-0.9.0-py3-none-any.whl` | `296d9b01eb9949a19a845a77fbbe0bd53ad17405c5a87913204c48b246cd0d28` |

**Two URLs given to me for this survey are stale.**
`https://ftp.ncbi.nlm.nih.gov/toolkit/annotation/current/software/` returns
**HTTP 404** (the whole `/toolkit/` tree is gone from the HTTPS mirror); the
current location is `https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/<prog>/`.
`https://github.com/ena-webin-cli/webin-cli/releases` is **404**; the repository
is [`enasequence/webin-cli`](https://github.com/enasequence/webin-cli).
Neither URL appears in `docs/insdc-coverage.md` today, so nothing there needs a
link fix — but if the PR records where the tools come from, use the corrected
paths, and note that DDBJ now publishes an offline validator
([`ddbj/ddbj-validator`](https://github.com/ddbj/ddbj-validator)), which the
coverage table does not mention.

Platform note: the macOS builds are **native arm64** (`Mach-O 64-bit executable
arm64`), so no Rosetta was needed. Rosetta is in fact **not installed** on this
machine (`arch -x86_64 /usr/bin/true` → `Bad CPU type in executable`, `oahd` not
running), which would have blocked the run had the macOS build been x86-64 only.
The `linux64.*` builds on the same FTP directory are **x86-64 ELF**, not arm64 —
they are the wrong architecture for an arm64 Linux container, so no container
fallback was attempted.

## Fixtures

Two contigs, 240 bp and 210 bp, generated from a seeded PRNG
([fixtures/gen_sequences.py](fixtures/gen_sequences.py)); one gene/mRNA/exon/CDS
at `ctg1:21..170` on the plus strand, start `ATG`, stop `TAA`, no internal stop,
phase 0. Fictional organism *Exampleus syntheticus*. The taxon URI uses
`https://identifiers.org/taxonomy:999999999`; NCBI Taxonomy `esearch` for
`999999999[txid]` returns `"count":"0"`, so the placeholder is verifiably
unassigned rather than someone else's species. No ORCID is present anywhere:
the FHR schema requires author URIs to match the ORCID pattern, and a fake one
was not written (the field is optional, so it is omitted).
`schemaVersion` is `"2.1"` (FHR) and `"1.1"` (FHGFF3), schema URLs the v0.5.0
w3id forms — matching shared spec `origin/main` at commit `9db66060b0d8`.

| File | What it is | `bioheaders verify` |
| --- | --- | --- |
| `fhr_noheader.fsa` | plain FASTA, no header (control) | not applicable |
| `fhr_header.fsa` | same FASTA + FHR 2.1 `;~` block | **exit 0** `Checksum verified.` |
| `gff3_noheader.gff` | plain GFF3, one gene/mRNA/exon/CDS, one `# Ordinary comment` line (control) | not applicable |
| `fhgff3_header.gff` | same GFF3 + FHGFF3 1.1 `#~` block, `derivedFrom` → `annotates` → the FHR checksum above | **exit 0** `Checksum verified.` |
| `fhr_corrupt.fsa` | `fhr_header.fsa` with **one character** of the checksum value changed (still canonical base64, so only R3/R4 fail) | **exit 1** `Checksum verification failed` |
| `fhgff3_corrupt.gff` | same single-character stale-checksum control for FHGFF3 | **exit 1** `Checksum verification failed` |
| `fhr_r11_rawgt.fsa` | valid FHR file whose `documentation` value contains a **raw `>`** (the R11 hazard); checksum recomputed, so the file is valid with one warning | **exit 0** + `warning: … contains a raw '>'` (R11) |

`verify-links fhgff3_header.gff fhr_header.fsa` → exit 0,
`derivedFrom[0] FHR annotates: matched (fhr_header.fsa)`.

The stale-checksum controls are the important ones: they separate "the tool
ignores the header" from "the tool checks the header and finds it acceptable".

## Results

Command shapes (full text of every invocation in `evidence-harness.log`):

- **FASTA**: `mac.table2asn -indir in -o out -t template.sbt -V vb -M n -Z -j "[organism=Exampleus syntheticus] [isolate=SynthEus1]"`
- **GFF3**: same, with `sample.gff` sitting next to `sample.fsa` (table2asn pairs by basename; it logs `Recognized annotation format: GFF3`)
- Source qualifiers were passed identically in every arm via `-j`, so the only
  difference between paired arms is the presence of the FH block.
- No `-submit`-equivalent exists in table2asn: it writes files locally and never
  uploads. `-V v` is the validation report; `-Z` adds the discrepancy report.

### A. NCBI table2asn 1.29.324

| # | Fixture pair | Exit | Outcome | Evidence |
| --- | --- | --- | --- | --- |
| A1 | `fhr_noheader.fsa` vs `fhr_header.fsa` | 0 / 0 | **silently dropped** | `cmp`: **.sqn byte-identical**, and `.gbf` and `.dr` byte-identical; 0 header-token lines (`w3id\|schemaVersion\|x-fixture\|checksum`) anywhere in the outputs; records `lcl\|ctg1` 240 bp and `lcl\|ctg2` 210 bp in both. In the batch-mode variant (`-a s -V v`, no template) — the only form that writes `.val`/`.stats` for a FASTA-only run — those are byte-identical too |
| A2 | `gff3_noheader.gff` vs `fhgff3_header.gff` (FASTA fixed, unheadered) | 0 / 0 | **silently dropped, GFF3 parsed fully** | both arms log `Recognized annotation format: GFF3`; `.sqn`, `.gbf`, `.val`, `.dr` byte-identical; features present in both (`locus-tag "synGene1"`, `type mRNA`, CDS product); 0 header tokens in outputs |
| A3 | headered FASTA + headered GFF3 together, vs both plain | 0 | **silently dropped** | `.sqn`, `.gbf`, `.val`, `.dr`, `.stats` byte-identical to the plain control |
| A5 | `fhr_corrupt.fsa` (stale checksum) | 0 | **not checked at all** | `.sqn` byte-identical to the *valid* headered arm — table2asn cannot tell a valid FHR header from a broken one |
| A6 | `fhgff3_corrupt.gff` (stale checksum, FASTA unheadered) | 0 | **not checked at all** | `.sqn`, `.gbf`, `.val`, `.dr`, `.stats` byte-identical to the plain control |
| A7 | `fhr_r11_rawgt.fsa` (raw `>` in a header value) | 0 | **no bogus record** | exactly 2 records (`ctg1` 240 bp, `ctg2` 210 bp), `.sqn` byte-identical to the A1 headered arm |

A2 and A3 together cover the four FASTA × GFF3 header combinations: A1/A3 vary
the FASTA header, A2 varies the GFF3 header with the FASTA held plain, and A3
has both. No configuration produced an error or a difference.

Residual diagnostics, identical in the headered and header-free arms, and all
caused by the synthetic data rather than by the header:

```
Warning: valid [SEQ_DESCR.NoTaxonID] BioSource is missing taxon ID … Exampleus syntheticus
Warning: valid [SEQ_FEAT.GenCodeMismatch] Genetic code conflict between CDS (code 1) and BioSource (code 0) …
Error: valid [SEQ_DESCR.NoPubFound] No publications anywhere on this entire record. …
Info: valid [GENERIC.MissingPubRequirement] No submission citation anywhere on this entire record. …
```

and from the discrepancy report, `FATAL: BAD_LOCUS_TAG_FORMAT: 1 locus tag is
incorrectly formatted.` (an unregistered synthetic prefix). No message ever
mentions the header lines, and table2asn never warns that it ignored something.
table2asn also prints `This copy of mac is more than 1 year old` on every run —
that is a build-age nag (built 2025-09-16), not a data problem, and it does not
change the exit code.

### B. NCBI asnvalidate 3.29.324

Runnable standalone from the same FTP directory (`mac.asnvalidate.gz`), so it
was not skipped. It validates the **`.sqn`** that table2asn produced:

```
$ mac.asnvalidate -i gff-header.sqn -o gff-header.sqn.val      → exit 0, empty .val (no findings)
$ mac.asnvalidate -i gff-noheader.sqn -o gff-noheader.sqn.val  → exit 0, empty .val
```

Both arms are identical, which is expected and tells us nothing about headers:
asnvalidate consumes ASN.1, not FASTA or GFF3. Fed a FASTA directly it fails on
the **control** too, so the header is not the cause:

```
$ mac.asnvalidate -i plain.fsa  → exit 1  FAILURE: Unable to process invalid ASN.1 file plain.fsa
$ mac.asnvalidate -i fhr.fsa    → exit 1  Error: (CObjReaderParseException::eFormat) File format not supported
```

**This qualifies the issue's own premise and row S11 of the coverage table.**
The issue records "INSDC Sequence v1.0 lists `asnvalidate`/`table2asn` for FASTA",
and row **S11** defers sequence-body validation to "INSDC tools". For these
purposes only **table2asn reads FASTA and GFF3**; `asnvalidate` is an ASN.1
validator and is not on the header path at all. (`docs/insdc-coverage.md` does
not name `asnvalidate`, so no row text needs deleting — but S11 and AN.a can now
cite measured behaviour instead of deferring to unnamed tools.)

(`asnvalidate -V v` is rejected — `Error: Unknown argument: "V"`, exit 1 — the
flag belongs to table2asn. Stringency selection is `-v`/`-Q`/`-P`.)

### C. ENA Webin-CLI 11.0.0 — could not be run

Java 27 (`openjdk 27.0.1.0.3`) starts the jar fine; `-help` and `-fields` run
offline with **exit 0**. The validate path does not:

| Command (in a populated submission directory) | Exit | Exact message |
| --- | --- | --- |
| `java -jar webin-cli-11.0.0.jar -validate -context genome -manifest manifest.tsv` | **2** | `ERROR: Missing required option: '-userName=USER'` |
| `… -validateFiles -context annotation -manifest manifest.tsv` | **2** | `ERROR: Missing required option: '-userName=USER'` |
| `… -validateFiles … -userName=nonexistent-probe-191` | **2** | `ERROR: Password must be provided using one of the following options: -password, -passwordEnv, -passwordFile` |

The refusal happens at argument parsing, before any file is opened, and there is
no offline or unauthenticated mode. `-test` selects ENA's *test service* but
still requires an account. **No account was created and no credential was
attempted**; the run stops here. ENA's treatment of `;~` and `#~` therefore
stays **unknown**.

Two useful observations from the parts that *were* reachable:

1. **The formats differ from NCBI's, as the issue predicted.** `-fields
   -context genome` takes a `FASTA` file (as `.fasta.gz`); `-context sequence`
   takes **only `TAB` or `FLATFILE`**, no FASTA; `-context annotation` (new in
   11.0.0) takes a **`GFF3` file as `.gff3.gz`** with
   `ANALYSIS_TYPE DECOUPLED_ANNOTATION` and a `PRIMARY_ID` that must be a real
   versioned GCA/sequence accession. So FH* files are never validated in place:
   they are rewrapped in a manifest and compressed, and the header question is
   about how ENA's reader handles the bytes inside.
2. **The GFF3 engine is inside the jar and can be run without an account.**
   `webin-cli-11.0.0.jar` bundles `gff3tools-5.5.1.jar`, and
   `uk.ac.ebi.ena.webin.cli.context.annotation.Gff3Validator` delegates to
   `uk.ac.ebi.embl.gff3tools.validation.ValidationEngineBuilder` (confirmed by
   `javap` on the bundled class). Running that engine directly on the fixtures
   is *not* the same as running `webin-cli -validate` — it exercises ENA's own
   parser and rule set, but not the manifest checks, not the server-side rules,
   and not the upload path. Reported separately for exactly that reason.

| Engine run | Exit | Outcome |
| --- | --- | --- |
| `Main validation gff3_noheader.gff` (report-only, no output argument) | 0 | **silent**: nothing on stdout but log lines, no findings reported |
| `Main validation fhgff3_header.gff` (report-only) | 0 | same — the `#~` block raises no finding; accepted as ordinary GFF3 comments |
| both arms with `--sequence ctg1:ctg1.seq --sequence ctg2:ctg2.seq -` (rewrite to stdout) | 0 / 0 | `The file has passed all validations!` in both; **outputs byte-identical to each other**, and the `#~` block is absent from both |
| `fhgff3_corrupt.gff` (stale checksum) | 0 | `The file has passed all validations!`, output byte-identical to the valid arm — no header checking |

The rewrite is not FH-specific and it is not harmless: `gff3tools` **rewrites**
rather than copies. Given `-` it emitted only

```
##gff-version 3
##sequence-region ctg1 1 240
ctg1	synthetic	mRNA	21..170	… ID=rna1;locus_tag=SYNGENE1;
ctg1	synthetic	exon	…
ctg1	synthetic	CDS	…
##FASTA
>ctg1|cds1
MYDSDWLEESYRYGVLNATLNRLPRPNVTGMSQNSEDSPWKQHPSMNPY
```

— dropping the `#~` block, the `#!genome-build` directive **and** the ordinary
comment line, upper-casing `locus_tag`, and dropping the standalone `gene`
feature. Any tool that rewrites bytes breaks an FH checksum
([docs/FHGFF3.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FHGFF3.md)
says so for `gt gff3 -sort -tidy`); this adds `gff3tools`/Webin-CLI to that list
for anyone who pipes a submission through its fixing mode. Report-only mode
writes nothing, so the default `-validate` path would not corrupt bytes — but
that path needs an account, which is the wall recorded above.

### C2. DDBJ ddbj-validator 1.0.94 — the failure

DDBJ's public offline validator (announced 2026-10-23) was found during this
survey and tested in its fully local mode, `-l`, which skips DB and API queries
— no account, no submission. It needs a DDBJ `.ann` alongside the FASTA, so a
synthetic `.ann` (fixtures/ddbj_sample.ann) was written from their own test
corpus and held fixed across arms; the FASTA is the only variable.

| # | FASTA | Exit | Report findings beyond the control |
| --- | --- | --- | --- |
| D1 | `fhr_noheader.fsa` (control) | 0 | **no ERROR**. Warnings only: `ANN0410/0450/0470 Missing BioProject/BioSample/SRA accession` (inherent to synthetic data), auto-cleanup `SEQ0100` (adds `//`) |
| D2 | `fhr_header.fsa` | 0 | **`SEQ0080:ERR:sequence: 1 file: Missing FASTA definition line (>Entry name).`** and **`SEQ0090:ERR:sequence: 1 sequence: Invalid nucleotide code ';' at 1 position.`** + `SEQ0085:WAR … Invalid characters … were automatically removed from the sequence.` |
| D3 | `fhr_corrupt.fsa` | 0 | same two errors as D2 — it never gets far enough to care about the checksum |
| D4 | `fhr_r11_rawgt.fsa` | 0 | same two errors |
| D5 | control FASTA + **one** ordinary `;` comment line | 0 | `SEQ0080` error only, no `SEQ0090` |
| D6 | control FASTA + the header block re-marked as ordinary `;` comments (18 lines, no `~`) | 0 | **both `SEQ0080` and `SEQ0090`** — identical to D2 |

D5/D6 are the controls that matter: a plain `;` comment block of the same size
produces the same failure, so the break is **generic leading-`;`-comment
intolerance in a DDBJ context, not a reaction to the `~` marker**. The practical
result is unchanged: an FHR FASTA is rejected by DDBJ's own validator, and by
`-l` at that, without any network or account.

Worse than rejection is the auto-fix. `ddbj-validator` writes
`out/fixed/sample.fasta` by default, and for the FHR arm that file begins

```
>;~schema: https://w3id.org/fair-bioheaders/fhr/v0.5.0
;~schemaversion:'2.1'
;~genome:exampleussyntheticussyntheticexamplegenome(syntheus1;notarealorganism)
…
;~checksum:mpzmu067e+ufurtwrzdqui20ndyoppihwzxsgskoeeg=
//
>ctg1 Exampleus syntheticus synthetic contig one
```

It has invented a **sequence record named `;~schema:`** whose "sequence" is the
lower-cased, punctuation-stripped metadata, and terminated it with `//`. A
submitter who trusts the auto-fixed output would ship exactly that garbage.
The genuine sequence still survives in the file (`ctg1`/`ctg2` records intact),
so the damage is additive, not destructive — but it is silent corruption of the
survey's class **b** sitting on top of a class **c** rejection.

`ddbj-validator` consumes no GFF3 (its annotation format is `.ann`), so FHGFF3
has no DDBJ reader to test.

### Summary matrix

Class letters are the ones defined in
[docs/TOOL_COMPATIBILITY.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/TOOL_COMPATIBILITY.md)
(**a** works, output identical; **b** works but silently corrupts; **c** fails;
**n/a** the control fails too).

| Fixture | table2asn 1.29.324 | asnvalidate 3.29.324 | Webin-CLI 11.0.0 | gff3tools 5.5.1 (bundled) | ddbj-validator 1.0.94 |
| --- | --- | --- | --- | --- | --- |
| FHR FASTA, valid | **a** (dropped) | n/a (ASN.1 only) | **unknown** (needs account) | not exercised (FASTA path failed on the control too) | **c** → **b** in `fixed/` |
| FHGFF3 GFF3, valid | **a** (dropped) | n/a | **unknown** (needs account) | **a** report-only; **b** rewrite (drops all comments) | n/a (no GFF3 input) |
| FHR FASTA, stale checksum | **a** (indistinguishable from valid) | n/a | unknown | — | **c** (same as valid) |
| FHGFF3 GFF3, stale checksum | **a** (indistinguishable) | n/a | unknown | **a** (indistinguishable from valid) | n/a |
| FHR FASTA, raw `>` (R11) | **a** — 2 records, no bogus one | n/a | unknown | not run | **c** (same as valid) |
| plain control | exit 0, same outputs | exit 0 | exit 2 (account wall) | exit 0 | exit 0, 0 errors |

## Environment limits

1. **Webin-CLI cannot be run without a Webin account.** Both `-validate` and
   `-validateFiles` exit 2 at option parsing: `ERROR: Missing required option:
   '-userName=USER'`, then `ERROR: Password must be provided using one of the
   following options: -password, -passwordEnv, -passwordFile`. No offline mode
   exists. Not worked around, by design.
2. **The stale NCBI FTP path.** `ftp.ncbi.nlm.nih.gov/toolkit/annotation/current/software/`
   → 404. Tools were taken from `asn1-converters/by_program/`.
3. **The stale Webin-CLI repo.** `github.com/ena-webin-cli/webin-cli` → 404;
   the live repo is `enasequence/webin-cli`.
4. **No Rosetta.** `arch -x86_64` fails (`Bad CPU type in executable`; `oahd`
   not running). Not blocking: the NCBI macOS builds are arm64. The `linux64`
   builds are x86-64 ELF, so a container fallback would also have been blocked
   on this arm64 host without qemu — Docker is available, but nothing needed it.
5. **`gff3tools` FASTA provider could not be made to resolve sequences.**
   `--sequence <file>.fasta` dies with `Unable to resolve sequence stats for
   sequence ctg1` / `No sequence source found for seqId: ctg1` **on the plain
   control as well as on the FHR file**, with byte-identical failure. So the
   FHR-header question is untested on that code path; the `key:path` plain-
   sequence form worked and is what the table above reports.
6. **Fictional organism ⇒ unavoidable noise.** `NoTaxonID`, `NoPubFound`,
   `BAD_LOCUS_TAG_FORMAT` and the DDBJ `DBLINK` warnings come from synthetic
   metadata, never from the header: each appears identically in the
   header-free control.
7. **Schema-forced omission.** `metadataAuthor.uri` could not be populated
   because the FHR schema pins it to the ORCID pattern; the field was left out
   rather than filled with an invented ORCID.
8. **Placeholder `PRIMARY_ID`.** The Webin-CLI annotation manifest needed a real
   versioned assembly accession; the synthetic fixtures have none, so
   `GCA_900000000.1` was entered as a placeholder with a `DESCRIPTION` marking it
   as such. It was never sent anywhere — the CLI stopped at the credential wall
   before reading the manifest.
9. **Single platform, single machine.** macOS 27.2 arm64, Python 3.15.0, OpenJDK
   27.0.1.0.3. Linux and Windows paths are untested.

## What this does and does not prove (row AN.a's question)

**Proves**, for the pinned versions and the exact commands above:

- An FHR `;~` block and an FHGFF3 `#~` block are **accepted without error and
  without warning by NCBI table2asn**, in every combination tested (FASTA alone,
  GFF3 alone, both together; `-V v` batch mode `-a s`, and `-V vb -M n -Z` with a
  template). Because the `.sqn` is
  byte-identical to the header-free control, table2asn provably does nothing
  with the header: it drops it, rewrites nothing, and reports nothing. The
  embedded provenance does not reach a GenBank submission by any path that
  table2asn controls.
- table2asn's own validation is unaffected in both directions: it does not
  reject an FH file, and it does not verify one (stale-checksum files are
  indistinguishable from valid ones). FH validity is not something NCBI's
  toolchain will check for us.
- The R11 escaping rule is load-bearing but table2asn is not the risk: its
  `;`-comment handling means a raw `>` inside a header value creates no bogus
  record for *this* reader. The tools that do break on it are the kseq-style
  readers already catalogued in `TOOL_COMPATIBILITY.md`.
- **DDBJ's public offline validator rejects an FHR FASTA** (`SEQ0080`,
  `SEQ0090`, both hard ERRORs) and its default auto-fix produces a corrupted
  FASTA with a fabricated record built from the metadata. The rejection is
  generic leading-comment intolerance (an ordinary `;` block of the same size
  fails identically), which is worth stating precisely — but it is DDBJ's own
  documented validator rejecting the file, so "strip before submission" is
  confirmed, not merely advised.
- Row **S11** can now cite measured behaviour, and `asnvalidate` should not be
  described as a FASTA checker: it does not read FASTA at all.

**Does not prove** — and must not be written as if it did:

- **Nothing about ENA.** Webin-CLI's validate path never executed. That
  `gff3tools` accepts `#~` is evidence about ENA's bundled parser, not about
  Webin-CLI's submission checks, not about the server-side validators, and not
  about what ENA stores or displays after a real submission. The ENA cells stay
  **unknown** until someone with a test account runs them.
- **Nothing about accepted submissions.** Every run is local and validation-only.
  No `.sqn` was uploaded, no Webin analysis was created, no DDBJ MSS ticket was
  filed. "table2asn accepts it" is not "GenBank will publish it with/without the
  metadata".
- **Nothing about the real submission portals'** (WebIn2, NCBI's submission
  portal, DDBJ NSSS/GGS) behaviour with browser-uploaded FH files.
- **Nothing beyond this shape of file.** Two tiny contigs, one gene, ASCII-only,
  LF endings, no `##FASTA` section in the GFF3, no CRLF, no BGZF, one synthetic
  taxon, and headers of moderate size (18 header lines). A real FHR file can
  carry a far larger header block — the spec's own `examples/example.fhr.fasta`
  has 53 `;~` lines — plus CDS micro-variants, `\x3E`-escaped values, or an
  embedded `##FASTA`; none of those were tested.
  Prokaryotic-mode (`-gcode=11`), `-submit`-portal-specific flags, and ENA's
  actual `.gff3.gz` upload were not exercised.
- **Nothing durable.** These are snapshots of `table2asn 1.29.324` (built
  2025-09-16), `webin-cli 11.0.0`, `gff3tools 5.5.1` and `ddbj-validator 1.0.94`
  at one commit. `ddbj-validator` in particular is beta, its README says so, and
  it was pushed the same day it was tested here; the DDBJ result could change
  with any release. Re-run before repeating it.

## Reproduction

The packaged harness is [`harness/`](harness) (`run-evidence.sh` + `fixtures/` +
its own [README](harness/README.md)). From a clean directory:

```bash
mkdir survey && cd survey
cp -r /path/to/harness/* .
./run-evidence.sh              # TOOLDIR=/path/to/cache reuses downloads
```

Requirements: macOS on Apple silicon, Python 3 with `venv`, `curl`, `gzip`,
`unzip`, `shasum`, and a JRE. Outputs: `evidence.log`, `jobs.tsv`, `runs/`.

Verification performed 2026-11-10, three independent runs (the interactive one,
`harness-selftest/`, and a from-scratch run of the packaged `harness/` in a
throwaway directory): the fixtures rebuild byte-for-byte — all seven of
`fhr_noheader.fsa`, `fhr_header.fsa`, `gff3_noheader.gff`, `fhgff3_header.gff`,
`fhr_corrupt.fsa`, `fhgff3_corrupt.gff`, `fhr_r11_rawgt.fsa` compare identical
across runs, with the FHR checksum
`MpZmU067e+UfurTwRzDQUI20nDyoPPIhwzXSgsKoeEg=` and the FHGFF3 checksum
`+flbvX8aFIfurIF6USXWhvPZNMZkbbnZsc30m7OcxEM=` reproduced exactly — and all 45
arms reproduce, including every `cmp` result quoted above (the `.sqn` files are
byte-identical between independent runs). Transcripts of the clean run are in
`evidence-harness.log`; exit codes in `jobs-harness.tsv`.

The harness writes only inside its own directory, downloads only from NCBI FTP,
GitHub releases and PyPI, and never passes `-submit` or any credential argument.

## Caveats for whoever writes the PR

- The `#~`/`;~` **drop is silent everywhere it works**. The compatibility table
  should say plainly that no INSDC tool preserves or displays FH provenance;
  "accepted" must not be readable as "supported".
- The DDBJ finding argues *against* softening the strip-before-submit guidance,
  and it is the strongest single result here because it comes from DDBJ's own
  public validator, not from inference.
- The `gff3tools` rewrite result (drops every comment line, upper-cases
  `locus_tag`, removes the `gene` feature) is a **checksum-destroying** behavior
  and belongs in `TOOL_COMPATIBILITY.md` even though it is not header-specific.
- `ddbj-validator` was not in the issue's plan at all. If maintainers would
  rather treat this as preliminary, the honest cell is "c on 1.0.94 @ `f3d3599`,
  beta tool, re-run before relying on it".
