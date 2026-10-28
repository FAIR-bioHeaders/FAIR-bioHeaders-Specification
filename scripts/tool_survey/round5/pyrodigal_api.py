#!/usr/bin/env python3
"""Run the pyrodigal Python API on a FASTA file and print one line per gene.

Usage: pyrodigal_api.py bundled|biopython FASTA

`bundled` reads the file with the FASTA reader shipped in pyrodigal (the one
its CLI uses, pyrodigal/tests/fasta.py); `biopython` reads it with
Bio.SeqIO.parse(path, "fasta"), the pattern shown in pyrodigal's README.
Each record is trained on and searched with GeneFinder in single mode
(translation table 4). Output: record, begin, end, strand, MD5 of the protein.
"""
import hashlib
import sys

import pyrodigal

mode, path = sys.argv[1], sys.argv[2]
if mode == "bundled":
    from pyrodigal.tests.fasta import parse
    recs = [(r.id, r.seq.encode()) for r in parse(path)]
else:
    import gzip
    from Bio import SeqIO
    with (gzip.open(path, "rt") if path.endswith(".gz") else open(path)) as fh:
        recs = [(r.id, bytes(r.seq)) for r in SeqIO.parse(fh, "fasta")]
for name, seq in recs:
    gf = pyrodigal.GeneFinder()
    gf.train(seq, translation_table=4)
    for g in gf.find_genes(seq):
        prot = g.translate()
        print(name, g.begin, g.end, g.strand, hashlib.md5(prot.encode()).hexdigest(), sep="\t")
