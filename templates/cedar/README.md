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

One versioned template per released header type at the **current**
`schemaVersion` named by [`schemas/versions.json`](../../schemas/versions.json):

| File | Type | Contract `schemaVersion` | Pinned schema URL |
| --- | --- | --- | --- |
| [`fhr.json`](fhr.json) | FHR | 2.1 (v0.5.0) | `https://w3id.org/fair-bioheaders/fhr/v0.5.0` |
| [`fhp.json`](fhp.json) | FHP | 1.1 (v0.5.0) | `https://w3id.org/fair-bioheaders/fhp/v0.5.0` |
| [`fhgff3.json`](fhgff3.json) | FHGFF3 | 1.1 (v0.5.0) | `https://w3id.org/fair-bioheaders/fhgff3/v0.5.0` |

FHT is **not** represented: its family schema is not released and it is absent
from the registry, so per #162 it stays explicitly deferred until
FHT-Specification#8/#9/#10 and FAIR-bioHeaders-Specification#157 are resolved.
No legacy FHT draft fields are presented here as adopted.

Each template is generated, never hand-edited. It is derived from the same
committed schema bytes the website reference pins (verified by SHA-256:
`tests/test_cedar.py` and `scripts/make_cedar.py --check` recompute the digest
of the working-tree schema), and each template's own description records its
target `schemaVersion`, the fixed contract URL and the **SHA-256 of the source
schema file** — the same digest-pinning discipline this repository applies to
`FHGFF3 header/provenance.json` and the website's `schema-snapshots/`.

## Extension fields are omitted on purpose

Since v0.5.0 the contracts accept top-level keys matching
`^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` (docs/FORMAT.md R15). These templates
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
if an `x-` key ever reaches a template.

## How to regenerate

```sh
python scripts/make_cedar.py           # rewrite templates/cedar/*.json
python scripts/make_cedar.py --check   # drift check (what CI runs)
```

The generator uses only the standard library and never the network. When a
schema release changes a contract, `--check` and `tests/test_cedar.py` fail on
the digest/provenance mismatch, and the templates are regenerated on the
release's own review cycle. A template whose `pav:version` is
`<schemaVersion>.0` tracks its contract; the emitted shape is the CEDAR
template JSON-LD format 1.6.0 (per the meta-schemas and reference templates in
[`cedar-model-validation-library`](https://github.com/metadatacenter/cedar-model-validation-library)).

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
checksum and unanswered optional values, but retains supplied nested parent
checksums such as `derivedFrom[].checksum`. The resulting unbound metadata is
not yet a complete contract instance because the root checksum is required.
`bioheaders combine` is the supported pre-binding step: it computes that root
checksum over the exact file bytes and validates the bound header. Do not run
`bioheaders validate` on fresh, unbound metadata or enter a checksum by hand;
validate and verify the resulting bound file as shown above. The toolkit remains
the validator and writer, while `flatten_export` only restores the record shape.

Known form limits, stated rather than hidden: the FHP `geneticCode` numeric
input cannot block the contract's range gaps (1-6, 9-16, 21-33 — only
validation can); the FHGFF3 "annotates at most once / genome link
alternative" conditionals are enforced by the schema, not the form; the FHR
`assemblySoftware` legacy string alternative is not offered; and identifier
fields carry their schema patterns plus authority guidance in help text, but
no live CEDAR terminology-server bindings (that enrichment belongs to the
published instance, if maintainers choose it).

## What this directory is not

- **Not a CEDAR publication.** Publishing to a real CEDAR workbench — the
  instance, account, ownership, review of wording and assignment of CEDAR
  artifact/property URIs — is a **separate maintainer action, deliberately not
  done here** (#162 open question). The generated `@id`s are null, the
  `pav`/`oslc` stamps empty and the status is `bibo:draft`; the synthetic
  `https://w3id.org/fair-bioheaders/templates/cedar/<type>#…` property URIs
  exist only to make generation deterministic and say nothing about
  publication.
- Not a new contract, version or release: nothing here changes a schema, a
  `schemaVersion` or `schemas/versions.json`.
- Not a feature/biology validator for GFF3 content: that is `gff3-validator`.

Licence: MPL-2.0, as the repository LICENSE.
