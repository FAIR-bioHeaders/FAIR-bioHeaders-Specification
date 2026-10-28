# FHR tool-compatibility survey

Scripts behind [docs/TOOL_COMPATIBILITY.md](../../docs/TOOL_COMPATIBILITY.md).

| File | Purpose |
| --- | --- |
| `make_inputs.py` | Writes small deterministic control and FHR-headed FASTA, GFA and GFF3 files |
| `run_survey.py` | Runs each tool on a control/FHR pair and classifies the result |
| `fp.py` | Reduces tool output to a comparable fingerprint (names, lengths, MD5s) |
| `gff_probe.mjs` | Parses GFF3 with `@gmod/gff`, the JBrowse 2 parser |
| `run_all.sh` | Regenerates inputs and reruns everything |
| `make_marker_variants.py` | Copies the inputs with the leading `;` lines marked `#` or unmarked, for the comment-marker comparison |
| `environment-extra.yml`, `rust/` | The extra FASTA parsers of 2026-10-18; `rust/` builds small noodles-fasta and rust-bio readers |
| `results/results-extra.tsv` | Results of the extra parsers with the leading lines marked `;`, marked `#` or unmarked (`header_marker` column) |
| `environment-annotation.yml` | The annotation and assembly tools of 2026-10-19, as separate environments; `run_survey.py` finds them through the `S3*` PATH-prefix variables, `BUSCO_LINEAGE` and `COMPLEASM_LIB` (see the file's header) |
| `results/results-annotation.tsv` | Results of the annotation and assembly tools with the leading lines marked `;` (R11 header), marked `#`, unmarked, or `;` with a raw `@`/`>` value (`header_marker` column) |
| `round4/` | The 2026-10-22 survey (R and Bioconductor readers, JBrowse 2 FASTA code, Bakta, Kraken2, BWA-MEM2, Ensembl VEP): `make_round4_inputs.py` writes the inputs from a control FASTA, `run_round4.py` runs and classifies the tests, with small probes (`r_probe.R`, `indexedfasta_probe.mjs`, `header_fai.py`) and `package.json` |
| `environment-round4.yml` | The 2026-10-22 tools, as separate environments; `run_round4.py` finds them through the `R4*` PATH-prefix variables (see the file's header) |
| `results/results-round4.tsv` | Results of the 2026-10-22 survey with the leading lines marked `;` (R11 header), one `;comment` line, `#`, unmarked, or `;` with a raw `@`/`>` value (`header_marker` column) |
| `round5/` | The round-5 survey of 2026-10-28 (gene callers, clustering, alignment and phylogeny tools, eggNOG-mapper, CheckM2's genome reader, with genome, protein (FHP) and alignment inputs): `make_round5_inputs.py` writes the inputs from a control genome and its proteins, `run_round5.py` runs and classifies the tests, with the probe `pyrodigal_api.py` |
| `environment-round5.yml` | The round-5 tools, as separate environments; `run_round5.py` finds them through the `R5*` PATH-prefix variables (see the file's header) |
| `results/results-round5.tsv` | Results of the round-5 survey with the leading lines marked `;` (R11 FHR or FHP header), one `;comment` line, `#`, unmarked, `;` with a raw `@`/`>` value, or gzip (`header_marker` column) |
| `environment.yml`, `environment-graph.yml`, `package.json` | Tested tool versions |
| `results/results.tsv` | Results of the 2026-10-08 run |

## Setup

```bash
micromamba create -n survey -f environment.yml
micromamba create -n survey-graph -f environment-graph.yml
python -m venv fhrcli && fhrcli/bin/pip install fhr==0.3.3   # fhr-* CLIs
mkdir node && cp package.json node/ && (cd node && npm install)
export PATH=$MAMBA_ROOT_PREFIX/envs/survey/bin:$PATH:$MAMBA_ROOT_PREFIX/envs/survey-graph/bin:$PWD/fhrcli/bin
SURVEY_NODE_DIR=$PWD/node ./run_all.sh /tmp/fhr-survey
```

Extra FASTA parsers (2026-10-18). FASTX.jl needs the official Julia binary
(1.11.7) with `FASTX` 2.2.0 installed (`julia -e 'using Pkg; Pkg.add(name="FASTX", version="2.2.0")'`):

```bash
micromamba create -n survey-extra -f environment-extra.yml
(cd rust && cargo build --release --locked)
python3 make_inputs.py /tmp/fhr-survey/inputs --fhr-bin "$(dirname "$(command -v fhr-fasta-combine)")"
python3 make_marker_variants.py /tmp/fhr-survey/inputs   # writes inputs-hash and inputs-text
export PATH=$MAMBA_ROOT_PREFIX/envs/survey-extra/bin:$MAMBA_ROOT_PREFIX/envs/survey/bin:$PATH JULIA=/path/to/julia
ONLY="Biostrings,scikit-bio,noodles,rust-bio,FASTX,Easel,EMBOSS,MMseqs2,DIAMOND,CD-HIT,Clustal,MUSCLE,IQ-TREE"
for v in inputs inputs-hash inputs-text; do
  python3 run_survey.py /tmp/fhr-survey/$v /tmp/fhr-survey/results-$v --only "$ONLY"
done
```

## Classes

- `a`: exit 0 and the output fingerprint matches the control run. The header was
  ignored, or passed through (`header_lines_in_output` > 0).
- `b?`: exit 0 but the output differs from the control. This may be silent
  corruption. Check `results/diff/`.
- `c`: the tool failed. `c(rc0)` means it printed an error and wrote no data
  but still exited 0.
- `n/a`: the control run failed too, so the header is not the cause.

FASTA and GFA headers come from `fhr-fasta-combine`/`fhr-gfa-combine` with
`examples/example.fhr.yaml`. GFF3 `#~` headers are hand-written because FHGFF3
is unreleased. `edge.comment1.fa` has a single leading `;` line. It is not a
valid FHR file; it probes parsers that read leading lines as an unnamed record.
`concat.fhr.fa` (`cat fhr.fa extra.fhr.fa`) and `concat.mixed.fa`
(`cat control.fa extra.fhr.fa`) are also invalid under R10. They show what
tools do with header lines that follow a record.
