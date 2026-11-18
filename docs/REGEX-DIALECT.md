# Regular-expression dialect for `pattern`

This is the single normative home for what a JSON Schema `pattern` in a
FAIR-bioHeaders contract means when it is evaluated. Every other page that needs
this policy links here instead of restating it, so the policy has exactly one
place to change.

It records the [2026-11-18 ruling](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/264#issuecomment-6991186339),
recorded by the operating agent under the maintainer's direction: option 3 is
adopted, with no schema, `schemaVersion` or release change. Publication remains
a separate action.

## The floor

**ECMA-262 is the only normative floor for `pattern`.** JSON Schema draft
2020-12 defines `pattern` as an ECMA-262 regular expression, unanchored, tested
against the whole instance string. Concretely, in an ECMA-262 `pattern` with no
flags:

- `$` matches only at the end of the string, `^` only at its start. Neither is a
  line anchor here: an ECMA-262 `/m` (multiline) flag exists, but JSON Schema
  applies no flags, and no contract pattern in this family sets one.
- `[]` matches nothing and `[^]` matches any character: ECMA-262 permits an
  empty class body.
- `\d` and `\w` use ASCII digit/word sets with no flags. `\s` includes
  Unicode whitespace and line terminators even without `u`, including U+00A0
  (NO-BREAK SPACE) and U+FEFF (ZERO WIDTH NO-BREAK SPACE); `\S` is its complement.
  See ECMA-262's [character-class escape rules](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-runtime-semantics-compiletocharset).

**A JSON Schema `pattern` applies to the complete string value, not to a line
within it.** `^` and `$` bound the value; a value that contains a line feed is
one string, and a pattern is never run per line.

A third-party validator may read these constructs differently, and that
divergence is a property of the validator, not a second floor the contract must
satisfy. Where a difference changes which records validate, this family resolves
it on the implementation side: the toolkit evaluates contract `pattern` through
an adapter that reads `$` as end of string, as ECMA-262 requires
(`bioheaders/schema_validator.py`, FAIR-bioHeaders-Tools#189, merged to toolkit
`main`; this source-state observation does not establish a package release).

## Where engines actually differ, and what this family does about it

Python's `re`, used by the `jsonschema` package this repository's own scripts
run, differs from ECMA-262 in ways that have been measured:

- `$` also matches before one trailing newline, so a value such as
  `"soft-masked\n"` passes an anchored pattern under Python and fails it under
  ECMA-262. This changes released-contract outcomes; whitespace-set differences
  in released `\S` constraints do too (below). The toolkit's adapter corrects
  the anchor by rewriting every unescaped `$` outside a character class to `\Z`.
- `\d` and `\w` are Unicode-aware in Python where ECMA-262 without flags is
  ASCII, and `\s` is Unicode-aware in both but over different whitespace sets.
  Measured on the same 2026-11-18 pass: no released pattern uses `\d`, `\w`,
  `\s`, `\D` or `\W` outside a character class, and `\S` appears outside a
  character class in **7** entries of the three released contracts, which are
  **2** distinct pattern strings (`^\S+$` and the `scholarlyArticle` DOI
  pattern). U+FEFF is non-space in Python but whitespace in
  ECMA-262, while U+00A0 is whitespace in both. For example, `"gene\uFEFF"`
  passes Python's `^\S+$` but fails ECMA-262's: that exact released constraint
  applies to `FeatureCount.featureType` and `GenomeReference.accession` in
  `fhgff3.json`. U+0085 illustrates the opposite direction: Python treats it as
  whitespace and ECMA-262 does not. These are regex outcomes, not assertions
  that a whole record satisfies every other contract or format requirement.
- A class whose first character is `]` starts a non-empty class in Python
  (`[]]` matches `]`) and an empty one in ECMA-262 (`[]]` matches nothing and
  `[^]` matches any character); Python rejects `[^]` outright as an unterminated
  set. No released pattern uses either form; the toolkit still translates them
  with their ECMA meaning.

Differences like the last two matter for anyone building a new consumer, so a
reader must not assume that a contract pattern compiles identically in every
engine.

## RE2 and other restricted engines: a compatibility observation

Staying inside the RE2 subset — no lookaround, no backreferences, no inline
flags, no conditionals — is a **non-normative compatibility observation**. It is
not a requirement a contract has to meet, and nothing in this family rejects a
pattern for being RE2-hostile. Nothing here claims that any tool certifies it:
the census script proposed in #270 and under review in #272 (open, not merged as
this PR is written) is an **inventory and drift gate for the `pattern` keyword
of the released contracts** — it fails when a released `pattern` is added,
removed or edited against its committed baseline, and it reports lookaround and
other constructs in the draft and proposal scope **informationally only**, so it
can never reject the drafts' lookarounds. It deliberately does **not** compile
patterns, prove ECMA-262 validity, certify engine or RE2 compatibility, or cover
`patternProperties` keys. So the observation below is a measurement of record,
taken by hand for this page and not produced by that tool; if #272 merges, read
its output for the current released-`pattern` figures and this page only for the
dialect rule.

Measurement of record: 2026-11-18, `origin/main` at `24eab38` (this PR's base),
walking every `pattern` keyword, every `patternProperties` key and every
`propertyNames` exception pattern of six files:

| file | regex entries | entries ending in `$` | entries using lookaround |
| --- | --- | --- | --- |
| `fhr.json` | 11 | 9 | 0 |
| `fhp.json` | 25 | 21 | 0 |
| `fhgff3.json` | 28 | 24 | 0 |
| `schemas/core.yaml` | 7 | 7 | 0 |
| `schemas/shared.yaml` | 1 | 1 | 0 |
| `schemas/versions.json` | 0 | 0 | 0 |
| **total** | **72** | **62** | **0** |

**Which scope each figure covers, so that two honest censuses are not read as a
disagreement.** The table above counts *regex entries*, not pattern strings, and
its class set is `pattern` keywords **plus** `patternProperties` keys **plus**
`propertyNames` exception patterns, over **six** files: 72 entries, 62 ending in
`$`, 0 using lookaround. The census under review in #272 counts the `pattern`
keyword only — it deliberately excludes `patternProperties` keys — over **nine**
files, adding the three root `*_linkml.yml` models: its committed
`.github/pattern-baseline.json` (read at head `79e30c5c`, identical at `a2051760`) records
`patternCount` 72 with 62 `$`-terminated entries and 0 using lookaround, and 15 distinct strings. The
two totals coincide at 72/62/0 **by composition, not by agreement**: this page's
64 contract entries are 49 `pattern` keywords + 5 `patternProperties` keys + 10
`propertyNames` exception patterns, and #272's 72 are 59 in those same three
contracts plus 5 in the three LinkML models, 7 in `core.yaml` and 1 in
`shared.yaml`. A figure quoted from one scope does not validate the other,
and neither supersedes the other — the same trap as comparing a pin against the
wrong ref.

The `$`-terminated patterns live in the three released contracts at the
repository root, in `schemas/core.yaml`, and in the one `lineageDataset` slot of
`schemas/shared.yaml`; `schemas/versions.json` is a version registry and carries
no regex at all. Those per-file figures count occurrences, not patterns: the
three contracts hold 16 distinct regexes among their 64 entries, because
a LinkML pattern appears both in `$defs` and at the emitted instance path. None
of the 16, and none of the 8 entries in `schemas/core.yaml` and
`schemas/shared.yaml` together, uses lookaround, a backreference, an inline flag
group, a conditional or `\A`/`\z`. All 7 `schemas/core.yaml` entries and the
single `schemas/shared.yaml` entry end in `$`; the 10 entries that do not are all
in the three contracts and are the extension-field exception patterns of rule R15
in `docs/FORMAT.md` — 5 literal line-feed patterns and 5 `^x-` prefix tests, once
per contract and, for the two generated contracts, again in their `$defs`
copy — which are key-name tests, not unanchored value patterns.

## The drafts

The unreleased draft contracts hold `(?![\s\S])` end anchors: three occurrences
in `fht.json` of
[FHT-Specification](https://github.com/FAIR-bioHeaders/FHT-Specification) and
one in `development/model/fhgm-model.schema.json` of
[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification), as
read from each repository's `main` on 2026-11-18. That is the LinkML generator's
way of writing "end of string". Under the ECMA-262 floor these patterns are
**correct and publishable**; they are not a defect to fix and they do not make
either draft non-conformant. Both remain drafts under rule V7: this page grants
them no release, no version, no registry row and no identifier.

## What this page does not decide

Declaring `"$schema": https://json-schema.org/draft/2020-12/schema` fixes the
dialect of `pattern` and the meaning of the keywords. It does not establish:

- that every implementation shares one regex engine, or reads the constructs
  above the same way;
- that `format` assertions behave identically — in draft 2020-12 `format` is an
  annotation, and a conforming validator must opt in to asserting it (see the
  `format` section of [SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md));
- that a record which validates in one engine is therefore conformant for a
  consumer. The schemas do not express every requirement: required values must
  be non-empty, `format` must be asserted, and NaN and infinities are invalid
  (rules R8, R11 to R13 in [FORMAT.md](FORMAT.md)).

No schema or contract byte changes as a consequence of this page, and none is
proposed here.
