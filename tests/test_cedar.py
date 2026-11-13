# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The generated CEDAR authoring templates (issue #162, drafts per 2026-11-13).

The templates under templates/cedar/ are derived artifacts: this suite proves
they regenerate byte-stably from the committed schemas, carry the exact schema
provenance (SHA-256, contract URL, contract version), mirror each contract's
required list, omit the pattern-defined extension slots, keep the CEDAR 1.6.0
occurrence shape, and round-trip a filled export of every released type back
into a record that validates against the real JSON Schema (Draft 2020-12).

The two DRAFT templates (FHT, FHGM) get the same byte-stability, required-list,
extension-omission and occurrence-shape checks against their pinned snapshots
in templates/cedar/drafts/, plus draft-only guarantees: the embedded digest
equals the stored snapshot and provenance.json, a tampered snapshot refuses to
generate, the visible status/title/description draft markings are present and
absent from the released templates, no w3id URL appears in a draft template,
every contract path is covered, and filled exports flatten into records that
validate against the stored draft schema (Draft 2020-12 + FormatChecker).
"""

import base64
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

import yaml
from jsonschema import Draft4Validator, Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import make_cedar  # noqa: E402

TEMPLATE_DIR = ROOT / "templates" / "cedar"
REGISTRY = json.loads((ROOT / "schemas" / "versions.json").read_text(encoding="utf-8"))
STEMS = ("fhr", "fhp", "fhgff3")
DRAFT_STEMS = ("fht", "fhgm")
ALL_STEMS = STEMS + DRAFT_STEMS
DRAFT_PROVENANCE = json.loads((TEMPLATE_DIR / "drafts" / "provenance.json")
                              .read_text(encoding="utf-8"))
FHT_RAW_MAIN = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
# header type stem -> (contract file, a filled released example record, its format)
TYPES = {
    "fhr": ("fhr.json", "examples/example.fhr.json", "json"),
    "fhp": ("fhp.json", "examples/fhp/rich-database.fhp.json", "json"),
    "fhgff3": ("fhgff3.json", "examples/fhgff3/rich.fhgff3.yaml", "yaml"),
}


def contract_path(stem):
    """The bytes the template for ``stem`` is generated from: the committed
    released schema, or the byte-pinned draft snapshot."""
    if stem in DRAFT_STEMS:
        return ROOT / DRAFT_PROVENANCE["snapshots"][stem]["local"]
    return ROOT / TYPES[stem][0]


def contract_schema(stem):
    return json.loads(contract_path(stem).read_text(encoding="utf-8"))


def entry_version(stem):
    return DRAFT_PROVENANCE["snapshots"][stem]["contractVersion"]


# ---------------------------------------------------------------------------
# Synthetic draft fixtures. These exercise the draft contracts' shape rules in
# the round-trip tests; they are format-valid placeholders, NOT real resource
# citations. Digests are derived from fixed seeds so the files are stable, and
# the accessions/URIs are reserved or example values (10.5555 test DOI prefix,
# example.org) or clearly-synthetic patterns (SRR000000, GCA_000000001.1).
# The one non-synthetic identity pair is intentional: taxon name and URI agree
# at NCBI Taxonomy (7227 = Drosophila melanogaster), and 0000-0002-1825-0097 is
# ORCID's published example iD.
# ---------------------------------------------------------------------------

def _fixture_checksum(seed):
    """A deterministic, obviously synthetic FHR-family checksum-shaped value."""
    return base64.b64encode(hashlib.sha512(seed.encode("utf-8")).digest()[:32]).decode("ascii")


def _fixture_seqcol(seed):
    """A deterministic, obviously synthetic 32-character SeqCol-shaped digest."""
    return (base64.urlsafe_b64encode(hashlib.sha256(seed.encode("utf-8")).digest()[:24])
            .decode("ascii").rstrip("="))


FHT_FIXTURE = {
    "schema": FHT_RAW_MAIN,
    "schemaVersion": "1.0",
    "transcriptome": "CEDAR round-trip example transcript set (synthetic)",
    "transcriptomeSynonym": ["example-drosophila-txset"],
    "version": "0.0-test",
    "assemblyType": "genome-guided",
    "moleculeType": "mRNA",
    "strandedness": "forward",
    "taxon": {"name": "Drosophila melanogaster",
              "uri": "https://identifiers.org/taxonomy:7227"},
    "metadataAuthor": [{"name": "CEDAR fixture author", "nameType": "Personal",
                        "uri": "https://orcid.org/0000-0002-1825-0097"}],
    "dateCreated": "2026-11-13",
    "sequencingRuns": ["SRR000000"],
    "sample": [{"tissue": "whole body", "developmentalStage": "adult"}],
    "completeness": {"buscoVersion": "5.8.4", "lineageDataset": "diptera_odb10",
                     "mode": "transcriptome", "completeSingle": 278,
                     "completeDuplicated": 0, "fragmented": 1, "missing": 0,
                     "total": 279},
    "vitalStats": {"totalTranscripts": 279, "N50": 2048,
                   "averageTranscriptLength": 1470.5},
    "derivedFrom": [{"headerType": "FHR", "checksum": _fixture_checksum("fht-parent-genome"),
                     "relationship": "transcribedFrom",
                     "seqcol_id": _fixture_seqcol("fht-parent-genome")}],
    "checksum": _fixture_checksum("fht-cedar-roundtrip"),
}

FHGM_FIXTURE_MINIMAL = {
    "modelId": "GLEAN-EXAMPLE-0001",
    "modelVersion": "1",
    "featureId": "gene-EXAMPLE-1",
    "reference": {"genomeReference": {
        "accession": "GCA_000000001.1",
        "seqcol_id": _fixture_seqcol("fhgm-example-genome"),
        "assemblyName": "ExampleDomestic1"}},
}

FHGM_FIXTURE_REVISED = {
    "modelId": "GLEAN-EXAMPLE-0001",
    "modelVersion": "2",
    "featureId": "gene-EXAMPLE-1",
    "reference": {"annotates": _fixture_checksum("fhgm-parent-fhr")},
    "predecessor": {"annotationChecksum": _fixture_checksum("fhgm-prior-snapshot"),
                    "modelId": "GLEAN-EXAMPLE-0001", "modelVersion": "1"},
    "contributors": [{"name": "Example curator", "role": "model curator",
                      "nameType": "Personal",
                      "uri": "https://orcid.org/0000-0002-1825-0097"}],
    "evidence": [{"description": "Synthetic fixture evidence statement",
                  "uri": "https://example.org/evidence/example-1"}],
    "methods": {"software": [{"name": "example-glean", "version": "0.0-test",
                              "uri": "https://example.org/soft/example-glean"}],
                "protocol": "https://example.org/protocol/example-curation",
                "limitations": ["Synthetic fixture record; asserts nothing biological"]},
    "publication": {"article": "10.5555/example.doigroup.1",
                    "deposit": ["example-db:EXAMPLE-1"]},
    "reuseConditions": "CC0-1.0 (synthetic fixture)",
}


def load_template(stem):
    return json.loads((TEMPLATE_DIR / f"{stem}.json").read_text(encoding="utf-8"))


def header_type(stem):
    return next(name for name, file_stem in make_cedar.TYPES.items() if file_stem == stem)


def contract_version(stem):
    return REGISTRY["releases"][REGISTRY["current"]][header_type(stem)]


def contract_url(stem):
    return (f"https://w3id.org/fair-bioheaders/{REGISTRY['w3id'][header_type(stem)]}"
            f"/{REGISTRY['current']}")


def to_plain(value):
    """Normalize YAML-loaded scalars (ISO dates) to their JSON string form."""
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def load_example(example, fmt):
    text = (ROOT / example).read_text(encoding="utf-8")
    return json.loads(text) if fmt == "json" else to_plain(yaml.safe_load(text))


def walk_keys(node, path=""):
    """Yield (path, key) for every mapping key at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key
            yield from walk_keys(value, f"{path}/{key}")
    elif isinstance(node, list):
        for item in node:
            yield from walk_keys(item, f"{path}[]")


def context_mapping(properties):
    context = {}
    for key, schema in properties.items():
        if "enum" in schema:
            context[key] = schema["enum"][0]
        elif "properties" in schema:
            context[key] = {
                name: definition["enum"][0]
                for name, definition in schema["properties"].items()
                if "enum" in definition
            }
    return context


def wrap_export(value, node, root=False):
    """Wrap one record value the way a CEDAR artifact export presents it.

    Scalars become {"@value": ...} with the numeric datatypes the generated
    fields declare; element instances additionally carry the JSON-LD identity
    keys that flatten_export must drop.
    """
    if value is None:
        return {"@value": None}
    if isinstance(value, bool):
        return {"@value": value}
    if isinstance(value, int):
        return {"@value": str(value), "@type": "xsd:long"}
    if isinstance(value, float):
        return {"@value": str(value), "@type": "xsd:double"}
    if isinstance(value, str):
        return {"@value": value}
    if isinstance(value, list):
        return [wrap_export(item, node["items"]) for item in value]
    if isinstance(value, dict):
        inner = {}
        for key, item in value.items():
            form_key = make_cedar.form_field_name(key) if root else key
            inner[form_key] = wrap_export(item, node["properties"][form_key])
        context_schema = node["properties"]["@context"]["properties"]
        inner.update({"@context": context_mapping(context_schema),
                      "@id": "urn:example:instance",
                      "@type": ["https://example.invalid/Instance"]})
        return inner
    raise AssertionError(f"unexpected value {value!r}")


class CedarTemplateTests(unittest.TestCase):
    def test_regenerated_templates_are_byte_stable(self):
        """The committed bytes equal two fresh in-process generations."""
        for stem in ALL_STEMS:
            committed = (TEMPLATE_DIR / f"{stem}.json").read_bytes()
            first = make_cedar.render(stem).encode("utf-8")
            second = make_cedar.render(stem).encode("utf-8")
            self.assertEqual(first, second, f"{stem}: generation is not deterministic")
            self.assertEqual(committed, first,
                             f"{stem}: committed template drifted; run scripts/make_cedar.py")

    def test_check_mode_passes_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_cedar.py"),
                                 "--check"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("up to date", result.stdout)

    def test_embedded_schema_digest_matches_committed_bytes(self):
        for stem in STEMS:
            schema_file, _, _ = TYPES[stem]
            digest = hashlib.sha256((ROOT / schema_file).read_bytes()).hexdigest()
            template = load_template(stem)
            for key in ("description", "schema:description"):
                found = re.search(re.escape(make_cedar.SHA_MARKER) + r" ([0-9a-f]{64})",
                                  template[key])
                self.assertIsNotNone(found, f"{stem}: {key} states no schema digest")
                self.assertEqual(found.group(1), digest,
                                 f"{stem}: embedded digest does not match {schema_file}")

    def test_required_set_equals_contract_required(self):
        for stem in ALL_STEMS:
            schema = contract_schema(stem)
            template = load_template(stem)
            contract_required = [name for name in template["required"]
                                 if name not in make_cedar.FIXED_REQUIRED]
            # The released checksum rule extends unchanged to the drafts: a
            # root checksum is written by `bioheaders combine` over the exact
            # file bytes, never by the form, so it stays out of the template's
            # required list (an FHGM model record has no checksum at all and
            # its required list therefore matches the contract exactly).
            expected = [make_cedar.form_field_name(name) for name in schema["required"]
                        if name != "checksum"]
            self.assertEqual(set(contract_required), set(expected),
                             f"{stem}: template required list differs from the schema")
            self.assertEqual(contract_required, expected,
                             f"{stem}: required fields should follow the schema, except checksum")
            self.assertEqual(template["required"][:9], make_cedar.FIXED_REQUIRED,
                             f"{stem}: the CEDAR 1.6.0 fixed required tuple must lead")

    def test_no_extension_slot_reaches_the_form(self):
        for stem in ALL_STEMS:
            for path, key in walk_keys(load_template(stem)):
                self.assertFalse(key.startswith("x-"),
                                 f"{stem}: extension key {key!r} at {path or '/'}")

    def test_pinned_identity_fields(self):
        for stem in STEMS:
            template = load_template(stem)
            url = contract_url(stem)
            version = contract_version(stem)
            schema_field = make_cedar.form_field_name("schema")
            schema_literals = template["properties"][schema_field]["_valueConstraints"]["literals"]
            version_literals = (template["properties"]["schemaVersion"]
                                ["_valueConstraints"]["literals"])
            self.assertEqual([entry["label"] for entry in schema_literals], [url],
                             f"{stem}: schema field must pin the released contract URL")
            self.assertEqual([entry["label"] for entry in version_literals], [version],
                             f"{stem}: schemaVersion field must pin the current contract version")
            self.assertIn(url, template["description"])
            self.assertEqual(template["pav:derivedFrom"], url)
            self.assertEqual(template["pav:version"], f"{version}.0")

    def test_cedar_occurrence_shape(self):
        """Structural checks mirroring the CEDAR 1.6.0 meta-schemas."""
        for stem in ALL_STEMS:
            template = load_template(stem)
            self.assertEqual(template["$schema"], make_cedar.DRAFT04)
            self.assertEqual(template["@type"], make_cedar.CEDAR_TEMPLATE)
            self.assertEqual(template["schema:schemaVersion"], make_cedar.CEDAR_FORMAT_VERSION)
            self.assertEqual(template["type"], "object")
            self.assertEqual(template["bibo:status"], "bibo:draft")
            for key in make_cedar.BOOKKEEPING + ["@context", "@id"]:
                self.assertIn(key, template["properties"], f"{stem}: properties lacks {key}")
            self.assertIn("_ui", template)
            order = template["_ui"]["order"]
            context_properties = template["properties"]["@context"]["properties"]
            self.assertEqual(context_properties["schema"]["enum"],
                             ["http://schema.org/"])
            schema = contract_schema(stem)
            if "schema" in schema["properties"]:
                self.assertIn("header_schema", context_properties)
            self.assertEqual(order, [make_cedar.form_field_name(name)
                                     for name in schema["properties"]],
                             f"{stem}: form order must cover every contract field exactly")
            for name in order:
                field = template["properties"][name]
                if field.get("type") == "array":
                    self.assertEqual(sorted(field), ["items", "minItems", "type"])
                    node = field["items"]
                else:
                    node = field
                self.assertIn(node["@type"], (make_cedar.CEDAR_FIELD, make_cedar.CEDAR_ELEMENT))
                self.assertEqual(node["schema:schemaVersion"], make_cedar.CEDAR_FORMAT_VERSION)
                self.assertEqual(node["schema:name"],
                                 "schema" if name == make_cedar.form_field_name("schema") else name,
                                 f"{stem}: {name} must export under its contract name")
                if node["@type"] == make_cedar.CEDAR_ELEMENT:
                    self.assertEqual(node["required"][:2], ["@context", "@id"])
                    self.assertEqual(list(node["_ui"]["order"]), list(node["properties"])[3:])
                    self.assertEqual(node["additionalProperties"], False)
                else:
                    self.assertIn("_valueConstraints", node)
                    self.assertIn("_ui", node)

    def test_nested_required_matches_each_definition(self):
        """Every element's required members equal the schema object's required[]."""
        for stem in ALL_STEMS:
            schema = contract_schema(stem)
            defs = schema.get("$defs") or schema.get("definitions") or {}
            template = load_template(stem)
            meta = make_cedar.load_contracts()[stem]

            def contract_object(node):
                node = make_cedar.deref(node, defs)
                if "anyOf" in node:
                    node = make_cedar.Generator(stem, schema, meta).normalize(node)
                return node

            def check(scope_node, cedar_node, root=False):
                for member, member_schema in scope_node.get("properties", {}).items():
                    form_name = make_cedar.form_field_name(member) if root else member
                    form = cedar_node["properties"][form_name]
                    target = contract_object(member_schema)
                    if target.get("type") == "array":
                        target = make_cedar.deref(target.get("items", {}), defs)
                        form = form["items"]
                    if target.get("properties"):
                        self.assertEqual(set(form["required"][2:]),
                                         set(target.get("required", [])),
                                         f"{stem}: {member} element required mismatch")
                        check(target, form)

            check(schema, template, root=True)

    def test_filled_exports_round_trip_and_validate(self):
        for stem in STEMS:
            schema_file, example, fmt = TYPES[stem]
            record = load_example(example, fmt)
            template = load_template(stem)
            artifact = wrap_export(record, template, root=True)
            artifact.update({"@id": "urn:example:artifact",
                             "@type": ["https://example.invalid/FhRecord"],
                             "schema:isBasedOn": "https://example.invalid/template",
                             "schema:name": "export", "schema:description": "",
                             "pav:createdOn": "2026-11-12T00:00:00Z",
                             "pav:createdBy": None, "pav:lastUpdatedOn": None,
                             "oslc:modifiedBy": None, "pav:derivedFrom": "urn:example:source"})
            Draft4Validator.check_schema(template)
            template_validator = Draft4Validator(template, format_checker=FormatChecker())
            errors = sorted(template_validator.iter_errors(artifact), key=lambda e: e.json_path)
            self.assertEqual([], [e.message for e in errors],
                             f"{stem}: filled export failed generated-template validation")
            flat = make_cedar.flatten_export(artifact)
            self.assertEqual(flat, record, f"{stem}: CEDAR export round trip lost data")
            schema = json.loads((ROOT / schema_file).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            errors = sorted(validator.iter_errors(flat), key=lambda e: e.json_path)
            self.assertEqual([], [e.message for e in errors],
                             f"{stem}: filled export failed schema validation")

    def test_partial_exports_omit_empty_optional_values_and_root_checksum(self):
        for stem in STEMS:
            schema_file, example, fmt = TYPES[stem]
            record = load_example(example, fmt)
            record["checksum"] = None
            record["documentation"] = None
            record["taxon"]["name"] = None
            template = load_template(stem)
            artifact = wrap_export(record, template, root=True)
            artifact.update({"@context": context_mapping(
                template["properties"]["@context"]["properties"]),
                "@id": "urn:example:artifact",
                "@type": ["https://example.invalid/FhRecord"],
                "schema:isBasedOn": "https://example.invalid/template",
                "schema:name": "partial export", "schema:description": "",
                "pav:createdOn": "2026-11-12T00:00:00Z",
                "pav:createdBy": None, "pav:lastUpdatedOn": None,
                "oslc:modifiedBy": None, "pav:derivedFrom": "urn:example:source"})
            template_validator = Draft4Validator(template, format_checker=FormatChecker())
            errors = sorted(template_validator.iter_errors(artifact), key=lambda e: e.json_path)
            self.assertEqual([], [e.message for e in errors],
                             f"{stem}: partial export failed generated-template validation")
            flat = make_cedar.flatten_export(artifact)
            self.assertNotIn("checksum", flat)
            self.assertNotIn("documentation", flat)
            self.assertNotIn("name", flat["taxon"])
            if stem == "fhgff3":
                parent_checksum = record["derivedFrom"][0]["checksum"]
                self.assertEqual(flat["derivedFrom"][0]["checksum"], parent_checksum)
            schema = json.loads((ROOT / schema_file).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker())
                          .iter_errors(flat))
            self.assertEqual(["'checksum' is a required property"],
                             [error.message for error in errors],
                             f"{stem}: pre-binding record should only need its file checksum")
            invalid_required = copy.deepcopy(artifact)
            invalid_required["schemaVersion"] = {"@value": None}
            invalid_flat = make_cedar.flatten_export(invalid_required)
            self.assertIsNone(invalid_flat["schemaVersion"],
                              f"{stem}: an unanswered required value must not be omitted")
            invalid_errors = list(Draft202012Validator(schema, format_checker=FormatChecker())
                                  .iter_errors(invalid_flat))
            self.assertTrue(any("schemaVersion" in error.json_path for error in invalid_errors),
                            f"{stem}: missing required value did not remain a validation error")

    def test_example_fields_are_all_covered_by_the_template(self):
        for stem in STEMS:
            _, example, fmt = TYPES[stem]
            record = load_example(example, fmt)
            template = load_template(stem)

            def check(record_node, cedar_node, where, root=False):
                for key, value in record_node.items():
                    form_key = make_cedar.form_field_name(key) if root else key
                    self.assertIn(form_key, cedar_node["properties"],
                                  f"{stem}: example uses {where}{key} but the form lacks it")
                    form = cedar_node["properties"][form_key]
                    if form.get("type") == "array":
                        form = form["items"]
                        if isinstance(value, list) and value and isinstance(value[0], dict):
                            check(value[0], form, f"{where}{key}[].")
                    elif isinstance(value, dict):
                        check(value, form, f"{where}{key}.")

            check(record, template, "", root=True)


class CedarDraftTemplateTests(unittest.TestCase):
    """Guarantees specific to the two pinned DRAFT templates (2026-11-13)."""

    def build_artifact(self, stem, record):
        """Wrap a filled draft record the way a CEDAR artifact export presents it."""
        template = load_template(stem)
        artifact = wrap_export(record, template, root=True)
        artifact.update({"@id": "urn:example:artifact",
                         "@type": ["https://example.invalid/FhRecord"],
                         "schema:isBasedOn": "https://example.invalid/template",
                         "schema:name": "export", "schema:description": "",
                         "pav:createdOn": "2026-11-13T00:00:00Z",
                         "pav:createdBy": None, "pav:lastUpdatedOn": None,
                         "oslc:modifiedBy": None, "pav:derivedFrom": "urn:example:source"})
        return template, artifact

    # -- pinning ---------------------------------------------------------------

    def test_draft_provenance_digests_match_stored_sources(self):
        for stem in DRAFT_STEMS:
            entry = DRAFT_PROVENANCE["snapshots"][stem]
            snapshot = ROOT / entry["local"]
            digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            self.assertEqual(digest, entry["sha256"],
                             f"{stem}: snapshot bytes differ from provenance.json")
            self.assertEqual(make_cedar.git_blob_sha1(snapshot), entry["gitBlobSha1"],
                             f"{stem}: snapshot is not the git blob recorded upstream")
            template = load_template(stem)
            for key in ("description", "schema:description"):
                found = re.search(re.escape(make_cedar.SHA_MARKER) + r" ([0-9a-f]{64})",
                                  template[key])
                self.assertIsNotNone(found, f"{stem}: {key} states no schema digest")
                self.assertEqual(found.group(1), digest,
                                 f"{stem}: embedded digest does not match the snapshot")

    def test_draft_snapshot_pin_refuses_tampering(self):
        entry = DRAFT_PROVENANCE["snapshots"]["fhgm"]
        path = ROOT / entry["local"]
        original = path.read_bytes()
        committed = (TEMPLATE_DIR / "fhgm.json").read_bytes()
        try:
            path.write_bytes(original + b"\n")  # a single byte breaks the pin
            with self.assertRaises(SystemExit) as ctx:
                make_cedar.render("fhgm")
            self.assertIn("pinned", str(ctx.exception))
        finally:
            path.write_bytes(original)
        self.assertEqual(make_cedar.render("fhgm").encode("utf-8"), committed,
                         "restoring the snapshot bytes must restore the template")

    # -- visibility --------------------------------------------------------------

    def test_draft_status_is_visible_and_released_templates_have_no_status_key(self):
        for stem in DRAFT_STEMS:
            template = load_template(stem)
            self.assertEqual(template["status"], "draft", f"{stem}: no embedded status")
            for key in ("title", "description", "schema:description"):
                self.assertIn("DRAFT", template[key], f"{stem}: {key} hides the draft state")
            self.assertNotIn("release v", template["title"])
            self.assertIn(f"contract schemaVersion {entry_version(stem)}",
                          template["description"])
        for stem in STEMS:
            self.assertNotIn("status", load_template(stem),
                             f"{stem}: released templates carry no contract-status key")

    def test_no_w3id_url_appears_in_draft_templates(self):
        for stem in DRAFT_STEMS:
            raw = (TEMPLATE_DIR / f"{stem}.json").read_text(encoding="utf-8")
            self.assertNotIn("w3id.org", raw,
                             f"{stem}: draft templates must not cite any w3id URL")
            self.assertNotIn("https://w3id", raw,
                             f"{stem}: draft templates must not cite any w3id URL")
            # Prose may NAME the w3id form (the FHT draft schema's own field
            # description does); what must not appear is a resolvable w3id URL.
        for stem in STEMS:  # sanity: the rule is draft-only; released pin w3id URLs
            self.assertIn("w3id.org", (TEMPLATE_DIR / f"{stem}.json")
                          .read_text(encoding="utf-8"))

    def test_fht_pins_the_raw_main_contract_url_and_draft_version(self):
        template = load_template("fht")
        literals = (template["properties"][make_cedar.form_field_name("schema")]
                    ["_valueConstraints"])
        self.assertEqual([entry["label"] for entry in literals["literals"]], [FHT_RAW_MAIN])
        self.assertEqual(literals["defaultValue"], FHT_RAW_MAIN)
        version_literals = (template["properties"]["schemaVersion"]
                            ["_valueConstraints"]["literals"])
        self.assertEqual([entry["label"] for entry in version_literals],
                         [DRAFT_PROVENANCE["snapshots"]["fht"]["contractVersion"]])
        for source_key in ("repository", "ref", "commit", "retrieved", "local",
                           "gitBlobSha1"):
            self.assertIn(DRAFT_PROVENANCE["snapshots"]["fht"][source_key],
                          template["description"], f"fht: provenance omits {source_key}")
        self.assertEqual(template["pav:derivedFrom"], FHT_RAW_MAIN)
        self.assertEqual(template["pav:version"], "1.0.0")

    def test_fhgm_template_authors_a_model_record_not_a_file_header(self):
        template = load_template("fhgm")
        schema = contract_schema("fhgm")
        self.assertNotIn("schema", schema["properties"])
        self.assertNotIn("schemaVersion", schema["properties"])
        self.assertNotIn("checksum", schema["properties"])
        self.assertNotIn(make_cedar.form_field_name("schema"), template["properties"])
        for phrase in ("ONE FHGM model record", "x-fhgm-models", "bioheaders combine",
                       "not a toolkit feature yet"):
            self.assertIn(phrase, template["description"],
                          f"fhgm: provenance transport wording missing: {phrase}")
        self.assertEqual(template["pav:version"], "0.1.0")
        self.assertIn(DRAFT_PROVENANCE["snapshots"]["fhgm"]["commit"],
                      template["description"])

    def test_fht_extension_pattern_property_stays_out_and_is_documented(self):
        snapshot = contract_schema("fht")
        slots = list(snapshot.get("patternProperties", {}))
        self.assertEqual(slots, ["^x-[A-Za-z0-9][A-Za-z0-9_.-]*$"],
                         "the FHT draft's open slot moved; revisit the omission")
        template = load_template("fht")
        self.assertIn("patternProperty", template["description"])
        self.assertIn("intentionally omitted", template["description"])

    # -- coverage ------------------------------------------------------------

    def test_draft_field_coverage(self):
        """Every contract path has a form slot; census matches the documented size."""
        expected = {"fht": 66, "fhgm": 32}  # named paths; FHT's x- slot is omitted by design

        def check(self_, stem, scope_node, cedar_node, count, defs, root=False):
            for member, member_schema in scope_node.get("properties", {}).items():
                form_name = make_cedar.form_field_name(member) if root else member
                self.assertIn(form_name, cedar_node["properties"],
                              f"{stem}: contract field {member} missing from the form")
                count.append(form_name)
                form = cedar_node["properties"][form_name]
                target = make_cedar.deref(member_schema, defs)
                alternatives = target.get("anyOf", [])
                if any(not (set(branch) <= {"required", "description"})
                       for branch in alternatives):
                    target = make_cedar.Generator(stem, contract_schema(stem),
                                                  make_cedar.load_contracts()[stem]
                                                  ).normalize(target)
                if target.get("type") == "array":
                    form = form["items"]
                    target = make_cedar.deref(target.get("items", {}), defs)
                if target.get("properties"):
                    check(self_, stem, target, form, count, defs)

        for stem in DRAFT_STEMS:
            schema = contract_schema(stem)
            defs = schema.get("$defs") or {}
            count = []
            check(self, stem, schema, load_template(stem), count, defs, root=True)
            self.assertEqual(len(count), expected[stem],
                             f"{stem}: census mismatch - {sorted(count)}")

    # -- round trips -----------------------------------------------------------

    def test_fht_filled_export_round_trips_and_validates_against_draft(self):
        record = copy.deepcopy(FHT_FIXTURE)
        template, artifact = self.build_artifact("fht", record)
        Draft4Validator.check_schema(template)
        errors = sorted(Draft4Validator(template, format_checker=FormatChecker())
                        .iter_errors(artifact), key=lambda e: e.json_path)
        self.assertEqual([], [e.message for e in errors],
                         "filled FHT export failed generated-template validation")
        flat = make_cedar.flatten_export(artifact)
        self.assertEqual(flat, record, "FHT CEDAR export round trip lost data")
        schema = contract_schema("fht")
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker())
                        .iter_errors(flat), key=lambda e: e.json_path)
        self.assertEqual([], [e.message for e in errors],
                         "flattened FHT record failed draft schema validation")

    def test_fhgm_filled_exports_round_trip_and_validate_against_draft(self):
        for label, record in (("minimal", FHGM_FIXTURE_MINIMAL),
                              ("predecessor revision", FHGM_FIXTURE_REVISED)):
            record = copy.deepcopy(record)
            template, artifact = self.build_artifact("fhgm", record)
            self.assertNotIn(make_cedar.form_field_name("schema"), artifact,
                             "FHGM export must round-trip with no schema URL at all")
            Draft4Validator.check_schema(template)
            errors = sorted(Draft4Validator(template, format_checker=FormatChecker())
                            .iter_errors(artifact), key=lambda e: e.json_path)
            self.assertEqual([], [e.message for e in errors],
                             f"{label}: filled FHGM export failed template validation")
            flat = make_cedar.flatten_export(artifact)
            self.assertEqual(flat, record, f"{label}: FHGM round trip lost data")
            schema = contract_schema("fhgm")
            Draft202012Validator.check_schema(schema)
            errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker())
                            .iter_errors(flat), key=lambda e: e.json_path)
            self.assertEqual([], [e.message for e in errors],
                             f"{label}: flattened FHGM record failed draft schema validation")


if __name__ == "__main__":
    unittest.main()
