# Structured-voucher evidence review and impact analysis (evidence pin)

**Status**: evidence pin. Not a contract, not an adoption, not a release
proposal. Recorded maintainer decision of **2026-11-12** on
[#139](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/139):
**Option C — the structured-voucher proposal stays a proposal ceiling**; the
only authorized work is pinning this evidence review (prepared under the #211
packet H coordination). No schema, version, registry or example byte changed
by this document; the released FHR 2.1 / FHP 1.1 / FHGFF3 1.1 contracts and
the free-text `voucherSpecimen` are unchanged.

This page **supplements, and does not restate,** the merged proposal
[`shared-voucher-descriptions.md`](shared-voucher-descriptions.md) (PR #140):
the proposed string-or-list shape, family ownership table, semantics and
implementation acceptance criteria live there. Added here: the verified
external evidence base, the importing-type and consumer impact census, and the
open-decision list so a future A-vs-B contract choice is fast.

## Verification method

Every external URL below was fetched on **2026-11-12** with
`curl -sSL -o /dev/null -w "%{http_code} %{url_effective}"` (redirects
followed); status quotes from the Darwin Core and DCMI term lists are the
rendered text of the live pages, and OLS lookups used the EBI OLS4
`/api/search` and class pages. Items that could not be verified are listed as
such with their failure mode; nothing is cited that was not reached, and no
identifier, accession or relationship is invented. Repository claims cite the
bytes at the commit this document was authored against
(`origin/main` `692cffe`, schemas identical to the v0.5.0 release).

## 1. Evidence base: external standards a structured voucher relationship could cite

| # | Source (pinned URL) | Role for voucher evidence | Verified 2026-11-12 |
| --- | --- | --- | --- |
| E1 | <http://rs.tdwg.org/dwc/terms/materialSampleID> (landing `https://dwc.tdwg.org/list/#dwc_materialSampleID`; term version IRI `.../dwc/terms/version/materialSampleID-2026-10-13`) | Darwin Core identifier for a material sample: "An identifier for the dwc:MaterialSample (as opposed to a particular digital record ...)". The list marks it with the note "It is recommended to use dwc:materialEntityID in place of this term." | HTTP 200 |
| E2 | <http://rs.tdwg.org/dwc/terms/materialEntityID> (`#dwc_materialEntityID`) | Darwin Core term the maintenance documentation now recommends in place of E1 — the vocabulary itself moves under curators | HTTP 200 |
| E3 | <http://rs.tdwg.org/dwc/terms/basisOfRecord> (`#dwc_basisOfRecord`) | "The specific nature of the data record", recommended against a controlled vocabulary: the natural home of the preserved-specimen / photograph / human-observation distinctions #139 describes | HTTP 200 |
| E4 | <http://rs.tdwg.org/dwc/terms/associatedMedia> (`#dwc_associatedMedia`) | "A list (concatenated and separated) of associated ac:Media resources": the evidence-image case (photograph of a specimen) already has a biodiversity-informatics term | HTTP 200 |
| E5 | GSC MIxS <https://w3id.org/mixs>; term page <https://www.ebi.ac.uk/ols4/ontologies/gscmixs/classes?obo_id=MIXS%3A0000026> | MIxS `source_mat_id` ("source material identifiers", `MIXS:0000026`): the extraction/sequencing material identifier. Maintainer review rule from #139: map to it **only** for explicitly identified material used for extraction/sequencing — a population description or proxy voucher does not qualify | HTTP 200 (both) |
| E6 | INSDC minimum specifications, `Sample` category at the pinned commit <https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Sample> | The deposit-side requirement set [`docs/insdc-coverage.md`](../insdc-coverage.md) rows `Sample` and A.b assess against; those rows already name `voucherSpecimen` and #139 | HTTP 200 |
| E7 | Dublin Core `dcterms:source` <https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/source/> (alias <http://purl.org/dc/terms/source>) | "A related resource from which the described resource is derived ... intended to be used with non-literal values ... Best practice is to identify the related resource by means of a URI or a string conforming to a formal identification system." Confirms the #139 mapping note: `dcterms:source` requires an identified resource, so free-text and proxy vouchers cannot silently map to it | HTTP 200 |
| E8 | schema.org <https://schema.org/identifier>, <https://schema.org/url> | The proposed `identifier`/`url` members' web-document vocabulary (export side only; the canonical mapping stays `fhr:voucherSpecimen`) | HTTP 200 |
| E9 | PROV-O <https://www.w3.org/TR/prov-o/> | Candidate relation vocabulary for a *future* structured-predicate revision (explicitly out of #140's initial scope) | HTTP 200 |
| E10 | ECO "voucher specimen phenotypic analysis evidence" <http://purl.obolibrary.org/obo/ECO_0000050> (OLS4 page HTTP 200) | Demonstrates biodiversity/ontology practice already distinguishes voucher-backed evidence kinds; supports the "record the role, do not infer derivation" guidance | HTTP 200 via OLS |
| E11 | Halfon et al. 2026, *How to write (and review) a Genome Report*, <https://doi.org/10.1093/gbe/evag258> | DOI resolution verified via the doi.org handle API (`responseCode 1`, target `academic.oup.com/gbe/article/doi/10.1093/gbe/evag258/8907573`); publisher page returned HTTP 403 to automated fetching, so **full text not accessed here** — the page/box citations of this reference are those recorded in the #139 maintainer comment of 2026-10-17 | DOI resolves; text not verified |
| E12 | Tvedte et al. 2026, *Toward standardization in arthropod and biodiversity genome projects*, <https://doi.org/10.1093/genetics/iyag172> | Same: handle resolution verified; publisher HTTP 403 to curl; content claims carried from the #139 comment, not re-derived | DOI resolves; text not verified |

### Could not verify / negative results (equally evidence)

| Item | Result on 2026-11-12 | Consequence |
| --- | --- | --- |
| `https://genomics-standards-consortium.github.io/mixs/source/metadata-term/mixs/source_mat_id/` | HTTP 404 (site restructured) | Cite MIxS via the `w3id` (E5) + OLS4 page, not the retired path |
| `https://tools.tdwg.org/materialsample/`, `https://tools.tdwg.org/material_sample/`, `https://www.tdwg.org/standards/material-sample/`, `https://www.tdwg.org/standards/ms/` | connection failure / 404 | The TDWG *Material Sample* best-practice document has no stable reachable URL today; rely on the DwC term IRIs (E1–E4), which do resolve |
| `http://rs.tdwg.org/dwc/terms/associatedSequence` | HTTP 404 | Do not cite it; the specimen↔sequence link needs another authority if ever required |
| OBO Relation Ontology "has voucher specimen" | OLS4 `ontology=ro` search for "voucher" returned no RO term | There is **no ready-made RO voucher predicate**; a structured-relation revision would map to PROV-O (E9) or define locally — this feeds the same gap recorded for `derivedFrom`'s provisional vocabulary (spec #54) |
| `http://purl.obolibrary.org/obo/MIXS_0000026` | OBO pURL redirect 404 (berkeleybop) | Use the OLS4 class page (E5) as the resolvable citation |

### What this evidence does and does not license

Supports: broad voucher semantics (population, specimen, tissue, image, proxy
— E3/E4/E10 vocabulary exists precisely because these roles differ); optional
persistent identifiers with a "construct-or-omit" fallback (E1/E2); strict
separation of "material used for sequencing" from "evidence associated with
the source" (E5 conditional rule, E7's derivation wording).

Does **not** support: requiring museum accessions; inferring derivation,
pooling or specimen examination from co-occurrence; promoting free text to
`dcterms:source` (E7); or claiming any external standard mandates #140's
object shape — none does; #140 remains an FH*-specific design.

## 2. Compatibility and versioning assessment

**Importing types today** (slot verified in the committed bytes at `692cffe`):
`schemas/core.yaml` defines `voucherSpecimen` ("Description of the physical
sample"); `fhr_linkml.yml`, `fhp_linkml.yml` and `fhgff3_linkml.yml` each opt
in, and `fhr.json`/`fhp.json`/`fhgff3.json` expose it as an optional string.
FHT has no released shared contract; its initial contract is the coordination
point (#140 ownership table). An adoption therefore touches **three released
types plus the FHT draft**, not only FHR — changing the shared definition
means checking every importing type (AGENTS.md, "Models, generated artifacts
and compatibility").

Published representations that carry the field (census at `692cffe`):

- canonical JSON-LD: `terms#voucherSpecimen` is mapped with `kind: exact`,
  `coercion: literal` (`mappings/fhr-jsonld-dcmi.yml`), summarized as
  "DCMI: none" in `docs/TERMS.md`/`docs/MAPPINGS.md` — an object list breaks
  the literal coercion and needs its own property-scoped-context decision
  (`scripts/make_jsonld.py` regeneration);
- one-way schema.org export: `mappings/fhr-schemaorg-export.yml` states
  "Free text; structured specimens are #101." (#101 is tracked by #139) —
  export behavior must be re-reviewed, and canonical round-trip identity
  preserved separately (#56 discipline);
- conformance suite: 25 of the 286 vectors carry `voucherSpecimen`, all in
  the JSON-LD FHR format; the `fasta`, `gfa`, `microdata`, `fhp-fasta` and
  `fhgff3` formats currently carry it in none. Adoption adds valid/invalid
  vectors (description-only, identifier, URL, mixed-list rejection, empty-list
  rejection, Unicode/escaping) per affected type — string-or-list must also
  round-trip through the `;~`/`#~` line serialization (R8/R11/R12/R13 rules)
  and HTML microdata;
- released examples: eight `examples/*fhr*` files (yaml/json/jsonld/export/
  minimal.jsonld/microdata html/fasta/gfa) contain a `voucherSpecimen` string;
  none may be rewritten (immutable published bytes);
- INSDC assessment: `docs/insdc-coverage.md` rows `Sample` and A.b and the
  #139 cross-reference line name the field; a new `schemaVersion` fails
  `tests/test_insdc_coverage.py` until the assessment is re-pinned (#157 rule).

**Version implications** (assessment only — no versions assigned here): if
implemented exactly as #140 proposes, every currently valid record stays
valid with unchanged meaning, so the change qualifies as **additive → minor
increments per type** (from FHR 2.1 / FHP 1.1 / FHGFF3 1.1 to the next
minors), following the v0.5.0 precedent and the same mechanism the 2026-11-12
#170 decision applied to `lineageDataset`. Consequences to schedule:

1. structure-using records are **invalid under the older validators**:
   toolkit selection rules (V-series, `docs/SCHEMA-VERSIONS.md`) and the
   versioned bundles in `fair-bioheaders` must ship the new schemas before
   support is advertised;
2. adding or editing a header field **recomputes the file checksum**, which
   cascades into every `derivedFrom` child link — including FHGFF3's
   genome-link alternative; existing files stay untouched by default, and no
   back-migration may rewrite them;
3. `schemas/versions.json`, `docs/SCHEMA-VERSIONS.md`, `llms.txt`
   (`tests/test_llms_txt.py`), drift baselines (`scripts/check_schema_drift.py`),
   the website's digest-pinned `schema-snapshots/` (its
   `scripts/schema_fields.py --check` fails on any schema-byte change), the
   CEDAR templates (#162, regenerated from the same digests), and the
   companion copies checked by `scripts/check_release.py` all move in the
   same coordinated release;
4. pinned downstream mirrors re-pin through their own parity machinery: FHGFF3
   `header/` (`header/provenance.json`, `check_header_parity.py`) and
   FHR-Specification's compatibility `fhr.json`/`fhp.json`/`fhgff3.json`
   (`published-files.yml` against shared main).

## 3. Affected consumers (explicit list)

- **FAIR-bioHeaders-Tools** `bioheaders` CLI (`validate`/`combine`/`verify`/
  `strip`, JSON-LD reader/writer, assess): bundled schemas, FASTA/GFA/GFF3/
  microdata/JSON-LD serializers for both alternatives; released version
  coordination (0.9.0 currently bundles v0.5.0).
- **`fair-bioheaders.github.io`**: schema snapshot digests, generated field
  tables (`schema_fields.py` notes), `/table-builder/` and
  `/metadata-viewer/` forms — a structured voucher needs UI work or an
  explicit "unsupported in the form" notice.
- **gff3-validator**: optional FHGFF3 header validation hook (HDR rules)
  against the published schema bundle.
- **FHGFF3 repository** `header/` byte-copy tree (parity CI) and
  `tests/test_fhgff3_microdata.py` fixtures.
- **FHR-Specification / FHP-Specification** compatibility files and their
  checks; **FHT-Specification** contract development (#6/#7 lineage).
- **Claude plugin** (`plugins/fair-bioheaders`) skill guidance and any
  downstream curators citing `llms.txt`.
- None of these may be updated by this pin; each belongs to the future
  implementation cycle #140 already enumerates.

## 4. Open decisions for the future contract choice (A-vs-B)

The 2026-11-12 decision records that a later choice between the proposed
adoption routes (the "#211 packet H" A-vs-B menu) must be made by the joint
maintainers. To make that choice fast, the decision-relevant questions, with
where this pin leaves each:

1. **Shape scope** — adopt #140's `{description, identifier?, url?}` list
   as-is, or split role/entity kinds? Evidence: E1–E4/E10 show external
   practice separates identifier, record-kind and media links; #140 starts
   deliberately minimal. Unresolved by design.
2. **DwC alignment depth** — reference `dwc:materialSampleID`/`materialEntityID`
   semantics (E1/E2) in guidance only, or align member naming? Both terms are
   live; E1 is flagged in the term list as recommended-against in favor of E2,
   so any naming alignment should target E2 — decision deferred.
3. **Relationship predicates** — keep "describe the role in ordinary
   language" (no controlled vocabulary, #140) or add structured predicates
   later (E9; the RO-gap negative result means no off-the-shelf predicate).
4. **Mapping posture** — canonical JSON-LD coercion and the one-way
   schema.org/DCMI/MIxS export treatment (E5 conditional rule, E7
   non-literal constraint); any promotion of MIxS `source_mat_id` must keep
   the "identified extraction/sequencing material only" condition.
5. **Version target and release packaging** — which release carries the
   minors for which subset of types (all three vs FHR-first vs FHT-first);
   concrete versions assigned only with the implementation decision (#140
   rule preserved).
6. **Conformance and serialization budget** — new vectors per format,
   FASTA/GFA escaping proof, microdata representation, toolkit release
   sequencing (§2 items 1–4).
7. **Legacy posture** — confirm no migration of existing records and the
   parent-link cascade policy (§2 item 2).

## 5. Boundary statement

This document pins evidence and impact; it decides nothing. `voucherSpecimen`
remains optional free text under FHR 2.1 / FHP 1.1 / FHGFF3 1.1. Adoption,
version increments, releases, tags and publication remain joint maintainer
actions (GOVERNANCE.md), each with its own cycle as AGENTS.md requires. The
BUSCO-side item of the same 2026-11-12 decision set is tracked under #170,
not here.
