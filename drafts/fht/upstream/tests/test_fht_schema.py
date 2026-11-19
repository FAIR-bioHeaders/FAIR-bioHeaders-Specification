"""Contract checks for the generated FHT JSON Schema."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "fht.json"
CHECKSUM = "A" * 43 + "="


def minimal():
    """A field-level minimal record; not a byte-backed #8 fixture."""
    return {
        "schema": (
            "https://raw.githubusercontent.com/FAIR-bioHeaders/"
            "FHT-Specification/main/fht.json"
        ),
        "schemaVersion": "1.0",
        "transcriptome": "Example transcriptome",
        "assemblyType": "de novo",
        "taxon": {
            "name": "Arabidopsis thaliana",
            "uri": "https://identifiers.org/taxonomy:3702",
        },
        "version": "1.0",
        "metadataAuthor": [{"name": "Example author"}],
        "dateCreated": "2026-10-24",
        "checksum": CHECKSUM,
    }


class FhtSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def record(self, **changes):
        value = minimal()
        value.update(changes)
        return value

    def assert_valid(self, value):
        errors = sorted(self.validator.iter_errors(value), key=str)
        self.assertEqual(errors, [], [error.message for error in errors])

    def assert_invalid(self, value, fragment):
        errors = sorted(self.validator.iter_errors(value), key=str)
        self.assertTrue(errors, f"expected a validation error containing {fragment!r}")
        self.assertTrue(
            any(fragment in error.message for error in errors),
            [error.message for error in errors],
        )

    def test_approved_q4_required_values_are_nonempty(self):
        for field in ("transcriptome", "version", "dateCreated"):
            for value in ("", " ", "\t\n"):
                with self.subTest(field=field, value=value):
                    record = self.record(**{field: value})
                    self.assertTrue(list(self.validator.iter_errors(record)))
                    # The explicit nonblank rule also works without format assertion.
                    self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(record)))
        self.assert_invalid(self.record(metadataAuthor=[]), "non-empty")
        for author in ({}, {"uri": "https://orcid.org/0000-0002-1825-0097"},
                       {"name": ""}, {"name": " ", "nameType": "Organizational"}):
            with self.subTest(author=author):
                self.assertTrue(list(self.validator.iter_errors(self.record(metadataAuthor=[author]))))
        self.assert_valid(self.record(metadataAuthor=[{"name": "Named metadata author"}]))

    def test_q4_assembly_author_items_are_named_but_the_list_stays_optional(self):
        self.assert_valid(self.record())
        self.assert_valid(self.record(assemblyAuthor=[{"name": "Named assembly author"}]))
        self.assert_invalid(self.record(assemblyAuthor=[]), "non-empty")
        for author in ({}, {"uri": "https://orcid.org/0000-0002-1825-0097"},
                       {"name": ""}, {"name": " ", "nameType": "Organizational"},
                       {"name": "\t\n"}):
            with self.subTest(author=author):
                record = self.record(assemblyAuthor=[author])
                self.assertTrue(list(self.validator.iter_errors(record)))
                self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(record)))
        self.assertEqual(self.schema["properties"]["assemblyAuthor"]["items"],
                         {"$ref": "#/$defs/AssemblyAuthor"})
        self.assertNotIn("assemblyAuthor", self.schema["required"])

    def test_q4_does_not_tighten_taxon_or_the_shared_author(self):
        self.assert_valid(self.record(taxon={}))
        self.assertNotIn("required", self.schema["$defs"]["Author"])
        self.assertNotIn("minLength", self.schema["$defs"]["Author"]["properties"]["name"])
        self.assertEqual(self.schema["properties"]["metadataAuthor"]["minItems"], 1)
        self.assertEqual(self.schema["properties"]["metadataAuthor"]["items"],
                         {"$ref": "#/$defs/MetadataAuthor"})

    def test_q8_extraction_parent_is_independent_of_construction_method(self):
        parent = {"headerType": "FHR", "relationship": "transcribedFrom", "checksum": CHECKSUM}
        self.assert_valid(self.record(assemblyType="genome-guided", derivedFrom=[parent]))
        self.assert_valid(self.record(assemblyType="genome-guided"))
        self.assert_invalid(self.record(derivedFrom=[{"headerType": "FHR", "relationship": "transcribedFrom"}]),
                            "checksum")
        # Shape validation does not certify actual extraction from supplied bytes.

    def test_schema_is_a_valid_draft_2020_12_schema(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertFalse(self.schema["additionalProperties"])

    def test_required_fields(self):
        self.assertEqual(
            set(self.schema["required"]),
            {
                "schema",
                "schemaVersion",
                "transcriptome",
                "assemblyType",
                "taxon",
                "version",
                "metadataAuthor",
                "dateCreated",
                "checksum",
            },
        )

    def test_minimal_record_is_valid(self):
        self.assert_valid(minimal())

    def test_each_required_field_is_enforced(self):
        for name in self.schema["required"]:
            value = minimal()
            del value[name]
            self.assert_invalid(value, "'" + name + "' is a required property")

    def test_unknown_key_is_rejected(self):
        # With extension fields (R15) jsonschema names the key and the x- pattern.
        self.assert_invalid(
            self.record(masking="soft-masked"), "'masking' does not match any of the regexes"
        )

    def test_extension_fields(self):
        """FAIR-bioHeaders-Specification docs/FORMAT.md R15: top-level x- keys only."""
        self.assertEqual(
            list(self.schema["patternProperties"]), ["^x-[A-Za-z0-9][A-Za-z0-9_.-]*$"]
        )
        for key in ("x-a", "x-1", "x-example-studyNote", "x-a.b-c_d", "x-transcriptome"):
            for value in ("text", 2, 0.5, True, None, [1, "a"], {"@id": "x", "n": [None]}):
                with self.subTest(key=key, value=value):
                    self.assert_valid(self.record(**{key: value}))
        for key in ("X-a", "x-", "x-_a", "x- a", "x-a b", "x-\u00e4", "x-\uff41", "x-a\r",
                    "x-a\u2028", "xa", "x_a", "ext-a"):
            with self.subTest(key=key):
                self.assert_invalid(self.record(**{key: 1}), "does not match any of the regexes")
        # Python's "$" matches before a final line feed; the key is still invalid.
        self.assert_invalid(self.record(**{"x-a\n": 1}), "should not be valid under")
        nested = self.record()
        nested["taxon"] = dict(nested["taxon"], **{"x-a": 1})
        self.assert_invalid(nested, "Additional properties")
        author = self.record()
        author["metadataAuthor"] = [{"name": "Example author", "x-a": 1}]
        self.assert_invalid(author, "Additional properties")

    def test_schema_url_and_version(self):
        raw_main = minimal()["schema"]
        self.assert_valid(self.record(schema=raw_main))
        # Rule V7: a draft is cited only by its owning repository's raw-main
        # URL and never takes a release form; a reader routes release forms to
        # FHR under V5. The release forms are added when FHT is published.
        for value in (
            "https://w3id.org/fair-bioheaders/fht/v0.4.0",
            "https://w3id.org/fair-bioheaders/fht/v0.4.0/",
            "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/v0.6.0/fht.json",
            "https://raw.githubusercontent.com/FAIR-bioHeaders/"
            "FAIR-bioHeaders-Specification/v0.6.0/fht.json",
            "https://example.org/fht.json",
            raw_main + "\n",
        ):
            with self.subTest(schema=value):
                self.assert_invalid(self.record(schema=value), "was expected")
        self.assert_invalid(self.record(schemaVersion=1.0), "is not of type 'string'")
        self.assert_invalid(self.record(schemaVersion="1.1"), "is not one of ['1.0']")

    def test_assembly_type_values(self):
        for value in ("de novo", "genome-guided", "annotation-derived"):
            self.assert_valid(self.record(assemblyType=value))
        self.assert_invalid(self.record(assemblyType="mixed"), "is not one of")
        self.assert_invalid(self.record(assemblyType="unknown"), "is not one of")

    def test_molecule_type_is_optional_and_restricted(self):
        self.assert_valid(minimal())
        for value in ("mRNA", "rRNA", "tRNA", "transcribed RNA", "mixed"):
            self.assert_valid(self.record(moleculeType=value))
        for value in ("total RNA", "cDNA", "ncRNA", "Mixed", "unknown"):
            self.assert_invalid(self.record(moleculeType=value), "is not one of")

    def test_molik_clarifications_keep_existing_field_shapes(self):
        record = self.record(moleculeType="mixed", taxon={},
                             sample=[{"tissue": "leaf"}, {"tissue": "root"}],
                             strandedness="reverse",
                             documentation="Synthetic library protocol and kit description",
                             relatedLink=["https://example.org/protocol/synthetic-kit"])
        self.assert_valid(record)
        self.assertEqual(self.schema["required"], ["schema", "schemaVersion", "transcriptome",
                         "assemblyType", "taxon", "version", "metadataAuthor",
                         "dateCreated", "checksum"])
        self.assert_invalid(self.record(sample="text instead of retained array"),
                            "is not of type 'array'")
        for key in ("libraryProtocol", "libraryKit", "assemblyProtocol"):
            self.assert_invalid(self.record(**{key: "https://example.org/protocol"}),
                                "does not match any of the regexes")

    def test_strandedness_is_optional_and_normalized(self):
        for value in ("unstranded", "forward", "reverse"):
            self.assert_valid(self.record(strandedness=value))
        self.assert_invalid(self.record(strandedness="firststrand"), "is not one of")
        self.assert_invalid(self.record(strandedness="secondstrand"), "is not one of")

    def test_sample_is_an_ordered_non_empty_array(self):
        sample = {"tissue": "ovary", "tissueIdentifier": "UBERON:0000992"}
        self.assert_valid(self.record(sample=[sample]))
        self.assert_valid(
            self.record(
                sample=[
                    {"tissue": "ovary", "condition": "control"},
                    {"tissue": "fat body", "condition": "treated"},
                ]
            )
        )
        self.assert_invalid(self.record(sample=[]), "should be non-empty")
        self.assert_invalid(self.record(sample=sample), "is not of type 'array'")
        self.assert_invalid(
            self.record(sample=[{"tissueIdentifier": "not-a-curie"}]),
            "does not match",
        )
        self.assert_invalid(
            self.record(sample=[{"sampleName": "invented"}]),
            "Additional properties",
        )

    def test_empty_strings_and_empty_sample_objects_are_rejected(self):
        self.assert_invalid(self.record(transcriptome=""), "does not match")
        self.assert_invalid(self.record(transcriptome="   "), "does not match")
        self.assert_invalid(
            self.record(transcriptomeSynonym=[""]), "does not match"
        )
        self.assert_invalid(self.record(libraryStrategy=""), "does not match")
        self.assert_invalid(self.record(libraryStrategy="   "), "does not match")
        self.assert_invalid(self.record(instrument=[""]), "does not match")
        for key in (
            "tissue",
            "developmentalStage",
            "condition",
            "strain",
        ):
            self.assert_invalid(
                self.record(sample=[{key: ""}]), "does not match"
            )
        self.assert_invalid(
            self.record(sample=[{}]), "is not valid under any of the given schemas"
        )

    def test_sequencing_runs_are_run_accessions(self):
        self.assert_valid(self.record(sequencingRuns=["SRR123456", "ERR7", "DRR1"]))
        self.assert_invalid(self.record(sequencingRuns=[]), "should be non-empty")
        self.assert_invalid(
            self.record(sequencingRuns=["SRS123456"]), "does not match"
        )

    def test_vital_stats_constraints(self):
        self.assert_valid(
            self.record(
                vitalStats={
                    "totalTranscripts": 0,
                    "N50": 1,
                    "averageTranscriptLength": 0,
                }
            )
        )
        self.assert_invalid(
            self.record(vitalStats={"totalTranscripts": -1}), "less than the minimum"
        )
        self.assert_invalid(
            self.record(vitalStats={"N50": 0}), "less than the minimum"
        )
        self.assert_invalid(
            self.record(vitalStats={"averageTranscriptLength": -0.1}),
            "less than the minimum",
        )
        self.assert_invalid(
            self.record(vitalStats={"geneCount": 10}), "Additional properties"
        )

    def test_derived_from_reviewed_parent_pairs(self):
        fht_parent = {
            "headerType": "FHT",
            "relationship": "filteredFrom",
            "checksum": CHECKSUM,
        }
        fhr_parent = {
            "headerType": "FHR",
            "relationship": "transcribedFrom",
            "checksum": CHECKSUM,
        }
        self.assert_valid(self.record(derivedFrom=[fht_parent]))
        self.assert_valid(self.record(derivedFrom=[fhr_parent]))
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {
                        "headerType": "FHR",
                        "relationship": "assembledFrom",
                        "checksum": CHECKSUM,
                    }
                ]
            ),
            "is not valid under any of the given schemas",
        )
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {
                        "headerType": "FHP",
                        "relationship": "filteredFrom",
                        "checksum": CHECKSUM,
                    }
                ]
            ),
            "is not valid under any of the given schemas",
        )
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {"headerType": "FHT", "relationship": "filteredFrom"}
                ]
            ),
            "'checksum' is a required property",
        )
        self.assert_invalid(self.record(derivedFrom=[]), "should be non-empty")

    def test_rich_record_combines_optional_groups(self):
        value = self.record(
            moleculeType="mRNA",
            assemblySoftware=[
                {
                    "name": "gffread",
                    "version": "0.12.7",
                    "commandLineOption": ["-w"],
                }
            ],
            sample=[{"tissue": "ovary", "tissueIdentifier": "UBERON:0000992"}],
            libraryStrategy="RNA-Seq",
            strandedness="forward",
            sequencingRuns=["SRR123456"],
            instrument=["Example sequencer"],
            vitalStats={
                "totalTranscripts": 10,
                "N50": 500,
                "averageTranscriptLength": 300.5,
            },
            completeness={
                "lineageDataset": "insecta_odb10",
                "buscoVersion": "6.1.0",
                "mode": "transcriptome",
                "completeSingle": 100,
                "completeDuplicated": 2,
                "fragmented": 3,
                "missing": 4,
                "total": 109,
            },
            derivedFrom=[
                {
                    "headerType": "FHR",
                    "relationship": "transcribedFrom",
                    "checksum": CHECKSUM,
                }
            ],
            identifier=["example:1"],
            accessionID={"name": "Example", "url": "https://example.org/x"},
            scholarlyArticle="10.1234/abc",
            documentation="https://example.org/doc",
            relatedLink=["https://example.org"],
            funding="Example grant",
            reuseConditions="CC0",
            voucherSpecimen="Example freezer",
        )
        self.assert_valid(value)

    def test_legacy_compatible_fields_are_retained(self):
        self.assert_valid(
            self.record(
                transcriptomeSynonym=["Example synonym"],
                assemblyAuthor=[{"name": "Example assembler"}],
                instrument=["Example sequencer"],
            )
        )

    def test_legacy_md5_checksum_is_not_accepted(self):
        self.assert_invalid(
            self.record(checksum="md5:7582b26fcb0a9775b87c38f836e97c42"),
            "does not match",
        )

    def test_null_is_not_an_unknown_value(self):
        self.assert_invalid(self.record(moleculeType=None), "is not of type 'string'")

    def test_completeness_reuses_shared_counts(self):
        self.assert_valid(
            self.record(
                completeness={
                    "lineageDataset": "insecta_odb10",
                    "buscoVersion": "6.1.0",
                    "mode": "transcriptome",
                    "completeSingle": 100,
                    "completeDuplicated": 2,
                    "fragmented": 3,
                    "missing": 4,
                    "total": 109,
                }
            )
        )
        self.assert_invalid(
            self.record(
                completeness={
                    "lineageDataset": "insecta_odb10",
                    "completeSingle": 0,
                    "completeDuplicated": 0,
                    "fragmented": 0,
                    "missing": 0,
                    "total": 0,
                }
            ),
            "less than the minimum",
        )

    def test_dotted_busco_lineage_follows_the_shared_grammar(self):
        # Shared #170 decided dotted versions at v0.6.0: the pinned shared
        # pattern now accepts one or more dot-separated numeric components.
        # Malformed dot forms stay rejected, and a measured lineage is never
        # renamed or coerced to fit the pattern.
        for dataset in ("insecta_odb12.2", "insecta_odb12.2.1"):
            with self.subTest(lineageDataset=dataset):
                self.assert_valid(
                    self.record(
                        completeness={
                            "lineageDataset": dataset,
                            "completeSingle": 1,
                            "completeDuplicated": 0,
                            "fragmented": 0,
                            "missing": 0,
                            "total": 1,
                        }
                    )
                )
        for dataset in ("insecta_odb12.", "insecta_odb.12", "insecta_odb12..2",
                        "insecta_odb12.2b", "Insecta_odb12.2"):
            with self.subTest(lineageDataset=dataset):
                self.assert_invalid(
                    self.record(
                        completeness={
                            "lineageDataset": dataset,
                            "completeSingle": 1,
                            "completeDuplicated": 0,
                            "fragmented": 0,
                            "missing": 0,
                            "total": 1,
                        }
                    ),
                    "does not match",
                )

    def test_date_created_is_an_iso_date(self):
        self.assert_invalid(self.record(dateCreated="2026-10-24T12:00:00"), "is not a 'date'")

    def test_checksum_is_a_44_character_sha512_256_value(self):
        self.assert_invalid(self.record(checksum="A" * 43), "does not match")
        self.assert_invalid(self.record(checksum="A" * 44), "does not match")


    def test_local_patterns_agree_across_regex_dialects(self):
        """FHT-local patterns avoid "$" and "\\S", whose meaning differs between
        Python's re (jsonschema) and ECMA-262 (ajv, browsers)."""
        blank = ["", " ", "\t\n", "\ufeff", "\u001c", "\u001f", "\u0085",
                 "\u00a0", "\u2028", "\u3000", " \ufeff\u0085 "]
        for value in blank:
            for field in ("transcriptome", "version", "dateCreated"):
                with self.subTest(field=field, value=value):
                    errors = list(self.validator.iter_errors(self.record(**{field: value})))
                    self.assertTrue(errors)
            with self.subTest(field="metadataAuthor.name", value=value):
                self.assertTrue(list(self.validator.iter_errors(
                    self.record(metadataAuthor=[{"name": value}]))))
            with self.subTest(field="sample.tissue", value=value):
                self.assertTrue(list(self.validator.iter_errors(
                    self.record(sample=[{"tissue": value}]))))
        for value in ("x", " x ", "\u200b", "\ufeffx", "caf\u00e9"):
            with self.subTest(nonblank=value):
                self.assert_valid(self.record(transcriptome=value,
                                              sample=[{"tissue": value}]))
        self.assert_valid(self.record(sequencingRuns=["SRR1"],
                                      sample=[{"tissueIdentifier": "UBERON:1"}]))
        self.assert_invalid(self.record(sequencingRuns=["SRR1\n"]), "does not match")
        self.assert_invalid(self.record(sample=[{"tissueIdentifier": "UBERON:1\n"}]),
                            "does not match")
        local = json.dumps(self.schema["properties"]["sequencingRuns"]) + json.dumps(
            self.schema["$defs"]["Sample"])
        self.assertNotIn("$\"", local)
        self.assertNotIn('\\\\S"', local)


if __name__ == "__main__":
    unittest.main()
