#!/bin/sh
# Reproduce the FHR pilot artifact (FAIR-bioHeaders/FHT-Specification#40).
# Re-downloads the published assembly from NCBI, rebuilds the FHR header with
# the RELEASED fair-bioheaders (no network beyond NCBI/PyPI), and compares
# every digest recorded in pilot/README.md. Exits non-zero on any mismatch.
#
# Needs: curl, python3 (>=3.9, stdlib only), and a clean venv:
#   python3 -m venv .venv-pilot
#   .venv-pilot/bin/pip install fair-bioheaders==0.11.0
set -eu

BASE=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
PYTHON_VENV=$(CDPATH= cd "${PYTHON_VENV:-"$BASE/.venv-pilot"}" && pwd)
WORK=${PILOT_WORK_DIR:-/tmp/fhr-pilot-GCA_036971475.1}
mkdir -p "$WORK"
cd "$WORK"

F=GCA_036971475.1_USDA_Prosapia_bicincta_1.0
D=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/036/971/475/GCA_036971475.1_USDA_Prosapia_bicincta_1.0

echo '== 1. fetch assembly FASTA (expect 598121128 bytes) =='
[ -f "$F"_genomic.fna.gz ] || curl -sS -o "$F"_genomic.fna.gz "$D/$F"_genomic.fna.gz
echo 73af3dde8beabe4bb7e722aafa31b9c9c9529f40d29582a5b10ae2475b5601e4\  "$F"_genomic.fna.gz | shasum -a 256 -c -

echo '== 2. decompress (expect 2247394312 bytes) =='
[ -f "$F"_genomic.fna ] || gunzip -c "$F"_genomic.fna.gz > "$F"_genomic.fna
echo 9100ebee1c0169a656660cc679d044f1b210ea13f8296e37ef3ef8c42fea35ba\  "$F"_genomic.fna | shasum -a 256 -c -

echo '== 3. combine with the released toolkit (checksum is computed, never written by hand) =='
BH=$PYTHON_VENV/bin/bioheaders
"$BH" --version
"$BH" combine "$BASE"/pilot/metadata.fhr.yaml "$F"_genomic.fna -o "$F".fhr.fasta

echo '== 4. verify identities recorded in pilot/README.md =='
"$BH" verify "$F".fhr.fasta
grep -q ';~checksum: GzNUcBwcd/kAnGzI2dNGsJQbp2mrhJxzLNPvZVzw/Lw=' "$F".fhr.fasta \
  && echo 'FHR checksum matches the recorded value'
[ "$(wc -c < "$F".fhr.fasta)" -eq 2247396983 ] && echo 'combined size matches'
echo c3e01149d1dc194a73664974c42a6307f207955b3a7951399b7f54a5bfafd560\  "$F".fhr.fasta | shasum -a 256 -c -

echo '== 5. verify-links (primary assembly: no recorded parents) =='
"$BH" verify-links "$F".fhr.fasta

echo 'OK: pilot reproduces byte-for-byte'
