# Mapping v1: assembly descriptive foundation

**Adopted; the “official” label is withheld until an exporter ships.** The
[scope-down decision](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56#issuecomment-6829221221)
and [adoption decision](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-6880245660)
cover the existing root-field inventory, separate supplemental context and curated
qualified-DCMI fixture. They do not adopt six complete target adapters.
[#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56)
remains open for the scoped implementation/shipment handoff and documentation.

## Identity, compatibility and available artifacts

“Mapping v1” names the adopted scope, not a new serialized profile identifier.
The existing context `profileVersion: "0.1.0-draft.1"`, schema `$id` and paths under
`mappings/proposals/` are retained for compatibility. The word `draft` in that
legacy token does not undo adoption; adoption does not publish an exporter,
assign a new profile release, or authorize an “official” claim. No FH* schema,
field, requiredness, vocabulary or contract version changes here.

| Artifact | Scope |
| --- | --- |
| [Root inventory](../../mappings/proposals/assembly-dcmi.yml) | Every FHR v0.4.0 root field has a conditional handling rule or explicit non-projection reason. Nested values remain in the preserved source. |
| [Context schema](../../mappings/proposals/assembly-export-context.schema.json) | Supplemental assertions with fixed identity and conflict rules; separate from the FHR header. |
| [Delivery/status record](../../mappings/proposals/profile-status.yml) | Adopted foundation, withheld official label, implementation handoff and deferred target work. |
| [Rich source/context/graph/report](../../tests/fixtures/mapping-proposal/) | Independently curated semantic expectation, not output of a shipped exporter. |
| [Minimal companion](../../tests/fixtures/mapping-proposal/minimal/) | Explicit title and separate creators; absent publisher/issue date/DOI stay absent. |
| [Metadata-only reference](../../tests/fixtures/mapping-reference/) | A reference to a resource held elsewhere, not a complete FHR header or verified sequence. |

The existing [canonical JSON-LD/DCMI table](../../mappings/fhr-jsonld-dcmi.yml),
[MIxS projection](../MAPPINGS.md) and [schema.org export](../SCHEMAORG-EXPORT.md)
remain separate. Do not edit their terms or use lossy Simple DC as an intermediate
store. The adopted assembly foundation supports **FHR v0.4.0 / schemaVersion
`"2.0"` only**. Newer FHR releases, FHP, FHGFF3 and future FHT/FHGM mappings need
explicit scope review; their existence does not widen this profile automatically.

## Resource subjects and conservative handling

Keep the assembly, metadata record, related publication and specification/software
as distinct subjects. The assembly and metadata record require distinct IRIs.

- `assemblyAuthor` creates generic `dcterms:Agent` nodes for the assembly;
  `metadataAuthor` creates them for the separately identified metadata record.
  Preserve full names, identifiers, order and `nameType` in the source. Do not
  split names or infer Person/Organization classifications in the graph.
- `dateCreated` is assembly creation. Only explicit context `publicationDate`
  produces `dcterms:issued`; `publicationYear` is preserved context and checked
  for agreement when both are supplied, not substituted for a missing date.
- `title` comes from context. `genome` is not a title fallback. A source version
  string does not establish a resource-valued `hasVersion`/`isVersionOf` relation.
- A supplied taxonomy IRI becomes a subject; protocol and generic links remain
  generic relations. An article DOI is a relation to the article, never the
  assembly's DOI. No link is fetched or classified by an exporter.
- Supplied rights text becomes a labelled `dcterms:RightsStatement`; it is not
  silently promoted to a license URI or replaced by the software's license.
- Source `schema` constrains the metadata record, not the assembly. File checksum
  and SeqCol remain source assertions, not registered identifiers or verified
  digests merely because metadata was exported.

The inventory's unsupported root fields remain explicitly unprojected. In
particular, the accession repository name does not supply an accession, funding
text does not supply grant roles, and metrics/software structures retain their
values and types in the source. Conditional terms do not declare unconditional
SKOS equivalence or change the canonical context.

## Context checking and conflict policy

The context requires `profileVersion`, `resourceKind: "assembly"`, `resourceIRI`,
`metadataRecordIRI` and a nonblank title. Publisher, publication date/year and
resource DOI are optional **known** assertions. Unknown values are omitted;
null/empty assertions and undeclared context keys are rejected.

The checker accepts the fixed source citation aliases listed in
[`check_mapping_context.py`](../../scripts/check_mapping_context.py), rejects
other types/releases/raw-main citations, duplicate JSON properties and non-JSON
numeric constants, and checks context without rewriting either input. It rejects:

- equal assembly/metadata-record IRIs;
- conflicting publication date and year;
- an assembly DOI or DOI-resolver resource IRI identifying the source's article.

DOI scope comparisons are case-insensitive and recognize HTTP(S) `doi.org` /
`dx.doi.org` resolver paths, including percent escapes, without resolving them.
No conflicting value silently wins. The helper checks context/identity only;
it does **not** validate source conformance, verify a sequence, export a graph or
assess a registration/deposit. The Tools exporter must independently validate
its source against the fixed released contract before projecting it.

```sh
python scripts/check_mapping_context.py tests/fixtures/mapping-proposal/context.json \
  --source tests/fixtures/mapping-proposal/source.json
python -m unittest discover -s tests -p test_mapping_proposal.py -v
```

## Tools exporter handoff

The [handoff contract](EXPORTER-HANDOFF.md) defines the existing fixture semantics,
complete source/context preservation, expected omissions and required negative
controls. Implement one deterministic **qualified DCMI descriptive** exporter in
Tools; do not recreate canonical JSON-LD, MIxS or schema.org export.

A projection bundle must retain the complete parsed source/context, including
ordered arrays and typed nested values, alongside graph and report. Preserve
original input bytes when copying named sidecars; do not claim reformatted JSON
is byte-identical. The graph alone loses ordering, classification and nested
structure. Its loss report and the source/context remain necessary even when
an RDF parser accepts the graph. No reverse mapping is defined.

The shared graph fixtures are independent semantic expectations. An exporter
must match their RDF meaning and produce repeatable output bytes for the same
inputs. A passing checked-out script is not installed-toolkit acceptance; the
consumer must verify its installed wheel and package the required mapping data.
Exporter merger, package shipment and applying the official label are separate
records. This document makes none of those claims.

## Metadata-only source references

A [public NCBI metadata snapshot](../../tests/fixtures/mapping-reference/README.md)
shows how to record an accession-bearing assembly reference without obtaining its
sequence. Keep repository release dates and submitter roles as supplied; neither
is automatically publication date or assembly creator. Missing roles, DOI and
version details stay identified as gaps.

Recording a landing/source URL does not archive the resource or promise future
persistence. Without sequence bytes it establishes no exact file checksum,
SeqCol digest or verified parent-file identity. This reference example cannot be
passed to the assembly exporter as though it were a complete FHR source. It is
foundation documentation, not a dataset pilot, deposit or publisher integration.

## Deferred targets and completion boundary

The [status record](../../mappings/proposals/profile-status.yml) keeps DataCite,
Crossref, ARK, BibTeX/BibLaTeX visible as **deferred**, not implemented v1 targets.
EZID serializations build on those target profiles and are also deferred. Their
candidate versions are research references, not claims of target validation or
endorsement. Deep nested/per-target crosswalks, registration schemas, resolver
policies, ANVL, citation rendering and family extensions belong to separately
reviewed follow-ups; the old six-target checklist is not v1 acceptance.

To finish the scoped #56 handoff: merge the owning artifacts, implement/test the
Tools exporter, verify actual shipment, and deliver the adopted guidance and
examples to [website #29](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/issues/29).
Website consumption does not wait for a Janeway adapter or a downstream pilot.
Do not claim a deposit, minted identifier, reverse mapping or target endorsement.

## Pinned vocabulary

The foundation uses [DCMI Terms 2020-01-20](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/),
checked offline against `tests/fixtures/dcmi-terms-2020-01-20.txt`. Existing target
research references remain in the delivery record for deferred work. Tests do not
call a live vocabulary, DOI resolver, registration service or deposit API.
