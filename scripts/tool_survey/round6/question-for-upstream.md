# DRAFT — question for the INSDC GFF3 Specification draft editors (not posted)

Target thread: The-Sequence-Ontology/Specifications #41 (INSDC GFF3
Specification v0.5.1 DRAFT feedback).
From: FAIR-bioHeaders project (spec issue #210). Status: **draft, reviewed
only inside the project; do not post without maintainer action.**

---

**Subject: Scope of the ASCII common rule (draft v0.5.1, p. 6, lines 145–150)
— does it constrain comment bytes, and serialized bytes or decoded values?**

Dear draft editors,

FAIR-bioHeaders (FHGFF3) embeds YAML metadata inside ordinary GFF3 comment
lines: header lines start with `#~` after `##gff-version 3`, and one
`#~checksum:` line carries a SHA-512/256 over the file's exact bytes (every
byte except that one line). Our format rule permits UTF-8 header text (ASCII ⊂
UTF-8, so ASCII-only files satisfy both). The draft lists ASCII as a common
rule across its profiles; we would like to submit before assuming either
reading. Three linked questions:

1. **Which bytes does the ASCII rule constrain?** Feature lines only, or also
   `##`/`#!` directives, ordinary `#` comment lines, and — critically for us —
   embedded metadata carried in comment lines (e.g. `#~annotation: …`)?
   The draft text (p. 6) does not, as far as we can tell, enumerate comment
   bytes; a scope sentence would settle it.
2. **Serialized bytes or decoded values?** If a non-ASCII character is carried
   in an ASCII-only serialization — e.g. the YAML double-quoted escape
   `"Caf\u00E9 annotation"` (bytes `5C 75 30 30 45 39`, all ASCII) that
   *decodes* to `Café annotation` — is that conformant? I.e., does the rule
   apply to the octets in the file, to the values a parser reconstructs, or
   both? If it applies only to serialized bytes, conformant producers can keep
   any Unicode value by escaping.
3. **What must tools do with comment bytes on rewrite?** The draft lists ENA
   gff3tools as a validation resource (p. 23, lines 563–567). If comments (or
   embedded metadata) are dropped or re-serialized by a listed tool, a
   checksum computed over the pre-tool bytes — e.g. our `#~checksum:` — no
   longer covers the file. Should the draft state whether conformant
   validation/conversion tools preserve comment lines byte-for-byte, and how a
   downstream integrity claim should be treated after rewriting?

**Why we ask now — byte-level observations (2026-11-10, synthetic four-fixture
matrix, full evidence in FAIR-bioHeaders-Specification#210):**

Four otherwise byte-identical GFF3 files (same directives, same 5 features,
same `##FASTA` section, same ordinary ASCII comment in each) differing only in
the header annotation scalar:

| Fixture | Serialized bytes of the value | Plain GFF3 | gff3tools (source-pinned `1bbe070`) | gff3 1.0.1 | gffutils 0.14 |
| --- | --- | --- | --- | --- | --- |
| 1 no header | — | parses | comment-skip path | parses, 0 errors | parses |
| 2 ASCII header | `Synthetic annotation` | parses | comment-skip path | parses, 0 errors | parses |
| 3 raw UTF-8 | `Caf` `C3 A9` `annotation` | parses | comment-skip path¹ | parses, 0 errors, raw bytes preserved | parses |
| 4 ASCII escape | `Caf` `5C 75 30 30 45 39` `annotation` | parses | comment-skip path¹ | parses, 0 errors, escape preserved | parses |

¹ gff3tools was **not executed** — its build requires authenticated EBI
package artifacts — so this column is from its pinned source: every `#` line,
ordinary or `#~`, matches `COMMENT = ^#.*$` and is dropped; only
`##gff-version <version>` is re-emitted on any write path. The string `#~`
occurs nowhere in that codebase.

Observed rewrites (gffutils 0.14 export, per fixture): ordinary comments
**dropped**, all `#~` metadata **dropped**, `##sequence-region`/`#!genome-build`
directives **dropped**, and only the feature lines re-emitted byte-identically.
simple-gff3 was parsed and inspected but not exercised through a rewrite path.
We separately verified that a stale checksum claim on fixture 4's unchanged
escaped-annotation bytes fails verification, as it must.

We reproduced **no failure** in any parser we could run, and none of our
fixtures are intended to be submitted anywhere (validation-only, local). Our
tentative conclusion, pending your answer, is to advise FHGFF3 producers
targeting INSDC profiles to serialize non-ASCII metadata values as ASCII-only
YAML escapes — which our reader confirms decodes to exactly the same value —
and to treat any post-tool file as requiring checksum regeneration. But we
would rather state the boundary than guess it:

- If the ASCII rule covers comment bytes, is fixture 3 non-conformant while
  fixture 4 is conformant?
- If it does not cover comments at all, could the draft say so explicitly, so
  embedded-metadata formats built on GFF3 comments have a defined home?

Thank you — David Molik, on behalf of the FAIR-bioHeaders project
(FAIR-bioHeaders-Specification issue #210; related #191 for broader
submission-validator testing).
