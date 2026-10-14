# Research: Schema versions and schema selection

**Feature**: 012-schema-versioning | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

Each decision records the choice, why, and what else was considered.

## D-01 `schemaVersion` is a `"MAJOR.MINOR"` string

**Decision**: A JSON string matching `^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`, set in the shared core
(`schemas/core.yaml`). Each header type pins its accepted values with an enum.

**Rationale** (Adam, 2026-10-14):
- a string has no float ambiguity: `"2.10"` and `"2.1"` are different versions, while the numbers
  2.10 and 2.1 are equal;
- DataCite (`schemaVersion` in its XML and JSON) and schema.org (`schemaVersion`, range Text)
  treat schema versions as text;
- tools that write YAML quote the value, so hand-written headers are the only place where
  `2.0` must be written `"2.0"`.

**Alternatives**: a number (`2.0`, `2.1`…), which breaks at minor 10 and loses the distinction
between `2` and `2.0`; an integer major only, which cannot express minor changes (rejected by
David's request).

## D-02 Major and minor

**Decision**: As FR-002. A change is major when some instance valid before is invalid after, or a
valid value changes meaning. It is minor when every instance valid before stays valid with the same
meaning and something new becomes allowed. Changes that alter no validation outcome do not bump the
version. Removing a deprecated optional field is major.

**Rationale**: This is the compatibility definition the constitution (principle II) already uses,
and it is the usual semantic-versioning reading for data contracts (SchemaVer's MODEL/REVISION
split, minus ADDITION, which FHR does not need with closed objects).

**Alternatives**: SchemaVer `MODEL-REVISION-ADDITION` (three parts; more than FHR needs);
calendar versions (do not express compatibility).

## D-03 FHR v0.4 is 2.0; FHP and FHGFF3 start at 1.0

**Decision**: FHR `"2.0"`; FHP `"1.0"`; FHGFF3 `"1.0"`.

**Rationale**: The v0.4 tightening (#35) rejects previously valid values (unanchored patterns,
44 `=` checksums, typo keys in nested objects), so it is major. The additive changes on the same
line (`nameType`, scaffold statistics) do not need a separate minor version because nothing has
been released between them. FHP and FHGFF3 have never been released, so their first contract is
1.0 (Adam).

## D-04 The version registry `schemas/versions.json`

**Decision**: A small JSON file:

```json
{
  "current": "v0.4.0",
  "releases": {
    "v0.3.0": {"FHR": 1},
    "v0.3.1": {"FHR": 1},
    "v0.4.0": {"FHR": "2.0", "FHP": "1.0", "FHGFF3": "1.0"}
  }
}
```

`current` names the release the working tree's schemas belong to: the release being prepared on a
release line, or the latest release on `main`. Legacy releases keep the value as published (the
number 1).

**Rationale**: The rule needs data that tools and the website can read without parsing prose; a
test keeps it equal to the schemas' enums (SC-001). It also tells `check_conformance.py` which
release the working tree stands for before the tag exists.

**Alternatives**: deriving versions from tags at run time (needs git and tags everywhere; no
answer before tagging); prose only (not checkable).

## D-05 The selection rule

**Decision**: The table in [contracts/schema-selection.md](contracts/schema-selection.md):
1. raw-main `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/<file>`
   → current schema of the file's type;
2. raw tag `…/FHR-Specification/vX.Y.Z/<file>` or w3id
   `https://w3id.org/fair-bioheaders/<type>/vX.Y.Z` (optional trailing slash) → that release's
   schema of the type;
3. a raw URL with any other ref, a release the reader does not have, or a release without that
   type → unsupported-version;
4. any other value → FHR, current schema.

Files: `fhr.json` (FHR), `fhp.json` (FHP), `fhgff3.json` (FHGFF3); w3id types `fhr`, `fhp`,
`fhgff3`.

**Rationale**: Rules 1–3 are David's decision. Rule 4 is today's behaviour for the FHR `schema`
field, which has never been constrained; constraining it would be a separate schema decision.
Branch and commit refs are refused because no reader can know which schema they meant without
fetching, and fetching is out of scope.

**Alternatives**: treating unknown releases as current (silent substitution, ruled out); fetching
unknown versions online (network, availability and trust problems; not offline); recognising the
w3id PATH form `…/fhr/vX.Y.Z/fhr.json` (an extra spelling with no benefit; documented as not a
schema URL).

## D-06 Raw-main means current; no v0.3.1 fallback

**Decision**: A file that cites raw-main is checked against the current schema. Once the current
FHR schema is 2.0, a raw-main file with `schemaVersion: 1` fails, with the ordinary schemaVersion
error.

**Rationale**: David, #44: v0.3.1 has no users whose files need preserving; raw-main is the
current canonical schema.

## D-07 Released schemas come from tags; tools bundle copies

**Decision**: The specification repository stores no copies. `check_conformance.py --schema` gets a
released schema from the working tree when the release is the registry's `current`, and otherwise
with `git show <tag>:<file>`; the CI checkout fetches tags. The toolkit bundles each distinct
released schema once, named by type and version (`fhr-1.json`, later `fhr-2.0.json`), with a
registry recording tag, file and SHA-256.

**Rationale**: Tags are immutable sources; bundling keeps tools offline (constitution V).

**Alternatives**: copies under `schemas/released/` in this repository (duplicates the tags and can
drift); fetching from w3id at run time (network).

## D-08 Microdata, JSON-LD and the mapping table

**Decision**:
- Microdata keeps `itemtype` = the raw-main `fhr.json` URL (rule M1 identifies FHR items by it); the
  `schema` itemprop carries the versioned URL; `schemaVersion` is written with
  `data-fhr-type="string"`.
- JSON-LD keeps the literal term `fhr:schemaVersion`; the vocabulary's range becomes `sdo:Text`
  (generated from the LinkML range).
- The mapping table's `schemaVersion` notes say it is a string.

## D-09 Toolkit rollout (one draft PR)

**Decision**:
1. **Now, on toolkit `main`**: the selection rule, unsupported-version results and the bundled
   v0.3.0/v0.3.1 FHR copy. The current copies stay equal to FHR-Specification `main`, so
   `check_release.py` on `main` still passes and FHR results do not change for raw-main files.
2. **Prepared as a draft**: the v0.4 copies (current FHR 2.0, FHP 1.0, FHGFF3 1.0, registry with
   `v0.4.0`), examples and fixtures. It merges when FHR-Specification v0.4.0 is released.

*As implemented:* the two steps are one draft PR (FAIR-bioHeaders-Tools#57). Step 1 alone would
already disagree with spec `main`: its `jsonld-schema-versioned-url` vector cites `fhr/v0.4.0`,
which a toolkit without v0.4.0 must report as unsupported.

**Rationale**: The toolkit's `main` must stay consistent with the specification's `main`, which
keeps v0.3 schemas until the release. Release-line CI needs a converter that knows 2.0, so it
installs the draft branch by pinned commit until a toolkit release has it (as gff3-validator did
for FHGFF3).

## D-10 Migration

**Decision**: No automatic rewrite. A file citing raw-main with `schemaVersion: 1` either:
- moves to v0.4: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.4.0` and
  `schemaVersion` to `"2.0"`, fix anything the tightening rejects, and recompute the checksum
  (`bioheaders convert file.fa meta.yaml`, edit, `bioheaders strip`, `bioheaders combine`); or
- pins v0.3.1: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.3.1` and recompute the
  checksum.

Both change header bytes, so the checksum must be recomputed; that is why tools must not do it
silently.
