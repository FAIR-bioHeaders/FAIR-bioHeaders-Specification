#!/usr/bin/env python3
"""Build the chr4 (NC_004353.4) subset of a verified GCF_000001215.4 delivery.

Standard library only, deterministic, no clock, no network. Part of the FHT
real-data pilot for FAIR-bioHeaders/FHT-Specification#8 and #10; see
README.md in this directory for the provenance of every input.

Definitions (read from the delivery, never assumed):

``reference slice``
    the single FASTA record whose sequence id is ``NC_004353.4``, copied
    verbatim (defline and sequence lines, byte for byte) from
    ``<prefix>_genomic.fna``.

``transcript set``
    every GFF3 feature on sequence name ``NC_004353.4`` whose type is one of
    ``mRNA``, ``lnc_RNA``, ``antisense_RNA``, ``miRNA``, ``snoRNA``,
    ``primary_transcript`` and whose ``ID`` attribute is ``rna-<accession>``.
    Features whose ID is a FlyBase-internal ``gnl|`` name have no public
    accession, therefore no record in ``<prefix>_rna.fna``; they are reported
    as excluded instead of being given an invented accession.

``transcript slice``
    the ``<prefix>_rna.fna`` records whose sequence id is one of those
    accessions, copied verbatim, in ``<prefix>_rna.fna`` order.

``derivation proof``
    for each selected transcript, the spliced join of its own GFF ``exon``
    intervals on ``NC_004353.4`` (reverse-complemented on the minus strand),
    compared with the delivered transcript bytes. This is what makes the FHT
    header's ``transcribedFrom`` parent link a checked statement rather than a
    guess.

Usage:

    python3 extract_chr4.py --dir WORK [--out WORK/out] [--control raw/chr4.fna.gz]
"""

import argparse
import gzip
import hashlib
import json
import os
import sys

CHR4_DEFAULT = "NC_004353.4"
PREFIX_DEFAULT = "GCF_000001215.4_Release_6_plus_ISO1_MT"
TX_TYPES = ("mRNA", "lnc_RNA", "antisense_RNA", "miRNA", "snoRNA", "primary_transcript")
COMP = str.maketrans(
    "ACGTNRYKMSWBDHVacgtnrykmswbdhv", "TGCANYRMKSWVHDBtgcanyrmkswvhdb"
)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path):
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def records(path):
    """Yield (defline bytes without '>', [sequence line bytes]) over raw bytes."""
    opener = gzip.open if path.endswith(".gz") else open
    header = None
    seq = []
    with opener(path, "rb") as handle:
        for line in handle:
            if line.startswith(b">"):
                if header is not None:
                    yield header, seq
                header = line[1:].rstrip(b"\r\n")
                seq = []
            else:
                seq.append(line.rstrip(b"\r\n"))
    if header is not None:
        yield header, seq


def parse_attrs(field):
    attrs = {}
    for part in field.rstrip("\n").split(";"):
        if part:
            key, _, value = part.partition("=")
            attrs[key] = value
    return attrs


def measure(paths):
    """Record/base statistics and a full character census of FASTA bytes."""
    count = bases = lower = upper = 0
    counts = {}
    lengths = []
    for _header, seq in records(paths):
        blob = b"".join(seq)
        count += 1
        bases += len(blob)
        lengths.append(len(blob))
        for byte in set(blob):
            char = chr(byte)
            counts[char] = counts.get(char, 0) + blob.count(byte)
        lower += sum(1 for byte in blob if 97 <= byte <= 122)
        upper += sum(1 for byte in blob if 65 <= byte <= 90)
    lengths.sort(reverse=True)
    run = 0
    n50 = 0
    for length in lengths:
        run += length
        if run >= bases / 2:
            n50 = length
            break
    letters = lower + upper
    return {
        "records": count,
        "bases": bases,
        "longest_record": lengths[0] if lengths else 0,
        "shortest_record": lengths[-1] if lengths else 0,
        "N50": n50,
        "lowercase_chars": lower,
        "uppercase_chars": upper,
        "lowercase_fraction_of_letters": round(lower / letters, 8) if letters else 0.0,
        "lowercase_fraction_of_all_symbols": round(lower / bases, 8) if bases else 0.0,
        "character_counts": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=".", help="directory holding the delivery files")
    parser.add_argument("--prefix", default=PREFIX_DEFAULT)
    parser.add_argument("--chrom", default=CHR4_DEFAULT)
    parser.add_argument("--control", help="NCBI per-chromosome chr4.fna(.gz) for the case control")
    parser.add_argument("--out", help="output directory (default: <dir>/out)")
    args = parser.parse_args(argv)

    work = os.path.abspath(args.dir)
    out = os.path.abspath(args.out or os.path.join(work, "out"))
    os.makedirs(out, exist_ok=True)
    genomic = os.path.join(work, args.prefix + "_genomic.fna")
    rna = os.path.join(work, args.prefix + "_rna.fna")
    gff = os.path.join(work, args.prefix + "_genomic.gff")
    for path in (genomic, rna, gff):
        if not os.path.exists(path):
            raise SystemExit(f"missing input: {path}")

    report = {"sequence_name": args.chrom, "delivery_prefix": args.prefix}

    # 1. reference slice ---------------------------------------------------
    ref_path = os.path.join(out, "chr4_genomic.fna")
    hits = 0
    with open(ref_path, "wb") as sink:
        for header, seq in records(genomic):
            if header.split(b" ", 1)[0].decode() == args.chrom:
                hits += 1
                sink.write(b">" + header + b"\n")
                for line in seq:
                    sink.write(line + b"\n")
    if hits != 1:
        raise SystemExit(f"expected exactly one {args.chrom} record, found {hits}")
    report["reference_slice_records_found"] = hits
    ref_measures = measure(ref_path)
    report["reference_slice_measures"] = ref_measures
    ref_cc = ref_measures["character_counts"]
    ref_letters = sum(
        ref_cc.get(c, 0) + ref_cc.get(c.lower(), 0) for c in "ACGT"
    )
    report["reference_slice_gc_percent_of_letters"] = round(
        100
        * (
            sum(ref_cc.get(c, 0) for c in "CGcg")
            / ref_letters
        ),
        4,
    ) if ref_letters else 0.0

    # 2. NCBI's own per-chromosome file: independent control ---------------
    if args.control and os.path.exists(args.control):
        control_bytes = (
            gzip.open(args.control, "rb").read()
            if args.control.endswith(".gz")
            else open(args.control, "rb").read()
        )
        slice_bytes = open(ref_path, "rb").read()
        report["control_assembly_structure_chr4"] = {
            "path": os.path.basename(args.control),
            "bytes": len(control_bytes),
            "md5": hashlib.md5(control_bytes).hexdigest(),
            "sha256": hashlib.sha256(control_bytes).hexdigest(),
            "identical_to_extracted_slice": control_bytes == slice_bytes,
            "identical_ignoring_letter_case": control_bytes.upper() == slice_bytes.upper(),
            "differs_only_in_letter_case": (
                control_bytes != slice_bytes
                and control_bytes.upper() == slice_bytes.upper()
            ),
        }

    # 3. transcript set from the GFF --------------------------------------
    transcripts = []
    excluded = []
    exons = {}
    region = None
    with open(gff, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("##sequence-region " + args.chrom + " "):
                region = line.strip()
                continue
            if line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 9 or fields[0] != args.chrom:
                continue
            attrs = parse_attrs(fields[8])
            if fields[2] == "exon":
                parent = attrs.get("Parent", "")
                if parent.startswith("rna-"):
                    exons.setdefault(parent[4:], []).append(
                        (int(fields[3]), int(fields[4]))
                    )
                continue
            if fields[2] not in TX_TYPES:
                continue
            prefix, _, accession = attrs.get("ID", "").partition("-")
            if prefix != "rna":
                continue
            row = {
                "id": accession,
                "feature_type": fields[2],
                "start": int(fields[3]),
                "end": int(fields[4]),
                "strand": fields[6],
                "parent": attrs.get("Parent", ""),
            }
            (excluded if accession.startswith("gnl|") else transcripts).append(row)
    by_id = {row["id"]: row for row in transcripts}
    if len(by_id) != len(transcripts):
        raise SystemExit("duplicate transcript accession on the sliced sequence name")
    report["gff_sequence_region_line"] = region
    report["gff_transcript_features_total"] = len(transcripts) + len(excluded)
    report["gff_transcript_features_with_public_accession"] = len(transcripts)
    report["gff_transcript_features_without_accession_excluded"] = [
        {k: row[k] for k in ("id", "feature_type", "start", "end")}
        for row in sorted(excluded, key=lambda r: r["start"])
    ]
    report["selected_by_feature_type"] = {}
    for row in transcripts:
        kind = row["feature_type"]
        report["selected_by_feature_type"][kind] = (
            report["selected_by_feature_type"].get(kind, 0) + 1
        )

    # 4. transcript slice, verbatim from _rna.fna -------------------------
    rna_path = os.path.join(out, "chr4_rna.fna")
    wanted = set(by_id)
    observed = {}
    raw_observed = {}
    total_in_delivery = 0
    with open(rna_path, "wb") as sink:
        for header, seq in records(rna):
            total_in_delivery += 1
            accession = header.split(b" ", 1)[0].decode()
            if accession in wanted:
                observed[accession] = "".join(
                    line.decode() for line in seq
                ).upper()
                raw_observed[accession] = "".join(line.decode() for line in seq)
                sink.write(b">" + header + b"\n")
                for line in seq:
                    sink.write(line + b"\n")
    report["rna_records_in_delivery"] = total_in_delivery
    report["rna_records_selected"] = len(observed)
    report["rna_accessions_requested_but_absent"] = sorted(wanted - set(observed))
    report["transcript_slice_measures"] = measure(rna_path)

    # 5. derivation proof --------------------------------------------------
    genome_raw = "".join(
        "".join(seq.decode() for seq in chunk) for _h, chunk in records(ref_path)
    )
    genome = genome_raw.upper()
    if len(genome) != ref_measures["bases"]:
        raise SystemExit("reference slice length disagrees with its own measurement")

    def join(intervals, source, strand):
        spliced = "".join(source[start - 1 : stop] for start, stop in sorted(intervals))
        return spliced if strand != "-" else spliced.translate(COMP)[::-1]

    equals = with_masking_case = mismatch = 0
    mismatches = []
    for accession in sorted(observed):
        intervals = exons.get(accession)
        if not intervals:
            continue
        strand = by_id[accession]["strand"]
        rebuilt = join(intervals, genome, strand)
        rebuilt_raw = join(intervals, genome_raw, strand)
        if rebuilt == observed[accession]:
            equals += 1
            if rebuilt_raw == raw_observed[accession]:
                with_masking_case += 1
        else:
            mismatch += 1
            mismatches.append(
                {
                    "accession": accession,
                    "feature_type": by_id[accession]["feature_type"],
                    "exon_intervals": len(intervals),
                    "reconstructed_length": len(rebuilt),
                    "observed_length": len(observed[accession]),
                }
            )
    # Negative controls: prove the comparison can fail and that the case
    # distinction is not vacuous. A guard that never rejects proves nothing.
    complement = "ACGTNRYKMSWBDHVacgtnrykmswbdhv".translate(COMP)
    controls = {
        "parent_bytes_are_case_variable": genome_raw != genome,
        "reverse_complement_table_is_correct": complement
        == "TGCANYRMKSWVHDBtgcanyrmkswvhdb",
    }
    for accession in sorted(observed):
        if not exons.get(accession):
            continue
        strand = by_id[accession]["strand"]
        rebuilt = join(exons[accession], genome, strand)
        observed_bases = raw_observed[accession]
        mutant = (
            ("C" if observed_bases[0] != "C" else "G") + observed_bases[1:]
        )
        controls["single_base_mutation_of_a_transcript_is_detected"] = (
            rebuilt != mutant
        )
        controls_accession = accession
        break
    else:
        controls_accession = None

    report["derivation_proof"] = {
        "transcripts_checked": equals + mismatch,
        "equals_exon_join_of_parent": equals,
        "equal_including_the_parent_masking_case": with_masking_case,
        "equal_only_after_case_folding_of_the_soft_masked_parent": equals
        - with_masking_case,
        "mismatching": mismatch,
        "mismatches": sorted(mismatches, key=lambda r: r["accession"])[:40],
        "negative_controls": controls,
        "negative_control_accession": controls_accession,
        "transcripts_selected": len(observed),
        "transcripts_selected_without_exon_rows": sorted(
            accession for accession in observed if not exons.get(accession)
        ),
    }

    # 6. transcripts table ------------------------------------------------
    tsv_path = os.path.join(out, "chr4_transcripts.tsv")
    comment = "# accession feature_type start end strand parent_gff_id exon_intervals has_rna_record\n"
    with open(tsv_path, "w", encoding="utf-8") as sink:
        sink.write(comment)
        for row in sorted(transcripts, key=lambda r: (r["start"], r["end"], r["id"])):
            sink.write(
                "\t".join(
                    str(value)
                    for value in (
                        row["id"],
                        row["feature_type"],
                        row["start"],
                        row["end"],
                        row["strand"],
                        row["parent"],
                        len(exons.get(row["id"], [])),
                        row["id"] in observed,
                    )
                )
                + "\n"
            )

    # 7. digests ----------------------------------------------------------
    for label, path in (
        ("reference_slice", ref_path),
        ("transcript_slice", rna_path),
        ("transcript_table", tsv_path),
    ):
        report[label] = {
            "path": os.path.basename(path),
            "bytes": os.path.getsize(path),
            "sha256": sha256_file(path),
            "md5": md5_file(path),
        }
    for label, path in (
        ("delivery_genomic_fna", genomic),
        ("delivery_rna_fna", rna),
        ("delivery_genomic_gff", gff),
    ):
        report[label] = {"path": os.path.basename(path), "sha256": sha256_file(path)}

    text = json.dumps(report, indent=2, sort_keys=True)
    with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as sink:
        sink.write(text + "\n")
    print(text)
    proof = report["derivation_proof"]
    if proof["mismatching"] or proof["transcripts_checked"] != proof["transcripts_selected"]:
        raise SystemExit("derivation proof incomplete: see report.json")
    if not all(value is True for value in proof["negative_controls"].values()):
        raise SystemExit("derivation proof negative controls failed: see report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
