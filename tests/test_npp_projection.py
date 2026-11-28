"""CI regression for the NPP projection fixtures (#249, round NPP-2 on #292).

Asserts the full green state: the source fixture validates against this
repository's own fhr.json, the fixture file's checksum recomputes exactly
(FORMAT.md R2-R4), the three outputs are byte-deterministic rebuilds, the XML
parses with entity resolution left off (stdlib ElementTree default), and every
negative fixture fails with exactly its expected codes. A missing SHA-512/256
implementation is reported as a failure, never a silent pass.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import npp_projection  # noqa: E402


class NppProjectionFixtures(unittest.TestCase):
    def test_fixtures_are_consistent(self):
        errors = npp_projection.check()
        self.assertEqual(errors, [], "fixture harness reported: " + "; ".join(errors))

    def test_jats_taxon_uri_and_statistic_units(self):
        source = npp_projection.load_json(npp_projection.FIX / "source.fhr.json")
        context = npp_projection.load_yaml(npp_projection.FIX / "context.yaml")
        root = ET.fromstring(
            npp_projection.build_jats(source, context, source["checksum"])
        )

        taxon_uri = source["taxon"]["uri"]
        uri_keywords = [
            keyword
            for keyword in root.findall("./kwd-group/kwd")
            if keyword.text == taxon_uri
        ]
        self.assertEqual(len(uri_keywords), 1)
        self.assertNotIn("specific-use", uri_keywords[0].attrib)

        rows = {
            row.findtext("th"): "".join(row.find("td").itertext())
            for row in root.findall("./table-wrap/table/tbody/tr")
        }
        l_statistics = ("L50", "L90", "scaffoldL50", "scaffoldL90")
        n_statistics = ("N50", "N90", "scaffoldN50", "scaffoldN90")
        for statistic in l_statistics:
            with self.subTest(statistic=statistic):
                self.assertNotIn("bp", rows[f"vitalStats.{statistic}"])
        for statistic in n_statistics:
            with self.subTest(statistic=statistic):
                self.assertTrue(rows[f"vitalStats.{statistic}"].endswith("(bp)"))

    def test_preprint_projection_preserves_manuscript_vs_dataset_identity(self):
        source = npp_projection.load_json(npp_projection.FIX / "source.fhr.json")
        preprint_ctx = npp_projection.load_yaml(
            npp_projection.FIX / "preprint" / "context-preprint.yaml"
        )
        xml_text = npp_projection.build_crossref(source, preprint_ctx, preprint=True)
        root = ET.fromstring(xml_text)
        self.assertEqual(root.tag, "preprint")
        title = root.findtext("./titles/title")
        self.assertEqual(title, preprint_ctx["article"]["title"])
        self.assertNotIn(source["genome"], title)
        authors = [el.text for el in root.findall("./contributors/names/name/author_name")]
        expected_authors = [a["name"] for a in preprint_ctx["article"]["authors"]]
        self.assertEqual(authors, expected_authors)
        for creator in source.get("assemblyAuthor", []):
            self.assertNotIn(creator["name"], authors)
        for curator in source.get("metadataAuthor", []):
            self.assertNotIn(curator["name"], authors)
        related = root.find("./relatedItems/relatedIdentifier")
        self.assertIsNotNone(related)
        self.assertEqual(related.attrib.get("relationType"), "References")
        self.assertEqual(related.text, preprint_ctx["deposit"]["datasetRecord"]["doi"])

    def test_semantic_failures_detect_article_doi_conflicts_and_identifier_mixup(self):
        source = npp_projection.load_json(npp_projection.FIX / "source.fhr.json")
        context = npp_projection.load_yaml(npp_projection.FIX / "context.yaml")
        bad_source_article = deepcopy(source)
        bad_source_article["scholarlyArticle"] = "10.5555/conflicting-article"
        codes = {
            c.split(":")[0]
            for c in npp_projection.semantic_failures(bad_source_article, context, None)
        }
        self.assertIn("ARTICLE_DOI_CONFLICT", codes)

        bad_source_ident = deepcopy(source)
        bad_source_ident["identifier"] = ["doi:" + context["article"]["doi"]]
        ident_codes = {
            c.split(":")[0]
            for c in npp_projection.semantic_failures(bad_source_ident, context, None)
        }
        self.assertIn("IDENTITY_MIXUP", ident_codes)


if __name__ == "__main__":
    unittest.main()
