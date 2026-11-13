# Schema versions and schema selection

Every FAIR-bioHeaders header names the schema it follows in `schema` and the version of that
schema's contract in `schemaVersion`. This page says what the version means, which releases carry
which versions, and how a reader chooses the schema to validate a file against. The toolkit, the
gff3-validator header checks and the website follow it. The design is in
[specs/012-schema-versioning](../specs/012-schema-versioning/spec.md) (maintainer decision on
[#44](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/44), 2026-10-14).

Known gaps between this normative text and what the current schemas can express, with
their status, target release and decisions, are tracked in
[SCHEMA-GAP-AUDIT.md](SCHEMA-GAP-AUDIT.md).

## Three different versions

| Value | Example | What it versions |
| --- | --- | --- |
| `schemaVersion` | `"2.0"` | The metadata contract of one header type (this page) |
| Release tag | `v0.4.0` | A release of this repository; it can carry several header types |
| `version` | `1.2.0` | The assembly, protein set or annotation the header describes |

A release tag alone never changes `schemaVersion`, and neither ever changes the described data's
`version`.

## schemaVersion

`schemaVersion` is a string `"MAJOR.MINOR"`: two non-negative integers without leading zeros
(`^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`). Each header type has its own version.

- **Major** (`2.0` → `3.0`): some file that was valid becomes invalid, or a valid value changes
  meaning. Examples: a new required field, a removed field, a tighter pattern, range or enum, a
  closed object, a changed type.
- **Minor** (`2.0` → `2.1`): every valid file stays valid with the same meaning, and something
  new is allowed. Examples: a new optional field, a relaxed constraint.
- **No change**: descriptions, examples, documentation and generated files that change no
  validation outcome.

The schema of version M.N accepts `schemaVersion` values `"M.0"` to `"M.N"`. A record that states
an earlier minor is held to that minor: what a later minor allows is invalid in it. For example,
the FHR 2.1 schema accepts `schemaVersion: '2.0'`, but extension fields
([FORMAT.md](FORMAT.md) R15), added in 2.1, are invalid in a record that states `'2.0'`, exactly
as under the 2.0 schema; likewise the FHP and FHGFF3 1.2 schemas accept `schemaVersion: '1.1'`,
but a dotted BUSCO dataset version (#170), added in 1.2, is invalid in a record that states
`'1.0'` or `'1.1'`. A record that uses a feature states the minor that added it, or a later
one.

In YAML headers write the version quoted: `schemaVersion: '2.0'`. Unquoted, `2.0` is the number
2.0 and fails. The toolkit quotes it when it writes YAML.

## Values the schema does not check

The schemas are the validation contract, but two requirements are not expressed by their
keywords. They are normative for a conforming record and validator. A third, link schemes,
is a recommendation that validators report as a warning.

### Required values are non-empty

`required` makes a key present; it does not give the key a value. A record with `genome: ""`,
`version: ""`, `taxon: {}`, `metadataAuthor: []` or `assemblyAuthor: [{}]` still passes
`fhr.json` 2.0, and the same emptiness passes the equivalent fields of `fhp.json` and
`fhgff3.json`. Such a record does not describe the data. Required values must be non-empty:

- `genome`, `version`, `proteome` and `annotation` are non-empty strings;
- `taxon` has a non-empty `name` or `uri`;
- `metadataAuthor` and, where the type has it, `assemblyAuthor` are non-empty lists, and every
  author has a non-empty `name`.

Starting from `examples/minimal.fhr.json` and emptying the applicable fields for each type at
once still validates with jsonschema 4.x and `bioheaders validate` 0.8.0 and later. Such a record
is schema-valid under 2.0 but not conforming: validators should warn and must not report it as
invalid until the next major `schemaVersion` can reject it. `minLength: 1` on the required
strings, `minItems: 1` on the author lists, `required: [name]` plus `minLength: 1` on an author's
`name`, and a required, non-empty `taxon.uri` that identifies an NCBI Taxonomy or ITIS taxon
(decided in [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189);
see [SCHEMA-GAP-AUDIT.md](SCHEMA-GAP-AUDIT.md#gap-1-taxon-identifier-decided-189)), are planned for the next major `schemaVersion` (FHR 3.0, and the next major of FHP and FHGFF3).
They are a major change because they invalidate records that are valid under 2.0, so they do not
belong in a minor release.

### `format` is asserted

The schemas use JSON Schema draft 2020-12, where `format` is an annotation: a validator that
does not opt in ignores it. A conforming validator must assert every `format` the schemas
declare (currently `date` and `uri`): `date` on `dateCreated`, and `uri` on every URI or URL
field, including `relatedLink` items, `taxon.uri`, author, accession and software `uri`/`url`
values, `assemblyProtocol`, `predictionProtocol`, `annotationProtocol`, and FHP/FHGFF3
`source[].url`.
`dateCreated: "2022-13-45"` and `relatedLink: ["not a URI"]` are invalid even though a bare
`Draft202012Validator` accepts them; `bioheaders validate` and this repository's scripts pass a
`FormatChecker` and reject them. A validator that cannot assert `format` must report that
limitation instead of calling the record valid.

Numbers are covered by rule R13 in [FORMAT.md](FORMAT.md): NaN and infinities are invalid.

### Link schemes

`format: uri` accepts any URI scheme, including `javascript:`, `data:` and `file:`. Rule R14 in
[FORMAT.md](FORMAT.md) says these values should use `http` or `https` (with `ftp`, `urn:`,
`doi:` and `info:` also accepted). Validators warn about any other scheme, and the JSON-LD
writers refuse to write it as a link, but such a record stays valid under FHR 2.0 and 2.1 and
FHP and FHGFF3 1.0, 1.1 and 1.2. A `pattern` that restricts the schemes is a candidate for the next major
`schemaVersion` of each type: it would invalidate records that are valid now, so it does not
belong in a minor or patch release.

## Versions by release

The machine-readable form is [`schemas/versions.json`](../schemas/versions.json).

| Release | FHR | FHP | FHGFF3 |
| --- | --- | --- | --- |
| v0.3.0, v0.3.1 | `1` (a number) | – | – |
| v0.4.0, v0.4.1, v0.4.2 | `"2.0"` | `"1.0"` | `"1.0"` |
| v0.5.0 | `"2.1"` | `"1.1"` | `"1.1"` |
| v0.6.0 (prepared, not yet tagged) | `"2.1"` | `"1.2"` | `"1.2"` |

v0.4.1 and v0.4.2 changed only format rules (docs/FORMAT.md, docs/JSONLD.md and schema
selection), not the schemas, so their schemas are the v0.4.0 ones; `current` in
`versions.json` stayed `v0.4.0` and the examples cited v0.4.0 until v0.5.0.

v0.5.0 adds extension fields ([FORMAT.md](FORMAT.md) R15): top-level keys that start with `x-`.
That is a minor change for each type (FHR 2.1, FHP 1.1, FHGFF3 1.1): every record valid under
2.0 or 1.0 stays valid with the same meaning, and the new schemas reject extension fields in a
record that states `'2.0'` or `'1.0'`. A record that cites a v0.4.x schema URL is checked against
the v0.4.x schema (V2, V3), where an `x-` key is an unknown key, so files with extension fields
cite v0.5.0 or later and state the new version. Readers that predate v0.5.0 report such files as
an unsupported schema version (V4), or as invalid if they cite raw-main.

v0.6.0 adds dotted BUSCO dataset versions (#170): the shared `Completeness.lineageDataset`
pattern widens from `^[a-z0-9_]+_odb[0-9]+$` to `^[a-z0-9_]+_odb[0-9]+(\.[0-9]+)*$`, so dataset
ids documented by the BUSCO user guide, such as `enterobacterales_odb12.2`, are valid. That is a
minor change for FHP (`"1.2"`) and FHGFF3 (`"1.2"`) only; FHR (`"2.1"`) has no completeness slot
and is unchanged. Every record valid under 1.0 or 1.1 stays valid with the same meaning, and the
new schemas reject a dotted version in a record that states `'1.0'` or `'1.1'`. A record that
cites a v0.4.x or v0.5.0 schema URL is checked against that release's schema (V2, V3), where a
dotted version fails the old pattern, so files with dotted dataset versions cite v0.6.0 or later
and state the new version. Readers that predate v0.6.0 report such files as an unsupported schema
version (V4), or as invalid if they cite raw-main. v0.6.0 is prepared on `main` under the
pre-release exception below (`preRelease` in `schemas/versions.json`) until its tag exists.

FHR 2.0 is a major version because the v0.4 tightening
([SCHEMA-CHANGES-v0.4.md](SCHEMA-CHANGES-v0.4.md)) rejects some values v0.3 accepted. The additive
v0.4 changes (author `nameType`, scaffold statistics) are part of 2.0. FHP and FHGFF3 are first
released in v0.4.0.

## Schema files on main

A schema change has its own release. The three schema files in the working tree are therefore
byte-identical to the copies at the release named by `current` in `schemas/versions.json`:
`fhr.json`, `fhp.json` and `fhgff3.json` equal `git show <current>:<file>`.
`tests/test_schema_versions.py` checks this. A missing tag is skipped only when
`schemas/versions.json` sets `preRelease` to the same tag as `current` (the documented
pre-release exception below). A missing tag without that marker fails, so a typo in `current`
cannot look like a shallow checkout; fetch tags with `git fetch --tags` in a shallow clone.
Setting `preRelease` while its tag already exists also fails, so the marker must be cleared
when the release is tagged. CI checks out full history and tags, so the byte comparison runs
there. If the tag exists but a schema file is missing from it, the check fails: an incomplete
release is not an exception.

The exception is a deliberate, reviewed schema change that must be prepared before its release
tag exists. Record it in the pull request and the release tracker, set `current` and its
`releases` entry to the release being prepared, set `preRelease` to the same tag, and update
every example and `llms.txt` to the prepared release's URL and version: the example and
`llms.txt` tests follow `current`, so they do not skip. The schema-byte check skips only for
that explicit marker until the tag exists. For publication, clear `preRelease` in the final
release-branch commit, tag that commit, and then run the release-identity check. The check
will fail between clearing the marker and creating the tag. Carry the cleared registry to
main. Do not edit a released file, delete the check or weaken it. Tags and released files are
immutable, and publishing a tag is a maintainer action; once the release reaches main, the
working tree and the tag agree again.

## Choosing the schema

A reader looks only at the record's `schema` value. `<file>` is `fhr.json`, `fhp.json` or
`fhgff3.json` and gives the header type; `<type>` is `fhr`, `fhp` or `fhgff3`. Matching is exact.

Raw URLs may name the repository by its current name, `FAIR-bioHeaders-Specification`, or by
`FHR-Specification`, its name until #108. Both forms are recognised everywhere and mean the
same; existing files cite the old form, and it keeps serving the same files.

- [V1] `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/<file>` selects
  the reader's **current** schema of that type: the copy of `main` the reader has. There is no
  fallback to an older release, except for FHR 1 records (V6).
- [V2] `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/vX.Y.Z/<file>` selects
  **release vX.Y.Z's** schema of that type.
- [V3] `https://w3id.org/fair-bioheaders/<type>/vX.Y.Z`, with or without a trailing slash, selects
  release vX.Y.Z's schema of that type, the same as V2.
- [V4] If the reader does not have that release, the release has no schema of that type, or a raw
  URL names any ref other than `main` or a release tag, the result is **unsupported-version**. The
  file is not checked against another schema. The message names the value and the releases the
  reader has, for example
  `FHR: unsupported schema version: https://w3id.org/fair-bioheaders/fhr/v0.0.0 (this tool has FHR
  schemas for main (v0.6.0), v0.3.0, v0.3.1, v0.4.0, v0.4.1, v0.4.2, v0.5.0, v0.6.0)`.
- [V5] Any other value, including the w3id path form `…/fhr/v0.4.0/fhr.json`, is **FHR**, checked
  against the current FHR schema. FHR's `schema` field has never been constrained; this keeps that
  behaviour.
- [V6] **FHR 1 compatibility.** A record whose `schema` is the raw-main `fhr.json` URL (V1, under
  either repository name) and whose `schemaVersion` is the number 1 is an **FHR 1** record. It is
  checked against release v0.3.1's FHR schema, the last FHR 1 contract, and the result is that
  schema's result. `1` and `1.0` are the same number (JSON, and YAML's `1` and `1.0`, give the
  number 1); the string `"1"`, a boolean and any other number are not 1, so V1 applies to them
  unchanged. The record is **deprecated, not invalid**: readers should warn and name the two
  fixes in [Migrating](#migrating-files-that-cite-raw-main-with-schemaversion-1), for example
  `FHR: warning: schemaVersion 1 via the raw-main schema URL is read as FHR 1 (v0.3.1); cite
  https://w3id.org/fair-bioheaders/fhr/v0.3.1 or move to schemaVersion "2.0"`. V6 applies only
  to FHR: FHP and FHGFF3 were first released in v0.4.0 with `schemaVersion` `"1.0"`, so they have
  no earlier raw-main contract. For microdata without `data-fhr-type`, `schemaVersion` text that
  reads as the JSON number 1 counts as the number 1 (rule M3 then converts it with the v0.3.1
  schema, whose `schemaVersion` is a number).
- [V7] **Unreleased draft contracts (opt-in).** A reader may recognise a **draft** contract: a
  `<file>` outside V1's list, cited as the raw-main URL of the development repository that owns
  that type, `https://raw.githubusercontent.com/FAIR-bioHeaders/<repo>/main/<file>`. The lane is
  never the default: it applies only where the user has explicitly chosen to read that
  repository's draft. Without that choice, V5 governs such a value and the outcome is exactly what
  it was before V7 existed. With it, the record is read against the draft at the revision the
  reader is built with, and the reader warns on every record it reads this way: the warning names
  the draft, the commit and the digest it is pinned to, and says the result is not a
  released-contract result, for example `<type>: warning: schema …/<repo>/main/<file> is an
  unreleased draft (commit <full sha>, sha256 <digest> of those bytes); read against that pinned
  draft, not a released schema`.

V6 exists because FHR 1 (releases up to v0.3.1) told writers to cite the raw-main URL with
`schemaVersion: 1`, and FHR 1 writers commonly wrote `1.0`. When raw-main moved to FHR 2.0 in
v0.4.0, V1 alone made every such file fail on its `schemaVersion`, even when it was valid FHR 1.
The record's own `schemaVersion` says which contract it was written for, and FHR 2.0 requires the
string `"2.0"`, so no record that FHR 2.0 accepts is read differently: V6 only turns a certain
failure into the FHR 1 result. v0.3.0 and v0.3.1 publish the same FHR schema; v0.3.1 is named
as the later release. A reader that predates V6 reports these files as invalid.

Readers use copies of the released schemas (tags are the source) and say which release their
current copy is; they do not fetch schemas at run time. Microdata keeps the raw-main `fhr.json`
URL as its `itemtype` (rule M1 identifies FHR items by it); the `schema` itemprop carries the
versioned URL.

V7 opens a lane beside V1 (#221, decision of 2026-11-13); it adds nothing to V1's list, and a draft
never takes a release form.
A w3id URL `https://w3id.org/fair-bioheaders/<type>/vX.Y.Z` or a raw tag URL naming a release for a
type that no release registers stays "any other value" under V5, as it is today, and a reader must
not read it as the draft: no release number is invented for a draft, and an unpublished type has
no row in `schemas/versions.json` to select. A reader that reports a near-miss schema URL, as
fair-bioheaders 0.10.0 does (Tools#125), keeps doing so for such a value: V7 changes neither that
warning nor the FHR result. Only the raw-main URL of the owning development repository is in the
lane.

A reader that implements the lane ships the draft bytes it recognises and pins them the way this
family pins a copied tree: the commit of the development repository and the SHA-256 of the exact
schema bytes, the pair `header/provenance.json` records for the FHGFF3 development copy and the
digest `scripts/make_cedar.py` writes into every template's provenance line. Selection runs against
the pinned bytes, never against `main` at run time, so a rewrite of a draft cannot move a reading
that claims to be current out of sight; when the bytes a reader holds no longer match the digest it
states, it says so instead of quietly choosing a newer draft.

Publication moves a type out of the lane. The release adds the type's `<file>` to V1 and its row to
`schemas/versions.json`; from then on its released bytes are governed by V1 to V4 and its
`schemaVersion` by the rules above. V7 then stands ready for the next unreleased revision of that
type or of another one; it never reaches released bytes, and nothing published is rewritten: V1 to
V6 keep their text and their outcomes, and V7 is additive. Until a type is registered, reading it
through the lane recognises a proposal, it does not adopt one: a record that cites a draft URL is
experimental, is not a conforming record of a released type, and stays in its own development
repository rather than in this one's examples or vectors.

Two drafts are in the lane today: the transcriptome contract drafted in
[FHT-Specification](https://github.com/FAIR-bioHeaders/FHT-Specification), whose conformance suite
cites `https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`, and the
gene-model records drafted in
[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification) and described in
[FHGM.md](FHGM.md). The rule names neither: it describes the shape of the lane, and any type
repository holding a draft contract is covered the same way. FHGM is the general case worth
stating, because its records carry no `schema` field at all: they ride inside an FHGFF3 header as
extension fields ([FORMAT.md](FORMAT.md) R15), so the file is routed by its own FHGFF3 citation
under V1 to V3 and the lane selects only the contract and the validator that a tool applies to the
records. For a type whose records name no schema, V7 chooses what validates them; it never chooses
what they are.

## Writing files

New files and examples cite the versioned URL of the release they target, preferably the w3id form:

```yaml
schema: https://w3id.org/fair-bioheaders/fhr/v0.6.0
schemaVersion: '2.1'
```

The raw-main URL stays the canonical "current schema" link in documentation. Tools keep a file's
`schema` value as written when they combine, strip or convert it.

## Migrating files that cite raw-main with schemaVersion 1

Such a file is an FHR 1 file, read against v0.3.1 by rule V6 with a deprecation warning. It stays
valid while it is valid FHR 1, but raw-main is the current-schema link, so new and updated files
should cite a versioned URL. No tool rewrites it, because any change to the header changes the
checksum. To clear the warning, choose one:

- **Move to v0.4**: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.4.0` and
  `schemaVersion` to `'2.0'`, fix anything the v0.4 tightening rejects
  ([SCHEMA-CHANGES-v0.4.md](SCHEMA-CHANGES-v0.4.md)), and recompute the checksum.
- **Pin v0.3.1**: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.3.1`, keep
  `schemaVersion: 1`, and recompute the checksum.

With the toolkit and standard shell tools (checked with `bioheaders` 0.8.0 and later):

```bash
grep '^;~' legacy.fa | cut -c3- > metadata.yaml   # recover the YAML header (use '^#~' for GFA)
# edit schema and schemaVersion in metadata.yaml as above
bioheaders strip legacy.fa plain.fa               # output is positional, not -o
bioheaders combine metadata.yaml plain.fa -o genome.fhr.fa   # new checksum
```

With a toolkit that implements V6, `bioheaders convert legacy.fa metadata.yaml` can replace
the first step, since an FHR 1 header now validates. Older toolkits (before V6) reject such a
file with `1.0 is not of type 'string'`; with them, recover the header text with `grep`, edit
it, and recombine.
