#!/usr/bin/env python3
"""NPP projection fixture harness for #249 (round NPP-2, #292).

Builds and checks the deterministic publication outputs (JATS table-wrap
fragment, offline Crossref dataset fragment, projection report) for the FHR
publication slice, and runs the negative fixtures.

This is a TEST FIXTURE GENERATOR, not a shipped exporter: it exists so the
crosswalk's claims are machine-checked. It performs no registration and makes
no adoption or official-profile claim. Schema validation uses this repository's
own fhr.json (contract 2.1); file integrity recomputes SHA-512/256 over the
fixture bytes - if the digest implementation is unavailable the check FAILS
loudly rather than passing vacuously.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "mappings" / "proposals" / "fixtures" / "npp-fhr-publication"
CROSSWALK = ROOT / "mappings" / "proposals" / "npp-fhr-publication.yml"
CTX_SCHEMA = ROOT / "mappings" / "proposals" / "npp-fhr-publication.context.schema.json"

UNIT_LABELS = {  # units asserted by the contract itself (FORMAT.md vitalStats definitions)
    "totalBasePairs": "bp", "L50": "bp", "N50": "bp", "L90": "bp", "N90": "bp",
    "scaffoldN50": "bp", "scaffoldN90": "bp", "scaffoldL50": "bp", "scaffoldL90": "bp",
    "gcContent": "% of A+C+G+T+U",
}
LINK_OK = re.compile(r"^(https|ftp)://[^\s<>\"'`]+$")  # R14 approximation (documented)


def sha512_256_b64(data: bytes) -> str:
    try:
        digest = hashlib.new("sha512_256", data).digest()
    except Exception as error:  # never a vacuous pass
        raise RuntimeError(f"SHA-512/256 unavailable: {error}") from error
    return base64.b64encode(digest).decode("ascii")


def file_checksum(data: bytes) -> str:
    """FORMAT.md rules R2-R4 for FASTA headers: the whole ';~checksum:' line and
    its terminator are excluded (R3); SHA-512/256 over every remaining byte (R4).
    Fixture files are toolkit-generated, so the ';~' container prefix is fixed."""
    kept = b"".join(line for line in data.splitlines(keepends=True)
                    if not line.startswith(b";~checksum:"))
    return sha512_256_b64(kept)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def flatten(value, prefix=""):
    """Leaves as (crosswalk-path-without-indices, display path, value)."""
    out = []
    if isinstance(value, dict):
        for key, sub in value.items():
            out.extend(flatten(sub, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        for index, sub in enumerate(value):
            out.extend(flatten(sub, f"{prefix}[{index}]"))
    else:
        base = re.sub(r"\[\d+\]", "[]", prefix)
        out.append((base, prefix, "" if value is None else str(value)))
    return out


def validate_context(context: dict) -> list[str]:
    from jsonschema import Draft202012Validator, FormatChecker
    schema = json.loads(CTX_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"CONTEXT_SCHEMA: {e.json_path}: {e.message}" for e in validator.iter_errors(context)]


def semantic_failures(source: dict, context: dict, fasta_bytes: bytes | None) -> list[str]:
    errors = []
    deposit = context.get("deposit", {})
    if "agency" not in deposit:
        errors.append("AGENCY_UNPINNED: no agency route in context (tbd Q6); a DOI projection cannot be claimed")
    dataset = deposit.get("datasetRecord") or {}
    if dataset.get("doi") and dataset["doi"] == context.get("article", {}).get("doi"):
        errors.append("IDENTITY_MIXUP: dataset record DOI equals the article DOI; identities must stay distinct")
    if fasta_bytes is not None:
        stated = source.get("checksum", "")
        actual = file_checksum(fasta_bytes)
        if stated != actual:
            errors.append(f"CHECKSUM_MISMATCH: header states {stated}, file bytes hash to {actual}")
    return errors


def link_ok(value: str) -> bool:
    return bool(LINK_OK.match(value or ""))


def build_jats(source: dict, context: dict, source_digest: str) -> str:
    authors = "; ".join(a.get("uri") and f"{a['name']} ({a['uri']})" or a["name"]
                        for a in context["article"]["authors"])
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- binding: profile=npp-fhr-publication/0.1.0-draft.1; source-schema="
        f"{source['schema']}; schemaVersion={source['schemaVersion']}; "
        f"associated-file-sha512-256={source_digest}; harness=scripts/npp_projection.py (fixture generator, not an exporter) -->",
        "<!-- jats-fragment: single synthetic root so the file parses as XML; the real adapter inserts these elements into a pinned JATS flow, slots tbd(Q3) -->",
        '<jats-fragment xmlns:xlink="http://www.w3.org/1999/xlink">',
        '<table-wrap id="fh-metadata-synthetic-example" specific-use="fa-bioheaders">',
        "<label>FAIR-bioHeaders metadata (FHR)</label>",
        "<caption><title>Verified FAIR-bioHeaders header of the associated data file</title></caption>",
        "<table><thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>",
    ]
    for base, display, value in flatten(source):
        unit = UNIT_LABELS.get(display.rsplit(".", 1)[-1])
        shown = f"{escape(value)} ({unit})" if unit and value else escape(value)
        lines.append(f"<tr><th>{escape(display)}</th><td>{shown}</td></tr>")
    lines += ["</tbody></table>", "</table-wrap>"]
    taxon = source["taxon"]
    lines += [
        '<kwd-group kwd-group-type="taxonomic-classification">',
        f"<kwd>{escape(taxon['name'])}</kwd>",
    ]
    if link_ok(taxon.get("uri", "")):
        lines.append(f'<kwd specific-use="uri">{escape(taxon["uri"])}</kwd>')
    lines.append("</kwd-group>")
    year, month, day = (source["dateCreated"].split("-") + ["", ""])[:3]
    lines.append(
        f'<date date-type="data-creation"><year>{year}</year>'
        + (f"<month>{int(month):02d}</month>" if month else "")
        + (f"<day>{int(day):02d}</day>" if day else "") + "</date>"
    )
    accession = source.get("accessionID") or {}
    lines.append(
        f'<related-object object-type="dataset" document-id="{escape(accession.get("name", source["genome"]))}"'
        f' content-type="genome-assembly"><ext-link ext-link-type="uri"'
        f' xlink:href="{escape(accession.get("url", ""))}">{escape(accession.get("url", ""))}</ext-link>'
        f" {escape(source['genome'])} version {escape(str(source['version']))}</related-object>"
    )
    if source.get("funding"):
        lines.append(f"<funding-group><funding-statement>{escape(source['funding'])}</funding-statement></funding-group>")
    links = []
    for key in ("documentation", "relatedLink", "assemblyProtocol"):
        value = source.get(key)
        for candidate in ([value] if isinstance(value, str) else (value or [])):
            if link_ok(candidate):
                links.append(candidate)
    for item in source.get("assemblySoftware", []):
        if isinstance(item, dict) and link_ok(item.get("uri", "")):
            links.append(item["uri"])
    for index, link in enumerate(links, 1):
        lines.append(f'<supplementary-material id="fh-link-{index}">'
                     f'<ext-link ext-link-type="uri" xlink:href="{escape(link)}">{escape(link)}</ext-link>'
                     "</supplementary-material>")
    lines.append("</jats-fragment>")
    return "\n".join(lines) + "\n"


def build_crossref(source: dict, context: dict, preprint: bool = False) -> str:
    deposit = context["deposit"]
    genome_title = f"{source['genome']} (version {source['version']})"
    root = "preprint" if preprint else "dataset"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f"<!-- offline {root}-record projection PREPARED from the authoritative header and example context;",
        "     NOT a deposit, NOT schema-validated (Crossref XSD pin is open per profile-status.yml) -->",
        f'<{root} xmlns:xlink="http://www.w3.org/1999/xlink">',
        "<contributors><names>",
        "<!-- assembly creators map to record creators and metadata curators to contributors;",
        "     undifferentiated author_name is used because FHR may omit nameType and person vs",
        "     organization classification must not be invented (no-invention rule) -->",
    ]
    for author in source.get("assemblyAuthor", []):
        lines.append(f'<name><author_name>{escape(author["name"])}</author_name>'
                     "<!-- role: creator (dataset record) --></name>")
    for author in source.get("metadataAuthor", []):
        lines.append(f'<name><author_name>{escape(author["name"])}</author_name>'
                     "<!-- role: contributor/metadata-curator --></name>")
    lines += ["</names>", "</contributors>", f"<titles><title>{escape(genome_title)}</title></titles>",
              f'<publicationDate><year>{source["dateCreated"][:4]}</year>'
              f'<month>{int(source["dateCreated"][5:7]):02d}</month>'
              f'<day>{int(source["dateCreated"][8:10]):02d}</day></publicationDate>',
              f"<publisher>{escape(deposit['publisher'])}</publisher>"]
    lines.append("<subjects>")
    lines.append(f'<subject subjectScheme="NCBI_Taxonomy">{escape(source["taxon"]["name"])}</subject>')
    if link_ok(source["taxon"].get("uri", "")):
        lines.append(f'<subjectSchemeUri>{escape(source["taxon"]["uri"])}</subjectSchemeUri>')
    lines.append("</subjects>")
    reuse = source.get("reuseConditions", "")
    if link_ok(reuse):
        lines.append(f"<rightsList><rights rightsURI=\"{escape(reuse)}\"/></rightsList>")
    if not preprint:
        article_doi = context["article"]["doi"]
        lines.append(
            "<relatedItems><relatedIdentifier relatedIdentifierType=\"DOI\" "
            f"relationType=\"IsDescribedBy\">{escape(article_doi)}</relatedIdentifier></relatedItems>"
        )
    # Preprint surface: no IsDescribedBy article relation is asserted (a preprint is
    # not described by a journal article in these fixtures); inventing one is forbidden.
    if source.get("funding"):
        lines.append(f"<fundingData><funder><funderIdentifierType>ISNI</funderIdentifierType>"
                     f"<funderName>{escape(source['funding'])}</funderName></funder>"
                     "<!-- example judgment: the verbatim FHR funding line is placed as funderName; no award identifier is parsed or invented -->"
                     "</fundingData>")
    if context.get("editorial", {}).get("composedSummariesApproved") and source.get("vitalStats"):
        stats = ", ".join(f"{key}={value}" for key, value in source["vitalStats"].items())
        lines.append(f"<descriptions><description content-type=\"composed-stats-summary\">As reported in the authoritative header: {escape(stats)}</description></descriptions>")
    lines.append(f"</{root}>")
    return "\n".join(lines) + "\n"


def build_report(source: dict, context: dict, jats: str, crossref: str, source_digest: str) -> str:
    crosswalk = load_yaml(CROSSWALK)
    leaf_paths = {base for base, _, _ in flatten(source)}
    losses = []
    for entry in crosswalk["entries"]:
        for axis in ("jats", "doi"):
            if entry[axis]["kind"] == "unsupported":
                losses.append({"path": entry["path"], "axis": axis,
                               "note": entry[axis].get("loss") or entry[axis].get("note") or "no faithful target"})
    report = {
        "profileVersion": crosswalk["profile_version"],
        "generatedBy": "scripts/npp_projection.py (fixture harness; deterministic - timestamps excluded from outputs)",
        "binding": {
            "sourceSchema": source["schema"], "sourceSchemaVersion": str(source["schemaVersion"]),
            "associatedFileSha512_256": source_digest,
            "articleDoi": context["article"]["doi"],
            "datasetDoi": (context["deposit"].get("datasetRecord") or {}).get("doi"),
        },
        "coveredPaths": sorted(leaf_paths),
        "losses": sorted(losses, key=lambda item: (item["path"], item["axis"])),
        "conditionalsApplied": {
            "taxonUriAsKwd": link_ok(source["taxon"].get("uri", "")),
            "rightsList": link_ok(source.get("reuseConditions", "")),
            "composedStats": bool(context.get("editorial", {}).get("composedSummariesApproved")),
        },
    }
    return yaml.safe_dump(report, sort_keys=False, width=100, allow_unicode=True)


def build_all() -> dict[str, str]:
    source = load_json(FIX / "source.fhr.json")
    context = load_yaml(FIX / "context.yaml")
    preprint_context = load_yaml(FIX / "preprint" / "context-preprint.yaml")
    fasta = (FIX / "spikeset.fhr.fasta").read_bytes()
    digest = file_checksum(fasta)
    jats = build_jats(source, context, digest)
    crossref = build_crossref(source, context)
    report = build_report(source, context, jats, crossref, digest)
    outputs = {
        "output-jats.xml": jats,
        "output-crossref-dataset.xml": crossref,
        "projection-report.yaml": report,
        "preprint/output-crossref-preprint.xml": build_crossref(source, preprint_context, preprint=True),
    }
    # Parity rule (#292, 2026-11-21): the verified-metadata table is
    # surface-independent; contexts differing only by surface must produce it
    # byte-identically, so generated/uploaded and journal/repository paths stay
    # indistinguishable downstream.
    assert build_jats(source, preprint_context, digest) == jats, "surface parity broken: JATS projection differs"
    return outputs


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check() -> list[str]:
    errors = validate_context(load_yaml(FIX / "context.yaml"))
    if errors:
        return errors
    source = load_json(FIX / "source.fhr.json")
    fhr_schema = load_json(ROOT / "fhr.json")
    from jsonschema import Draft202012Validator, FormatChecker
    validator = Draft202012Validator(fhr_schema, format_checker=FormatChecker())
    errors += [f"SOURCE_CONTRACT: {e.json_path}: {e.message}" for e in validator.iter_errors(source)]
    context = load_yaml(FIX / "context.yaml")
    fasta = (FIX / "spikeset.fhr.fasta").read_bytes()
    errors += semantic_failures(source, context, fasta)
    preprint_context = load_yaml(FIX / "preprint" / "context-preprint.yaml")
    errors += [f"PREPRINT_CONTEXT: {e}" for e in validate_context(preprint_context)]
    errors += [f"PREPRINT_SEMANTIC: {e}" for e in semantic_failures(source, preprint_context, fasta)]
    for name, content in build_all().items():
        stored = (FIX / name).read_text(encoding="utf-8")
        if stored != content:
            errors.append(f"OUTPUT_DRIFT: {name} differs from the deterministic rebuild")
    for xml_name in ("output-jats.xml", "output-crossref-dataset.xml",
                     "preprint/output-crossref-preprint.xml"):
        try:
            ET.fromstring((FIX / xml_name).read_text(encoding="utf-8"))
        except ET.ParseError as error:
            errors.append(f"XML_WELLFORMED: {xml_name}: {error}")
    for negative in sorted((FIX / "failures").iterdir()):
        expected = set(load_yaml(negative / "expected-failures.yaml")["expectedCodes"])
        neg_source = (load_json(negative / "source.fhr.json")
                      if (negative / "source.fhr.json").exists() else source)
        neg_context = load_yaml(negative / "context.yaml")
        neg_fasta = ((negative / "corrupted.fhr.fasta").read_bytes()
                     if (negative / "corrupted.fhr.fasta").exists() else fasta)
        try:
            found = {code.split(":")[0] for code in semantic_failures(neg_source, neg_context, neg_fasta)}
        except RuntimeError as error:
            found = {str(error)}
        if found != expected:
            errors.append(f"NEGATIVE_FIXTURE {negative.name}: expected {sorted(expected)}, got {sorted(found)}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true", help="write the three deterministic outputs")
    args = parser.parse_args(argv)
    if args.build:
        for name, content in build_all().items():
            (FIX / name).write_text(content, encoding="utf-8")
            print(f"wrote {name} ({len(content)} bytes)")
        return 0
    errors = check()
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("NPP projection fixtures: OK (source contract-validated, integrity recomputed, outputs deterministic, negatives exact)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
