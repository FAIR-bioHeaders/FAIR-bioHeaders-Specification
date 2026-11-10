#!/usr/bin/env bash
# Reproduce the issue #191 INSDC submission-validator survey from a clean dir.
#
#   ./run-evidence.sh            # full run (downloads tools if missing)
#   TOOLDIR=/path/to/cache ./run-evidence.sh
#
# Validation-only. Nothing here submits to NCBI, ENA or DDBJ, and no account is
# created or used. All data are synthetic.
#
# Tested on macOS 27.2 arm64 with system Python 3.15 and OpenJDK 27.
# Exit codes and outputs of every run are appended to evidence.log.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
FIX="$ROOT/fixtures"
RUNS="$ROOT/runs"
BIN="${TOOLDIR:-$ROOT/bin}"
LOG="$ROOT/evidence.log"
JOBS="$ROOT/jobs.tsv"

T2A_VERSION=1.29.324
ASN_VERSION=3.29.324
T2A_SHA_MAC=94f276a1283be339f10272f71963bce22053a8463987bac3c1ed55a7078583c1
ASNVAL_SHA_MAC=f66d9ba2c0fcda33537144f2a1d39f9426dce80f5d75a390a8cfae8ff3e6cf
WEBIN_JAR_SHA=2202cd76cda299c05ee831811c210c574f2fe7f53b28a2824ff2c3532aea48b8
DDBJ_COMMIT=f3d359969da65d2f755b6a9357eba2f3bc093484
BIOHEADERS_VERSION=0.9.0
ORG='[organism=Exampleus syntheticus] [isolate=SynthEus1]'

mkdir -p "$BIN" "$RUNS"
: > "$LOG"; : > "$JOBS"
say() { printf '%s\n' "$*" | tee -a "$LOG"; }
record() { printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$JOBS"; }

# ---------------------------------------------------------------- tool fetch
fetch() { # fetch <url> <outfile> <expected-sha256|->
  local url=$1 out=$2 want=$3
  if [[ -s "$BIN/$out" ]]; then
    if [[ "$want" == - ]]; then say "cached  $out (no pinned digest)"; return 0; fi
    if [[ "$(shasum -a 256 "$BIN/$out" | cut -d' ' -f1)" == "$want" ]]; then
      say "cached  $out"; return 0
    fi
  fi
  say "fetch   $out <- $url"
  curl -fsSL --retry 3 -o "$BIN/$out" "$url" || { say "FAILED  $out"; return 1; }
  if [[ "$want" != - ]]; then
    local got; got=$(shasum -a 256 "$BIN/$out" | cut -d' ' -f1)
    [[ "$got" == "$want" ]] || { say "DIGEST MISMATCH $out got=$got want=$want"; return 1; }
  fi
}

have_java() { # a working JRE, not Apple's /usr/bin/java stub
  command -v java >/dev/null 2>&1 && java -version >/dev/null 2>&1 && return 0
  export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
  java -version >/dev/null 2>&1
}

say "=== 0. environment"
{ sw_vers; uname -m; python3 --version; java -version; } >>"$LOG" 2>&1 || true

say "=== 1. downloads"
NCBI_BASE=https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program
fetch "$NCBI_BASE/table2asn/mac.table2asn.gz"   mac.table2asn.gz   -
fetch "$NCBI_BASE/asnvalidate/mac.asnvalidate.gz" mac.asnvalidate.gz -
fetch "$NCBI_BASE/table2asn/DOCUMENTATION/VERSIONS" VERSIONS -
fetch "https://github.com/enasequence/webin-cli/releases/download/11.0.0/webin-cli-11.0.0.jar" \
      webin/webin-cli-11.0.0.jar "$WEBIN_JAR_SHA"
for f in mac.table2asn mac.asnvalidate; do
  [[ -s "$BIN/${f%.gz}" ]] || gzip -dfc "$BIN/$f.gz" > "$BIN/${f%.gz}"
  chmod +x "$BIN/${f%.gm}" 2>/dev/null || true; chmod +x "$BIN/${f%.gz}"
done
T2A="$BIN/mac.table2asn"; ASNV="$BIN/mac.asnvalidate"
[[ -s "$BIN/mac.table2asn" ]] && say "table2asn $("$T2A" -version) (expect $T2A_VERSION)"
[[ -s "$BIN/mac.asnvalidate" ]] && say "asnvalidate $("$ASNV" -version) (expect $ASN_VERSION)"

say "=== 2. fixture venv (fair-bioheaders $BIOHEADERS_VERSION)"
[[ -x "$ROOT/venv/bin/bioheaders" ]] || { python3 -m venv "$ROOT/venv"; "$ROOT/venv/bin/pip" install -q "fair-bioheaders==$BIOHEADERS_VERSION"; }
BH="$ROOT/venv/bin/bioheaders"; "$BH" --version >>"$LOG" 2>&1 || true

say "=== 3. fixtures"
# The FH* metadata JSON is written here so a clean checkout reproduces the
# fixtures without reading them back in. Values are synthetic; the taxon ID is
# an unassigned NCBI placeholder (checked: esearch db=taxonomy term=999999999
# returns "count":"0"), and no ORCID is given because the schema requires a
# real-format ORCID and none may be invented.
cat > "$FIX/fhr_meta.json" <<'JSON'
{
  "schema": "https://w3id.org/fair-bioheaders/fhr/v0.5.0",
  "schemaVersion": "2.1",
  "genome": "Exampleus syntheticus synthetic example genome (SynthEus1; not a real organism)",
  "taxon": { "name": "Exampleus syntheticus", "uri": "https://identifiers.org/taxonomy:999999999" },
  "version": "1.0.0",
  "metadataAuthor": [ { "name": "Synthetic fixture author (issue #191; not a real person or org)", "nameType": "Organizational" } ],
  "assemblyAuthor": [ { "name": "Synthetic fixture author (issue #191; not a real person or org)" } ],
  "dateCreated": "2026-11-10",
  "masking": "not-masked",
  "documentation": "Synthetic fixture for FAIR-bioHeaders issue #191 validation testing; fictional organism, invented identifiers.",
  "x-fixture": "insdc-191"
}
JSON
( cd "$FIX" && "$ROOT/venv/bin/python" gen_sequences.py >>"$LOG" 2>&1 )
( cd "$FIX" && "$BH" combine fhr_meta.json fhr_noheader.fsa -o fhr_header.fsa >>"$LOG" 2>&1 )
FHR_SUM=$(grep '^;~checksum:' "$FIX/fhr_header.fsa" | sed 's/^;~checksum: //')
say "FHR checksum of fhr_header.fsa: $FHR_SUM"
FHR_SUM="$FHR_SUM" "$ROOT/venv/bin/python" - "$FIX/fhgff3_meta.json" <<'PY' >>"$LOG" 2>&1
import json, os
p = __import__("sys").argv[1]
d = {
  "schema": "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0",
  "schemaVersion": "1.1",
  "annotation": "Exampleus syntheticus synthetic example annotation (not a real annotation)",
  "taxon": {"name": "Exampleus syntheticus", "uri": "https://identifiers.org/taxonomy:999999999"},
  "version": "1.0.0",
  "metadataAuthor": [{"name": "Synthetic fixture author (issue #191; not a real person or org)", "nameType": "Organizational"}],
  "dateCreated": "2026-11-10",
  "derivedFrom": [{"headerType": "FHR", "relationship": "annotates", "checksum": os.environ["FHR_SUM"]}],
  "documentation": "Synthetic FHGFF3 fixture for FAIR-bioHeaders issue #191; fictional organism, invented identifiers.",
  "x-fixture": "insdc-191",
}
json.dump(d, open(p, "w"), indent=2); open(p, "a").write("\n")
PY
( cd "$FIX" && "$BH" combine fhgff3_meta.json gff3_noheader.gff --type gff3 -o fhgff3_header.gff >>"$LOG" 2>&1 )
( cd "$FIX" && "$ROOT/venv/bin/python" gen_r11_fixture.py >>"$LOG" 2>&1 )
( cd "$FIX" && "$ROOT/venv/bin/python" gen_controls.py >>"$LOG" 2>&1 )
FHR_REAL=$(grep '^;~checksum:' "$FIX/fhr_header.fsa" | sed 's/^;~checksum: //')
FHG_REAL=$(grep '^#~checksum:' "$FIX/fhgff3_header.gff" | sed 's/^#~checksum: //')
say "expected FHR checksum $FHR_REAL ; FHGFF3 checksum $FHG_REAL"

say "=== 4. fixture self-attestation (bioheaders $BIOHEADERS_VERSION)"
verify() { say "\$ bioheaders verify $1"; ( cd "$FIX" && "$BH" verify "$(basename "$1")" ) >>"$LOG" 2>&1
           record "bioheaders-verify" "$(basename "$1")" "$?"; }
verify "$FIX/fhr_header.fsa"
verify "$FIX/fhgff3_header.gff"
verify "$FIX/fhr_r11_rawgt.fsa"
say "\$ bioheaders verify fhr_corrupt.fsa  (negative control; must fail)"
( cd "$FIX" && "$BH" verify fhr_corrupt.fsa ) >>"$LOG" 2>&1; record "bioheaders-verify" "fhr_corrupt.fsa" "$?"
( cd "$FIX" && "$BH" verify-links fhgff3_header.gff fhr_header.fsa ) >>"$LOG" 2>&1
record "bioheaders-verify-links" "fhgff3_header.gff" "$?"

# ------------------------------------------------------------- 5. table2asn
say "=== 5. NCBI table2asn $T2A_VERSION"

run_t2a() { # run_t2a <case> <fsa> <gff|-> <outname>
  local case=$1 fsa=$2 gff=$3 out=$4
  local d="$RUNS/t2a/$case"
  rm -rf "$d"; mkdir -p "$d/in"
  cp "$fsa" "$d/in/$out.fsa"
  [[ "$gff" == "-" ]] || cp "$gff" "$d/in/$out.gff"
  local args=(-indir "$d/in" -o "$d/out" -t "$FIX/template.sbt" -V vb -M n -Z -j "$ORG")
  say "\$ mac.table2asn ${args[*]}"
  ( cd "$d" && "$T2A" "${args[@]}" > stdout.log 2> stderr.log ); local rc=$?
  record "table2asn" "$case" "$rc"; say "  exit=$rc"
  [[ -f "$d/out.val" ]] && { say "  --- out.val"; cat "$d/out.val" >>"$LOG"; }
}

run_t2a fasta-noheader "$FIX/fhr_noheader.fsa" - sample
run_t2a fasta-header   "$FIX/fhr_header.fsa"   - sample
run_t2a fasta-corrupt  "$FIX/fhr_corrupt.fsa"  - sample
run_t2a fasta-r11      "$FIX/fhr_r11_rawgt.fsa" - sample
run_t2a gff-noheader   "$FIX/fhr_noheader.fsa" "$FIX/gff3_noheader.gff" sample
run_t2a gff-header     "$FIX/fhr_noheader.fsa" "$FIX/fhgff3_header.gff" sample
run_t2a gff-corrupt    "$FIX/fhr_noheader.fsa" "$FIX/fhgff3_corrupt.gff" sample
run_t2a both-header    "$FIX/fhr_header.fsa"   "$FIX/fhgff3_header.gff" sample

compare() { # compare <label> <a> <b>
  if cmp -s "$2" "$3"; then say "$1: IDENTICAL"; else say "$1: DIFFERS"; fi
}
W="$RUNS/t2a"
compare "sqn fasta header vs plain"   "$W/fasta-header/out"        "$W/fasta-noheader/out"
compare "gbf fasta header vs plain"   "$W/fasta-header/out.gbf"    "$W/fasta-noheader/out.gbf"
compare "sqn corrupt vs valid header" "$W/fasta-corrupt/out"       "$W/fasta-header/out"
compare "sqn R11 vs valid header"     "$W/fasta-r11/out"           "$W/fasta-header/out"
compare "sqn gff header vs plain"     "$W/gff-header/out"          "$W/gff-noheader/out"
compare "sqn gff corrupt vs plain"    "$W/gff-corrupt/out"         "$W/gff-noheader/out"
compare "val gff corrupt vs plain"    "$W/gff-corrupt/out.val"     "$W/gff-noheader/out.val"
compare "val gff header vs plain"     "$W/gff-header/out.val"      "$W/gff-noheader/out.val"
compare "sqn both-header vs plain"    "$W/both-header/out"         "$W/gff-noheader/out"
for c in fasta-header gff-header both-header; do
  say "header text leaked into $c outputs: $(grep -rlE 'w3id|schemaVersion|x-fixture' "$W/$c/out" "$W/$c/out.gbf" 2>/dev/null | wc -l | tr -d ' ') file(s)"
done

say "=== 6. asnvalidate $ASN_VERSION (validates the .sqn, not the FASTA/GFF3)"
mkdir -p "$RUNS/t2a/asnval"
for c in gff-noheader gff-header; do
  cp "$W/$c/out" "$RUNS/t2a/asnval/$c.sqn"
  say "\$ mac.asnvalidate -i $c.sqn -o $c.sqn.val"
  ( cd "$RUNS/t2a/asnval" && "$ASNV" -i "$c.sqn" -o "$c.sqn.val" > "$c.stdout" 2> "$c.stderr" )
  record "asnvalidate" "$c" "$?"
  say "  --- $c.sqn.val"; cat "$RUNS/t2a/asnval/$c.sqn.val" >> "$LOG" 2>/dev/null
done
say "\$ mac.asnvalidate -i plain.fsa   (does it read FASTA at all?)"
cp "$FIX/fhr_noheader.fsa" "$RUNS/t2a/asnval/plain.fsa"
cp "$FIX/fhr_header.fsa" "$RUNS/t2a/asnval/fhr.fsa"
( cd "$RUNS/t2a/asnval" && "$ASNV" -i plain.fsa -o /dev/null > asn-plain.stdout 2> asn-plain.stderr )
record asnvalidate-plain-fsa control "$?"; grep FAILURE "$RUNS/t2a/asnval/asn-plain.stderr" >> "$LOG" 2>&1
say "\$ mac.asnvalidate -i fhr.fsa"
( cd "$RUNS/t2a/asnval" && "$ASNV" -i fhr.fsa -o /dev/null > asn-fhr.stdout 2> asn-fhr.stderr )
record asnvalidate-plain-fsa fhr "$?"; grep -iE 'Error|FAILURE' "$RUNS/t2a/asnval/asn-fhr.stderr" | head -3 >> "$LOG" 2>&1

# ------------------------------------------------------------- 7. Webin-CLI
say "=== 7. ENA Webin-CLI 11.0.0"
JAR="$BIN/webin/webin-cli-11.0.0.jar"
if have_java; then
  mkdir -p "$RUNS/webin"
  for ctx in genome annotation sequence; do
    say "\$ java -jar webin-cli-11.0.0.jar -fields -context=$ctx"
    java -jar "$JAR" "-fields" "-context=$ctx" 2>/dev/null \
      | grep -vE '^[0-9:]{8},[0-9]+ \|-' > "$RUNS/webin/fields-$ctx.txt"
    record "webin-cli-fields" "$ctx" "${PIPESTATUS[0]}"
  done
  mk_webin_dir() { # mk_webin_dir <case> <manifest-block> <datafile>
    local d="$RUNS/webin/$1"; rm -rf "$d"; mkdir -p "$d"
    printf '%s' "$2" > "$d/manifest.tsv"; cp "$3" "$d/"
  }
  gzip -9nc "$FIX/fhr_noheader.fsa" > "$RUNS/webin/gen-plain.fasta.gz"
  gzip -9nc "$FIX/fhr_header.fsa"   > "$RUNS/webin/gen-fhr.fasta.gz"
  gzip -9nc "$FIX/gff3_noheader.gff" > "$RUNS/webin/an-plain.gff3.gz"
  gzip -9nc "$FIX/fhgff3_header.gff" > "$RUNS/webin/an-fhgff3.gff3.gz"
  gen_manifest() { printf 'NAME\tsyn-191\nSTUDY\tSample-Study-Synthetic-191\nASSEMBLY_NAME\tExamSyntheticAssembly1\nASSEMBLY_TYPE\tcontig\nMOLECULE_TYPE\tgenomic DNA\nCOVERAGE\t1\nPLATFORM\tILLUMINA\nFASTA\t%s\n' "$1"; }
  ann_manifest() { printf 'NAME\tsyn-191\nSTUDY\tSample-Study-Synthetic-191\nANALYSIS_TYPE\tDECOUPLED_ANNOTATION\nPRIMARY_ID\tGCA_900000000.1\nDESCRIPTION\tSynthetic issue 191 fixture; the accession is a placeholder, not a real assembly\nGFF3\t%s\n' "$1"; }
  for arm in plain fhr; do
    fa=$([ "$arm" = plain ] && echo gen-plain.fasta.gz || echo gen-fhr.fasta.gz)
    mk_webin_dir "genome-$arm" "$(gen_manifest "$fa")" "$RUNS/webin/$fa"
  done
  for arm in plain header; do
    g=$([ "$arm" = plain ] && echo an-plain.gff3.gz || echo an-fhgff3.gff3.gz)
    mk_webin_dir "annot-$arm" "$(ann_manifest "$g")" "$RUNS/webin/$g"
  done
  for d in genome-plain genome-fhr annot-plain annot-header; do
    for mode in -validate -validateFiles; do
      say "\$ java -jar webin-cli-11.0.0.jar $mode -context $( [[ $d == genome* ]] && echo genome || echo annotation ) -manifest manifest.tsv   (in $d)"
      ( cd "$RUNS/webin/$d" && java -jar "$JAR" "$mode" -context \
          "$( [[ $d == genome* ]] && echo genome || echo annotation )" \
          -manifest manifest.tsv > "evidence${mode}.out" 2> "evidence${mode}.err" )
      rc=$?; record "webin-cli${mode}" "$d" "$rc"
      say "  exit=$rc  $(grep -E '^ERROR' "$RUNS/webin/$d/evidence${mode}.out" | head -1)"
    done
  done
  say "STOP: Webin-CLI refuses to run -validate/-validateFiles without a Webin"
  say "account. No account was created and no credential was used."

  # 7b. the GFF3 engine Webin-CLI bundles, invoked directly (offline, no account)
  say "=== 7b. gff3tools 5.5.1 (BOOT-INF/lib inside webin-cli-11.0.0.jar) run directly"
  GT="$BIN/gff3tools/libs"
  if [[ ! -d "$GT" ]]; then
    mkdir -p "$BIN/gff3tools/tmp" && cd "$BIN/gff3tools"
    unzip -o -q "$JAR" 'BOOT-INF/lib/*' -d tmp && mkdir -p libs && mv tmp/BOOT-INF/lib/*.jar libs/ && rm -rf tmp && cd "$ROOT"
  fi
  G="$ROOT/venv/bin/python"
  mkdir -p "$RUNS/webin/gff3tools-lib" && cd "$RUNS/webin/gff3tools-lib"
  # plain-sequence side-cars: the FASTA provider needs one file per seqId
  "$G" - "$FIX/fhr_noheader.fsa" <<'PY'
import sys
seqs = {}; cur = None
for line in open(sys.argv[1]):
    line = line.strip()
    if line.startswith('>'):
        cur = line[1:].split()[0]; seqs[cur] = []
    elif line and cur:
        seqs[cur].append(line)
for k, v in seqs.items():
    open(f'{k}.seq', 'w').write(''.join(v))
PY
  for arm in noheader header; do
    g=$([ "$arm" = noheader ] && echo "$FIX/gff3_noheader.gff" || echo "$FIX/fhgff3_header.gff")
    say "\$ gff3tools validation $g (report-only)"
    java -cp "$GT/*" uk.ac.ebi.embl.gff3tools.cli.Main validation "$g" > "$arm.reportonly.out" 2> "$arm.reportonly.err"
    record "gff3tools-reportonly" "$arm" "$?"
    say "\$ gff3tools validation $g --sequence ctg1:ctg1.seq --sequence ctg2:ctg2.seq -  (rewrite to stdout)"
    java -cp "$GT/*" uk.ac.ebi.embl.gff3tools.cli.Main validation "$g" \
      --sequence ctg1:ctg1.seq --sequence ctg2:ctg2.seq - > "$arm.rewrite.out.gff" 2> "$arm.rewrite.err"
    record "gff3tools-rewrite" "$arm" "$?"
  done
  compare "gff3tools rewrite header vs plain" header.rewrite.out.gff noheader.rewrite.out.gff
  say "gff3tools rewrite of the FHGFF3 arm:"; cat header.rewrite.out.gff >> "$LOG"
  say "\$ bioheaders verify fhgff3_corrupt.gff  (negative control; must fail)"
  ( cd "$FIX" && "$BH" verify fhgff3_corrupt.gff ) >>"$LOG" 2>&1
  record "bioheaders-verify" "fhgff3_corrupt.gff" "$?"
  say "\$ gff3tools validation fhgff3_corrupt.gff ..."
  java -cp "$GT/*" uk.ac.ebi.embl.gff3tools.cli.Main validation "$FIX/fhgff3_corrupt.gff" \
    --sequence ctg1:ctg1.seq --sequence ctg2:ctg2.seq - > corrupt.rewrite.out.gff 2> corrupt.rewrite.err
  record "gff3tools-rewrite" "corrupt-checksum" "$?"
  compare "gff3tools corrupt-header rewrite vs header" corrupt.rewrite.out.gff header.rewrite.out.gff
  say "NOTE: the gff3tools FASTA sequence provider fails on the plain control too"
  cp "$FIX/fhr_noheader.fsa" plainctl.fasta; cp "$FIX/fhr_header.fsa" fhrctl.fasta
  java -cp "$GT/*" uk.ac.ebi.embl.gff3tools.cli.Main validation "$FIX/fhgff3_header.gff" \
    --sequence plainctl.fasta - > fasta-provider-plain.out 2> fasta-provider-plain.err
  record gff3tools-fasta-provider control "$?"
  java -cp "$GT/*" uk.ac.ebi.embl.gff3tools.cli.Main validation "$FIX/fhgff3_header.gff" \
    --sequence fhrctl.fasta - > fasta-provider-fhr.out 2> fasta-provider-fhr.err
  record gff3tools-fasta-provider fhr "$?"
  grep -m1 'Unable to resolve\|passed' fasta-provider-plain.err fasta-provider-plain.out >> "$LOG" 2>&1
  cd "$ROOT"
else
  say "SKIP 7/7b: no JRE on PATH (expected java at /opt/homebrew/opt/openjdk/bin)"
  record "webin-cli" "no-java" 127
fi

# ------------------------------------------------------------- 8. DDBJ
say "=== 8. DDBJ ddbj-validator @ $DDBJ_COMMIT"
if [[ ! -x "$ROOT/venv-ddbj/bin/ddbj-validator" ]]; then
  python3 -m venv "$ROOT/venv-ddbj" && "$ROOT/venv-ddbj/bin/pip" install -q \
    "git+https://github.com/ddbj/ddbj-validator.git@$DDBJ_COMMIT"
fi
DV="$ROOT/venv-ddbj/bin/ddbj-validator"
if [[ -x "$DV" ]]; then
  "$DV" --version >>"$LOG" 2>&1 || true
  rm -rf "$RUNS/ddbj"
  ddbj_run() { # ddbj_run <case> <fasta>
    local d="$RUNS/ddbj/$1"; rm -rf "$d"; mkdir -p "$d/in"
    cp "$2" "$d/in/sample.fasta"; cp "$FIX/ddbj_sample.ann" "$d/in/sample.ann"
    say "\$ ddbj-validator -l in -o out   ($1)"
    ( cd "$d" && "$DV" -l in -o out > stdout.log 2> stderr.log )
    record "ddbj-validator" "$1" "$?"
    say "  --- report"; grep -E 'ERR|WAR' "$d/out/reports/validation_report_summary.txt" >>"$LOG" 2>/dev/null
  }
  ddbj_run plain    "$FIX/fhr_noheader.fsa"
  ddbj_run fhr      "$FIX/fhr_header.fsa"
  ddbj_run corrupt  "$FIX/fhr_corrupt.fsa"
  ddbj_run r11      "$FIX/fhr_r11_rawgt.fsa"
  mkdir -p "$ROOT/controls"
  { echo '; ordinary FASTA comment line (not FAIR-bioHeaders)'; cat "$FIX/fhr_noheader.fsa"; } \
    > "$ROOT/controls/semicolon_line.fsa"
  ddbj_run c1-semicolon "$ROOT/controls/semicolon_line.fsa"
  "$ROOT/venv/bin/python" - "$FIX" "$ROOT/controls/semicolon_block.fsa" <<'PY'
import pathlib, sys
fix, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
lines = (fix / "fhr_header.fsa").read_text().splitlines(keepends=True)
hdr = [l for l in lines if l.startswith(";~")]
rec = [l for l in lines if not l.startswith(";~")]
dst.write_text("".join("; " + l[2:] for l in hdr) + "".join(rec))
PY
  ddbj_run c3-semicolon-block "$ROOT/controls/semicolon_block.fsa"
  compare "ddbj fixed FASTA plain vs fhr" "$RUNS/ddbj/plain/out/fixed/sample.fasta" \
                                           "$RUNS/ddbj/fhr/out/fixed/sample.fasta"
  say "DDBJ auto-fixed FASTA for the FHR arm (first 20 lines):"
  head -20 "$RUNS/ddbj/fhr/out/fixed/sample.fasta" >> "$LOG"
  say "DDBJ takes no GFF3 input: the annotation format is .ann, so FHGFF3 has no DDBJ reader to test."
else
  say "SKIP 8: ddbj-validator not installed"
fi

# ------------------------------------------------------------- 9. strip path
say "=== 9. bioheaders strip round-trip (the documented workaround)"
mkdir -p "$RUNS/strip"
"$BH" strip "$FIX/fhr_header.fsa" "$RUNS/strip/sample.fsa"; record strip fhr "$?"
"$BH" strip "$FIX/fhgff3_header.gff" "$RUNS/strip/sample.gff"; record strip fhgff3 "$?"
compare "strip fhr  -> plain fixture" "$RUNS/strip/sample.fsa" "$FIX/fhr_noheader.fsa"
compare "strip fhgff3 -> plain fixture" "$RUNS/strip/sample.gff" "$FIX/gff3_noheader.gff"
run_t2a fasta-stripped "$RUNS/strip/sample.fsa" - sample
compare "table2asn sqn stripped vs headered" "$W/fasta-stripped/out" "$W/fasta-header/out"

say
say "=== summary (tool, case, exit code)"
column -t -s $'\t' "$JOBS" | tee -a "$LOG"
say
say "Full logs: $LOG"
say "Per-run directories: $RUNS"
