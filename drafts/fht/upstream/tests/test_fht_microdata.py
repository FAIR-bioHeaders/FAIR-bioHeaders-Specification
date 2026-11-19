# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Proposal-only FHT binding tests; full declared-dialect schema validation."""

import copy
import hashlib
import json
import subprocess
import sys
import unittest
import warnings
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import yaml
from fht_microdata import (FHT_ITEMTYPE, MicrodataError, owning_commit, read_page,
                           write_page)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "microdata"


def typed_equal(test, left, right):
    test.assertIs(type(left), type(right))
    if isinstance(left, dict):
        test.assertEqual(list(left), list(right))
        for key in left:
            typed_equal(test, left[key], right[key])
    elif isinstance(left, list):
        test.assertEqual(len(left), len(right))
        for a, b in zip(left, right):
            typed_equal(test, a, b)
    else:
        test.assertEqual(left, right)


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)


class FHTMicrodataTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(
            (ROOT / "examples" / "minimal-de-novo.fht.json").read_text()
        )

    def test_explicit_draft_opt_in_required(self):
        with self.assertRaisesRegex(MicrodataError, "allow_draft"):
            write_page(self.record)
        with self.assertRaisesRegex(MicrodataError, "allow_draft"):
            read_page(write_page(self.record, allow_draft=True))

    def test_seven_canonical_json_yaml_html_pairs(self):
        for path in sorted((ROOT / "examples").glob("*.fht.json")):
            with self.subTest(path=path.name):
                record = json.loads(path.read_text())
                typed_equal(
                    self, record, yaml.safe_load(path.with_suffix(".yaml").read_text())
                )
                html = ROOT / "examples" / "html" / (path.stem + ".html")
                typed_equal(self, record, read_page(html.read_text(), allow_draft=True))
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/make_fht_microdata.py"), "--check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_29_fields_and_nested_order_use_existing_rich_record(self):
        payload = (ROOT / "conformance/valid/fht-fasta-rich.fht.fasta").read_text()
        record = yaml.safe_load(
            "\n".join(
                line[2:] for line in payload.splitlines() if line.startswith(";~")
            )
        )
        schema = json.loads((ROOT / "fht.json").read_text())
        self.assertTrue(set(schema["properties"]).issubset(record))
        emitted = {
            key: value for key, value in record.items() if not key.startswith("x-")
        }
        typed_equal(
            self,
            emitted,
            read_page(
                write_page(record, allow_draft=True, warn=lambda _: None),
                allow_draft=True,
            ),
        )

    def test_zero_float_unicode_and_whitespace_preserved(self):
        # Synthetic typing/bounds control, not measured statistics for a FASTA.
        record = copy.deepcopy(self.record)
        record["documentation"] = (
            '  <script>unsafe()</script> & "quotes"\r\n雪 😀 @ > {{ literal }}  '
        )
        record["identifier"] = ["example:second", "example:first", "example:second"]
        record["vitalStats"] = {
            "totalTranscripts": 0,
            "N50": 1,
            "averageTranscriptLength": 0.0,
        }
        text = write_page(
            record, allow_draft=True, title="</title><script>unsafe()</script>"
        )
        typed_equal(self, record, read_page(text, allow_draft=True))
        markup = Markup()
        markup.feed(text)
        self.assertFalse(
            set(markup.tags) & {"script", "iframe", "object", "a", "input"}
        )
        self.assertFalse(
            any(
                name.startswith("on") or name == "hidden"
                for name, _ in markup.attributes
            )
        )
        self.assertIn("&lt;script&gt;", text)
        self.assertEqual(text.count("caption>FHT metadata record"), 1)

    def test_committed_rule_derived_rejections(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        self.assertEqual(set(manifest["invalid"]),
                         {path.name for path in (FIXTURES / "invalid").glob("*.html")})
        for name, expected in manifest["invalid"].items():
            with self.subTest(name=name, reason=expected["reason"]):
                self.assertIsInstance(expected["error"], str)
                self.assertTrue(expected["error"].strip(), "missing rejection rule")
                with self.assertRaisesRegex(MicrodataError, expected["error"]):
                    read_page(
                        (FIXTURES / "invalid" / name).read_text(), allow_draft=True
                    )

    def test_visible_value_fixtures_differ_from_a_readable_page_only_by_the_defect(self):
        """Each visible-values fixture is the minimal de novo example plus one
        concealment, so the rejection is that defect's and nothing else's."""
        base = (ROOT / "examples/html/minimal-de-novo.fht.html").read_text()
        read_page(base, allow_draft=True, warn=lambda message: None)
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        for name, expected in manifest["invalid"].items():
            if not expected["reason"].startswith(("Visible values", "R14")):
                continue
            with self.subTest(name=name):
                text = (FIXTURES / "invalid" / name).read_text()
                self.assertNotEqual(text, base)
                self.assertEqual(text.count("itemscope itemtype"), 1)

    def test_safe_links_and_shown_attribute_values_still_read(self):
        base = (ROOT / "examples/html/minimal-de-novo.fht.html").read_text()
        date = '<span itemprop="dateCreated" data-fhr-type="string">2026-09-15</span>'
        for markup, value in [
            ('<a itemprop="relatedLink" href="https://example.org/x">'
             'https://example.org/x</a>', ["https://example.org/x"]),
            ('<a itemprop="relatedLink" href="doi:10.5555/x">doi:10.5555/x</a>',
             ["doi:10.5555/x"]),
        ]:
            with self.subTest(markup=markup):
                page = base.replace(date, date + '</td></tr><tr><th scope="row">'
                                    'relatedLink</th><td>' + markup)
                record = read_page(page, allow_draft=True, warn=lambda message: None)
                self.assertEqual(record["relatedLink"], value)
        version = '<span itemprop="version" data-fhr-type="string">1.0</span>'
        page = base.replace(version, '<data itemprop="version" value="1.0">1.0</data>')
        self.assertEqual(read_page(page, allow_draft=True,
                                   warn=lambda message: None)["version"], "1.0")
        # Visibility is inherited only from ancestors: a hidden sibling elsewhere
        # in the page does not hide the record.
        page = base.replace("<h1>", '<div hidden>unrelated</div><h1>')
        read_page(page, allow_draft=True, warn=lambda message: None)

    def test_concealed_scalar_descendants_are_rejected(self):
        record = json.loads((ROOT / "examples/minimal-de-novo.fht.json").read_text())
        base = write_page(record, allow_draft=True)
        name = record["metadataAuthor"][0]["name"]
        for attrs in ('hidden', 'style="display:none"', 'style="visibility:hidden"'):
            with self.subTest(attrs=attrs):
                page = base.replace(name, f'Visible<span {attrs}><b>Hidden</b></span>')
                with self.assertRaisesRegex(MicrodataError, "not visible"):
                    read_page(page, allow_draft=True, warn=lambda message: None)
        # Visible descendants contribute text; unrelated concealed siblings do not.
        page = base.replace(name, 'Visible<span><b>Nested</b></span>')
        self.assertEqual(read_page(page, allow_draft=True, warn=lambda message: None)
                         ["metadataAuthor"][0]["name"], "VisibleNested")
        page = base.replace("<h1>", '<div hidden>unrelated</div><h1>')
        read_page(page, allow_draft=True, warn=lambda message: None)

    def test_concealed_attribute_array_items_and_containers_are_rejected(self):
        base = (ROOT / "examples/html/minimal-de-novo.fht.html").read_text()
        for tag in ("a", "area"):
            for attrs in ('hidden', 'style="display:none"'):
                with self.subTest(tag=tag, attrs=attrs):
                    item = (f'<{tag} itemprop="item" href="https://hidden.example/" '
                            f'{attrs}>https://shown.example/</{tag}>')
                    row = ('<tr><th scope="row">relatedLink</th><td>'
                           '<ol itemprop="relatedLink" data-fhr-type="array">'
                           + item + '</ol></td></tr>')
                    page = base.replace('</tbody></table></body>',
                                        row + '</tbody></table></body>')
                    with self.assertRaisesRegex(MicrodataError, "not visible"):
                        read_page(page, allow_draft=True, warn=lambda _: None)
        # Even an empty concealed object item cannot evade the property gate.
        row = ('<tr><th scope="row">sample</th><td>'
               '<ol itemprop="sample" data-fhr-type="array">'
               '<div itemprop="item" itemscope data-fhr-type="object" hidden>'
               '</div></ol></td></tr>')
        with self.assertRaisesRegex(MicrodataError, "not visible"):
            read_page(base.replace('</tbody></table></body>',
                                   row + '</tbody></table></body>'),
                      allow_draft=True, warn=lambda _: None)

    def test_inline_style_comment_and_escape_visibility_guards(self):
        base = (ROOT / "examples/html/minimal-de-novo.fht.html").read_text()
        anchor = '<span itemprop="version" data-fhr-type="string">1.0</span>'
        self.assertEqual(base.count(anchor), 1)
        for style in (
            "display:/**/none", "display:none /*x*/", "DISPLAY:/**/NoNe/**/!important",
            "visibility:/**/hidden", "content-visibility:hidden/*x*/", "display:none/*",
            r"displ\61 y:none", r"display:n\6f ne", r"display:none!impor\74 ant",
            'font-family:"/*";display:none',
        ):
            with self.subTest(style=style):
                # Cover a direct property and an ancestor of an attribute-valued item.
                page = base.replace(anchor, anchor.replace("<span ", f"<span style='{style}' "))
                with self.assertRaisesRegex(MicrodataError, "not visible"):
                    read_page(page, allow_draft=True, warn=lambda _: None)
                row = ('<tr><th>relatedLink</th><td>'
                       f"<ol itemprop='relatedLink' data-fhr-type='array' style='{style}'>"
                       '<a itemprop="item" href="https://example.org/">'
                       'https://example.org/</a></ol></td></tr>')
                page = base.replace('</tbody></table></body>',
                                    row + '</tbody></table></body>')
                self.assertNotEqual(page, base)
                with self.assertRaisesRegex(MicrodataError, "not visible"):
                    read_page(page, allow_draft=True, warn=lambda _: None)
        # Removing comments must not concatenate identifiers into concealment.
        for style in ("color:/**/red", "display:/**/block", "dis/**/play:none"):
            with self.subTest(visible_style=style):
                page = base.replace(anchor, anchor.replace("<span ", f"<span style='{style}' "))
                self.assertEqual(read_page(page, allow_draft=True,
                                           warn=lambda _: None)["version"], "1.0")

    def test_parser_capability_is_checked_instead_of_version(self):
        import fht_microdata
        base = (ROOT / "examples/html/minimal-de-novo.fht.html").read_text()
        self.assertTrue(fht_microdata._supports_rcdata())
        with patch.object(sys, "version_info", (3, 9, 0)):
            # A capable backport is accepted regardless of its version label.
            read_page(base, allow_draft=True, warn=lambda _: None)

        class ParserWithoutRCDATA(HTMLParser):
            RCDATA_CONTENT_ELEMENTS = ()

        with patch.object(fht_microdata, "HTMLParser", ParserWithoutRCDATA):
            self.assertFalse(fht_microdata._supports_rcdata())
            with self.assertRaisesRegex(MicrodataError, "RCDATA-capable"):
                read_page(base, allow_draft=True)
            # Writing escaped markup does not use html.parser.
            self.assertIn("FHT metadata record", write_page(self.record, allow_draft=True))

    def test_release_and_wrong_family_selection_never_fall_back(self):
        for value in [
            FHT_ITEMTYPE.replace("/main/", "/v0.7.0/"),
            "https://w3id.org/fair-bioheaders/fht/v0.7.0",
            FHT_ITEMTYPE.replace("FHT-Specification", "FAIR-bioHeaders-Specification"),
            FHT_ITEMTYPE.replace("fht.json", "fhr.json"),
        ]:
            with self.subTest(schema=value):
                record = dict(self.record, schema=value)
                with self.assertRaisesRegex(MicrodataError, "unsupported"):
                    write_page(record, allow_draft=True)

    def test_full_contract_and_format_checker_reject_invalid_metadata(self):
        for key, value in [
            ("dateCreated", "2026-02-31"),
            ("assemblyType", "guessed"),
            ("schemaVersion", 1.0),
            ("unexpected", "value"),
        ]:
            record = dict(self.record)
            record[key] = value
            with self.subTest(key=key), self.assertRaises(MicrodataError):
                write_page(record, allow_draft=True)
        for value in [float("nan"), float("inf")]:
            record = dict(self.record, vitalStats={"averageTranscriptLength": value})
            with self.assertRaisesRegex(MicrodataError, "non-finite"):
                write_page(record, allow_draft=True)

    def test_unrepresentable_html_text_is_reported_without_coercion(self):
        for value in ["NUL\x00text", "unpaired\ud800"]:
            record = dict(self.record, documentation=value)
            with self.assertRaisesRegex(MicrodataError, "not losslessly representable"):
                write_page(record, allow_draft=True)
            text = write_page(dict(self.record, documentation="sentinel"), allow_draft=True)
            with self.assertRaisesRegex(MicrodataError, "not losslessly representable"):
                read_page(text.replace("sentinel", value), allow_draft=True)

    def test_family_optional_end_tags_and_first_attribute_wins(self):
        text = write_page(self.record, allow_draft=True)
        text = text.replace(
            'itemprop="version"', 'itemprop="version" itemprop="unexpected"'
        )
        text = text.replace("</li>", "")
        typed_equal(self, self.record, read_page(text, allow_draft=True))

    def test_html_literal_line_endings_normalize_before_character_references(self):
        record = dict(self.record, documentation="alpha\nbeta")
        text = write_page(record, allow_draft=True)
        for ending in ["\r\n", "\r"]:
            with self.subTest(ending=repr(ending)):
                typed_equal(
                    self, record,
                    read_page(text.replace("alpha\nbeta", "alpha" + ending + "beta"),
                              allow_draft=True),
                )
        original = dict(self.record, documentation="alpha\r\nbeta")
        text = write_page(original, allow_draft=True)
        self.assertIn("alpha&#13;\nbeta", text)
        typed_equal(self, original, read_page(text, allow_draft=True))

    def test_nonvoid_self_closing_slash_does_not_close_property(self):
        text = write_page(self.record, allow_draft=True)
        text = text.replace('itemprop="version" data-fhr-type="string">',
                            'itemprop="version" data-fhr-type="string"/>')
        typed_equal(self, self.record, read_page(text, allow_draft=True))

    def test_repeated_array_items_and_duplicate_containers_differ(self):
        record = dict(self.record, identifier=["example:second", "example:first"])
        text = write_page(record, allow_draft=True)
        begin = text.index('<ol itemprop="identifier"')
        end = text.index("</ol>", begin) + len("</ol>")
        ordinary = (
            '<span itemprop="identifier">example:second</span>'
            '<span itemprop="identifier">example:first</span>'
        )
        typed_equal(
            self,
            record,
            read_page(text[:begin] + ordinary + text[end:], allow_draft=True),
        )

    def test_untyped_scalars_use_the_selected_schema(self):
        record = dict(
            self.record,
            vitalStats={
                "totalTranscripts": 0,
                "N50": 1,
                "averageTranscriptLength": 0.0,
            },
        )
        text = write_page(record, allow_draft=True)
        for name in ("string", "integer", "number"):
            text = text.replace(f' data-fhr-type="{name}"', "")
        typed_equal(self, record, read_page(text, allow_draft=True))

    def test_m5_extensions_warn_and_are_omitted_not_bound(self):
        record = dict(self.record, **{"x-lab-values": {"zero": 0, "flag": False}})
        warnings = []
        text = write_page(record, allow_draft=True, warn=warnings.append)
        self.assertEqual(len(warnings), 1)
        self.assertIn("x-lab-values", warnings[0])
        self.assertNotIn('itemprop="x-lab-values"', text)
        self.assertIn("Extension fields omitted from HTML (M5)", text)
        typed_equal(self, self.record, read_page(text, allow_draft=True))
        unsafe = text.replace(
            "</tbody></table></body>",
            '<tr><td><span itemprop="x-lab-values">bad</span></td></tr></tbody></table></body>',
        )
        with self.assertRaisesRegex(MicrodataError, "M5"):
            read_page(unsafe, allow_draft=True)

    def test_omitted_extensions_do_not_require_html_representability(self):
        for value in ["NUL\x00text", "unpaired\ud800"]:
            record = dict(self.record, **{"x-local": {"unserialized": value}})
            warnings = []
            text = write_page(record, allow_draft=True, warn=warnings.append)
            self.assertEqual(len(warnings), 1)
            self.assertIn("x-local", warnings[0])
            self.assertNotIn('itemprop="x-local"', text)
            typed_equal(self, self.record, read_page(text, allow_draft=True))
        with self.assertRaisesRegex(MicrodataError, "non-finite"):
            write_page(
                dict(self.record, **{"x-local": {"number": float("inf")}}),
                allow_draft=True, warn=lambda _: None,
            )

    def test_direct_inert_array_children_never_contribute_metadata(self):
        record = dict(self.record, identifier=["example:real"])
        text = write_page(record, allow_draft=True)
        for tag in ["script", "template"]:
            for attributes in ['', ' itemprop="item" data-fhr-type="string"']:
                inert = f'<{tag}{attributes}>example:malicious</{tag}>'
                altered = text.replace('</ol>', inert + '</ol>', 1)
                typed_equal(self, record, read_page(altered, allow_draft=True))
        # An end tag inside template contents cannot close the outer array.
        inert = ('<template></ol><span itemprop="identifier">'
                 'example:template</span></template>')
        altered = text.replace('</ol>', inert + '</ol>', 1)
        typed_equal(self, record, read_page(altered, allow_draft=True))

    def test_every_successful_read_reports_verified_draft_provenance(self):
        text = write_page(self.record, allow_draft=True)
        diagnostics = []
        for _ in range(2):
            read_page(text, allow_draft=True, warn=diagnostics.append)
        self.assertEqual(len(diagnostics), 2)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("default")
            for _ in range(2):
                read_page(text, allow_draft=True)
        self.assertEqual(len(captured), 2)
        provenance = json.loads((FIXTURES / "provenance.json").read_text())
        commit = owning_commit(provenance["fhtSchemaSha256"])
        for message in diagnostics:
            for detail in ["V7 FHT draft", FHT_ITEMTYPE, commit,
                           provenance["fhtSchemaSha256"], "released=false"]:
                self.assertIn(detail, message)
        original = Path.read_bytes
        def tampered(file):
            raw = original(file)
            return raw + b" " if file == ROOT / "fht.json" else raw
        with patch.object(Path, "read_bytes", tampered):
            with self.assertRaisesRegex(MicrodataError, "provenance"):
                read_page(text, allow_draft=True, warn=diagnostics.append)
        self.assertEqual(len(diagnostics), 2)
        schema = json.loads((ROOT / "fht.json").read_text())
        schema["description"] = "custom unmatched contract"
        with self.assertRaisesRegex(MicrodataError, "custom schema"):
            read_page(text, schema=schema, allow_draft=True, warn=diagnostics.append)

    def test_owning_commit_is_resolved_and_verified_from_history(self):
        pinned = json.loads((FIXTURES / "provenance.json").read_text())["fhtSchemaSha256"]
        commit = owning_commit(pinned)
        # Independent of the helper: the commit is on the checked-out history,
        # it last changed fht.json, and its stored blob has the pinned digest.
        def git(*args):
            return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                                  capture_output=True).stdout
        git("merge-base", "--is-ancestor", commit, "HEAD")
        self.assertEqual(git("log", "-1", "--format=%H", "--", "fht.json").decode().strip(),
                         commit)
        self.assertEqual(hashlib.sha256(git("show", f"{commit}:fht.json")).hexdigest(),
                         pinned)
        self.assertNotIn("owningSourceCommit",
                         json.loads((FIXTURES / "provenance.json").read_text()))
        with self.assertRaisesRegex(MicrodataError, "does not hash to the pinned digest"):
            owning_commit("0" * 64)

    def test_warning_uses_the_verified_provenance_snapshot(self):
        text = write_page(self.record, allow_draft=True)
        pinned = json.loads((FIXTURES / "provenance.json").read_text())
        original = Path.read_text
        reads = 0

        def changed(file, *args, **kwargs):
            nonlocal reads
            raw = original(file, *args, **kwargs)
            if file == FIXTURES / "provenance.json":
                reads += 1
                if reads > 1:
                    later = json.loads(raw)
                    later["fhtSchemaSha256"] = "0" * 64
                    return json.dumps(later)
            return raw

        diagnostics = []
        with patch.object(Path, "read_text", changed):
            read_page(text, allow_draft=True, warn=diagnostics.append)
        self.assertEqual(len(diagnostics), 1)
        self.assertIn(pinned["fhtSchemaSha256"], diagnostics[0])
        self.assertNotIn("0" * 64, diagnostics[0])

    def test_required_roots_do_not_imply_required_taxon_members(self):
        schema = json.loads((ROOT / "fht.json").read_text())
        self.assertEqual(len(schema["required"]), 9)
        for name in schema["required"]:
            record = dict(self.record)
            record.pop(name)
            with self.subTest(missing=name), self.assertRaises(MicrodataError):
                write_page(record, allow_draft=True)
        record = dict(self.record, taxon={})
        typed_equal(
            self,
            record,
            read_page(write_page(record, allow_draft=True), allow_draft=True),
        )

    def test_retained_sample_and_existing_protocol_routes(self):
        # Deliberately synthetic values and example.org URLs, not real accession claims.
        record = json.loads((ROOT / "examples/genome-guided.fht.json").read_text())
        sample = copy.deepcopy(record["sample"])
        record["documentation"] = (
            "Synthetic supplied library protocol and kit description."
        )
        record["relatedLink"] += [
            "https://example.org/library-protocol",
            "https://example.org/biosample/source-a",
        ]
        record["accessionID"] = {
            "name": "Synthetic transcript set",
            "url": "https://example.org/transcript-set",
        }
        extracted = read_page(write_page(record, allow_draft=True), allow_draft=True)
        typed_equal(self, record, extracted)
        self.assertEqual(extracted["sample"], sample)
        self.assertEqual(extracted["strandedness"], "reverse")
        self.assertNotEqual(
            extracted["accessionID"]["url"], extracted["relatedLink"][-1]
        )
        for name in ("libraryProtocol", "kit", "sampleAccession"):
            with self.subTest(unadopted=name), self.assertRaises(MicrodataError):
                write_page(
                    dict(record, **{name: "not a declared field"}), allow_draft=True
                )

    def test_mixed_molecules_follow_owning_contract(self):
        record = dict(self.record, moleculeType="mixed")
        typed_equal(
            self, record,
            read_page(write_page(record, allow_draft=True), allow_draft=True),
        )
        for field, value in [("moleculeType", "Mixed"), ("moleculeType", "unknown"),
                             ("assemblyType", "mixed")]:
            with self.subTest(field=field, value=value), self.assertRaises(MicrodataError):
                write_page(dict(self.record, **{field: value}), allow_draft=True)

    def test_q4_metadata_and_assembly_authors_are_named(self):
        record = dict(self.record, assemblyAuthor=[{"name": "Named assembly author",
                                                     "uri": "https://orcid.org/0000-0002-1825-0097"}])
        typed_equal(self, record, read_page(write_page(record, allow_draft=True),
                                          allow_draft=True, warn=lambda _: None))
        for authors in ([], [{}], [{"name": ""}], [{"name": " "}],
                        [{"uri": "https://orcid.org/0000-0002-1825-0097"}]):
            with self.subTest(authors=authors), self.assertRaises(MicrodataError):
                write_page(dict(record, metadataAuthor=authors), allow_draft=True)
            with self.subTest(assembly=authors), self.assertRaises(MicrodataError):
                write_page(dict(record, assemblyAuthor=authors), allow_draft=True)
        text = write_page(record, allow_draft=True)
        # The reader independently validates extracted metadata, not just writer output.
        altered = text.replace(record["metadataAuthor"][0]["name"], " ")
        self.assertNotEqual(altered, text)
        with self.assertRaises(MicrodataError):
            read_page(altered, allow_draft=True)

    def test_draft_and_source_bytes_are_pinned(self):
        provenance = json.loads((FIXTURES / "provenance.json").read_text())
        self.assertEqual(
            hashlib.sha256((ROOT / "fht.json").read_bytes()).hexdigest(),
            provenance["fhtSchemaSha256"],
        )
        for name, digest in provenance["canonicalSources"].items():
            self.assertEqual(
                hashlib.sha256((ROOT / "examples" / name).read_bytes()).hexdigest(),
                digest,
            )
