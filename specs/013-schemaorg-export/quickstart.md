# Quickstart: schema.org export

Run these from FAIR-bioHeaders-Specification:

```bash
python scripts/make_jsonld.py --check                       # export example and fixtures current
python -m unittest tests.test_schemaorg_export -v           # X1–X9, table, domains and ranges
```

Run this with the toolkit:

```bash
bioheaders convert examples/example.fhr.json /tmp/x.jsonld --jsonld-profile export
diff /tmp/x.jsonld examples/example.fhr.export.jsonld       # identical
bioheaders convert /tmp/x.jsonld /tmp/back.json              # refused: one-way export
```

| # | Scenario | Expected |
| --- | --- | --- |
| V1 | `make_jsonld.py --check` | exit 0; the canonical examples are unchanged |
| V2 | `test_schemaorg_export` | all pass, including domain and range checks against the v30.1 subset |
| V3 | The toolkit export equals the fixtures | byte-identical for every case |
| V4 | Reading an export back | refused, naming the canonical form |
| V5 | validator.schema.org with `examples/example.fhr.export.jsonld` (manual) | Dataset, CreativeWork, CreateAction, Observation, Grant, ScholarlyArticle, Taxon, Person and SoftwareApplication recognised; the only expected report is the example's text licence |
