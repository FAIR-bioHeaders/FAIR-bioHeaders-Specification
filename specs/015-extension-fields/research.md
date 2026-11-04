# Research: User-defined extension fields with an `x-` prefix

**Feature**: 015-extension-fields | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

Each decision records the choice, why, and what else was considered.

## R-01 The key pattern

**Decision**: Keep `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$`, case-sensitive, and add one schema rule: no
top-level key contains a line feed.

**Rationale**:
- `x-` is the prefix OpenAPI (`^x-`) and AsyncAPI use for specification extensions, so many
  implementers know it. FAIR-bioHeaders keys are camelCase, so an upper-case-only convention would
  not stand out, and `x-` cannot collide with a standard key: no standard key contains `-`.
- The character set after `x-` is the set of characters that need no quoting in YAML, JSON,
  shells or HTML attributes. It excludes `:` and `#` (YAML indicators inside plain scalars),
  spaces, quotes and `@`/`>` (R11), and it is ASCII, so there are no Unicode look-alikes or
  normalisation forms of one key. Requiring a letter or digit first rules out `x-`, `x--`, `x-.`
  and `x-_` as names.
- OpenAPI allows any characters after `x-`. Accepting that here would let keys hold the characters
  above, which R11 and YAML would then have to handle in keys, for no use case.
- Python's `re` (used by `jsonschema`) and ECMA-262 (JSON Schema's regex dialect) give the same
  result for this pattern on every probe (`x-a`, `x-1`, `x-a.b-c_d` match; `x-`, `X-a`, `x-_a`,
  `x- a`, `x-a b`, `x-ä`, `x-ａ` (fullwidth), `x-K` (Kelvin sign), `x-a\r` and `x-a` followed by
  U+2028 do not), with one exception: Python's `$` also matches before a final line feed, so
  `"x-a\n"` matches in Python and not in ECMA-262. Checked on 2026-11-03 with Python 3.13 `re` and
  Node.js 20 (with and without the `u` flag). The schema therefore also says
  `propertyNames: {not: {pattern: "\n"}}`, which both dialects read the same way. It rejects only
  keys that were already invalid (no standard key contains a line feed).
- Case-insensitive matching is never used, so `X-` is an ordinary unknown key; with `re.I`, Python
  would also have matched the Kelvin sign as `k`.

**Alternatives**: `x_` or `ext-` (no wider practice; `x_` reads like a typo of a camelCase key);
`^x-` alone (above); a required namespace segment `^x-[a-z0-9]+-` (rejected by the maintainers:
recommended, not enforced).

## R-02 How a minor version gates the new keys

**Decision**: The new schemas (FHR 2.1, FHP 1.1, FHGFF3 1.1) list the extension pattern in
`patternProperties` and add one conditional: if `schemaVersion` is the previous minor (`"2.0"`,
`"1.0"`), no key may start with `x-`. Schema selection (V1–V6) does not change.

**Rationale**:
- A record citing a v0.4.x schema URL (raw tag or w3id) already selects the v0.4.x schema by V2 and
  V3, where `x-` keys are unknown keys. Nothing changes for those records.
- A record citing raw-main selects the current schema (V1), which accepts `schemaVersion` `"2.0"`
  and `"2.1"` (docs/SCHEMA-VERSIONS.md: M.N accepts M.0 to M.N). Without the conditional, a record
  stating `"2.0"` could use a 2.1 feature. With it, such a record has exactly the 2.0 outcome: the
  only differences between the 2.0 and 2.1 schemas are the enum and the extension keys, and the
  conditional removes the latter for `"2.0"`.
- Putting the rule in the schema means every JSON Schema validator applies it, not only readers
  that implement a new selection rule.
- The change is minor (docs/SCHEMA-VERSIONS.md): every record valid under 2.0 is valid under 2.1
  with the same meaning; the conditional and the line-feed rule only reject records 2.0 already
  rejects.

**Alternatives**: a new selection rule V7 reading raw-main records that state `"2.0"` against the
v0.4.x schema (same outcome, but only for readers that implement V7; also changes error messages
for no gain); no gating (a `"2.0"` record with `x-` keys would be valid under raw-main but invalid
under v0.4.0, so one record would have two outcomes).

## R-03 Values and the YAML rules

**Decision**: Any JSON value (string, number, boolean, null, array, object, nested to the existing
limits). R8 (no duplicate keys, anchors, aliases, merge keys), R11, R12 and R13 apply. R14 does not
apply: extension values have no `format`.

**Rationale**: The toolkit's YAML loader, R12 check, R13 check and R11 FASTA writer already walk
every key and value, not only the schema's; the vectors and toolkit tests show it. A key in the
pattern can never be read as another YAML type: YAML 1.1 and 1.2 type plain scalars that start with
a digit, sign, `.`, `~`, or a word such as `true`/`yes`/`null`, and no such scalar starts with
`x-`. The FASTA writer escapes `>`/`@` in values; keys cannot contain them.

**Alternatives**: limiting values to scalars (rejected: gtars-style extra-field maps hold lists and
objects).

## R-04 JSON-LD, the schema.org export and microdata

**Decision**: Writers leave extension fields out and report the keys they left out. A JSON-LD
document (canonical or not) or a microdata item with an extension key is invalid (new rules J9 and
M5). The JSON-LD context and vocabulary are unchanged.

**Rationale**:
- J3 exists so that JSON readers and JSON-LD processors read the same values from one document.
  The FHR context has no `@vocab`, so a JSON-LD processor drops an `x-` key; a canonical (J1)
  reader, which reads the JSON, would keep it. Rejecting the key in both keeps the two readings
  equal.
- Leaving the fields out of writer output means no extension value (which may hold `@context`,
  `@id`, `<`, `>` or `&`) reaches JSON-LD processing or an HTML page through a writer, so the
  J3, J7 and J8 protections need no exception.
- Mapping extensions to a separate namespace (the issue's other option) would publish terms whose
  meaning the standard does not define, and each `x-` key would need an IRI rule. Leaving them out
  is the smaller change; mapping can be added later as a minor change.
- The schema.org export already writes only the fields it maps (X9); its documentation now says so
  for extension fields.

**Alternatives**: an `fhrx:` namespace (above); passing the keys through unmapped (a JSON-LD
processor would silently drop them, which J4 forbids).

## R-05 Release and toolkit sequencing

**Decision**: Prepare release v0.5.0 on `main` under the documented `preRelease` exception
(docs/SCHEMA-VERSIONS.md, "Schema files on main"): `current` and `preRelease` are `v0.5.0`, and the
examples and `llms.txt` cite it. The conformance CI runs the toolkit commit that bundles the
v0.5.0 schemas, pinned by hash, until toolkit 0.9.0 is released; then it pins
`fair-bioheaders==0.9.0`. Tagging v0.5.0 and releasing 0.9.0 are maintainer actions.

**Rationale**: The new valid vectors cite v0.5.0, which released toolkits (0.8.x) report as an
unsupported version, so they cannot run against a released toolkit until 0.9.0 exists. The CI
pinned a toolkit commit the same way during the v0.4 preparation (`fc36ebb`). A pinned commit is
immutable bytes, not a moving branch.

**Alternatives**: deferring the vectors until 0.9.0 (leaves the rule without conformance coverage
in the PR that adds it); a long-lived release branch (v0.4 used one, but a single schema change does
not need it).

## R-06 FHT

**Decision**: Add the rule to the FHT draft contract `"1.0"` (`fht_linkml.yml` generator and
`fht.json`), with no version change.

**Rationale**: FHT has no released contract, so no record depends on the closed top level, and
the draft can include the rule from its first release. The FHT generator gets the same
post-processing as the shared generator, without the version conditional (there is no older FHT
minor).
