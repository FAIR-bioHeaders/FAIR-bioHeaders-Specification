# Community profiles (proposal)

Draft mechanism for community profiles under
[issue #51](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/51)
(grant A.2.4, [spec 008 FR-004](../specs/008-multi-format-tools/spec.md)).
Nothing here is adopted or published, and the worked AgBioData example is not
endorsed by AgBioData. See [docs/PROFILES.md](../docs/PROFILES.md) for the
purpose, the review process and the boundaries.

A profile is a small LinkML model that imports a published type model and adds
community requirements without editing `fhr.json`, `fhp.json`, `fhgff3.json`,
`schemas/versions.json` or the type models.

## Layout

| Path | Purpose |
| --- | --- |
| `registry.yaml` | The draft profile registry (id, type, status, community, owner, issue). |
| `agbiodata-fhr.yaml` | The worked draft FHR profile (illustrative, not adopted). |
| `profile_schema.py` | Loads a profile with its base models and generates its JSON Schema. |
| `examples/agbiodata-fhr/` | Valid and invalid conformance instances for the profile. |

## Usage

```sh
python profiles/profile_schema.py --list
python profiles/profile_schema.py agbiodata-fhr --output /tmp/agbiodata-fhr.json
```

`profile_schema.py` reads only files in this checkout and needs no network. The
`validate --profile` command named in spec 008 FR-004 belongs to
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools).

## Checks

```sh
python -m unittest tests.test_profiles -v
```

The tests confirm the profile keeps every published FHR constraint, adds only
its documented requirements, accepts the valid instances and rejects the invalid
ones, and reports an unknown profile instead of silently passing.

`profile_schema.py` also reuses `json-schema-generator.py`'s post-generation
rules for the profile's base type, so constraints LinkML cannot express are not
lost. In particular, an FHGFF3-based profile keeps the genome-link rule
(genomeReference or exactly one `annotates` parent of type FHR). FHP needs no
type-specific rule; the tests pin that a profile keeps the published FHP
constraints too. A profile root that inherits none of FHR, FHP or FHGFF3 is
rejected with `UnsupportedProfileError`.
