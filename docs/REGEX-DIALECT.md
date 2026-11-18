# Regular-expression dialect for `pattern`

This is the single normative home for what a JSON Schema `pattern` in a
FAIR-bioHeaders contract means when it is evaluated. Every other page that needs
this policy links here instead of restating it, so the policy has exactly one
place to change.

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
- `\d`, `\w` and `\s` are ASCII-based (without the `u` flag).

**A JSON Schema `pattern` applies to the complete string value, not to a line
within it.** `^` and `$` bound the value; a value that contains a line feed is
one string, and a pattern is never run per line.

A third-party validator may read these constructs differently, and that
divergence is a property of the validator, not a second floor the contract must
satisfy. Where a difference changes which records validate, this family resolves
it on the implementation side: the toolkit evaluates contract `pattern` through
an adapter that reads `$` as end of string, as ECMA-262 requires
(`bioheaders/schema_validator.py`, FAIR-bioHeaders-Tools#189).

## Where engines actually differ, and what this family does about it

Python's `re`, used by the `jsonschema` package this repository's own scripts
run, differs from ECMA-262 in ways that have been measured:

- `$` also matches before one trailing newline, so a value such as
  `"soft-masked\n"` passes an anchored pattern under Python and fails it under
  ECMA-262. **This is the one difference the family relies on today**, in the
  sense that it changes the validation outcome of released contracts: the
  toolkit corrects it by rewriting every unescaped `$` outside a character class
  to `\Z`.
- `\d` and `\w` are Unicode-aware in Python where ECMA-262 without flags is
  ASCII, and `\s` is Unicode-aware in both but over different whitespace sets.
  Measured on the same 2026-11-18 pass: no released pattern uses `\d`, `\w`,
  `\s`, `\D` or `\W` outside a character class, and two of the 16 distinct
  released patterns use `\S`, so a value holding a character Python calls
  non-space and ECMA-262 calls space (for example U+00A0) is the kind of input
  where the two readings can disagree.
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
pattern for being RE2-hostile. It is reported by the `pattern` inventory that
`scripts/check_pattern_census.py` maintains once that script lands on `main`;
read its current output for any present-day figure rather than a number quoted
in prose. For the record, the measurement taken when this page was written
(2026-11-18, `origin/main` at `24eab38`, walking every `pattern`, every
`patternProperties` key and every `propertyNames` exception pattern of the
source files):

| file | regex entries | entries ending in `$` | entries using lookaround |
| --- | --- | --- | --- |
| `fhr.json` | 11 | 9 | 0 |
| `fhp.json` | 25 | 21 | 0 |
| `fhgff3.json` | 28 | 24 | 0 |
| `schemas/core.yaml` | 7 | 7 | 0 |
| `schemas/shared.yaml` | 1 | 1 | 0 |
| `schemas/versions.json` | 0 | 0 | 0 |

The `$`-terminated patterns live in the three released contracts at the
repository root, in `schemas/core.yaml`, and in the one `lineageDataset` slot of
`schemas/shared.yaml`; `schemas/versions.json` is a version registry and carries
no regex at all. Those per-file figures count occurrences, not patterns: the
three contracts hold 16 distinct pattern strings among their 64 entries, because
a LinkML pattern appears both in `$defs` and at the emitted instance path. None
of the 16, and none of the 8 LinkML entries, uses lookaround, a backreference,
an inline flag group, a conditional or `\A`/`\z`. All 7 `schemas/core.yaml`
entries and the single `schemas/shared.yaml` entry end in `$`; the 10 entries
that do not are the extension-field exception patterns of rule R15 in
`docs/FORMAT.md` — a literal line-feed pattern and a `^x-` prefix test, once
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
