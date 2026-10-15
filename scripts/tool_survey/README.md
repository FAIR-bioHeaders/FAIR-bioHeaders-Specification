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
