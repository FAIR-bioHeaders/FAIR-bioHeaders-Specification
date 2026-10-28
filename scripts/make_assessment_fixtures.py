# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Generate the synthetic FAIR header assessment fixtures (assessment/pairs, edge).

The output is deterministic: gzip members carry mtime 0, no file name and OS
byte 255 (unknown), and tar members are owned by uid/gid 0 with mtime 0. Real
provider captures in assessment/headers are copied, not generated. Their expected
outcomes, and those of the generated files, are listed in assessment/manifest.json.

Usage: python scripts/make_assessment_fixtures.py [--output DIR]
"""

import argparse
import base64
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

from make_conformance import bgzf

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / "assessment" / "headers"
# Fixtures cite the release they target (docs/SCHEMA-VERSIONS.md).
FHR_URL = "https://w3id.org/fair-bioheaders/fhr/v0.4.0"
FHT_URL = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
REFSEQ_GFF3 = "ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff"
FEATURE = b"ctg1\tsynthetic\tgene\t1\t20\t.\t+\t.\tID=gene1\n"
# Synthetic FHR metadata, the same as conformance/valid/fasta-lf.fhr.fasta.
FHR_METADATA = [
    f"schema: {FHR_URL}",
    "schemaVersion: '2.0'",
    "genome: Synthetic FHR conformance genome",
    "taxon:",
    "  name: Homo sapiens",
    "  uri: https://identifiers.org/taxonomy:9606",
    "version: 1.0.0",
    "metadataAuthor:",
    "- name: Synthetic metadata author (placeholder)",
    "assemblyAuthor:",
    "- name: Synthetic assembly author (placeholder)",
    "dateCreated: '2026-10-08'",
    "masking: not-masked",
    "documentation: Synthetic FHR conformance vector; not a real assembly.",
    "checksum: Z1p/siczUlN/N+lDB5Kg6vFRrztGErgLw9H4MfVfZeU=",
]


def gzip_bytes(data):
    # Python 3.12 writes OS byte 3 (Unix) in the gzip header; 3.13 and later
    # write 255 (unknown). Pin 255 so the output is the same on every version.
    member = bytearray(gzip.compress(data, mtime=0))
    member[9] = 255
    return bytes(member)


def tar_gz(name, data):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        info = tarfile.TarInfo(name)
        info.size, info.mtime, info.mode = len(data), 0, 0o644
        info.uname = info.gname = ""
        tar.addfile(info, io.BytesIO(data))
    return gzip_bytes(buffer.getvalue())


def lines(*items):
    return b"".join((item if isinstance(item, bytes) else item.encode("utf-8")) + b"\n"
                    for item in items)


def edge():
    """The edge cases of research R-15/R-18 (tasks.md T019)."""
    refseq = (HEADERS / REFSEQ_GFF3).read_bytes() + b"NC_003279.8\tRefSeq\tregion\t1\t15072434\t.\t+\t.\tID=NC_003279.8:1..15072434\n"
    gff3 = lines("##gff-version 3", "##sequence-region ctg1 1 20") + FEATURE
    return {
        "edge/no-header.fa": lines(">seq1", "ACGTACGTAC", "GGTTAACCAT"),
        "edge/gzip-refseq.gff.gz": gzip_bytes(refseq),
        "edge/bgzf-refseq.gff.gz": bgzf(refseq),
        "edge/gff3-in-tar.gff.gz": tar_gz("annotation.gff3", gff3),
        "edge/stub.bam": bgzf(b"BAM\x01" + bytes(60)),
        "edge/fhr-and-directives.gff3": lines("##gff-version 3", *("#~" + item for item in FHR_METADATA),
                                              "##sequence-region ctg1 1 20") + FEATURE,
        "edge/unknown-convention.txt": lines("% produced by a synthetic tool", "% columns: x y", "1 2", "3 4"),
        "edge/accession-in-comment.gff3": lines("##gff-version 3", "# built on GCF_000002985.6 (synthetic)",
                                                "##sequence-region ctg1 1 20") + FEATURE,
        "edge/malformed-checksum.gff3": lines(
            "##gff-version 3",
            "#~derivedFrom: [{headerType: FHR, relationship: annotates, checksum: "
            + "A" * 42 + "=}]",
            "##sequence-region ctg1 1 20") + FEATURE,
        "edge/conflicting-accessions.gff3": lines(
            "##gff-version 3", "#!genome-build-accession NCBI_Assembly:GCF_000002985.6",
            "#!genome-build-accession NCBI_Assembly:GCA_000002985.3", "##sequence-region ctg1 1 20") + FEATURE,
        "edge/non-utf8.gff3": lines("##gff-version 3") + b"#!data-source Synth\xe9tique\n" + FEATURE,
        "edge/fhr-valid.fhr.fasta": (ROOT / "conformance" / "valid" / "fasta-lf.fhr.fasta").read_bytes(),
        "edge/fht-stub.fa": lines(f";~schema: {FHT_URL}", ";~schemaVersion: 1.0",
                                  ";~transcriptome: Synthetic transcriptome stub (no published FHT schema)",
                                  ";~reuseConditions: CC0-1.0", ">tx1", "ACGUACGUAC"),
    }


# Scaled-down WBcel235: chromosome names with GenBank and RefSeq sequence names,
# and lengths divided by 100,000 (MtDNA by 1,000). Sequences are synthetic.
CHROMOSOMES = [
    ("I", "BX284601.5", "NC_003279.8", 151),
    ("II", "BX284602.5", "NC_003280.10", 153),
    ("III", "BX284603.4", "NC_003281.10", 138),
    ("IV", "BX284604.4", "NC_003282.8", 175),
    ("V", "BX284605.5", "NC_003283.11", 209),
    ("X", "BX284606.5", "NC_003284.9", 177),
    ("MtDNA", "X54252.1", "NC_001328.1", 14),
]


def sequence(name, length):
    """Deterministic synthetic bases for a sequence name."""
    bases = []
    counter = 0
    while len(bases) < length:
        for byte in hashlib.sha256(f"{name}:{counter}".encode()).digest():
            bases += ["ACGT"[(byte >> shift) & 3] for shift in (0, 2, 4, 6)]
        counter += 1
    return "".join(bases[:length])


def fasta_body(names=0, change=None):
    """FASTA records for CHROMOSOMES; names: 0 chromosome, 1 GenBank, 2 RefSeq."""
    text = []
    for row in CHROMOSOMES:
        bases = sequence(row[0], row[3])
        if change == row[0]:
            bases = bases[:9] + ("C" if bases[9] != "C" else "G") + bases[10:]
        text.append(f">{row[names]}")
        text += [bases[i:i + 60] for i in range(0, len(bases), 60)]
    return ("\n".join(text) + "\n").encode()


def fhr_genome(body, version):
    """An FHR FASTA whose checksum line is last, so the hash covers the rest."""
    metadata = [
        f"schema: {FHR_URL}",
        "schemaVersion: '2.0'",
        "genome: Synthetic WBcel235-style genome (not a real assembly)",
        "taxon:",
        "  name: Caenorhabditis elegans",
        "  uri: https://identifiers.org/taxonomy:6239",
        f"version: {version}",
        "metadataAuthor:",
        "- name: Synthetic metadata author (placeholder)",
        "assemblyAuthor:",
        "- name: Synthetic assembly author (placeholder)",
        "dateCreated: '2026-10-10'",
        "masking: not-masked",
        "documentation: Synthetic assessment fixture; sequences are not real.",
    ]
    header = "".join(f";~{line}\n" for line in metadata).encode()
    digest = hashlib.new("sha512_256", header + body).digest()
    value = base64.b64encode(digest).decode()
    return header + f";~checksum: {value}\n".encode() + body, value


def regions(names=0, rows=CHROMOSOMES, lengths=None):
    lengths = lengths or {}
    return [f"##sequence-region {row[names]} 1 {lengths.get(row[0], row[3])}" for row in rows]


def features(names=0):
    return "".join(f"{row[names]}\tsynthetic\tgene\t1\t10\t.\t+\t.\tID=gene{index}\n"
                   for index, row in enumerate(CHROMOSOMES, 1)).encode()


def derived(checksum):
    return f"#~derivedFrom: [{{headerType: FHR, relationship: annotates, checksum: {checksum}}}]"


def pairs():
    """The User Story 2 pairs of research R-18 (tasks.md T036)."""
    plain = fasta_body()
    genome, checksum = fhr_genome(plain, "1.0.0")
    genome_v2, _ = fhr_genome(fasta_body(change="I"), "2.0.0")
    md5s = {row[0]: hashlib.md5(sequence(row[0], row[3]).upper().encode()).hexdigest()
            for row in CHROMOSOMES}
    md5s["III"] = hashlib.md5(b"not the sequence of III").hexdigest()
    contigs = [f"##contig=<ID={row[0]},length={row[3]},md5={md5s[row[0]]}>" for row in CHROMOSOMES]
    annotation = lines("##gff-version 3", derived(checksum), *regions()) + features()
    return {
        "pairs/genome-plain.fa": plain,
        "pairs/genome-fhr.fa": genome,
        "pairs/genome-fhr-v2.fa": genome_v2,
        "pairs/genome-refseq-names.fa": fasta_body(names=2),
        "pairs/annotation-correct.gff3": annotation,
        "pairs/annotation-version-mismatch.gff3": annotation,
        "pairs/annotation-accession-only.gff3": lines(
            "##gff-version 3", "#!genome-build-accession NCBI_Assembly:GCF_000002985.6", *regions()) + features(),
        "pairs/annotation-no-link.gff3": lines("##gff-version 3", *regions()) + features(),
        "pairs/annotation-genbank-names.gff3": lines(
            "##gff-version 3", "#!genome-build WBcel235", "#!genome-build-accession NCBI_Assembly:GCA_000002985.3",
            *regions(names=1)) + features(names=1),
        "pairs/annotation-partial.gff3": lines(
            "##gff-version 3", *regions(rows=CHROMOSOMES[:6], lengths={"II": 154}), "##sequence-region Y 1 100")
            + features()[: features().index(b"MtDNA")],
        "pairs/variants-contig-md5.vcf": lines(
            "##fileformat=VCFv4.3", *contigs, "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
            f"I\t5\t.\t{sequence('I', 151)[4]}\tN\t.\tPASS\t."),
        "pairs/annotation-malformed-checksum.gff3": lines(
            "##gff-version 3", derived("A" * 42 + "="), *regions()) + features(),
    }


PAIRS = [
    ("pairs/annotation-correct.gff3", "pairs/genome-fhr.fa"),
    ("pairs/annotation-version-mismatch.gff3", "pairs/genome-fhr-v2.fa"),
    ("pairs/annotation-accession-only.gff3", "pairs/genome-plain.fa"),
    ("pairs/annotation-no-link.gff3", "pairs/genome-plain.fa"),
    ("pairs/annotation-genbank-names.gff3", "pairs/genome-refseq-names.fa"),
    ("pairs/annotation-partial.gff3", "pairs/genome-plain.fa"),
    ("pairs/variants-contig-md5.vcf", "pairs/genome-plain.fa"),
    ("pairs/annotation-malformed-checksum.gff3", "pairs/genome-fhr.fa"),
]


def fixtures():
    """Return {relative path: bytes} for every generated fixture."""
    pairs_tsv = "# derived<TAB>related, relative to assessment/ (contracts/data-files.md §5)\n"
    pairs_tsv += "".join(f"{derived}\t{related}\n" for derived, related in PAIRS)
    return {**edge(), **pairs(), "pairs.tsv": pairs_tsv.encode()}


def write(output):
    for name, content in sorted(fixtures().items()):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=ROOT / "assessment",
                        help="directory that receives pairs/ and edge/ (default: assessment/)")
    args = parser.parse_args()
    write(args.output)


if __name__ == "__main__":
    main()
