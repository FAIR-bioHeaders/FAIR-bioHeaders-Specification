# FHR format and compatibility

FHR release v0.3 and the converter 0.3.x packages retain numeric schemaVersion 1.
FHR release v0.4 uses the string schemaVersion `"2.0"`, and releases from v0.5
(currently v0.6.0) use `"2.1"`, which adds only extension fields (R15). The header
parsing rules below apply to all of these releases and are implemented from
converter 0.3.1.
The assembly's own version string is independent. No required fields were added.
Top-level metadata is closed, except for extension fields whose keys start with `x-` (R15,
from FHR 2.1, FHP 1.1 and FHGFF3 1.1); optional fields may be omitted, not replaced by null.

The consolidated status of the known schema-contract gaps, including R13, is in
[SCHEMA-GAP-AUDIT.md](SCHEMA-GAP-AUDIT.md).

The v0.4 schema is FHR schemaVersion `"2.0"`, a string: nested objects
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
| `vitalStats.N90` | Nonnegative integer | Contig length in base pairs at the 90% cumulative contig-length threshold; see [assembly statistics](#assembly-statistics-vitalstats). `N50`, `L50` and `L90` are also contig statistics (stated from v0.4). |
| `vitalStats.scaffoldN50`, `scaffoldN90`, `scaffoldL50`, `scaffoldL90` | Nonnegative integer (v0.4) | The same statistics computed over scaffolds. |
| `vitalStats.gcContent` | Number from 0 to 100 | Percentage of G/C bases, not a fraction: write `42.0` for 42%; `0.42` means 0.42%. Use the denominator and ambiguity rules in [assembly statistics](#assembly-statistics-vitalstats); document the calculation convention. |
| `seqcol_id` | 32 base64url characters | Unprefixed level-zero GA4GH refget sequence collection digest. |

SeqCol uses [sha512t24u](https://ga4gh.github.io/refget/seqcols/): SHA-512 truncated
to 24 bytes and URL-safe base64. Its default collection identity incorporates
names, lengths, and sequence digests; it is not simply a hash of concatenated
sequence letters. FHR stores a user-supplied digest and does not compute it,
resolve it, or verify it against a local genome. Different attribute profiles can
produce different digests; record that context in external documentation.

## Assembly statistics (`vitalStats`)

These normative FHR definitions are rule R16 (see the [rule list](#checksum-decision)).
They resolve the previously unspecified gap and length conventions, following the [jointly approved #251 proposal](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/251#issuecomment-6928652476).
They concern the genome assembly described by the whole file, not the header's
text or an external estimated genome size. FHP protein statistics and FHT
transcript statistics retain their own definitions. These units describe an assembly
as sequence records; this section does not define how a graph producer chooses
paths to turn graph segments into scaffolds.

- A **scaffold** is a FASTA record containing at least one sequence letter.
  A record without sequence contributes neither a scaffold nor a contig.
- A **contig** is a maximal nonempty run of non-`N` sequence letters within a
  scaffold. Every run of one or more `N`/`n` letters splits contigs: the minimum
  gap length is **one**, with no assembler-specific 10- or 100-`N` threshold.
  Leading/trailing `N` runs contribute to scaffold length but to no contig.
  Other nucleotide ambiguity letters remain in contig lengths. Sequence case
  changes neither these counts nor lengths.
- `numberScaffolds` and `numberContigs` count those units.
  `totalBasePairs` is the sum of scaffold lengths, **including `N` and other
  nucleotide ambiguity letters**. Lengths exclude deflines, metadata/comments
  and whitespace/line endings; no sequence bytes are rewritten to compute them.
- For `N50`, `L50`, `N90` and `L90`, sort contig lengths in descending order.
  The denominator is the **sum of contig lengths**, excluding `N` gaps.
  At percentage *x* (50 or 90), take the first cumulative sum at least
  *x*/100 of that denominator. `Nx` (`N50` or `N90`) is the length of the contig at that point;
  `Lx` (`L50` or `L90`) is the number of contigs counted, including that contig.
- `scaffoldN50`, `scaffoldL50`, `scaffoldN90` and `scaffoldL90` apply the same
  rule to descending scaffold lengths, with `totalBasePairs` as denominator.
  Do not use `totalBasePairs` as the contig N/L denominator or an external genome
  size as either denominator.
- `gcContent` is the percentage `100 * (G + C) / (A + C + G + T + U)`, counting
  case-insensitively and rounding to two decimal places. `N` and every other
  ambiguity letter are excluded from **both** numerator and denominator.
  `U` contributes to the denominator without being rewritten to `T`.
  Describe this convention in producer documentation; an unqualified fraction
  such as `0.42` still means 0.42%, not 42%.

**Empty denominators:** omit a statistic whose denominator is zero; zero is not
an unknown-value placeholder. An all-`N` nonempty record is a scaffold and adds to
`totalBasePairs`, but contributes zero contigs: contig N/L statistics are
undefined and omitted. Its GC percentage is also undefined and omitted. A
nonempty set containing no A/C/G/T/U likewise has undefined GC percentage.
Scaffold N/L statistics are undefined when there are no nonempty records.
Measured counts and total length may be zero where the existing schema permits
zero; optionality, numeric minima and all other validation constraints are
unchanged. Producers may reject an empty input rather than emit statistics;
no missing measurement is invented.

For example, records `AANNNCC` and `GNT` have scaffold lengths `[7, 3]`,
contig lengths `[2, 2, 1, 1]`, `totalBasePairs: 10`, `numberScaffolds: 2` and
`numberContigs: 4`. Contig `N50: 2`, `L50: 2`, `N90: 1`, `L90: 4` use denominator
6. Scaffold `scaffoldN50: 7`, `scaffoldL50: 1`, `scaffoldN90: 3`,
`scaffoldL90: 2` use denominator 10. `gcContent: 50.0` uses three G/C letters
among six A/C/G/T/U letters.

### Compatibility and publication scope

This is a **normative definition clarification**, not merely a formatting edit.
It adds no field, required value, schema constraint, term IRI or serialization;
model and vocabulary changes are limited to field descriptions that cite R16;
the published schema bytes and the version registry are unchanged.
Older headers may have used another gap threshold, denominator or GC convention:
do not silently reinterpret or rewrite their values, claim they were calculated
under this convention, or invalidate them through a new schema gate. Preserve
and document their producer methodology; any deliberate header correction
requires recomputing its file checksum and considering downstream parent links.

The current source implementation from
[Tools #175](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/pull/175)
uses these definitions: it omits undefined contig N/L and GC values, warns when
empty records are excluded, and rejects an input with no sequence-bearing
records. This is source implementation evidence, not a claim about an installed
release or a requirement to use that producer.

The maintainers must classify the publication under
[SCHEMA-VERSIONS](SCHEMA-VERSIONS.md#schemaversion): descriptions qualify for no
version change only when valid values retain their meaning; a changed meaning
requires the corresponding major-contract process. This PR assigns no release
or contract version and does not expand the existing guidance-only v0.6.1 scope.

<a id="checksum-decision-for-v03"></a>

## Checksum decision

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
- [R13] A numeric metadata value must be a finite number. YAML's `.nan`, `.inf`
  and `-.inf`, and `NaN` or `Infinity` written as a JSON extension, make the
  record invalid, as does a value that overflows to infinity. JSON cannot
  represent them, and JSON Schema's `minimum` and `maximum` comparisons with NaN
  are false, so a range check does not catch them; validators still report the
  record invalid.
- [R14] A value whose schema `format` is `uri` should be an `http` or `https` URL.
  These are `relatedLink`, `assemblyProtocol`, `accessionID.url`, a software `uri`,
  the taxon and author `uri`, and their FHP and FHGFF3 counterparts
  (`predictionProtocol`, `annotationProtocol`, a `source` `url`). `ftp` URLs and
  `urn:`, `doi:` and `info:` identifiers are also accepted. A value is checked as
  written: the scheme must start the value and is compared without regard to
  letter case, and a value with whitespace (Unicode whitespace included), a
  control character or a bidirectional formatting character (RFC 3987 section 4.1)
  anywhere has no accepted scheme. `http`, `https` and `ftp`
  also need `//` and a host. Any other value, for example a `javascript:`,
  `data:`, `vbscript:` or `file:` URI, stays schema-valid in FHR 2.0 and 2.1 (and
  FHP and FHGFF3 1.0, 1.1 and 1.2), but validators warn about it. Writers of
  linked-data forms do not write it as a link: a JSON-LD or schema.org export
  writer refuses the record
  ([JSONLD.md](JSONLD.md) J7, [SCHEMAORG-EXPORT.md](SCHEMAORG-EXPORT.md) X5). A
  tool that renders FHR metadata, for example as HTML, should make a link only
  from an accepted scheme. Such a value can't be rejected outright without
  invalidating records that the released schemas accept, so that waits for the
  next major `schemaVersion` of each type.
- [R15] **Extension fields.** A top-level key that matches `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$`
  is an extension field: a value the standard does not define, recorded by a producer for its
  own use. The prefix is `x-` in lower case, followed by an ASCII letter or digit and then
  ASCII letters, digits, `_`, `.` or `-`; no key may contain a line feed. Extension fields are
  allowed in FHR from `schemaVersion` `"2.1"`, in FHP and FHGFF3 from `"1.1"`, and in the FHT
  draft. A record that states an earlier `schemaVersion`, or that cites the schema of a release
  before v0.5.0, has no extension fields; in it an `x-` key is an unknown key, as before.
  - Every other unknown key is still invalid, so a misspelt standard field (`genom`, `X-genome`)
    is still caught. Nested objects (`taxon`, authors, `accessionID`, `vitalStats`, software,
    `derivedFrom`, `source`, `genomeReference` and the others) stay closed: an `x-` key inside
    one is invalid.
  - The value may be any JSON or YAML value: a string, number, boolean, `null`, array or
    object. R8, R11, R12 and R13 apply to extension keys and values as to every other key and
    value, and the checksum covers them like every other header byte (R3). A key in the
    pattern never needs quoting in YAML, and YAML 1.1 and 1.2 always read it as a string.
  - Validators accept extension fields and attach no meaning to them. Tools must not rely on
    them for anything the standard defines, and keep them as written when they combine, strip
    or convert to JSON or YAML.
  - An extension field never overrides a standard field. `x-genome` does not replace or qualify
    `genome`; the standard field always governs.
  - Use a namespace after the prefix, `x-<project>-<field>` (for example `x-refget-commonName`),
    so that independent groups do not choose the same name, such as `x-source`, for different
    things. The namespace is a recommendation; validators do not check it or warn about it.
  - If an extension becomes widely used, it is proposed as a standard field under its own,
    unprefixed name in a later minor `schemaVersion`. The `x-` key is not reserved, renamed or
    reinterpreted by that, so files that use it keep their meaning; writers move to the
    standard field.
  - JSON-LD, the schema.org export and HTML microdata carry no extension fields: writers leave
    them out and say which keys they left out, and a JSON-LD or microdata document that holds
    one is invalid ([JSONLD.md](JSONLD.md) J9, [MICRODATA.md](MICRODATA.md) M5,
    [SCHEMAORG-EXPORT.md](SCHEMAORG-EXPORT.md) X9). Use JSON or YAML to exchange them.
- [R16] **Assembly statistics.** FHR `vitalStats` values are computed as
  [Assembly statistics](#assembly-statistics-vitalstats) defines. Every run of one or more
  `N`/`n` letters splits contigs. Contig `N50`, `L50`, `N90` and `L90` use the summed contig
  length as denominator, and the `scaffold*` statistics use `totalBasePairs`, the summed
  scaffold length including `N`. `gcContent` excludes `N` and the other ambiguity letters from
  numerator and denominator. A statistic whose denominator is zero is omitted. The schema does
  not check stated statistics against the sequence and validators do not recompute them, so
  R16 makes no file invalid; values in older headers computed under another convention are
  kept as written and not reinterpreted.

Each header type has its containers: FHR headers go in FASTA and GFA files, FHP
headers in FASTA files, and FHGFF3 headers in GFF3 files. A header whose type
(chosen by its `schema` URL, see [SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md)) does not
match the file it is in makes the file invalid, even when its checksum matches.

Readers may refuse input beyond these limits, which real headers stay far below: a
header block larger than 1 MiB or longer than 10,000 lines, YAML metadata with more
than 20,000 nodes or nested more than 64 levels deep, and a metadata file (JSON,
YAML, JSON-LD or HTML) larger than 64 MiB after decompression. Writers stay within
them.

The bracketed ids R1 to R16 are stable labels for the rules above, used by the
[conformance vectors](../conformance/README.md); they add no requirements.
The vectors give each applicable rule valid and invalid files: FASTA/GFA files with expected
checksums computed independently of the converter, and for R9 HTML microdata files
with the expected extracted metadata (see [MICRODATA.md](MICRODATA.md)).
The JSON-LD form of FHR metadata and its rules J1 to J9 are in
[JSONLD.md](JSONLD.md).

The schemas do not express every requirement. Required values must be non-empty, `format` must
be asserted by the validator, and NaN and infinities are invalid (R13); see
[SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md#values-the-schema-does-not-check).

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
