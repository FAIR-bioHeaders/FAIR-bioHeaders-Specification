#!/usr/bin/env python3
"""Generate the synthetic sequences and plain (header-free) fixtures for issue #191.

Deterministic: seeded PRNG, no network. Run from the fixtures/ directory:
    python3 gen_sequences.py
Outputs: fhr_noheader.fsa, gff3_noheader.gff
"""
import random

random.seed(191)
BASES = "ACGT"

# ctg1: 20 bp flank + 150 bp synthetic CDS (ATG ... TAA) + 70 bp flank = 240 bp
# codons are drawn from all 64 triplets minus the three stops, so the CDS
# translates without internal stops.
CODONS = [a + b + c for a in BASES for b in BASES for c in BASES]
CODONS = [c for c in CODONS if c not in ("TAA", "TAG", "TGA")]
cds = "ATG" + "".join(random.choice(CODONS) for _ in range(48)) + "TAA"
left = "".join(random.choice(BASES) for _ in range(20))
right = "".join(random.choice(BASES) for _ in range(70))
contig1 = left + cds + right
contig2 = "".join(random.choice(BASES) for _ in range(210))


def wrap(seq, n=60):
    return "\n".join(seq[i : i + n] for i in range(0, len(seq), n))


with open("fhr_noheader.fsa", "w") as fh:
    fh.write(">ctg1 Exampleus syntheticus synthetic contig one\n")
    fh.write(wrap(contig1) + "\n")
    fh.write(">ctg2 Exampleus syntheticus synthetic contig two\n")
    fh.write(wrap(contig2) + "\n")

gene_start, gene_end = 21, 20 + len(cds)  # 21..170
with open("gff3_noheader.gff", "w") as fh:
    fh.write("##gff-version 3\n")
    fh.write("#!genome-build ExamSyn ExamSyntheticAssembly1\n")
    fh.write("##sequence-region ctg1 1 240\n")
    fh.write("# Ordinary comment: synthetic annotation, gene on ctg1 only.\n")
    fh.write(f"ctg1\tsynthetic\tgene\t{gene_start}\t{gene_end}\t.\t+\t.\tID=gene1;Name=gene1;locus_tag=synGene1\n")
    fh.write(f"ctg1\tsynthetic\tmRNA\t{gene_start}\t{gene_end}\t.\t+\t.\tID=rna1;Parent=gene1;locus_tag=synGene1\n")
    fh.write(f"ctg1\tsynthetic\texon\t{gene_start}\t{gene_end}\t.\t+\t.\tID=exon1;Parent=rna1\n")
    fh.write(f"ctg1\tsynthetic\tCDS\t{gene_start}\t{gene_end}\t.\t+\t0\tID=cds1;Parent=rna1;locus_tag=synGene1;product=synthetic protein\n")

print("ctg1", len(contig1), "ctg2", len(contig2), "cds", len(cds), "gene", gene_start, gene_end)
