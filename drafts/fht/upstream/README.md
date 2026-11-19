# FHT-Specification

FHT (FAIR Header Transcriptome) is a FAIR metadata header for reference
transcriptome FASTA files. It records who asserted the metadata, when, for which
taxon, how the transcript set was constructed and how to verify the exact file
bytes. The published paper describes the shared FAIR Header Reference concept:
Wright et al., *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122.

**Status: development contract for review under issue #7.** The LinkML model and
generated JSON Schema implement the design approved for #6. They are not a
published release, not adopted community guidance, and have no default support in the
family toolkit. Released toolkit 0.11.0 can read the revision-pinned development
contract through the opt-in rule V7 lane; this is draft recognition. No release tag, w3id alias, DOI or toolkit support is
established by this repository state. See
[the contract and migration record](docs/FHT-MIGRATION.md).

- Approved Q4/Q8 follow-up: [nonempty metadata values and actual genome extraction](docs/FHT-MIGRATION.md#narrow-q4q8-follow-up-after-51--2026-11-17); taxon rules stay unchanged; supplied `assemblyAuthor` items need a nonblank `name` (merged #52).
- Schema source: [`fht_linkml.yml`](fht_linkml.yml)
- Generated contract: [`fht.json`](fht.json). It is the normative contract:
  validate records with it, not with `linkml-validate` on the model, because the
  generator adds rules LinkML cannot express
  ([details](docs/FHT-MIGRATION.md#contract-version-and-urls)).
- Design and evidence: [`specs/fht-field-decisions.md`](specs/fht-field-decisions.md)
- Minimal and rich designs: [`specs/fht-record-designs.md`](specs/fht-record-designs.md)
- Revised spec 005 proposal: [`specs/005-rna-transcriptome-header/spec.md`](specs/005-rna-transcriptome-header/spec.md)
- Proposed typed HTML: [`docs/FHT-MICRODATA.md`](docs/FHT-MICRODATA.md),
  [seven readable pairs](examples/html/) and a test-only extractor/writer (#11);
  no installed runtime support or shared publication is established.
- Remaining review/publication docket: [`docs/FHT-DECISION-DOCKET.md`](docs/FHT-DECISION-DOCKET.md)
- Legacy draft schema: [`legacy/fht-v0.1.json`](legacy/fht-v0.1.json)

Conversion, validation and checksum computation belong to the family
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools);
FHT support there is pending ([issue #9](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/9)).
The former FHT-File-Converter repository is retired.

## Header shape

FHT uses the family `;~` comment block. The checksum below is a placeholder: real
headers must carry a computed SHA-512/256, never a hand-written or invented
value. See `docs/FORMAT.md` in the shared specification for the exact format and
escaping rules.

```text
;~schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json
;~schemaVersion: "1.0"
;~transcriptome: Bombus impatiens reference transcriptome
;~assemblyType: de novo
;~taxon:
;~  name: Bombus impatiens
;~  uri: https://identifiers.org/taxonomy:132113
;~version: "1.0"
;~metadataAuthor:
;~- name: Example author
;~dateCreated: "2026-10-24"
;~checksum: <computed SHA-512/256>
>transcript_1
ACGTACGT
```

The nine required fields are `schema`, `schemaVersion`, `transcriptome`,
`assemblyType`, `taxon`, `version`, `metadataAuthor`, `dateCreated` and
`checksum`. Optional fields cover biological molecule class, software, sample
context, library strategy/strandedness, run accessions, statistics, BUSCO
completeness, reviewed parent links and shared provenance/identity fields. Omit
unknown optional values. Empty optional values remain accepted under
[D1](docs/FHT-DECISION-DOCKET.md); prefer omission rather than invented
placeholders.

Extension fields: as in FHR 2.1, FHP 1.1 and FHGFF3 1.1 (FAIR-bioHeaders-Specification
`docs/FORMAT.md` rule R15), the draft accepts top-level keys that match
`^x-[A-Za-z0-9][A-Za-z0-9_.-]*$`, for example `x-<project>-<field>`, with any value the
standard does not define. Every other unknown key is still rejected, nested objects stay
closed, and an extension field never replaces a standard field. JSON-LD and HTML forms
leave extension fields out.

### Construction types

| Value | Use case |
| --- | --- |
| `de novo` | Reads reconstructed without a reference genome constructing or grouping the assembly |
| `genome-guided` | Read evidence plus a reference constructed models or grouped reads |
| `annotation-derived` | Sequences extracted from existing annotation coordinates and the matching genome |

A composite or uncertain history is not guessed. The record is incomplete until
the case is reviewed. Genome guidance alone does not justify a `transcribedFrom`
parent link.

## Verify the schema in this repository

```sh
python -m pip install -r requirements-linkml.txt
python -m unittest discover -s tests -v
python json-schema-generator.py
git diff --exit-code fht.json
python scripts/check_provenance.py
```

The tests validate the generated contract, required and optional fields, enum and
numeric constraints, reviewed parent pairs, legacy-compatible fields and exact
generation from the model. `tests/test_examples.py` validates the synthetic
examples in `examples/` (minimal and rich records for every construction type,
in JSON, YAML and embedded-FASTA form) against `fht.json` and recomputes each
FASTA file's SHA-512/256 checksum under the shared FORMAT.md rules. Their names,
statistics and sequence bytes are invented; taxon and ontology identifiers are
real. The byte-exact positive/rejection conformance vectors are in
`conformance/` (issue #8): RNA/cDNA, line-ending, comment, nested-checksum,
gzip/BGZF, parent-link and schema-selection cases with independently
cross-checked checksums — see [`conformance/README.md`](conformance/README.md)
for their scope. Installed-toolkit draft-lane round trips and stream evidence
are described in [the acceptance packet](docs/FHT-READINESS.md); default released
support remains #9.
The historical pre-contract examples are preserved verbatim under
`legacy/examples/` as review inputs, not valid FHT 1.0 fixtures.

Continuous-integration lanes and their local commands — documentation
Markdownlint plus local link/whitespace/conflict checks, the fixture lane
(regeneration determinism and the independent vector/examples reader),
legacy-draft schema health with its defect registry and classified examples,
and the scheduled external-link check — are documented in
[`docs/CI.md`](docs/CI.md).

## Related FHR citations

These DOI records identify FHR resources; they must not be represented as
FHT-specific release DOIs. For FHT-specific citation metadata, use the resource
actually referenced by your work rather than relabeling an FHR DOI.

Chicago bibliography entries are used below. Cite the published paper for a
general description of FHR; cite the specification or converter when using that
resource directly. The software and specification links are concept DOIs; for a
specific release, use the corresponding version DOI from Zenodo. Authors and
years follow the records resolved by the concept DOIs at the v0.3 documentation
update, and can change as later records are published.

### Published paper

Wright, Adam, Mark D. Wilkinson, Christopher Mungall, Scott Cain, Stephen Richards, Paul Sternberg, Ellen Provin, Jonathan L. Jacobs, Scott Geib, Daniela Raciti, Karen Yook, Lincoln Stein, and David C. Molik. “FAIR Header Reference Genome: A TRUSTworthy Standard.” *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122. <https://doi.org/10.1093/bib/bbae122>.

### Specification

Molik, David. *FHR Specification*. Data set. 2022. <https://doi.org/10.5281/zenodo.6762549>.

### Converter

Molik, David, and Adam Wright. *FHR File Converter*. Computer software. 2024. <https://doi.org/10.5281/zenodo.6762547>.

Machine-readable entries are maintained in
[FHR-Citation](https://github.com/FAIR-bioHeaders/FHR-Citation/blob/main/citation.bib).

## Licensing

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

New project contributions from March 2025 onward use [MPL-2.0](LICENSE). David Molik left USDA in February 2025. Historical USDA public-domain material remains public domain within the United States; its original notice is preserved in LICENSE. Previously granted permissions and third-party terms remain intact. The project includes both historical material and subsequent MPL-2.0 contributions; file notices and history identify provenance.

## Draft molecule classification update

[The recorded responses and clarifications](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6928571815)
supersede D1's initial omission of known heterogeneous sets: `mixed` is the fifth,
case-sensitive `moleculeType` value. It denotes producer-supported biological RNA
heterogeneity, not unknown composition, a library preparation, or the alphabet.
This is an additive enum change in the unreleased draft `1.0`, not publication or
joint curator adoption. Four-value readers, including the pinned 0.11.0 draft
reader, reject this newly valid value and need an explicit future consumer update.
The three construction values, nine required fields and existing taxon members
are retained. The ordered `sample` array remains; BioSample URLs belong in
`relatedLink`, following FHR. Describe protocol/kit information in `documentation`
and put actual protocol URLs in `relatedLink`; no protocol/kit field is added,
and `libraryStrategy` is not overloaded. Current statistics, parent behavior and
field names remain. No new required URI, sample deprecation or mixed construction
value is authorized. Publication and joint review remain separate gates.

See [mixed-molecules](examples/mixed-molecules.fht.yaml) and the
[prepublication evidence](docs/FHT-READINESS.md).
