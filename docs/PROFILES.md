# Community profiles

Status: **proposal**. This document describes a profile mechanism for review
under [issue #51](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/51)
(grant A.2.4, [spec 008 FR-004](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/specs/008-multi-format-tools/spec.md)).
Nothing here is adopted, published or endorsed, and no published schema, model,
release tag or example byte changes. The worked AgBioData example is an
illustration, not a claim of AgBioData review or endorsement.

## Purpose

A community can require more than the published header contract without asking
every other user to accept it. A *profile* is a small schema that layers extra
requirements — a slot made required, a value constraint, a naming rule — on top
of a header type. The published `fhr.json`, `fhp.json` and `fhgff3.json` stay
exactly as released; a profile is applied by a consumer that chooses it.

## What a profile is, and is not

A profile:

- imports a type's model (`fhr_linkml.yml` first) and keeps every base
  constraint;
- may make an existing optional slot required, narrow a range, add a pattern or
  add a naming rule;
- may add a community-only slot (an *extending* profile);
- is selected out of band (the proposed `validate --profile NAME`), not written
  into the record's `schema` field;
- is versioned and reviewed in its own right, separately from the base type.

A profile is **not** a new header type, a change to the published contract, or
a way to weaken a base requirement. It does not remove a required field, change
a field's meaning, or add a value to a base enum.

## The mechanism

A profile is a LinkML model under [`profiles/`](../profiles/) that imports a
published type model and defines one `tree_root` class with `is_a: <BaseClass>`:

```yaml
imports:
- linkml:types
- fhr_linkml
classes:
  AgBioDataFHR:
    is_a: FHR
    tree_root: true
    slot_usage:
      accessionID:
        required: true
```

`profiles/profile_schema.py` merges the profile with its imported base models
and generates a JSON Schema (draft 2020-12) whose root is the profile class:

```sh
python profiles/profile_schema.py agbiodata-fhr --output /tmp/agbiodata-fhr.json
python profiles/profile_schema.py --list
```

The generated schema is validated with the same `jsonschema` dependency as the
published schemas. LinkML resolves imports as `<name>.yaml`, while the published
models are `<name>.yml`; the loader reads the imported models into memory and
passes them through a `SchemaView` importmap rather than renaming or copying a
published file. No network access is needed.

Some published constraints cannot be expressed in LinkML and are added by
[`json-schema-generator.py`](../json-schema-generator.py) after generation: the
exact checksum/SeqCol lengths and the `schemaVersion` enum for every type, the
`assemblySoftware` union for FHR, and the genome-link rule for FHGFF3. The
profile generator loads that script and applies the same post-processing to the
profile's `tree_root` class, choosing the rules from the class's inherited type
(FHGFF3, FHP or FHR). FHP needs no type-specific rule today. A profile root that
does not inherit one of those published types is rejected with
`UnsupportedProfileError` instead of producing a schema that silently loses base
constraints. `tests/test_profiles.py` pins both the FHGFF3 genome-link rule and
the complete published FHP constraints.

The toolkit command named in spec 008 FR-004 (`validate --profile`) is a
downstream implementation in
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools),
not this repository. This repository defines the profile model and its
conformance cases; the base install keeps working without any profile.

## Authoring a profile

1. Pick the base type and open an issue that names the community, its owner, the
   requirements, and the applicability (which records the profile covers).
2. Add `profiles/<community>-<type>.yaml` importing the type's model, with one
   `tree_root` class and `slot_usage` for each tightened slot.
3. Register it in [`profiles/registry.yaml`](../profiles/registry.yaml) with
   `status: draft` and the tracking issue.
4. Add valid and invalid instances under `profiles/examples/<profile>/` and a
   test (see `tests/test_profiles.py`).
5. Review with the community and the maintainers. Do not claim consultation or
   endorsement that has not happened.

## Relationship to `schemaVersion`

A profile does not define or bump the base type's `schemaVersion`. A record that
follows a profile still cites the base type's `schema` URL and `schemaVersion`
from [`schemas/versions.json`](../schemas/versions.json); the profile is chosen
by the consumer, not encoded in the record. Two consequences:

- If a community requirement is later adopted into the base contract, the base
  contract takes its own minor or major increment per
  [SCHEMA-VERSIONS](SCHEMA-VERSIONS.md), and the profile should then drop the
  now-redundant constraint.
- A profile needs its own reviewable version. The draft registry records only
  `status`; assigning a profile version is an open question below.

## Why a profile is not a new header type

A header type changes the *subject* of the metadata (genome, protein set,
annotation), its container, its identity fields, its conformance vectors and its
release. A profile narrows how one community uses an existing type: same
subject, same container, same identity, same serialization. A requirement that
changes the subject or the meaning of a field is a base-contract change, not a
profile, and follows the schema-addition cycle in [AGENTS.md](../AGENTS.md).

## Boundary: profiles must not silently change published contracts

A profile never edits `fhr.json`, `fhp.json`, `fhgff3.json`, `schemas/versions.json`
or the type models, and never changes released bytes. Two boundaries follow from
the published schemas setting `additionalProperties: false`:

- **Constraining profile.** Requirements on existing slots make records stricter.
  A record valid under a constraining profile is also valid under the unchanged
  base schema. The AgBioData example is mostly this.
- **Extending profile.** A new community-only slot is unknown to the base
  schema, so a record that uses it is **not** valid under the unchanged base
  contract. This is allowed only as an explicit, reviewed profile extension, and
  consumers must report base validity separately from profile validity. See
  `valid-with-sample-identifiers.json`, which is profile-valid and base-invalid.

A **relaxed profile** is different again: removing a base requirement (for
example dropping `genome`, `assemblyAuthor` or `masking` for a non-genome
nucleotide set, tracked in
[#54](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/54))
cannot be expressed by an ordinary constraining subclass. It needs an explicitly
identified derived schema with its own URL and version, and its records must not
be described as conformant to the unchanged published FHR schema. Which base
constraints change would have to be listed for review. This proposal does not
implement a relaxed profile; `relaxed-nucleotide-set.json` shows the case that
would need one.

## Reporting base and profile results separately

A validator should report two independent results:

- **base**: does the record satisfy the cited published schema?
- **profile**: does the record satisfy the community requirements?

A record can be base-valid and profile-invalid (missing a community-required
slot) or profile-valid and base-invalid (an extending profile's own field). A
profile result never substitutes for a base result. An unknown or unavailable
profile is reported by name (`UnsupportedProfileError` in the loader) rather than
silently treated as passing.

## Conformance cases

The worked example lives in
[`profiles/examples/agbiodata-fhr/`](../profiles/examples/agbiodata-fhr/) and is
checked by `tests/test_profiles.py`:

| Case | Base | Profile | Shows |
| --- | --- | --- | --- |
| `valid.json` | valid | valid | a record that meets both |
| `valid-with-sample-identifiers.json` | invalid | valid | an extending profile's own field |
| `invalid-missing-accession.json` | valid | invalid | base-valid but missing a required community slot |
| `invalid-accession-name.json` | valid | invalid | a naming rule on a base slot |
| `invalid-identifier-name.json` | valid | invalid | a naming rule on a base slot |
| `invalid-sample-identifier.json` | invalid | invalid | a naming rule on a community slot |
| `unsupported-profile.json` | valid | invalid | a record for a profile this checkout does not provide |
| `relaxed-nucleotide-set.json` | invalid | invalid | a relaxed case that needs a derived schema |

All values are synthetic placeholders and no AgBioData endorsement is implied.

## Adoption and review

- A profile is a proposal until the named community and the maintainers review
  it; the registry `status` moves `draft` → `reviewed` → `adopted` only then.
- Publishing a profile schema URL, bundling it in the toolkit, or listing it on
  the website are maintainer actions, separate from merging the proposal.
- Community mappings (for example the BrAPI reference-metadata crosswalk
  requested on issue #51) are separate design work and should be coordinated
  with the mapping profiles tracked in #56 rather than duplicated here.

## Open questions for maintainers

- Profile identity and versioning: is a profile id enough, or does a profile
  need a `profileVersion` and a versioned URL?
- Should the registry record a consultation date and a community owner before
  `reviewed`, and who signs off for the community?
- For extending profiles, should the toolkit validate the base contract and the
  profile separately and report both, and should the base `schema` field be left
  untouched?
- For relaxed profiles, is a derived schema with its own `schemaVersion` the
  accepted mechanism, and which base constraints may change?
- Should a profile be allowed to tighten a slot that the base contract leaves
  open, and how should that interact with `schemaVersion` increments?
