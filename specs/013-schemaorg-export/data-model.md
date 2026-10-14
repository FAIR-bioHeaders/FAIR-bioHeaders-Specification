# Data model: the export graph

**Feature**: 013-schemaorg-export

The exact keys and their order are in [contracts/export.md](contracts/export.md). The rules are in
[docs/SCHEMAORG-EXPORT.md](../../docs/SCHEMAORG-EXPORT.md).

```text
_:metadata-record (CreativeWork) ──about──▶ ASSEMBLY (Dataset)  ◀──result── _:assembly-activity (CreateAction)
   creator → metadataAuthor                   creator → assemblyAuthor           instrument → SoftwareApplication*
   schemaVersion → schema URL                 about → Taxon                      actionProcess → HowTo (opt-in)
   fhr:schemaVersion                          identifier → strings, PropertyValue (accession), PropertyValue (SeqCol)
                                              subjectOf → ScholarlyArticle (strict DOI) / documentation URL
                                              funding → Grant(description)
                                              license, description, keywords, url, fhr:* canonical terms
_:observation-<KEY> (Observation) ──observationAbout──▶ ASSEMBLY
   measuredProperty → fhr:<KEY>, value, unitCode (UO), unitText
```

| Entity | schema.org class | Source fields | Identity |
| --- | --- | --- | --- |
| Assembly | `Dataset` | genome, version, dateCreated, taxon, assemblyAuthor, identifiers, documentation, reuseConditions, funding, FHR-only terms | export `id`, or `_:assembly` |
| Metadata record | `CreativeWork` | schema, schemaVersion, metadataAuthor | `_:metadata-record` |
| Assembly activity | `CreateAction` | assemblySoftware, assemblyProtocol (opt-in) | `_:assembly-activity` |
| Statistic | `Observation` | each numeric vitalStats key | `_:observation-<KEY>` |
| Grant | `Grant` | funding | blank, nested |
| Article | `ScholarlyArticle` | scholarlyArticle (strict DOI) | `https://doi.org/<DOI>` |
| SeqCol identifier | `PropertyValue` | seqcol_id | blank, nested |
