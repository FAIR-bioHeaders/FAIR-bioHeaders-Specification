# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Generate CEDAR workbench authoring templates from the released FH* schemas.

CEDAR (https://metadatacenter.org/) is a metadata-authoring workbench: its
templates give curators a guided form with field help, requiredness and
controlled values. The form is NOT a contract. ``fhr.json``, ``fhp.json`` and
``fhgff3.json`` stay the validation authority and the ``bioheaders`` toolkit
stays the validator and writer (FAIR-bioHeaders-Specification#162, decision
Option A of 2026-11-12).

One template per released header type at the CURRENT ``schemaVersion`` named by
``schemas/versions.json`` (the same registry the website reference build and
``tests/test_schema_versions.py`` follow). Every template embeds its contract
``schemaVersion``, the fixed versioned schema URL (the w3id form recommended by
docs/SCHEMA-VERSIONS.md rule V3) and the SHA-256 of the exact committed schema
bytes it was derived from, so a template that has fallen behind a schema edit
or release is visible in its own provenance line and fails ``--check``.

Pattern-defined extension slots (docs/FORMAT.md R15) are deliberately OMITTED:
they mean nothing to the standard, a form cannot guide an open-ended key, and
offering them in the authoring surface would invite values the contract does
not check. Curators who need them write YAML by hand.

The emitted shape is the CEDAR template JSON-LD format version 1.6.0: the
required keys, ``_ui``/``_valueConstraints`` blocks and the field, element and
multi-instance forms follow the CEDAR meta-schemas and reference templates in
https://github.com/metadatacenter/cedar-model-validation-library (``schema/
template.json``, ``schema/templateElement.json``, ``schema/literalTemplateField.
json`` and ``src/test/resources/templates/``). ``@id`` and the ``pav``/``oslc``
provenance stamps are ``null`` and ``bibo:status`` is ``bibo:draft`` because
these artifacts have not been published to any CEDAR instance; publication,
account ownership and identifier assignment are maintainer actions outside
this repository (#162). The synthetic per-field property URIs live under
``https://w3id.org/fair-bioheaders/templates/cedar/<type>#`` purely so the
generated ``@context`` mappings are deterministic; the CEDAR workbench assigns
its own property URIs when a template is published.

Commands, from the repository root:

    python scripts/make_cedar.py            # regenerate templates/cedar/*.json
    python scripts/make_cedar.py --check    # CI drift check (no writes)

``--check`` regenerates in memory and exits 1 with a unified diff if a
committed template differs (the scripts/make_jsonld.py pattern). Like that
script, this one uses only the standard library and never the network.
``flatten_export`` (imported by tests/test_cedar.py, also
``python scripts/make_cedar.py --flatten FILE``) converts a CEDAR artifact
export back into the plain FH* JSON record shape so it can round-trip through
``bioheaders validate`` before ``bioheaders combine``.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS_PATH = ROOT / "schemas" / "versions.json"
OUT_DIR = ROOT / "templates" / "cedar"

DRAFT04 = "http://json-schema.org/draft-04/schema#"
CEDAR = "https://schema.metadatacenter.org/core/"
CEDAR_TEMPLATE = CEDAR + "Template"
CEDAR_FIELD = CEDAR + "TemplateField"
CEDAR_ELEMENT = CEDAR + "TemplateElement"
CEDAR_FORMAT_VERSION = "1.6.0"
CEDAR_CONTEXT = {
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "pav": "http://purl.org/pav/",
    "bibo": "http://purl.org/ontology/bibo/",
    "oslc": "http://open-services.net/ns/core#",
    "schema": "http://schema.org/",
    "schema:name": {"@type": "xsd:string"},
    "schema:description": {"@type": "xsd:string"},
    "pav:createdOn": {"@type": "xsd:dateTime"},
    "pav:createdBy": {"@type": "@id"},
    "pav:lastUpdatedOn": {"@type": "xsd:dateTime"},
    "oslc:modifiedBy": {"@type": "@id"},
}
FIELD_CONTEXT = dict(CEDAR_CONTEXT, **{
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "skos:prefLabel": {"@type": "xsd:string"},
    "skos:altLabel": {"@type": "xsd:string"},
})
# The fixed JSON-LD bookkeeping every CEDAR template occurrence carries; the
# contract's own required list follows it in the template's "required" array.
FIXED_REQUIRED = ["@context", "@id", "schema:isBasedOn", "schema:name",
                  "schema:description", "pav:createdOn", "pav:createdBy",
                  "pav:lastUpdatedOn", "oslc:modifiedBy"]
BOOKKEEPING = ["schema:isBasedOn", "schema:name", "schema:description", "pav:createdOn",
               "pav:createdBy", "pav:lastUpdatedOn", "oslc:modifiedBy", "pav:derivedFrom"]
TYPE_DESC = {"oneOf": [{"type": "string", "format": "uri"},
                       {"type": "array", "minItems": 1,
                        "items": {"type": "string", "format": "uri"},
                        "uniqueItems": True}]}
NULL_URI = {"type": ["string", "null"], "format": "uri"}
NULL_DATETIME = {"type": ["string", "null"], "format": "date-time"}

# Registry file -> template file stem, matching schemas/versions.json.
TYPES = {"FHR": "fhr", "FHP": "fhp", "FHGFF3": "fhgff3"}
FORM_FIELD_ALIASES = {"schema": "header_schema"}


def form_field_name(name: str) -> str:
    """Avoid CEDAR context namespace collisions while retaining contract names."""
    return FORM_FIELD_ALIASES.get(name, name)


def contract_field_name(name: str) -> str:
    """Restore a contract key from its non-conflicting form alias."""
    return next((contract for contract, alias in FORM_FIELD_ALIASES.items()
                 if alias == name), name)

# ---------------------------------------------------------------------------
# Curated wording. Units follow docs/FORMAT.md and the schema descriptions;
# the fallback descriptions for undescribed FHR members are the wording the
# shared core objects give for the same members (schemas/core.yaml, and the
# generated $defs in fhp.json/fhgff3.json). Nothing here adds contract meaning.
# ---------------------------------------------------------------------------

UNITS = {
    "vitalStats.L50": "contigs", "vitalStats.L90": "contigs",
    "vitalStats.N50": "base pairs", "vitalStats.N90": "base pairs",
    "vitalStats.scaffoldL50": "scaffolds", "vitalStats.scaffoldL90": "scaffolds",
    "vitalStats.scaffoldN50": "base pairs", "vitalStats.scaffoldN90": "base pairs",
    "vitalStats.totalBasePairs": "base pairs",
    "vitalStats.numberContigs": "contigs", "vitalStats.numberScaffolds": "scaffolds",
    "vitalStats.gcContent": "percent of G/C bases (0 to 100, not a fraction)",
    "sequenceStats.sequenceCount": "sequences", "sequenceStats.geneCount": "genes",
    "sequenceStats.totalResidues": "amino-acid residues",
    "completeness.completeSingle": "BUSCO groups", "completeness.completeDuplicated": "BUSCO groups",
    "completeness.fragmented": "BUSCO groups", "completeness.missing": "BUSCO groups",
    "completeness.total": "BUSCO groups",
    "featureCounts[].count": "features",
}

FALLBACK_DESCRIPTIONS = {
    "taxon.name": "Name of the species",
    "taxon.uri": "Taxonomy URI",
    "accessionID.name": "Accession name",
    "accessionID.url": "Accession URL",
    "metadataAuthor[].name": "Name of the person or organization",
    "metadataAuthor[].uri": "ORCID URI",
    "assemblyAuthor[].name": "Name of the person or organization",
    "assemblyAuthor[].uri": "ORCID URI",
    # fhr.json's inline assemblySoftware item members; the wording is the
    # shared core Software object's (schemas/core.yaml, fhp.json $defs/Software).
    "assemblySoftware[].name": "Name of the software",
    "assemblySoftware[].uri": "URI of the software",
    "assemblySoftware[].version": "Version of the software",
    "assemblySoftware[].commandLineOption": "Command-line options given to the software, in order",
}

AUTHORITY = {
    "taxon.uri": "Look the taxon up in NCBI Taxonomy and cite it through identifiers.org; never guess the identifier.",
    "metadataAuthor[].uri": "A real ORCID iD; verify it at orcid.org.",
    "assemblyAuthor[].uri": "A real ORCID iD; verify it at orcid.org.",
    "seqcol_id": "The GA4GH refget sequence collection digest as supplied by the user; FHR does not calculate it.",
    "checksum": "Computed by `bioheaders combine` over the exact file bytes; never write or edit a checksum by hand.",
    "scholarlyArticle": "A registered DOI without the resolver prefix (for example 10.5281/zenodo.6762550).",
}

CAVEATS = {
    "FHR.assemblySoftware": "The contract also accepts a legacy plain-string form (docs/FORMAT.md); this guided form writes the structured object alternative only.",
    "FHP.geneticCode": "The contract allows only the ranges 1-6, 9-16 and 21-33; the numeric input cannot block the gaps, so validate before combining.",
    "FHGFF3.genomeReference": "The contract requires either genomeReference or a derivedFrom item with relationship annotates on an FHR parent; supply at least one (docs/FHGFF3.md).",
    "FHGFF3.derivedFrom": "At most one derivedFrom item may use relationship annotates, and then only with headerType FHR; the form does not enforce this, `bioheaders validate` does.",
}

# Display labels only; the template property keys stay the exact contract names.
LABELS = {
    "seqcol_id": "SeqCol ID",
    "gcContent": "GC content",
    "uri": "URI",
    "url": "URL",
    "name": "Name",
    "soVersion": "SO version",
}

SHA_MARKER = "source schema SHA-256:"
URL_MARKER = "contract URL:"
VERSION_MARKER = "contract schemaVersion"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_registry():
    """Current release per type: (contract schemaVersion, fixed schema URL, release tag)."""
    registry = json.loads(VERSIONS_PATH.read_text(encoding="utf-8"))
    release = registry["current"]
    out = {}
    for header_type, stem in TYPES.items():
        version = registry["releases"][release][header_type]
        url = f"https://w3id.org/fair-bioheaders/{registry['w3id'][header_type]}/{release}"
        out[stem] = {"type": header_type, "schemaVersion": version, "url": url,
                     "release": release, "file": registry["files"][header_type]}
    return out


def deref(node: dict, defs: dict) -> dict:
    """Resolve one local ``$ref``, letting a sibling ``description`` win.

    Same resolution rule the published contracts rely on (the website's
    scripts/schema_fields.py deref): a definition's description carries through
    unless the property states its own.
    """
    if not isinstance(node, dict):
        return {}
    if "$ref" not in node:
        return dict(node)
    name = node["$ref"].rsplit("/", 1)[-1]
    merged = dict(defs.get(name, {}))
    for key, value in node.items():
        if key != "$ref":
            merged[key] = value
    if not merged.get("description") and defs.get(name, {}).get("description"):
        merged["description"] = defs[name]["description"]
    return merged


def label_for(name: str) -> str:
    if name in LABELS:
        return LABELS[name]
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).replace("_", " ")
    return spaced[:1].upper() + spaced[1:]


class Generator:
    """Walks one published schema and emits its CEDAR template."""

    def __init__(self, stem: str, schema: dict, meta: dict):
        self.stem = stem
        self.schema = schema
        self.meta = meta
        self.defs = schema.get("$defs") or schema.get("definitions") or {}

    # -- descriptions -------------------------------------------------------

    def describe(self, path: str, node: dict, inherited: str | None = None) -> str:
        parts = []
        description = (node.get("description") or FALLBACK_DESCRIPTIONS.get(path)
                       or inherited)
        if description:
            parts.append(description.rstrip("."))
        if path == "schema":
            parts.append(f"This template fixes the {self.meta['type']} contract URL to the "
                         f"released {self.meta['release']} version "
                         f"({self.meta['url']}); docs/SCHEMA-VERSIONS.md allows other URLs "
                         "for existing records")
        else:
            caveat = CAVEATS.get(f"{self.meta['type']}.{path}")
            if caveat:
                parts.append(caveat)
        authority = AUTHORITY.get(path)
        if authority:
            parts.append(authority)
        parts = [part.rstrip(".") for part in parts if part]
        if not parts:
            raise SystemExit(f"make_cedar: {self.meta['type']}.{path} has no description; "
                             "the form must not invent one - curate the schema or add a "
                             "FALLBACK_DESCRIPTIONS entry quoting it")
        return ". ".join(parts) + "."

    # -- leaf fields --------------------------------------------------------

    def literal_field(self, path: str, name: str, node: dict, required: bool,
                      inherited: str | None = None) -> dict:
        """A single-valued CEDAR TemplateField for a scalar schema node."""
        node = deref(node, self.defs)
        kind = node.get("type")
        enum = node.get("enum")
        if enum and path == "schemaVersion":
            # One template targets exactly one contract version (issue #162
            # decision: current schemaVersion only); the older value in the
            # released enum belongs to the older template line.
            enum = [self.meta["schemaVersion"]]
        if path == "schema":
            # The template pins the fixed released contract URL (V3 w3id form).
            enum = [self.meta["url"]]
        vc = {"requiredValue": required}
        if enum is None and kind == "string":
            # A closed value set spelled out as a regex alternation (FHR
            # masking) becomes radio literals: derived from the schema bytes,
            # never curated here.
            group = re.fullmatch(r"^\^\(([a-z0-9|-]+(?:\|[a-z0-9|-]+)+)\)\$$",
                                 node.get("pattern", ""))
            if group:
                enum = group.group(1).split("|")
        if enum:
            ui = {"inputType": "radio"}
            vc["literals"] = [{"label": str(value)} for value in enum]
            if len(enum) == 1:
                vc["defaultValue"] = str(enum[0])
        elif node.get("format") == "date":
            ui = {"inputType": "temporal", "dateType": "single-date",
                  "temporalGranularity": "day"}
            vc["temporalType"] = "xsd:date"
            vc["regex"] = r"^\d{4}-\d{2}-\d{2}$"
        elif kind in ("integer", "number"):
            ui = {"inputType": "numeric"}
            vc["numberType"] = "xsd:long" if kind == "integer" else "xsd:double"
            for schema_key, cedar_key in (("minimum", "minValue"), ("maximum", "maxValue")):
                if schema_key in node:
                    vc[cedar_key] = node[schema_key]
        else:
            ui = {"inputType": "textfield"}
        for schema_key, cedar_key in (("pattern", "regex"), ("minLength", "minLength"),
                                      ("maxLength", "maxLength")):
            if not enum and schema_key in node and cedar_key not in vc:
                vc[cedar_key] = node[schema_key]
        unit = UNITS.get(path)
        if unit:
            vc["unitOfMeasure"] = unit
        value_props = {"@type": TYPE_DESC, "@value": {"type": ["string", "null"]},
                       "rdfs:label": {"type": ["string", "null"]}}
        value_required = ["@value"]
        if ui["inputType"] == "numeric":
            value_props["@type"] = {"type": "string", "format": "uri"}
            value_required = ["@value", "@type"]
        return {
            "$schema": DRAFT04,
            "@type": CEDAR_FIELD,
            "@context": FIELD_CONTEXT,
            "@id": None,
            "type": "object",
            "title": f"{label_for(name)} field schema",
            "description": self.describe(path, node, inherited),
            "_ui": ui,
            "_valueConstraints": vc,
            "properties": value_props,
            "required": value_required,
            "schema:name": name,
            "schema:description": self.describe(path, node, inherited),
            "pav:createdOn": None,
            "pav:createdBy": None,
            "pav:lastUpdatedOn": None,
            "oslc:modifiedBy": None,
            "schema:schemaVersion": CEDAR_FORMAT_VERSION,
            "additionalProperties": False,
        }

    # -- containers ---------------------------------------------------------

    def element(self, path: str, name: str, node: dict, required: bool,
                inherited: str | None = None) -> dict:
        """A CEDAR TemplateElement for a schema object with properties."""
        node = deref(node, self.defs)
        inner_required = list(node.get("required", []))
        if node.get("additionalProperties") is not False:
            raise self.refuse(node, "an open object; the form would have to allow keys "
                                    "the contract does not name")
        fields = {}
        context_map = {}
        order = []
        for member, member_node in node.get("properties", {}).items():
            member_path = f"{path}.{member}"
            order.append(member)
            fields[member] = self.field(member_path, member, member_node,
                                        member in inner_required)
            context_map[member] = {"enum": [self.property_uri(member_path)]}
        description = self.describe(path, node, inherited)
        return {
            "$schema": DRAFT04,
            "@type": CEDAR_ELEMENT,
            "@context": CEDAR_CONTEXT,
            "@id": None,
            "type": "object",
            "title": f"{label_for(name)} element schema",
            "description": description,
            "schema:name": name,
            "schema:description": description,
            "_ui": {
                "order": order,
                "propertyLabels": {member: label_for(member) for member in order},
                "propertyDescriptions": {member: fields[member]["description"]
                                         if "description" in fields[member]
                                         else fields[member]["items"]["description"]
                                         for member in order},
            },
            "properties": {
                "@context": {
                    "type": "object",
                    "properties": context_map,
                    "additionalProperties": False,
                    "required": list(order),
                },
                "@id": {"type": "string", "format": "uri"},
                "@type": TYPE_DESC,
                **fields,
            },
            "required": ["@context", "@id"] + [m for m in order if m in inner_required],
            "pav:createdOn": None,
            "pav:createdBy": None,
            "pav:lastUpdatedOn": None,
            "oslc:modifiedBy": None,
            "schema:schemaVersion": CEDAR_FORMAT_VERSION,
            "additionalProperties": False,
            "pav:version": self.meta["schemaVersion"] + ".0",
            "bibo:status": "bibo:draft",
        }

    def field(self, path: str, name: str, node: dict, required: bool) -> dict:
        """Dispatch one schema property to its CEDAR form."""
        node = deref(node, self.defs)
        target = self.normalize(node)
        if target.get("type") == "array":
            items = deref(target.get("items", {}), self.defs)
            inherited = (node.get("description") or target.get("description")
                         or items.get("description") or FALLBACK_DESCRIPTIONS.get(path))
            if items.get("type") == "object" or items.get("properties"):
                inner = self.element(f"{path}[]", name, items, False, inherited)
            else:
                inner = self.literal_field(f"{path}[]", name, items, True, inherited)
            inner["description"] = self.describe(path, node, inherited)
            inner["schema:description"] = inner["description"]
            return {"type": "array", "minItems": 0, "items": inner}
        if target.get("type") == "object" or target.get("properties"):
            return self.element(path, name, target, required)
        return self.literal_field(path, name, target, required)

    def normalize(self, node: dict) -> dict:
        """Reduce the shapes the released contracts use to object/array/scalar.

        anyOf alternatives are resolved deliberately (and their limits are
        stated in the field description via CAVEATS):
        - one object/array branch plus string branches: take the structured
          alternative (FHR assemblySoftware);
        - numeric range branches: one numeric field spanning the ranges
          (FHP geneticCode);
        anything else is refused so a future contract shape fails the drift
        check loudly instead of being averaged away silently.
        """
        if "anyOf" not in node:
            return node
        branches = [deref(branch, self.defs) for branch in node["anyOf"]]
        structured = [b for b in branches if b.get("type") in ("array", "object")
                      or b.get("properties")]
        if structured:
            if len(structured) != 1:
                raise self.refuse(node, "multiple structured anyOf branches")
            return structured[0]
        if all(b.get("type") in ("integer", "number") or not b.get("type") for b in branches):
            merged = {"type": "integer" if all(b.get("type") != "number" for b in branches)
                      else "number"}
            bounds = [(b.get("minimum"), b.get("maximum")) for b in branches]
            lower = [lo for lo, _ in bounds if lo is not None]
            upper = [hi for _, hi in bounds if hi is not None]
            if lower:
                merged["minimum"] = min(lower)
            if upper:
                merged["maximum"] = max(upper)
            for key in ("description",):
                if key in node:
                    merged[key] = node[key]
            return merged
        raise self.refuse(node, "unhandled anyOf combination")

    def refuse(self, node, why):
        return SystemExit(f"make_cedar: cannot derive a form field from a schema node ({why}); "
                          "extend make_cedar.py deliberately - do not average away contract "
                          "alternatives")

    def property_uri(self, path: str) -> str:
        return (f"https://w3id.org/fair-bioheaders/templates/cedar/{self.stem}"
                f"#/{path.replace('[]', '')}")

    # -- template root -------------------------------------------------------

    def provenance(self) -> str:
        digest = sha256_file(ROOT / self.meta["file"])
        return (f"CEDAR authoring template for FAIR-bioHeaders {self.meta['type']} "
                f"{VERSION_MARKER} {self.meta['schemaVersion']} ({URL_MARKER} "
                f"{self.meta['url']}, {self.meta['release']}). Generated by "
                f"scripts/make_cedar.py from the committed {self.meta['file']} bytes, "
                f"{SHA_MARKER} {digest}; do not hand edit. The JSON Schema and the "
                f"bioheaders toolkit remain the contract and validator; this form is "
                f"an authoring aid (#162). Pattern-defined extension slots "
                f"(docs/FORMAT.md R15) are intentionally omitted.")

    def template(self) -> dict:
        properties = self.schema["properties"]
        required = list(self.schema.get("required", []))
        fields = {}
        context_map = {}
        order = []
        for name, node in properties.items():
            if name.startswith("x-") or name == "patternProperties":
                raise SystemExit(f"make_cedar: extension field {name} must not reach the form")
            form_name = form_field_name(name)
            order.append(form_name)
            fields[form_name] = self.field(name, name, node, name in required)
            context_map[form_name] = {"enum": [self.property_uri(name)]}
        context_properties = {
            "rdfs": {"type": "string", "format": "uri",
                     "enum": ["http://www.w3.org/2000/01/rdf-schema#"]},
            "xsd": {"type": "string", "format": "uri", "enum": [CEDAR_CONTEXT["xsd"]]},
            "pav": {"type": "string", "format": "uri", "enum": [CEDAR_CONTEXT["pav"]]},
            "schema": {"type": "string", "format": "uri", "enum": [CEDAR_CONTEXT["schema"]]},
            "oslc": {"type": "string", "format": "uri", "enum": [CEDAR_CONTEXT["oslc"]]},
            "skos": {"type": "string", "format": "uri",
                     "enum": ["http://www.w3.org/2004/02/skos/core#"]},
            "rdfs:label": {"type": "object",
                           "properties": {"@type": {"type": "string",
                                                    "enum": ["xsd:string"]}}},
            "schema:isBasedOn": {"type": "object",
                                 "properties": {"@type": {"type": "string",
                                                          "enum": ["@id"]}}},
            "schema:name": {"type": "object",
                            "properties": {"@type": {"type": "string",
                                                     "enum": ["xsd:string"]}}},
            "schema:description": {"type": "object",
                                   "properties": {"@type": {"type": "string",
                                                            "enum": ["xsd:string"]}}},
            "pav:createdOn": {"type": "object",
                              "properties": {"@type": {"type": "string",
                                                       "enum": ["xsd:dateTime"]}}},
            "pav:createdBy": {"type": "object",
                              "properties": {"@type": {"type": "string",
                                                       "enum": ["@id"]}}},
            "pav:lastUpdatedOn": {"type": "object",
                                  "properties": {"@type": {"type": "string",
                                                           "enum": ["xsd:dateTime"]}}},
            "oslc:modifiedBy": {"type": "object",
                                "properties": {"@type": {"type": "string",
                                                         "enum": ["@id"]}}},
            "skos:notation": {"type": "object",
                              "properties": {"@type": {"type": "string",
                                                       "enum": ["xsd:string"]}}},
            "pav:derivedFrom": {"type": "object",
                                "properties": {"@type": {"type": "string",
                                                         "enum": ["@id"]}}},
            **context_map,
        }
        root_properties = {
            "@context": {
                "type": "object",
                "properties": context_properties,
                "required": list(context_properties),
                "additionalProperties": False,
            },
            "@id": NULL_URI,
            "@type": TYPE_DESC,
            "schema:isBasedOn": {"type": "string", "format": "uri"},
            "schema:name": {"type": "string", "minLength": 1},
            "schema:description": {"type": "string"},
            "pav:createdOn": NULL_DATETIME,
            "pav:createdBy": NULL_URI,
            "pav:lastUpdatedOn": NULL_DATETIME,
            "oslc:modifiedBy": NULL_URI,
            "pav:derivedFrom": {"type": "string", "format": "uri"},
        }
        root_properties.update(fields)
        description = self.provenance()
        return {
            "$schema": DRAFT04,
            "@type": CEDAR_TEMPLATE,
            "@context": CEDAR_CONTEXT,
            "@id": None,
            "type": "object",
            "title": f"FAIR-bioHeaders {self.meta['type']} {self.meta['schemaVersion']} "
                     f"(release {self.meta['release']}) CEDAR template",
            "description": description,
            "schema:name": f"FAIR-bioHeaders {self.meta['type']} {self.meta['schemaVersion']}",
            "schema:description": description,
            "schema:identifier": (f"https://w3id.org/fair-bioheaders/templates/cedar/"
                                  f"{self.stem}/{self.meta['schemaVersion']}"),
            "_ui": {
                "order": order,
                "propertyLabels": {name: label_for(contract_field_name(name)) for name in order},
                "propertyDescriptions": {
                    name: (node.get("description") or node["items"].get("description")
                           if node.get("type") == "array" else node.get("description"))
                    for name, node in fields.items()},
            },
            "properties": root_properties,
            "required": FIXED_REQUIRED + [
                form_field_name(name) for name in required if name != "checksum"],
            "pav:createdOn": None,
            "pav:createdBy": None,
            "pav:lastUpdatedOn": None,
            "oslc:modifiedBy": None,
            "pav:version": self.meta["schemaVersion"] + ".0",
            "pav:derivedFrom": self.meta["url"],
            "schema:schemaVersion": CEDAR_FORMAT_VERSION,
            "bibo:status": "bibo:draft",
            "additionalProperties": False,
        }


def render(stem: str) -> str:
    registry = load_registry()
    meta = registry[stem]
    schema = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
    template = Generator(stem, schema, meta).template()
    return json.dumps(template, indent=2, ensure_ascii=True) + "\n"


def generate_all():
    """Map output path -> rendered bytes for every released type."""
    return {OUT_DIR / f"{stem}.json": render(stem).encode("utf-8")
            for stem in TYPES.values()}


# ---------------------------------------------------------------------------
# CEDAR export round trip
# ---------------------------------------------------------------------------

# Keys a CEDAR artifact instance carries beside the contract fields. Only the
# JSON-LD/CEDAR bookkeeping keys are dropped when flattening; contract names
# such as ``description`` (FHP/FHGFF3 Source) must survive the round trip.
RESERVED_KEYS = set(FIXED_REQUIRED + BOOKKEEPING + [
    "@version", "skos:prefLabel", "skos:altLabel", "bibo:status", "pav:version",
    "schema:identifier", "schema:schemaVersion"])


def _coerce(entry: dict):
    value = entry.get("@value")
    datatype = entry.get("@type")
    if isinstance(value, str) and datatype in ("xsd:long", "xsd:int", "xsd:short", "xsd:byte"):
        return int(value)
    if isinstance(value, str) and datatype in ("xsd:double", "xsd:float", "xsd:decimal"):
        return float(value)
    return value


def _contract_for_export(artifact: dict):
    schema_value = artifact.get(form_field_name("schema"), artifact.get("schema"))
    if isinstance(schema_value, dict) and "@value" in schema_value:
        schema_value = _coerce(schema_value)
    if not isinstance(schema_value, str):
        raise ValueError("CEDAR export is missing its FAIR-bioHeaders schema URL")
    for stem, meta in load_registry().items():
        if schema_value == meta["url"]:
            schema = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
            return stem, meta, schema
    raise ValueError(f"unsupported FAIR-bioHeaders schema URL: {schema_value}")


def _contract_node(node, generator):
    node = deref(node, generator.defs)
    if "anyOf" in node and not (node.get("type") == "object" and node.get("properties")):
        node = generator.normalize(node)
    return node


def _flatten_value(value, node, generator):
    node = _contract_node(node, generator)
    if isinstance(value, list):
        item_node = node.get("items", {})
        return [_flatten_value(item, item_node, generator) for item in value]
    if isinstance(value, dict):
        if "@list" in value:
            return [_flatten_value(item, node.get("items", {}), generator)
                    for item in value["@list"]]
        if "@value" in value:
            return _coerce(value)
        return _flatten_object(value, node, generator)
    return value


def _flatten_object(artifact: dict, node: dict, generator, root=False) -> dict:
    node = _contract_node(node, generator)
    properties = node.get("properties", {})
    required = set(node.get("required", []))
    record = {}
    for key, value in artifact.items():
        if key in RESERVED_KEYS or key.startswith("@"):
            continue
        contract_key = contract_field_name(key) if root else key
        contract_node = properties.get(contract_key, {})
        flattened = _flatten_value(value, contract_node, generator)
        if root and contract_key == "checksum" and flattened in (None, ""):
            continue
        if flattened is None and contract_key not in required:
            continue
        record[contract_key] = flattened
    return record


def flatten_export(artifact: dict) -> dict:
    """Turn a CEDAR artifact instance export into the plain FH* JSON record.

    Drops the JSON-LD/CEDAR bookkeeping keys and unwraps ``{"@value": ...}``
    (with the numeric datatypes the generated fields declare). Empty optional
    values are omitted according to the selected contract's requiredness, and
    an empty root checksum is omitted for ``bioheaders combine`` to calculate.
    Supplied nested parent checksums are retained. The toolkit remains the
    authority: this helper only restores the record shape; it validates
    nothing.
    """
    stem, meta, schema = _contract_for_export(artifact)
    generator = Generator(stem, schema, meta)
    return _flatten_object(artifact, schema, generator, root=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def check_output(name: str, payload: str, errors: list) -> None:
    path = ROOT / name
    committed = path.read_text(encoding="utf-8") if path.exists() else ""
    if committed != payload:
        errors.extend(difflib.unified_diff(
            committed.splitlines(keepends=True), payload.splitlines(keepends=True),
            fromfile=f"a/{name}", tofile=f"b/{name}"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="regenerate in memory and fail on drift (no writes)")
    parser.add_argument("--flatten", metavar="FILE",
                        help="print the FH* JSON record flattened from a CEDAR artifact export")
    args = parser.parse_args(argv)
    if args.flatten:
        artifact = json.loads(Path(args.flatten).read_text(encoding="utf-8"))
        print(json.dumps(flatten_export(artifact), indent=2))
        return 0
    if args.check:
        errors = []
        for path, payload in generate_all().items():
            check_output(str(path.relative_to(ROOT)), payload.decode("utf-8"), errors)
        if errors:
            sys.stderr.writelines(errors)
            sys.stderr.write("make_cedar: templates/cedar/ has drifted from the committed "
                             "schemas; run python scripts/make_cedar.py\n")
            return 1
        print("make_cedar: CEDAR templates are up to date")
        return 0
    for path, payload in generate_all().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
