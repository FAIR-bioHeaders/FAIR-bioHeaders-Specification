# FHR conformance vectors

These FASTA and GFA files show how FHR header lines are parsed and which bytes the
SHA-512/256 checksum covers, as defined in
[docs/FORMAT.md](../docs/FORMAT.md#checksum-decision-for-v03). The HTML files show
how FHR metadata is extracted from microdata, as defined in
[docs/MICRODATA.md](../docs/MICRODATA.md#reading-rules). The `.jsonld` files show
how FHR metadata is read from its JSON-LD form, as defined in
[docs/JSONLD.md](../docs/JSONLD.md#reading-rules). The `.fhp.fasta` files apply the
same header and checksum rules to protein FASTA with the draft FHP header
([docs/FHP.md](../docs/FHP.md#rules)). The `.fhgff3.gff3` files apply them to GFF3
annotations with the draft FHGFF3 header, placed after `##gff-version 3`
([docs/FHGFF3.md](../docs/FHGFF3.md#rules)). Use them to check an FHR
reader or writer in any language against the specification.

## Layout

- `valid/`: files that a conforming implementation must accept.
- `invalid/`: files that it must reject.
- `manifest.json`: the expected outcome for every file.
- `*.gz`: gzip or BGZF copies. Validate their decompressed bytes.

Every file is byte-exact. `.gitattributes` turns off line-ending conversion for
this directory, so CR and CRLF vectors stay unchanged in every checkout. Don't
open and re-save them in an editor. Run the generator instead.

## Manifest

`rules` maps each stable rule id to a short summary: R1 to R14 from
docs/FORMAT.md, M1 to M4 from docs/MICRODATA.md, J1 to J8 from
docs/JSONLD.md, P1 to P2 from docs/FHP.md, G1 to G3 from docs/FHGFF3.md, and V1 to V6
(schema selection) from docs/SCHEMA-VERSIONS.md. V6 reads an FHR 1 record that cites the raw-main `fhr.json` URL with `schemaVersion` the number 1 against the v0.3.1 schema; `fasta-schema-raw-main-version-1`, which states `1.0` as FHR 1 writers did, was invalid before V6, so it is retired and the same bytes are the valid vector `fasta-schema-raw-main-version-1-0`. The J3 to J5 vectors are JSON-LD in other forms than the canonical
one, so a reader needs a JSON-LD processor for them. The invalid J3 vectors use a context other
than the FHR context alone (remapped, extended, `@import`ed, nested, schema.org `@vocab` or
remote) or `@nest`; a reader rejects them before expansion. J7 constrains writers, so it is
`notApplicable` for invalid input; the valid vectors citing it are writer output. J8 constrains
writers that embed JSON-LD in HTML: `jsonld-script-escaped` is writer output with `<`, `>`, `&`,
U+2028 and U+2029 written as `\u` escapes, and it reads back with the real characters. The same ids appear in
brackets in those documents, where the rule text is authoritative. R9 (repeated
attributes and token lists) and M1 to M4 are tested by the microdata vectors. R11 is a recommendation for FASTA header writers: its valid vectors show escaped `>` and `@` (read back as the real characters) and a raw value that stays valid, and it has no invalid vector. R12 requires YAML 1.1 and YAML 1.2 readers to agree on metadata types. R13 rules out NaN and infinities in numeric metadata; `fasta-nan-vital-stats` and `fasta-infinity-vital-stats` are its invalid vectors, and the valid vectors with numeric `vitalStats` (for example `microdata-canonical`) cite it. R14 makes validators warn about a `format: uri` value without an accepted link scheme, such as `javascript:`; such a record stays valid, so R14 has no invalid vector, and its valid vectors (`fasta-link-scheme-warning`, `jsonld-link-scheme-warning`) list it under `warnings`.

Every entry in `vectors` has these fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable vector name |
| `file` | Path relative to this directory |
| `format` | `fasta`, `gfa`, `microdata` (HTML), `jsonld`, `fhp-fasta` (protein FASTA with an FHP header) or `fhgff3` (GFF3 with an FHGFF3 header) |
| `compressed` | `true` for gzip/BGZF files; `compression` then gives `gzip` or `bgzf` |
| `expected` | `valid` or `invalid` |
| `rules` | Valid vectors only: the rules the file exercises |
| `description` | Valid vectors only: what the file exercises |
| `warnings` | Valid vectors only, optional: rules under which a validator should print a warning for the file (R14). `check_conformance.py --converter` requires a line containing `warning` on its standard error |
| `checksum` | Valid FASTA/GFA vectors only: the expected FHR checksum, base64 SHA-512/256 |
| `metadata` | Valid FASTA/GFA vectors: some expected parsed values (`genome`, `version`, `masking`; the V vectors also `schema` and `schemaVersion`; the R11 and R14 vectors also `documentation` or `relatedLink`). Valid `fhp-fasta` vectors: `proteome`, `version` and `sourceType`. Valid `fhgff3` vectors: `annotation` and `version`. Valid microdata and JSON-LD vectors: the complete expected metadata object. `microdata-schema-invalid`, `jsonld-missing-checksum` the P1/P2 `fhp-fasta` vectors and the G2/G3 `fhgff3` vectors: the metadata they yield, which fails `fhp.json` (P1), `fhgff3.json` (G2) or `fhr.json` (the other vectors, P2 and G3) |
| `rule` | Invalid vectors only: the rule the file breaks |
| `reason` | Invalid vectors only: how the file breaks that rule |
| `result` | Invalid V4 vectors only: `unsupported-version`. A reader must report that the cited schema version is unsupported (the toolkit prints `unsupported schema version`), not check the file against another schema |

Vector ids are stable and never reused. When a rule change alters a vector's expected
outcome, the vector is retired and a vector with a new id takes its place. `retired`
lists each retired id with the outcome it had (`expected`, and `rule` if it was
invalid), the id that replaces it (`replacedBy`) and the `reason`. No entry in
`vectors` uses a retired id.

An invalid vector breaks one rule and is otherwise correct. Where possible its
stated checksum matches the bytes, so an implementation can't pass by failing the
checksum comparison by accident. The R1, R3 and R4 vectors are the exception:
they deliberately carry a checksum computed the wrong way, or one made stale by
editing the file. Reasons describe the defect, not any implementation's error
message.

Compressed valid vectors decompress to the bytes of `fasta-lf` or `gfa-lf` and
have the same checksum.

Microdata has no checksum coverage rule: its `checksum` property is an ordinary
metadata value (here the `fasta-lf` checksum). A valid microdata vector instead
pins the whole extracted object, so every tricky value (first-wins attributes,
token lists, implied end tags, value attributes, escaping, typed and untyped
values) is checked exactly. JSON-LD vectors work the same way: their `checksum`
is an ordinary value, and each valid vector pins the metadata it reads back to. JSON numbers compare by value, so `1` and `1.0` are
equal, but strings, numbers and booleans are never equal to each other. Valid metadata conforms to `fhr.json`. The checksums are
real; valid vectors carry no placeholder checksum or SeqCol value.

## Using the vectors in another implementation

For each manifest entry, read `file` and decompress it if `compressed` is true.
For a `valid` FASTA/GFA vector, your implementation must accept the file, compute
`checksum`, and parse the listed `metadata` values. For a `valid` microdata or
JSON-LD vector, it must extract exactly `metadata`. For an `invalid` vector, it
must reject the file. Reporting the rule id is optional. Treat any difference as
a bug in the implementation or the vectors, and report it as an issue.

To run the FAIR-bioHeaders toolkit (or another CLI with the same commands and exit
codes) over the vectors. FASTA and GFA vectors go to `fhr-fasta-validate` and
`fhr-gfa-validate`. Microdata and JSON-LD vectors go to `fhr-convert in.html out.json`
or `fhr-convert in.jsonld out.json`, and the JSON it writes must equal `metadata`.
`--skip-format jsonld` leaves out the JSON-LD vectors for converters that predate them:

```bash
python scripts/check_conformance.py --converter           # commands on PATH
python scripts/check_conformance.py --converter .venv     # a virtual environment
python scripts/check_conformance.py --converter ../FAIR-bioHeaders-Tools  # a checkout
```

## Regenerating and checking

`scripts/make_conformance.py` builds every vector from small templates. It
computes the checksums with Python's `hashlib` (`sha512_256`) and `base64`,
independently of the converter. It writes gzip and BGZF data as stored deflate
blocks with mtime 0 and no file name, so the output doesn't depend on the local
zlib build. Rerunning it reproduces identical bytes.

```bash
python scripts/make_conformance.py            # rewrite valid/, invalid/, manifest.json
python scripts/check_conformance.py           # standard library only
python scripts/check_conformance.py --schema  # also validate metadata (PyYAML, jsonschema)
```

`check_conformance.py` regenerates the vectors in a temporary directory and
compares the bytes. It then checks that the manifest covers every rule in
docs/FORMAT.md, and recomputes each checksum with a separate reading of the
rules. CI runs these checks and then runs the released converter (`fhr` from PyPI)
over every vector. To add a vector, edit the generator, rerun it, and commit the
script together with its output.
