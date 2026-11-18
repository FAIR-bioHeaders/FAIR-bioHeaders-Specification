# CEDAR authoring templates

CEDAR (<https://metadatacenter.org/>) is a metadata-authoring workbench: a
template gives a curator a guided web form with field help, requiredness and
controlled values, and an exported record afterwards. **These templates are
authoring aids, not contracts.** The published JSON Schemas —
[`fhr.json`](../../fhr.json), [`fhp.json`](../../fhp.json),
[`fhgff3.json`](../../fhgff3.json) — remain the validation authority and the
[`fair-bioheaders` toolkit](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)
remains the validator and writer. The form never relaxes, adds to or replaces
the contract (FAIR-bioHeaders-Specification#162).

## What is here

One versioned template per header type. The three **released** types target the
**current** `schemaVersion` named by
[`schemas/versions.json`](../../schemas/versions.json); the two **draft** types
are generated from byte-pinned development snapshots and are labeled DRAFT
throughout (see [Draft templates](#draft-templates--fht-and-fhgm) below):

| File | Type | Status | Contract `schemaVersion` | Pinned schema URL |
| --- | --- | --- | --- | --- |
| [`fhr.json`](fhr.json) | FHR | released | 2.1 (registry `v0.6.0`) | `https://w3id.org/fair-bioheaders/fhr/v0.6.0` |
| [`fhp.json`](fhp.json) | FHP | released | 1.2 (registry `v0.6.0`) | `https://w3id.org/fair-bioheaders/fhp/v0.6.0` |
| [`fhgff3.json`](fhgff3.json) | FHGFF3 | released | 1.2 (registry `v0.6.0`) | `https://w3id.org/fair-bioheaders/fhgff3/v0.6.0` |
| [`fht.json`](fht.json) | FHT | **draft** | 1.0 (draft, unreleased) | `https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json` |
| [`fhgm.json`](fhgm.json) | FHGM | **draft** | model contract v0.1 (proposal) | none — an FHGM record carries no schema URL |

`v0.6.0` is published and is the registry's `current`; the templates track `versions.json` exactly, which is
what `scripts/make_cedar.py --check` verifies.

Each template is generated, never hand-edited. Released templates are derived
from the same committed schema bytes the website reference pins (verified by
SHA-256: `tests/test_cedar.py` and `scripts/make_cedar.py --check` recompute
the digest of the working-tree schema). Draft templates are derived from
byte-pinned snapshots under [`drafts/`](drafts/) with a provenance record of
repository, branch, commit, SHA-256, git blob hash and retrieval date — the
same digest-pinning discipline this repository applies to `FHGFF3
header/provenance.json` and the website's `schema-snapshots/`. Either way, each
template's own description records its target `schemaVersion`, the fixed
contract URL and the **SHA-256 of the source schema bytes** it came from.

## Draft templates — FHT and FHGM

Maintainer decision of 2026-11-13 ("CEDAR will expand to include FHGM and FHT")
supersedes the earlier FHT-deferred posture of #162: guided authoring now also
exists for the two draft contracts, **clearly labeled as drafts**. The
released-types list above is unchanged; no draft template joins it until its
contract is actually published.

Filling a draft form can produce records that the eventual released contract
**changes or rejects**. The draft schema bytes are the only authority for what
a draft accepts today, and drafts move: field names, requiredness, patterns
and meanings are still under curator review. FHGM's `modelVersion` is deliberately opaque through v0.x by the
[recorded review disposition](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/8#issuecomment-6881802036):
equality/difference only, with no ordering implied. This is settled baseline
behavior, not a pending choice of version syntax. FHT's dotted BUSCO lineage
grammar is already in this pinned snapshot (#170 is completed); its publication
and concrete curator acceptance remain separate. Treat draft-form outputs as
provisional and validate against the exact contract supported by the chosen
writer. The form pin and an installed writer's draft pin can differ.

**FHT** ([`fht.json`](fht.json)) is generated from the FHT-Specification draft
contract (`fht.json` on `main`; snapshot
[`drafts/fht.schema.json`](drafts/fht.schema.json)). The record's `schema`
field is pinned to `https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`
— the only FHT contract URL that exists. **No w3id URL exists for FHT and none
is invented here**: a draft template contains no `w3id.org` URL at all, and
`tests/test_cedar.py` fails if one ever appears. Promotion to a released-type
template happens with the FHT release itself (FAIR-bioHeaders-Specification#107
lane F, FHT-Specification#8/#9/#10).

**FHGM** ([`fhgm.json`](fhgm.json)) is generated from the native FHGM model
contract v0.1 in FHGM-Specification (`development/model/fhgm-model.schema.json`
at the commit recorded in
[`drafts/provenance.json`](drafts/provenance.json); proposal under
FAIR-bioHeaders-Specification#204, Option C). The shape difference from the
other four templates is deliberate and fundamental: **an FHGM record is a model
record, not a file header.** It has no `schema`, `schemaVersion` or `checksum`
field. The template authors exactly **one** model record; the transport is:

1. validate the standalone record against
   [`drafts/fhgm-model.schema.json`](drafts/fhgm-model.schema.json) using a
   Draft 2020-12 validator with format checking,
2. embed it as one item of the `x-fhgm-models` array in a **valid released
   FHGFF3 1.1 or 1.2 header**, retaining that carrier's paired schema URL/version (docs/FORMAT.md R15 transport — the extension never overrides a
   standard field),
3. recompute the enclosing file's checksum with `bioheaders combine` — the file
   checksum covers every embedded record byte like any other header byte, and
   any later record edit invalidates it,
4. run the owning FHGM-Specification's
   `development/model/validate_fhgm.py` on the bound FHGFF3 file. Supply the
   registered released base schemas; its `base-schemas.json` resolves the
   carrier's declared base and prints the selected release. Repeat
   `--base-schema` to provide both candidates; supply any predecessor snapshots
   explicitly through `--predecessor`.

```sh
git -C /path/to/FAIR-bioHeaders-Specification show v0.5.0:fhgff3.json > /tmp/fhgff3-v0.5.0.json
git -C /path/to/FAIR-bioHeaders-Specification show v0.6.0:fhgff3.json > /tmp/fhgff3-v0.6.0.json
python /path/to/FHGM-Specification/development/model/validate_fhgm.py \
  --base-schema /tmp/fhgff3-v0.5.0.json --base-schema /tmp/fhgff3-v0.6.0.json \
  bound.fhgff3.gff3
```

Use root-level release files, not `schemas/fhgff3.json` or floating main. The
checker's registered hashes must match those released bytes. Base selection is
implemented, not a request for curators to choose one universal carrier.

Model **resolution** (feature-target matching, predecessor-pointer verdicts,
reference agreement with the file header) is a draft checker rule set in
FHGM-Specification, **not a toolkit feature yet**. Promotion of the FHGM
template follows actual shared publication under #204; the publication direction
is already adopted. Merging readiness proposals does not publish the model.

## Extension fields are omitted on purpose

Since v0.5.0 the contracts accept top-level keys matching
`^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` (docs/FORMAT.md R15). The FHT **draft** schema
defines the same open slot natively as a JSON Schema `patternProperty`
(FHT-Specification#24) rather than through the released R15 contract; the
rationale is identical, so the draft FHT template omits it too. These templates
intentionally contain **no `x-` fields and no placeholder for them**:

- an extension means nothing to the standard, so a form cannot give it field
  help, a type or requiredness without inventing meaning;
- a guided surface should not invite values that no validator checks.

The templates pin the **current** schema URL and `schemaVersion`; omitting
extensions does not make an export valid under a previous release. Older
schemas may reject those newer identity values. To target an older release,
change both `schema` and `schemaVersion` to values accepted by that release,
then validate against its schema. These templates do not perform that
downgrade.

Curators who need extensions edit YAML directly; `tests/test_cedar.py` fails
if an `x-` key ever reaches a template. (The FHGM draft template authors
records that *become* the `x-fhgm-models` payload at file level — the form
still contains no `x-` key itself, because the array lives in the FHGFF3
header, not in the record.)

## How to regenerate

```sh
python scripts/make_cedar.py           # rewrite templates/cedar/*.json
python scripts/make_cedar.py --check   # drift check (what CI runs)
```

The generator uses only the standard library and never the network: it reads
the committed schemas and the pinned snapshots in [`drafts/`](drafts/). When a
schema release changes a contract, `--check` and `tests/test_cedar.py` fail on
the digest/provenance mismatch, and the templates are regenerated on the
release's own review cycle. For the **drafts**, `--check` is offline and
compares only against the local snapshot: it fails when a snapshot under
[`drafts/`](drafts/) is edited without updating
[`drafts/provenance.json`](drafts/provenance.json), but it never sees new
commits in FHT-Specification or FHGM-Specification. Nothing in this repository
watches those upstreams for schema changes; upstream drift is noticed by a
maintainer comparing the recorded commit with the owning repository's `main`
and re-pinning deliberately (snapshot and provenance together, against a named
commit — draft bytes are cited, never paraphrased). The CI owning-checker run
uses the separate FHGM checker commit recorded in `provenance.json` and asserts
that its model schema is byte-identical to the snapshot, so it too says nothing
about newer upstream commits. `--check` also reports any extra top-level
`*.json` in this directory as drift (delete it, or add its type to the
generator): every template here must be one the generator produces. A
template's `pav:version` is `<schemaVersion>.0` and tracks its contract; the
emitted shape is the CEDAR template JSON-LD format 1.6.0 (per the meta-schemas
and reference templates in
[`cedar-model-validation-library`](https://github.com/metadatacenter/cedar-model-validation-library)).
`tests/test_cedar_meta_schema.py` validates every template against that
library's template, element and field meta-schemas, vendored with their licence
in `tests/fixtures/cedar-meta-schemas/` at commit `34e65d2`. Those meta-schemas
reserve child names beginning with `schema`, `xsd`, `pav`, `oslc`, `rdfs` or
`skos`, so the form names the contract's `schema` and `schemaVersion` fields
`header_schema` and `header_schemaVersion`; each field's `schema:name` and
`flatten_export` keep the contract names.

A contract URI field constrained only by `format: uri` (`relatedLink`,
`assemblyProtocol`, `accessionID.url`, software and evidence `uri`, and the
like) is a CEDAR **link** field: the workbench checks that the value is a
well-formed absolute IRI and exports it as `{"@id": …}`, which `flatten_export`
reads back as the plain string. URI fields that also carry a `pattern` — the
identifiers.org `taxon.uri` and the ORCID `uri` of authors and contributors —
stay text fields with the contract's regex, because CEDAR's IRI-field value
constraints (`iri-field-meta-schema.json`) have no `regex` key and a link field
would drop the pattern. CEDAR's IRI check is not the JSON Schema `uri` format
check (it admits non-ASCII IRIs, for one), so the toolkit stays the validator.
`tests/test_cedar.py` checks every leaf field's value constraints (literals,
regex, numeric type and bounds, date type, link type and requiredness) against
its contract node for all five templates.

## From a filled form to a bound header — the round trip is mandatory

A CEDAR export is an artifact instance with JSON-LD wrappers
(`{"@value": …}`, `@context`, provenance keys), **not** yet a header record.
Flatten it to prepare the metadata for binding:

```sh
python scripts/make_cedar.py --flatten cedar-export.json > record.json
bioheaders combine record.json data.fa -o data.fh.fa
bioheaders validate data.fh.fa
bioheaders verify data.fh.fa
```

Leave the root checksum blank in the form. `flatten_export` omits an empty root
checksum and unanswered optional values, including optional elements whose
members were all left blank and optional multiple-value fields with no filled
entry (blank entries in a partly filled list are dropped). It keeps an
unanswered required value for the validator to judge, and retains supplied
nested parent checksums such as `derivedFrom[].checksum`. The resulting unbound metadata is
not yet a complete contract instance because the root checksum is required.
`bioheaders combine` is the supported pre-binding step: it computes that root
checksum over the exact file bytes and validates the bound header. Do not run
`bioheaders validate` on fresh, unbound metadata or enter a checksum by hand;
validate and verify the resulting bound file as shown above. The toolkit remains
the validator and writer, while `flatten_export` only restores the record shape.
A malformed export is refused rather than half-read: an object or list where a
field value belongs, or a numeric value that does not parse as its declared
datatype (such as `"2.5"` for `xsd:long`), makes `flatten_export` raise
`ValueError` naming the field path (for example `vitalStats.N50`), and
`--flatten` prints that message and exits 1.

Draft caveats on this path:

- **FHT:** the released toolkit (`fair-bioheaders` 0.11.0 and later) binds and
  checks FHT in the V7 draft lane. Opt in for every command; the default still refuses FHT:

  ```sh
  BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders combine record.json transcripts.fa -o transcripts.fht.fa
  BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders validate transcripts.fht.fa
  BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders verify transcripts.fht.fa
  ```

  This proves experimental draft processing, not an FHT release or curator
  acceptance. Each toolkit release bundles its own pinned FHT draft: 0.11.0
  bundles `11c69d66…`, which accepts the common `diptera_odb10` example but
  rejects `diptera_odb10.1`; 0.12.0 bundles `59ad9641…`, byte-identical to this
  CEDAR snapshot, which accepts both. The CI pin and its bundled FHT digest are
  recorded together in [`conformance/toolkit-pin.json`](../../conformance/toolkit-pin.json).
  Compare digests before claiming that a toolkit covers every template value;
  a successful common-value round trip does not show it. Keep an unsupported
  export unbound; do not silently rewrite a lineage or invent a checksum.
- **FHGM:** the flattened output is one **model record** to embed per the
  [transport steps above](#draft-templates--fht-and-fhgm), never a standalone
  `bioheaders combine` input. `flatten_export` recognizes an FHGM export by
  its required record keys because it carries no schema URL.

Known form limits, stated rather than hidden: the FHP `geneticCode` numeric
input cannot block the contract's range gaps (1-6, 9-16, 21-33 — only
validation can); the FHGFF3 "annotates at most once / genome link
alternative" conditionals are enforced by the schema, not the form; the FHR
`assemblySoftware` legacy string alternative is not offered; the FHT draft's
sample at-least-one-of and derivedFrom relationship pairings, and the FHGM
draft's reference choose-one and `minProperties` conditions, are likewise
schema/checker rules the form only states in help text; and identifier fields
carry their schema patterns plus authority guidance in help text, but no live
CEDAR terminology-server bindings (that enrichment belongs to the published
instance, if maintainers choose it).

## Reproducible workflow checks

```sh
python scripts/make_cedar.py --check
python -m unittest discover -s tests -p 'test_cedar.py' -v
CEDAR_TOOLKIT=/path/to/installed-toolkit/bin/bioheaders \
  CEDAR_FHGM_ROOT=/path/to/FHGM-Specification \
  python -m unittest discover -s tests -p 'test_cedar_toolkit.py' -v
```

The five existing templates regenerate deterministically. Filled exports flatten
without changing values, scalar types, array order or nested parent checksums.
Installed-toolkit checks run outside the checkout, bind the three released
headers plus opt-in FHT, validate/verify them, read metadata back and strip the
exact original payload. FHGM checks validate one standalone record, preserve it
inside both released FHGFF3 carriers, and invoke the owning model checker with
both registered bases. The tests confirm that base/checksum success alone does
not establish model-level validity. No reference-sequence, feature/biology,
curator acceptance or live CEDAR validation is performed by these checks.

Without `CEDAR_TOOLKIT`, installed integration is explicitly skipped. Without
`CEDAR_FHGM_ROOT`, owning model resolution is explicitly skipped; successful
carrier checks must never be reported as model conformance. The shared CI runs
the installed checks with the toolkit release pinned in
`conformance/toolkit-pin.json`, and runs the owning FHGM model check against a
checkout of FHGM-Specification at the commit recorded once in
[`drafts/provenance.json`](drafts/provenance.json) (`snapshots.fhgm.ownerChecker`),
whose model schema is byte-identical to the pinned snapshot.

## Promoting a draft template

Promotion follows actual shared publication, never just the already-recorded
adoption decision. For FHT, its published contract and registry entry precede
moving it from `DRAFT_TYPES` to `TYPES`, retiring its draft snapshot/provenance,
regenerating, and updating draft-status/no-w3id/coverage tests. Keep field shapes
and checksum handling under the publication review.

FHGM is a model record rather than a header family. Its publication must provide
the appropriate model-contract identity and template packaging; do not apply the
header-registry recipe mechanically or add `schema`, `schemaVersion`, checksum,
a registry row or a fabricated URL to an authored model record. Retain the
current pinned draft template until that publication work is reviewed.

## What this directory is not

- **Not a CEDAR publication.** Publishing to a real CEDAR workbench — the
  instance, account, ownership, review of wording and assignment of CEDAR
  artifact/property URIs — is a **separate maintainer action, deliberately not
  done here** (#162 open question). The generated `@id`s are null, the
  `pav`/`oslc` stamps empty and the status is `bibo:draft`; the synthetic
  property URIs (`https://w3id.org/fair-bioheaders/templates/cedar/<type>#…`
  for released types, a GitHub path base for the draft types) exist only to
  make generation deterministic and say nothing about publication.
- Not a new contract, version or release: nothing here changes a schema, a
  `schemaVersion` or `schemas/versions.json`. The draft templates cite draft
  schemas owned by FHT-Specification and FHGM-Specification; they adopt nothing.
- Not a feature/biology validator for GFF3 content: that is `gff3-validator`.

Licence: MPL-2.0, as the repository LICENSE.
