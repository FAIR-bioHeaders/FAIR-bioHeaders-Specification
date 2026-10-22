# AgBioData FHR profile conformance cases (draft)

Illustrative instances for the draft profile in `../../agbiodata-fhr.yaml`
([issue #51](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/51)).
Every value is a synthetic placeholder; author identifiers are reused from the
existing examples. Nothing here is AgBioData-endorsed or real assembly data.

`tests/test_profiles.py` checks each file against both the published `fhr.json`
and the generated profile schema.

| File | Published `fhr.json` | Profile | Purpose |
| --- | --- | --- | --- |
| `valid.json` | valid | valid | meets the base contract and the community requirements |
| `valid-with-sample-identifiers.json` | invalid | valid | uses the profile-only `sampleIdentifier` field (extension boundary) |
| `invalid-missing-accession.json` | valid | invalid | base-valid record missing the community-required `accessionID` |
| `invalid-accession-name.json` | valid | invalid | `accessionID.name` is neither an INSDC nor a community accession |
| `invalid-identifier-name.json` | valid | invalid | an identifier does not match the syntactic lowercase `prefix:accession` rule |
| `invalid-sample-identifier.json` | invalid | invalid | a `sampleIdentifier` does not match the syntactic lowercase `prefix:accession` rule |
| `relaxed-nucleotide-set.json` | invalid | invalid | a non-genome nucleotide set that needs a separately reviewed relaxed derived schema |

A profile result never replaces a base result: `valid-with-sample-identifiers.json`
is profile-valid and base-invalid because `sampleIdentifier` is outside the
published contract. See [docs/PROFILES.md](../../../docs/PROFILES.md).
