# FHR v0.3 format and compatibility

FHR release v0.3 and the converter 0.3.x packages retain numeric schemaVersion 1.
The header parsing rules below are implemented from converter 0.3.1.
The assembly's own version string is independent. No required fields were added.
Top-level metadata is closed; optional fields may be omitted, not replaced by null.

The unreleased v0.4 schema is FHR schemaVersion `"2.0"`, a string: nested objects
reject unknown keys, patterns are anchored, the checksum must be padded base64 of
32 bytes, statistics are nonnegative, and optional scaffold statistics and author
`nameType` are added. See [SCHEMA-CHANGES-v0.4.md](SCHEMA-CHANGES-v0.4.md) for every
change and a migration hint, and [SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md) for what
schemaVersion means and which schema a file's `schema` URL selects.

## New optional fields

| Field | Value | Meaning |
| --- | --- | --- |
| `assemblySoftware` | Legacy string or array of objects | Assembly software name; objects require `name`, with optional `uri`, `version`, and `commandLineOption` (array of argument strings). |
| `assemblyProtocol` | URI string | External assembly protocol/workflow documentation. |
| `vitalStats.N90` | Nonnegative integer | Contig length in base pairs at the 90% cumulative assembly-length threshold. `N50`, `L50` and `L90` are also contig statistics (stated from v0.4). |
| `vitalStats.scaffoldN50`, `scaffoldN90`, `scaffoldL50`, `scaffoldL90` | Nonnegative integer (v0.4) | The same statistics computed over scaffolds. |
| `vitalStats.gcContent` | Number from 0 to 100 | Percentage of G/C bases, not a fraction: write `42.0` for 42%; `0.42` means 0.42%. Contributors must document how ambiguous bases were handled. |
| `seqcol_id` | 32 base64url characters | Unprefixed level-zero GA4GH refget sequence collection digest. |

SeqCol uses [sha512t24u](https://ga4gh.github.io/refget/seqcols/): SHA-512 truncated
to 24 bytes and URL-safe base64. Its default collection identity incorporates
names, lengths, and sequence digests; it is not simply a hash of concatenated
sequence letters. FHR stores a user-supplied digest and does not compute it,
resolve it, or verify it against a local genome. Different attribute profiles can
produce different digests; record that context in external documentation.

## Checksum decision for v0.3

The [FHR paper](https://doi.org/10.1093/bib/bbae122) describes identity covering
metadata and sequence data together. The published schema specifies SHA-512/256
in a 44-character base64 representation; older README examples and converter
helpers used MD5 and described different coverage. v0.3 explicitly adopts:

1. [R1] Read the FASTA/GFA as bytes; do not normalize line endings, encoding, comments,
   sequence wrapping, ordering, or whitespace. For a gzip- or bgzip-compressed
   file, these are the decompressed bytes: compression is transport, so the same
   content has the same checksum whatever tool or level compressed it. A line ends
   at LF, at CRLF, or at a CR that is not followed by LF; the terminator belongs to
   the line. Every rule below uses lines in this sense. Writers should use LF or
   CRLF, because some FASTA readers treat a lone CR as an ordinary byte.
2. [R2] Require exactly one root-level header line matching `;~checksum:` (FASTA) or
   `#~checksum:` (GFA), with an unquoted key. Spaces may appear before the key
   only to match the root indentation of the other header lines, and before the
   colon.
   Nested properties named checksum remain covered. (From v0.4 FHR's nested
   objects reject unknown keys, so in FHR such a line occurs only inside a
   scalar; header types with nested checksums, such as `derivedFrom`, keep it.)
3. [R3] Exclude that entire line and its line terminator. Hash every other byte,
   including all other metadata and ordinary comments. The checksum covers the
   bytes of every other line but not where the checksum line sits among them, so
   moving it within the header block changes neither the checksum nor the
   metadata. Writers put it last in the header block.
4. [R4] Apply SHA-512/256 (the SHA-512/256 algorithm, not SHA-512 truncated manually).
   Encode its 32-byte digest using standard padded base64, with no `md5:` prefix.
   The encoding is canonical: 32 bytes leave two unused bits, which are zero, so
   the character before `=` is one of `AEIMQUYcgkosw048`. Any other value is
   invalid. Compare checksums as exact strings, never by decoding them.

Header lines are identified on the same byte lines that are hashed, so every
reader must agree on what the checksum line contains:

- [R5] The checksum line holds the checksum value and nothing else, because the
  whole line is excluded from the checksum (R3). After the prefix and the root
  indentation it has the unquoted key `checksum`, optional spaces, a colon, one or
  more spaces, the 44-character value (R4) either plain or in single or double
  quotes, and optional trailing spaces before the line terminator:

  ```
  checksum-line = prefix indent "checksum" *SP ":" 1*SP value *SP
  value         = b64 / "'" b64 "'" / DQUOTE b64 DQUOTE
  b64           = 42(ALPHA / DIGIT / "+" / "/") ("A" / "E" / "I" / "M" / "Q" / "U" /
                  "Y" / "c" / "g" / "k" / "o" / "s" / "w" / "0" / "4" / "8") "="
  ```

  (ABNF, RFC 5234; `prefix` is `;~` or `#~` and `indent` the root indentation.)
  Anything else on the line makes the file invalid: a tab, a YAML comment, a tag,
  other text, a block scalar indicator, or a value continued on the next line. Writers
  emit exactly `;~checksum: <value>` (`#~checksum: <value>` in GFA and GFF3).
- [R6] FHR header lines must be UTF-8 and must not contain U+0085, U+2028, or U+2029,
  which YAML treats as line breaks. Bytes outside header lines are not decoded.
- [R7] A FASTA/GFA file must not begin with a UTF-8 byte order mark. JSON, YAML, and
  HTML metadata may begin with one; it is ignored.
- [R8] FHR metadata must not contain duplicate mapping keys, YAML anchors, aliases,
  or merge keys.
- [R9] In microdata, the first of repeated attributes applies, and `itemtype` and
  `itemprop` are space-separated token lists.

- [R10] FHR lines must form the leading header block: every `;~`/`#~` line must come
  before the first FASTA `>` line, or the first GFA line that is neither a `#`
  comment nor blank. Ordinary comments and blank lines may be mixed in. A
  `;~`/`#~` line after that point, including one from a concatenated file, makes
  the file invalid; it is neither ignored nor merged.

- [R11] In FASTA files (FHR and FHP), FHR header lines should not contain a raw `>`
  or `@`. Many FASTA readers (kseq: BWA, minimap2, seqtk, `samtools dict`, pysam
  `FastxFile`) start a record at the first `>` or `@` anywhere in a line, so such a
  character silently adds a bogus record. Writers put a value that contains `>` or
  `@` in a double-quoted YAML scalar and write the characters as `\x3E` and `\x40`;
  YAML readers return the original characters, so the metadata is unchanged and every
  other format (JSON, YAML, JSON-LD, microdata) holds the real characters. A file with
  a raw `>` or `@` stays valid; validators warn. Ordinary `;` comment lines before the
  first record should avoid the characters too. Like R6, this keeps header lines
  readable the same way by FASTA tools and YAML readers: R6 excludes characters that
  YAML treats as line breaks, R11 those that FASTA readers treat as record starts.
  The checksum value (R5) is base64 and never contains either. GFA and GFF3 headers
  are not affected: their readers treat `#` lines as whole-line comments.
  A raw `>` or `@` can't occur on the checksum line, which R5 limits to the value.

- [R12] FHR metadata written as YAML, in header lines or in a YAML file, is read
  with YAML 1.2 core-schema types, and must read the same way under YAML 1.1, so
  that every YAML library returns the same values. Explicit tags (`!...`,
  including `!!str`, `!!binary` and `!!timestamp`) are invalid. A plain (unquoted)
  scalar that YAML 1.1 and YAML 1.2 read as different values is invalid: for
  example integers with a leading zero (`010`, which YAML 1.1 reads as octal 8),
  with `_` (`1_000`), or written `0b...` or `0o...`; sexagesimal numbers (`1:30`);
  `yes`, `no`, `on`, `off`, `y` and `n` in any letter case; and exponents written
  without a decimal point (`1e3`). Plain scalars that look like dates or times are
  strings, exactly as written. Quote such a value to keep it as text. Writers
  quote every string that either YAML version would read as another type.

The bracketed ids R1 to R12 are stable labels for the rules above, used by the
[conformance vectors](../conformance/README.md); they add no requirements.
The vectors give each rule valid and invalid files: FASTA/GFA files with expected
checksums computed independently of the converter, and for R9 HTML microdata files
with the expected extracted metadata (see [MICRODATA.md](MICRODATA.md)).
The JSON-LD form of FHR metadata and its reading rules J1 to J7 are in
[JSONLD.md](JSONLD.md).

Changing any covered metadata or data bytes invalidates the checksum. The
checksum does not authenticate an author or protect against malicious rewriting.
A supplied SeqCol digest identifies a collection through a separate algorithm.

The combine helpers regenerate a canonical YAML header, strip existing FHR lines
from the supplied payload, preserve every other payload byte, and compute the new
checksum. Strip removes complete FHR lines and leaves ordinary comments intact.
A bare metadata file's checksum is only a value; metadata validation does not
establish correspondence with a genome file.

## Migration

Recombine metadata with the original FASTA/GFA to recalculate old MD5 or
payload-only checksums. Do not relabel an MD5 digest as SHA-512/256. The synthetic
checksum and SeqCol placeholders in standalone examples are for structure only.

Legacy software strings remain accepted. New objects have a closed set of
properties and require a name. ORCID values now explicitly require strings;
previously the pattern-only definition could inadvertently accept nonstrings.
The checksum pattern also requires all 44 characters to be base64 characters,
closing a trailing-newline regex loophole. These corrections reject malformed
metadata rather than changing valid ORCID/checksum representations.
No implied license rename is introduced: `reuseConditions` remains the field.

Review a concrete schema/baseline diff for intentional changes, synchronize the
bundled converter schema, and run LinkML equivalence and example validation.
