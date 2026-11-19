#!/bin/sh
# Reproduce the *Drosophila melanogaster* chr4 FHR -> FHT pilot end to end
# (FAIR-bioHeaders/FHT-Specification#8 real examples, #10 pilot evidence).
#
# It re-downloads the pinned files from NCBI, re-verifies them against NCBI's
# own published digests, re-extracts the chr4 subset, re-authors both headers
# with the RELEASED fair-bioheaders 0.11.0, and compares every recorded byte
# count and digest in README.md. Anything that differs is a hard failure:
# nothing here is checked by eyeballing.
#
# Needs: curl, python3 (stdlib only) and a clean venv with the released toolkit:
#   python3 -m venv .venv-pilot
#   .venv-pilot/bin/pip install fair-bioheaders==0.11.0
#
# Runtime is dominated by ~76 MB of downloads plus the FHT draft-lane calls.
set -eu

BASE=$(CDPATH= cd "$(dirname "$0")/../.." && pwd)   # repository root
HERE=$(CDPATH= cd "$(dirname "$0")" && pwd)
PYTHON_VENV=$(CDPATH= cd "${PYTHON_VENV:-"$BASE/.venv-pilot"}" && pwd)
WORK=${PILOT_WORK_DIR:-/tmp/fht-pilot-dmel}
BH="$PYTHON_VENV/bin/bioheaders"
PY=python3

D=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/215/GCF_000001215.4_Release_6_plus_ISO1_MT
F=GCF_000001215.4_Release_6_plus_ISO1_MT
STRUCT=$D/${F}_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA

mkdir -p "$WORK"
cd "$WORK"

check() { # label expected actual
  if [ "$2" != "$3" ]; then
    echo "FAIL: $1: expected $2, got $3" >&2
    exit 1
  fi
  echo "ok:   $1 = $3"
}

digest() { # algorithm file
  "$PY" -c '
import hashlib,sys
h=hashlib.new(sys.argv[1])
with open(sys.argv[2],"rb") as fh:
    for chunk in iter(lambda: fh.read(1<<22), b""):
        h.update(chunk)
print(h.hexdigest())
' "$1" "$2"
}

fetch() { # url target
  [ -f "$2" ] || curl -fsS -o "$2" "$1"
}

echo '== 0. toolchain identity (released package, not a working tree) =='
"$BH" --version
"$PY" -c 'import sys; print("python", sys.version.split()[0])'

echo '== 1. fetch the pinned delivery files and verify them against NCBI =='
fetch "$D/${F}_genomic.fna.gz" "${F}_genomic.fna.gz"
fetch "$D/${F}_rna.fna.gz" "${F}_rna.fna.gz"
fetch "$D/${F}_genomic.gff.gz" "${F}_genomic.gff.gz"
fetch "$D/${F}_genomic_gaps.txt.gz" "${F}_genomic_gaps.txt.gz"
fetch "$D/${F}_assembly_report.txt" "${F}_assembly_report.txt"
fetch "$D/${F}_feature_count.txt" "${F}_feature_count.txt"
fetch "$D/md5checksums.txt" md5checksums.txt
fetch "$D/uncompressed_checksums.txt" uncompressed_checksums.txt
fetch "$D/annotation_hashes.txt" annotation_hashes.txt
fetch "$STRUCT/chr4.fna.gz" chr4.fna.gz
check 'md5checksums.txt sha256' \
  148f87060005d84a397d74a216cca8454d0f37bd8928be5ac9517169439c9fa1 "$(digest sha256 md5checksums.txt)"
check 'uncompressed_checksums.txt sha256' \
  edbc2647a9f35bca7c2695efde8690d65166249423b9d693ea0aefce635d632c "$(digest sha256 uncompressed_checksums.txt)"
check 'annotation_hashes.txt sha256' \
  8440fb061a189d21cc26f7d7db70d1daba6b242e17a3292ed480ccf2c1374ccc "$(digest sha256 annotation_hashes.txt)"

check "${F}_genomic.fna.gz sha256" \
  e69e907b5e87ce756236dcef93e82001cfd08f1a0ed5f22e36cbbd3a87ebc57d "$(digest sha256 ${F}_genomic.fna.gz)"
check "${F}_rna.fna.gz sha256" \
  bc3f402dbdb44b2ed075ddcd10800a1d15a123aeaf99c9cf16bf1085e3ec7855 "$(digest sha256 ${F}_rna.fna.gz)"
check "${F}_genomic.gff.gz sha256" \
  9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726 "$(digest sha256 ${F}_genomic.gff.gz)"
check "${F}_genomic_gaps.txt.gz sha256" \
  e993042891ae03def7e2e32c559e23cd34c8692ba677ff12a4026d93ddd18041 "$(digest sha256 ${F}_genomic_gaps.txt.gz)"
check "${F}_assembly_report.txt sha256" \
  22bf2cefea3bf4abc56aab340bdfb32f27dcd02b78f57c0762f8f1036e7963e7 "$(digest sha256 ${F}_assembly_report.txt)"
check "${F}_feature_count.txt sha256" \
  1bcc2d12804490dd10452dc9d98ca42c7125ccc2591dad0603ee9783c671d76d "$(digest sha256 ${F}_feature_count.txt)"
check "chr4.fna.gz control sha256" \
  c0d89f2a877d3f75896b72340bfbe0be5b9c7edcfb733565021bea147c157f3e "$(digest sha256 chr4.fna.gz)"

# Every compressed download is also compared with the MD5 that NCBI publishes
# for that exact path in md5checksums.txt.
verify_against_list() { # local-file listed-path pinned-md5 list-file
  published=$(awk -F'[ \t]+' -v p="$2" '$2==p {print $1}' "$4")
  check "$1 entry in $4" "$3" "$published"
  check "$1 computed md5 equals $4" "$3" "$(digest md5 "$1")"
}
verify_against_list "${F}_genomic.fna.gz" "./${F}_genomic.fna.gz" \
  869cf40e4f5c7ca27d04ca9ae7baee4f md5checksums.txt
verify_against_list "${F}_rna.fna.gz" "./${F}_rna.fna.gz" \
  45a0b3380c3a364873bd8258db7a9291 md5checksums.txt
verify_against_list "${F}_genomic.gff.gz" "./${F}_genomic.gff.gz" \
  1de22f17786c44ae98d7922116967b4e md5checksums.txt
verify_against_list "${F}_assembly_report.txt" "./${F}_assembly_report.txt" \
  ecb1db60e27f4f5ce3dd35fa46b4d7c6 md5checksums.txt
verify_against_list "${F}_feature_count.txt" "./${F}_feature_count.txt" \
  390ad2968539bd08d44810c8986fc188 md5checksums.txt
verify_against_list chr4.fna.gz \
  "./${F}_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chr4.fna.gz" \
  1531d6b6f84fe41947f21dcb8fa3db57 md5checksums.txt

echo '== 2. decompress and verify against NCBI uncompressed_checksums.txt =='
verify_uncompressed() { # archive uncompressed listed-md5 size [listed-path]
  listing=${5:-./$2}
  gzip -t "$1"
  [ -f "$2" ] || gunzip -c "$1" > "$2"
  published=$(awk -F'\t' -v p="$listing" '$1==p {print $2}' uncompressed_checksums.txt)
  published_size=$(awk -F'\t' -v p="$listing" '$1==p {print $4}' uncompressed_checksums.txt)
  check "$2 entry in uncompressed_checksums.txt" "$3" "$published"
  check "$2 computed md5 equals the published one" "$3" "$(digest md5 "$2")"
  check "$2 byte size equals the published one" "$4" "$(wc -c < "$2" | tr -d ' ')"
}
verify_uncompressed "${F}_genomic.fna.gz" "${F}_genomic.fna" \
  a201b53b7eab2eb161671e4b3ae670a0 145657746
verify_uncompressed "${F}_rna.fna.gz" "${F}_rna.fna" \
  76e78617dd3457f256f884ae68933372 96785880
verify_uncompressed "${F}_genomic.gff.gz" "${F}_genomic.gff" \
  399b4ac37cc123b724895334be589fdc 164988613
verify_uncompressed chr4.fna.gz chr4.fna edd1c69d6360fe22ee850c3bca51894b 1365033 \
  "./${F}_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chr4.fna"

echo '== 3. extract the chr4 subset and re-run the derivation proof =='
mkdir -p "$WORK/out"
"$PY" "$HERE/extract_chr4.py" --dir "$WORK" --control "$WORK/chr4.fna.gz" --out "$WORK/out" > "$WORK/out/stdout.json"
check "chr4_genomic.fna sha256" \
  9ea85183fc77137381a6e81adf8f088c84c68a888dc323ef8b286b4ef165e184 "$(digest sha256 out/chr4_genomic.fna)"
check "chr4_rna.fna sha256" \
  f196bb2cd5cc98d56ae2c3c365d1322e93a42d33d8ba8c0cad66e86fb2cffd3c "$(digest sha256 out/chr4_rna.fna)"
check "chr4_transcripts.tsv sha256" \
  bf679f3c1a9127f1c02b4a84f13bd55851ed51fcdc829cd71d3e6885a7631f3f "$(digest sha256 out/chr4_transcripts.tsv)"
check "transcripts proven as exon joins of the chr4 parent" 334 \
  "$("$PY" -c 'import json;print(json.load(open("out/report.json"))["derivation_proof"]["equals_exon_join_of_parent"])')"
check "derivation mismatches" 0 \
  "$("$PY" -c 'import json;print(json.load(open("out/report.json"))["derivation_proof"]["mismatching"])')"
diff "$HERE/chr4_transcripts.tsv" out/chr4_transcripts.tsv > /dev/null
echo 'ok:   chr4_transcripts.tsv equals the committed table'

echo '== 4. author the FHR header with the released toolkit (default path) =='
"$BH" combine "$HERE/metadata.fhr.yaml" out/chr4_genomic.fna -o GCF_000001215.4_chr4.fhr.fasta
check "FHR file bytes" 1368589 "$(wc -c < GCF_000001215.4_chr4.fhr.fasta | tr -d ' ')"
check "FHR file sha256" \
  5e797185f974ccefe01ae7c2dfd5fd6e3c8cf221dab83f6548c29a00f0824f40 "$(digest sha256 GCF_000001215.4_chr4.fhr.fasta)"
check "FHR checksum line" ';~checksum: qQs9oEKygk63F7ppYVl9te6U8lVHeE8Fbzlf7lmB4Yw=' \
  "$(grep '^;~checksum:' GCF_000001215.4_chr4.fhr.fasta)"
check "FHR header sha256" \
  e2b5266f60a5146d95f0cca0f9093f8e3bc4803376a2de265ab870668fb145ef \
  "$(digest sha256 "$HERE/header.fhr.txt")"
"$PY" - "$PWD/GCF_000001215.4_chr4.fhr.fasta" "$HERE/header.fhr.txt" <<'EOF'
import sys
kept = [line for line in open(sys.argv[1], "rb") if line.startswith(b";~")]
committed = open(sys.argv[2], "rb").read()
assert b"".join(kept) == committed, (len(kept), len(committed))
print("ok:   rebuilt FHR header block is byte-identical to header.fhr.txt")
EOF
"$BH" verify GCF_000001215.4_chr4.fhr.fasta
"$BH" verify-links GCF_000001215.4_chr4.fhr.fasta

echo '== 5. author the FHT header through the released draft lane =='
BIOHEADERS_EXPERIMENTAL_FHT=1 "$BH" combine "$HERE/metadata.fht.yaml" out/chr4_rna.fna \
  -o GCF_000001215.4_chr4_transcripts.fht.fasta 2> /dev/null
check "FHT file bytes" 1387037 "$(wc -c < GCF_000001215.4_chr4_transcripts.fht.fasta | tr -d ' ')"
check "FHT file sha256" \
  be72f9b29a138d4ab2f52189a750e849f738265f19c3488f97143a1ffb8f11f0 "$(digest sha256 GCF_000001215.4_chr4_transcripts.fht.fasta)"
check "FHT checksum line" ';~checksum: BUcrVpAVDG29yRm+DPmX2U5uHwFOSK/trlZpByY2DTk=' \
  "$(grep '^;~checksum:' GCF_000001215.4_chr4_transcripts.fht.fasta)"
check "FHT header sha256" \
  d90b0e90a61f4bf7813b42485319b086275ccc4da7008c47d1a664b5bcf3236b \
  "$(digest sha256 "$HERE/header.fht.txt")"
"$PY" - "$PWD/GCF_000001215.4_chr4_transcripts.fht.fasta" "$HERE/header.fht.txt" <<'EOF'
import sys
kept = [line for line in open(sys.argv[1], "rb") if line.startswith(b";~")]
committed = open(sys.argv[2], "rb").read()
assert b"".join(kept) == committed, (len(kept), len(committed))
print("ok:   rebuilt FHT header block is byte-identical to header.fht.txt")
EOF
BIOHEADERS_EXPERIMENTAL_FHT=1 "$BH" verify GCF_000001215.4_chr4_transcripts.fht.fasta 2> /dev/null

echo '== 6. parent link: positive, negative and re-derivation controls =='
BIOHEADERS_EXPERIMENTAL_FHT=1 "$BH" verify-links \
  GCF_000001215.4_chr4_transcripts.fht.fasta GCF_000001215.4_chr4.fhr.fasta 2> /dev/null \
  | grep -q 'derivedFrom\[0\] FHR transcribedFrom: matched' \
  && echo 'ok:   derivedFrom[0] FHR transcribedFrom matched the chr4 subset parent'
status=0
BIOHEADERS_EXPERIMENTAL_FHT=1 "$BH" verify-links \
  GCF_000001215.4_chr4_transcripts.fht.fasta "$BASE/conformance/parents/parent-genome.fhr.fasta" \
  > /dev/null 2>&1 || status=$?
check 'wrong-parent verify-links exit status' 3 "$status"
echo 'ok:   verify-links rejects a non-matching parent (exit 3 path exercised)'
"$PY" "$HERE/rederive_checksum.py" --self-test \
  GCF_000001215.4_chr4.fhr.fasta GCF_000001215.4_chr4_transcripts.fht.fasta

echo '== 7. strip round trip preserves the extracted bytes exactly =='
"$BH" strip GCF_000001215.4_chr4.fhr.fasta stripped.fhr.fna
"$PY" - <<EOF
import hashlib
a=open("stripped.fhr.fna","rb").read(); b=open("out/chr4_genomic.fna","rb").read()
assert a==b, (len(a), len(b))
print("ok:   strip(FHR) == out/chr4_genomic.fna")
EOF
BIOHEADERS_EXPERIMENTAL_FHT=1 "$BH" strip GCF_000001215.4_chr4_transcripts.fht.fasta stripped.fht.fna 2> /dev/null
"$PY" - <<EOF
a=open("stripped.fht.fna","rb").read(); b=open("out/chr4_rna.fna","rb").read()
assert a==b, (len(a), len(b))
print("ok:   strip(FHT, draft lane) == out/chr4_rna.fna")
EOF

echo 'OK: the pilot reproduces byte-for-byte'
