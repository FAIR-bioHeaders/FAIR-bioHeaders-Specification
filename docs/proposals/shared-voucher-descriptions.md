# Shared voucher descriptions (draft amendment)

Status: proposed for joint maintainer review; not an adopted schema contract.
Tracks [#139](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/139),
transferred from FHR-Specification #4. This document does not change validation,
release versions or existing files.

## Proposed contract

Keep `voucherSpecimen` optional. Preserve every existing string value verbatim
and with its existing broad meaning. Additionally allow a nonempty ordered list
of voucher description objects. Do not accept a bare object, mixed string/object
lists, nulls or empty lists under this proposal.

Each object has a required, nonempty string `description`, an optional nonempty
string `identifier`, and an optional absolute URI `url`. Objects reject unknown
properties. Identifiers need not be museum accessions or resolvable URLs. Multiple
entries may describe different evidence associated with the same resource; they
do not establish multiple sequenced individuals or pooled sequencing.

A voucher description can concern a population in an area, a preserved specimen,
tissue, a photograph, or representative/proxy evidence. A retained individual,
museum accession and direct use in sequencing are not prerequisites. The core's
current description, "Description of the physical sample", should be expanded to
express this meaning without narrowing legacy text.

Descriptions should state the evidence's role in ordinary language. The initial
proposal adds no controlled entity-kind or relationship vocabulary. Consumers
must not infer that a photograph, proxy voucher or population supplied material
for extraction. Structured relationship predicates can be reviewed separately.

## Illustrative fragments

These are proposal fragments, not complete records valid under current schemas.

```yaml
voucherSpecimen: "Population sampled along the north shore of Example Lake."
```

```yaml
voucherSpecimen:
  - description: "Population sampled along the north shore of Example Lake."
  - description: "Representative preserved specimen supporting identification."
    identifier: "EXM:Mamm:123"
    url: "https://example.org/specimens/123"
```

```yaml
voucherSpecimen:
  - description: "Remaining tissue from the sequenced individual."
    identifier: "lab:tissue-42"
  - description: "Photograph of that individual before DNA extraction."
    url: "https://example.org/images/42"
```

All names, identifiers and URLs above are synthetic.

## Ownership and application across the family

The shared slot and a reusable `VoucherDescription` class belong in
`schemas/core.yaml`. FHR, FHP and FHGFF3 already expose the core slot; coordinate
FHT adoption with its developing contract. The published JSON schemas and LinkML
models must agree on the string-or-list alternative, including list cardinality
and closed objects. Generated schemas must come from their generators.

| Type | Type-specific guidance to review |
| --- | --- |
| FHR | Describe evidence associated with the assembly's biological source, including population/locality cases. |
| FHT | Describe transcriptome source/evidence where known; do not infer pooling from multiple vouchers. |
| FHP | Support predicted, database and mixed-source protein sets without inventing vouchers or direct specimen access. |
| FHGFF3 | Keep voucher evidence distinct from the genome reference and annotation parent-file relationships. |

`derivedFrom` continues to identify parent files. Vouchers do not substitute for
its checksum links or establish material derivation. A child must not silently
copy a parent's voucher into a fresh assertion about the child. Parent evidence
may be displayed with its source clearly identified; missing child vouchers do
not imply missing parent evidence.

## Versioning and preservation

If every previously valid record stays valid with unchanged meaning, adding this
alternative qualifies for a minor contract increment under
[SCHEMA-VERSIONS](../SCHEMA-VERSIONS.md). Review each affected type independently;
FHT's initial contract may incorporate it without inheriting another type's
version. Assign concrete versions only with the implementation/release decision.

Keep immutable released schemas, fixed aliases and existing example/vector bytes
unchanged. Existing strings need no conversion. A record using the new structure
must cite a supporting schema. Editing a file-bound header, including its schema
reference, requires recomputing its checksum; changed parent checksums can also
require updating child links and child checksums.

## Implementation acceptance criteria

- Synchronize the core model, FHR published schema and generated FHP/FHGFF3 schemas;
  coordinate FHT explicitly. Review drift baselines only after inspecting diffs.
- Demonstrate old valid strings remain valid and unchanged; accept description-only
  and identifier/URL entries; reject invalid objects, URIs, scalar types, empty
  lists and mixed lists. Test every affected type, not just FHR.
- Round-trip strings and ordered object lists through each supported serialization.
  Preserve scalar types, Unicode, identifiers and escaping. Report unsupported
  representations rather than flattening objects to text.
- Review canonical JSON-LD contexts/vocabulary and one-way schema.org/DCMI/MIxS
  mappings separately. Preserve legacy literal behavior. Do not map proxy evidence
  to material used for extraction, or claim lossless export without tests.
- Update toolkit and browser readers/forms for both alternatives; distinguish
  structural validation from file or parent verification. Coordinate downstream
  consumers before advertising support.
- Add legacy, population/locality, museum specimen, tissue, photograph, proxy,
  multiple-source and explicit-pooling fixtures. Pooling must be asserted in
  appropriate metadata, never inferred from this list.
- Update type guidance, release notes and version records alongside implementation.

Funding, reuse conditions and broader specimen-database modeling are separate
amendments. This proposal neither adds required metadata nor adopts those changes.
