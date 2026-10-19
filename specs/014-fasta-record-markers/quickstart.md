# Quickstart: FASTA record markers (R11)

```bash
# Specification
python scripts/make_conformance.py && python -I scripts/check_conformance.py
python scripts/check_conformance.py --schema
# Real tools on the vectors (seqtk, bioawk, samtools from the survey environment)
seqtk comp conformance/valid/fasta-raw-record-markers.fhr.fasta      # bogus record example.org;
seqtk comp conformance/valid/fasta-escaped-record-markers.fhr.fasta  # Contig1 only
# Toolkit
fhr-fasta-combine meta.json body.fa -o out.fhr.fa   # escapes > and @
fhr-fasta-validate conformance/valid/fasta-raw-record-markers.fhr.fasta  # warns, exit 0
fhr-convert out.fhr.fa out.json                      # real characters
```
