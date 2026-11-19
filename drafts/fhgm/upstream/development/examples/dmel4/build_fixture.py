# SPDX-License-Identifier: MPL-2.0
"""Build the Drosophila melanogaster chromosome-4 FHGM example fixtures.

Real-data examples for shared #206 and FHGM #8/#9: an FHR single-chromosome
subset, an FHGFF3 1.1 annotation carrying two ``x-fhgm-models`` records over
the real RefSeq gene models ``gene-Dmel_CG11076`` (three mRNA transcripts,
five exons, three CDS) and ``gene-Dmel_CG11077`` (``Mpv17``; one transcript,
one exon, one CDS), and a second snapshot revising one record through a
``predecessor`` pointer. Every header checksum is computed by the released
``fair-bioheaders`` toolkit through ``bioheaders combine``; no checksum is
written by hand.

Inputs are the two whole NCBI RefSeq archives pinned in ``provenance.json``
(SHA-256 verified below; ``gzip -t`` integrity is checked before any read).
Nothing here publishes anything: FHGM is a draft, these are examples, not
conformance vectors, and the records claim no curator acceptance.

Usage (from any directory)::

    python3 build_fixture.py --fna-gz PATH --gff-gz PATH --outdir PATH \
        [--bioheaders PATH] [--payload-out PATH]

The payload row file doubles as the reproducibility witness: extracting it
from the pinned GFF archive must reproduce the committed bytes exactly.
"""

import argparse
import base64
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

SOURCE_ASSEMBLY = "GCF_000001215.4"
SOURCE_ASSEMBLY_NAME = "Release 6 plus ISO1 MT"
SOURCE_URL_FTP = (
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/215/"
    "GCF_000001215.4_Release_6_plus_ISO1_MT/"
)
CHR4 = "NC_004353.4"  # chromosome 4, 1,348,131 bp, GenBank AE014135.4
TAXON = {
    "name": "Drosophila melanogaster",
    "uri": "https://identifiers.org/taxonomy:7227",
}
DATE_CREATED = "2026-11-15"
METADATA_AUTHOR = [{"name": "FHGM real-data example builder (agent)", "nameType": "Organizational"}]
# Submitter, verbatim from the pinned assembly report header ("# Submitter:")
# and the esummary submitterorganization field.
ASSEMBLY_AUTHOR = [
    {
        "name": "The FlyBase Consortium/Berkeley Drosophila Genome Project/Celera Genomics",
        "nameType": "Organizational",
    }
]
# Model loci copied verbatim from the pinned RefSeq GFF3. The closure under
# ID/Parent is computed from the archive; these literals only state which
# gene rows seed it, so a silent source change surfaces as an assertion below.
GENE_IDS = ["gene-Dmel_CG11076", "gene-Dmel_CG11077"]

FNA_SHA256 = "e69e907b5e87ce756236dcef93e82001cfd08f1a0ed5f22e36cbbd3a87ebc57d"
GFF_SHA256 = "9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726"
# NCBI-published MD5s for the same two archives (md5checksums.txt).
FNA_MD5 = "869cf40e4f5c7ca27d04ca9ae7baee4f"
GFF_MD5 = "1de22f17786c44ae98d7922116967b4e"

FHGFF3_SCHEMA = "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0"
FHGFF3_SCHEMA_VERSION = "1.1"
FHR_SCHEMA = "https://w3id.org/fair-bioheaders/fhr/v0.6.0"
FHR_SCHEMA_VERSION = "2.1"


def digests(path):
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def check_archive(path, sha256_want, md5_want, label):
    if shutil.which("gzip") is None:  # pragma: no cover
        raise SystemExit("gzip is required for the archive integrity test")
    result = subprocess.run(["gzip", "-t", str(path)], check=False)
    if result.returncode != 0:
        raise SystemExit(f"{label}: gzip -t failed; the download is truncated or corrupt")
    md5, sha256 = digests(path)
    if sha256 != sha256_want or md5 != md5_want:
        raise SystemExit(
            f"{label}: digest mismatch\n"
            f"  sha256 {sha256} (want {sha256_want})\n"
            f"  md5    {md5} (want {md5_want})"
        )
    print(f"{label}: gzip -t OK, sha256 {sha256}")


def sha512t24u(data):
    return base64.urlsafe_b64encode(hashlib.sha512(data).digest()[:24]).decode("ascii")


def canonical(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("ascii")


def iter_fasta_records(handle):
    """Yield (id_token, raw_defline_line, [sequence_lines]) preserving bytes."""
    name = None
    defline = None
    chunks = []
    for line in handle:
        if line.startswith(b">"):
            if name is not None:
                yield name, defline, chunks
            defline = line
            name = line[1:].split()[0].decode("ascii")
            chunks = []
        elif name is not None:
            chunks.append(line)
    if name is not None:
        yield name, defline, chunks


def seqcol_id(fasta_bytes):
    """GA4GH SeqCol v1.0.0 level-0 digest, the S6k pilot recipe (see
    ../s6k/verify_reference.py): first token of each defline, uppercase
    sequences, original record order; a {"names", "sequences"} collection
    whose fields are digested (sha512t24u over canonical JSON) and then
    digested again as a map."""
    names = []
    seqs = []
    for name, _defline, chunks in iter_fasta_records(fasta_bytes.splitlines(keepends=True)):
        names.append(name)
        sequence = b"".join(chunks).replace(b"\n", b"").upper()
        seqs.append("SQ." + sha512t24u(sequence))
    collection = {"names": names, "sequences": seqs}
    level_one = {key: sha512t24u(canonical(value)) for key, value in collection.items()}
    return sha512t24u(canonical(level_one))


def extract_record(fna_gz, record_id):
    with gzip.open(fna_gz, "rb") as stream:
        for name, defline, chunks in iter_fasta_records(stream):
            if name == record_id:
                return defline + b"".join(chunks)
    raise SystemExit(f"{record_id}: not found in the pinned assembly FASTA")


def attr_map(field):
    out = {}
    for part in field.rstrip("\n").split(";"):
        key, sep, value = part.partition("=")
        if sep:
            out[key] = value
    return out


def extract_locus(gff_gz):
    """Return (header_note, rows) for the closure of GENE_IDS on CHR4, in the
    exact source order and byte-exact."""
    rows = []
    with gzip.open(gff_gz, "rt", encoding="ascii") as stream:
        for line in stream:
            if line.startswith("#"):
                continue
            columns = line.split("\t")
            if len(columns) != 9:
                continue
            rows.append((columns[0], columns[2], attr_map(columns[8]), line))
    ids_wanted = set(GENE_IDS)
    found = sorted(row[2]["ID"] for row in rows if row[0] == CHR4 and row[2].get("ID") in ids_wanted)
    if found != sorted(GENE_IDS):
        raise SystemExit(
            "gene closure seed mismatch: expected both GENE_IDS on "
            f"{CHR4}, found {found}"
        )
    # Transitive children under Parent= references, source order preserved.
    changed = True
    while changed:
        changed = False
        for row in rows:
            if row[0] != CHR4 or row[2].get("ID") in ids_wanted:
                continue
            parent = row[2].get("Parent")
            if parent and parent in ids_wanted:
                ids_wanted.add(row[2]["ID"])
                changed = True
    kept = [row[3] for row in rows if row[0] == CHR4 and row[2].get("ID") in ids_wanted]
    # The chromosome region row, so the seqid is defined inside the payload.
    region = [
        row[3]
        for row in rows
        if row[0] == CHR4 and row[1] == "region" and row[2].get("ID") == f"{CHR4}:1..1348131"
    ]
    if len(region) != 1:
        raise SystemExit("expected exactly one region row for NC_004353.4")
    # Source order: the region row precedes the gene rows in the RefSeq file.
    ordered_lines = region + kept
    return ordered_lines


def counts_of(lines):
    tally = {}
    for line in lines:
        kind = line.split("\t")[2]
        tally[kind] = tally.get(kind, 0) + 1
    return tally


def combine(bioheaders, metadata, sequence, output):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
        json.dump(metadata, handle)
        meta_path = Path(handle.name)
    subprocess.run(
        [str(bioheaders), "combine", str(meta_path), str(sequence), "-o", str(output)],
        check=True,
    )
    meta_path.unlink()


def header_checksum(fh_file):
    text = fh_file.read_text(encoding="ascii")
    match = re.search(r"^[;#]~checksum: (\S+)$", text, flags=re.M)
    if not match:
        raise SystemExit(f"{fh_file.name}: no checksum line produced by the toolkit")
    return match.group(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fna-gz", type=Path, required=True)
    parser.add_argument("--gff-gz", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--bioheaders", default="bioheaders")
    parser.add_argument(
        "--payload-out",
        type=Path,
        default=None,
        help="also write the extracted verbatim payload rows here for cmp",
    )
    args = parser.parse_args()

    if args.bioheaders == "bioheaders":
        bioheaders = shutil.which("bioheaders")
        if bioheaders is None:
            raise SystemExit("fair-bioheaders toolkit CLI not found on PATH")
    else:
        bioheaders = str(args.bioheaders)

    check_archive(args.fna_gz, FNA_SHA256, FNA_MD5, "genomic.fna.gz")
    check_archive(args.gff_gz, GFF_SHA256, GFF_MD5, "genomic.gff.gz")

    args.outdir.mkdir(parents=True, exist_ok=True)

    # --- FHR: single-chromosome subset FASTA -------------------------------
    record = extract_record(args.fna_gz, CHR4)
    if not record.startswith(f">{CHR4} ".encode()):
        raise SystemExit("unexpected defline for the chromosome 4 record")
    full_fasta = gzip.decompress(args.fna_gz.read_bytes())
    subset_path = args.outdir / "Dmel-NC_004353.4-chr4.fhr.fa"
    plain_subset = args.outdir / "Dmel-NC_004353.4-chr4.plain.fasta"
    plain_subset.write_bytes(record)

    chr4_seq = b"".join(record.splitlines(keepends=True)[1:])
    lower_chars = len(re.findall(rb"[acgtn]", chr4_seq))
    total = len(re.sub(rb"\s", b"", chr4_seq))
    masking = "soft-masked" if lower_chars else "not-masked"
    print(f"chr4 {total} bp, {lower_chars} lowercase bases -> masking {masking}")

    subset_seqcol = seqcol_id(record)
    full_seqcol = seqcol_id(full_fasta)
    del full_fasta
    print(f"SeqCol digest of the 1-record subset collection: {subset_seqcol}")
    print(f"SeqCol digest of the full {SOURCE_ASSEMBLY} collection: {full_seqcol}")

    fhr_meta = {
        "schema": FHR_SCHEMA,
        "schemaVersion": FHR_SCHEMA_VERSION,
        "genome": (
            "Drosophila melanogaster Release 6 plus ISO1 MT - chromosome 4 "
            "single-record subset of the RefSeq assembly collection"
        ),
        "genomeSynonym": ["dm6 (UCSC name of this assembly)"],
        "taxon": TAXON,
        "version": "1",
        "metadataAuthor": METADATA_AUTHOR,
        "assemblyAuthor": ASSEMBLY_AUTHOR,
        "dateCreated": DATE_CREATED,
        "masking": masking,
        "seqcol_id": subset_seqcol,
        "relatedLink": [SOURCE_URL_FTP],
    }
    combine(bioheaders, fhr_meta, plain_subset, subset_path)
    fhr_checksum = header_checksum(subset_path)
    plain_subset.unlink()
    print(f"FHR subset checksum (written by the toolkit): {fhr_checksum}")

    # --- FHGFF3 payload: verbatim RefSeq rows, closure over the two genes --
    lines = extract_locus(args.gff_gz)
    tally = counts_of(lines)
    print(f"payload rows: {len(lines)} {tally}")
    payload_path = args.outdir / "Dmel_CG11076-Mpv17.payload.gff3"
    payload_path.write_text("##gff-version 3\n" + "".join(lines), encoding="ascii")
    if args.payload_out:
        args.payload_out.write_bytes(payload_path.read_bytes())

    genome_reference = {
        "accession": SOURCE_ASSEMBLY,
        "seqcol_id": full_seqcol,
        "assemblyName": SOURCE_ASSEMBLY_NAME,
    }
    source_row = {
        "name": "NCBI RefSeq annotation, Release 6 plus ISO1 MT",
        "release": "GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz",
        "assemblyAccession": SOURCE_ASSEMBLY,
        "url": SOURCE_URL_FTP + "GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz",
        "description": (
            "All feature rows copied verbatim and in source order for "
            "gene-Dmel_CG11076 and gene-Dmel_CG11077 (Mpv17) on NC_004353.4 "
            "chromosome 4 plus the chromosome region row"
        ),
        "sequenceCount": 1,
    }
    feature_counts = [
        {"featureType": kind, "count": count} for kind, count in sorted(tally.items())
    ]

    def model_record(gene_id, feature_lines, reference):
        evidence = (
            f"{gene_id}: feature rows copied verbatim from the pinned RefSeq GFF3; "
            + feature_lines
        )
        return {
            "modelId": gene_id,
            "modelVersion": "1",
            "featureId": gene_id,
            "reference": reference,
            "evidence": [
                {
                    "description": evidence,
                    "uri": SOURCE_URL_FTP + "GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz",
                }
            ],
            "methods": {
                "software": [
                    {"name": "development/examples/dmel4/build_fixture.py"},
                    {"name": "fair-bioheaders", "version": "0.11.0",
                     "uri": "https://pypi.org/project/fair-bioheaders/"},
                ]
            },
        }

    # Dbxref identifiers as written in the source rows (FLYBASE:FBgn...,
    # GeneID:...), kept in the record as publication.deposit CURIEs of the
    # model-data locations. The source rows carry no personal authors and no
    # resolvable article DOI for these two models, so `contributors` and
    # `publication.article` stay absent: what the source does not state, the
    # record does not claim.
    def deposits(gene_id):
        for line in lines:
            columns = line.split("\t")
            attributes = attr_map(columns[8])
            if columns[2] == "gene" and attributes.get("ID") == gene_id:
                dbxref = attributes.get("Dbxref", "")
                wanted = [
                    part for part in dbxref.split(",") if part.startswith(("FLYBASE:", "GeneID:"))
                ]
                return wanted
        raise SystemExit(f"{gene_id}: gene row not found")

    def decorate(record_meta, gene_id):
        record_meta["publication"] = {"deposit": deposits(gene_id)}
        return record_meta

    cg11076 = decorate(
        model_record(
            "gene-Dmel_CG11076",
            "three mRNA transcripts (NM_166807.3, NM_143686.4, NM_001258500.1), "
            "five exons and three CDS, 1029711..1031757 on the minus strand",
            {"genomeReference": genome_reference},
        ),
        "gene-Dmel_CG11076",
    )
    mpv17 = decorate(
        model_record(
            "gene-Dmel_CG11077",
            "one mRNA transcript (NM_143687.4), one exon and one CDS, "
            "1028675..1029361 on the minus strand",
            {"annotates": fhr_checksum},
        ),
        "gene-Dmel_CG11077",
    )

    v1 = {
        "schema": FHGFF3_SCHEMA,
        "schemaVersion": FHGFF3_SCHEMA_VERSION,
        "annotation": (
            "Two Drosophila melanogaster chromosome-4 gene models "
            "(Dmel_CG11076 multi-isoform, Mpv17 single-exon), feature rows "
            "copied verbatim from the pinned RefSeq GFF3 archive"
        ),
        "taxon": TAXON,
        "version": "1",
        "metadataAuthor": METADATA_AUTHOR,
        "dateCreated": DATE_CREATED,
        "genomeReference": genome_reference,
        "derivedFrom": [
            {
                "checksum": fhr_checksum,
                "headerType": "FHR",
                "relationship": "annotates",
            }
        ],
        "source": [source_row],
        "featureCounts": feature_counts,
        "x-fhgm-models": [cg11076, mpv17],
    }
    v1_path = args.outdir / "Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3"
    combine(bioheaders, v1, payload_path, v1_path)
    v1_checksum = header_checksum(v1_path)
    print(f"snapshot v1 checksum: {v1_checksum}")

    v2_model = dict(cg11076)
    v2_model["modelVersion"] = "2"
    v2_model["predecessor"] = {
        "annotationChecksum": v1_checksum,
        "modelId": "gene-Dmel_CG11076",
        "modelVersion": "1",
    }
    v2_model["evidence"] = list(cg11076["evidence"]) + [
        {
            "description": (
                "Snapshot v2 records the same source-derived model rows; the "
                "revision is this example's own record revision (version 1 to "
                "version 2 of the record), not a claim about FlyBase or RefSeq "
                "model history."
            )
        }
    ]
    v2 = dict(v1)
    v2["version"] = "2"
    v2["x-fhgm-models"] = [v2_model, mpv17]
    v2_path = args.outdir / "Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3"
    combine(bioheaders, v2, payload_path, v2_path)
    v2_checksum = header_checksum(v2_path)
    print(f"snapshot v2 checksum: {v2_checksum}")

    report = {
        "assembly": SOURCE_ASSEMBLY,
        "assemblyName": SOURCE_ASSEMBLY_NAME,
        "chr4": CHR4,
        "fhrChecksum": fhr_checksum,
        "fhrSeqcolSubset": subset_seqcol,
        "assemblySeqcolFull": full_seqcol,
        "snapshotV1Checksum": v1_checksum,
        "snapshotV2Checksum": v2_checksum,
        "payloadRows": len(lines),
        "featureCounts": feature_counts,
        "masking": masking,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    sys.exit(main())
