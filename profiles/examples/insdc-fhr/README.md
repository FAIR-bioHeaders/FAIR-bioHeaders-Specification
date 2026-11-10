# Draft INSDC submission-readiness profile for FHR

This opt-in profile layers onto FHR 2.0 for a single genome assembly after
project and sample registration. It checks a subset of assembly metadata offline.
Validate the cited FHR schema and report the profile result separately. Archive
checks still cover record existence, public visibility, whether links describe
this assembly, taxonomy rank and name agreement, sample checklists and submission
acceptance.

| Requirement | Profile check |
| --- | --- |
| A.d, SA.T2 | `taxon.uri` must have the form `https://identifiers.org/taxonomy:<positive-taxid>`. |
| A.a, A.b, AY5 | `relatedLink` must include at least one recognizable BioProject URL and one recognizable BioSample URL. Other links may appear alongside them. |
| A.j | `assemblySoftware` must be a nonempty list with a nonblank name and version for each entry. Supply a nonblank `vitalStats.readTechnology` or at least one nonblank `instrument` entry. An instrument entry should identify the sequencing platform when used for this purpose. |

Require both record types because they identify different entities in the
[INSDC assembly specification](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Assembly).
Use accession-based HTTPS record links in these forms. The placeholders stand
for BioProject accessions such as `PRJNA…`, `PRJEB…` and `PRJDB…`, and BioSample
accessions such as `SAMN…`, `SAMEA…` and `SAMD…`.

| Archive | Project URL | Sample URL |
| --- | --- | --- |
| [NCBI](https://submit.ncbi.nlm.nih.gov/help/sequence-submission-guidance/) | `https://www.ncbi.nlm.nih.gov/bioproject/<project>` | `https://www.ncbi.nlm.nih.gov/biosample/<sample>` |
| [ENA](https://ena-browser-docs.readthedocs.io/en/latest/browser/ena-record.html) | `https://www.ebi.ac.uk/ena/browser/view/<project>` | `https://www.ebi.ac.uk/ena/browser/view/<sample>` |
| [DDBJ](https://www.ddbj.nig.ac.jp/news/en/2024-06-10_2-e.html) | `https://ddbj.nig.ac.jp/search/entry/bioproject/<project>` | `https://ddbj.nig.ac.jp/search/entry/biosample/<sample>` |

The checks also recognize the legacy DDBJ `/resource/` paths and the
[Identifiers.org BioProject resolver](https://registry.identifiers.org/registry/bioproject)
form `https://identifiers.org/bioproject:<project>`. Archive paths accept a
trailing slash. Search queries, run accessions and unrelated URLs do not satisfy
either requirement.

Apply the 1000-character limit to each rendered Assembly metadata value (A.k),
and check ASCII and absence of HTML on the actual Sample and Project values
(SA.1, SA.3, P.1). Prefer an archive-aware assessment of those outgoing records
because an FHR header carries neither the complete Sample and Project records nor
the final rendered Assembly values. For example, a Unicode author name in the
header may never appear in a Sample or Project record. This draft does not
implement the outgoing-record checks. See the
[coverage review](../../../docs/insdc-coverage.md) for the pinned requirements and [Kodama et al. (2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13548877/) for the publication context.

Generate the draft schema with
`python profiles/profile_schema.py insdc-fhr --output /tmp/insdc-fhr.schema.json`.
The fixtures use illustrative metadata and placeholder archive accessions.
`valid.json` passes both schemas. `invalid-missing-sample.json` passes FHR 2.0 and
fails the profile because the other links cannot substitute for a BioSample.
