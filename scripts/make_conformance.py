"""Write the FHR FASTA/GFA/microdata/JSON-LD conformance vectors and their manifest (stdlib only).

Every vector is built from a small metadata template. Expected checksums are
computed here with ``hashlib.sha512_256`` and base64 over the bytes the
docs/FORMAT.md rules cover, never by the FHR File Converter. Expected microdata
metadata is written out by hand from docs/FORMAT.md and docs/MICRODATA.md.
JSON-LD vectors are literal documents built with the reference writer of
scripts/make_jsonld.py (standard library only, no JSON-LD processor) and the
committed jsonld/fhr.context.jsonld; their expected metadata follows docs/JSONLD.md.
The expanded and other-context forms (rules J3 to J5) are rewritten from the
writer's output by the small functions below, not by a JSON-LD processor;
tests/test_jsonld_roundtrip.py checks with PyLD that each valid one expands to
the same RDF as the canonical document.
Output is deterministic: compressed vectors use stored deflate blocks, mtime 0
and no file name, so rerunning the script reproduces identical bytes.
"""

import argparse
import base64
import copy
import hashlib
from html import escape
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "conformance"
MANIFEST_VERSION = 1

# Stable, non-normative labels for the docs/FORMAT.md rules.
RULES = {
    "R1": "Checksum rule 1: hash the exact file bytes without normalization; "
          "for gzip/BGZF input, the decompressed bytes.",
    "R2": "Checksum rule 2: exactly one root-level checksum line with an unquoted "
          "key; spaces only to match root indentation and before the colon; nested "
          "checksum properties stay covered.",
    "R3": "Checksum rule 3: exclude that entire line and its terminator; hash every "
          "other byte, so changing covered bytes invalidates the checksum.",
    "R4": "Checksum rule 4: SHA-512/256 digest in standard padded base64, no prefix.",
    "R5": "Header parsing: the checksum value is a single-line YAML scalar on the "
          "checksum line; block scalars and continuation lines are invalid.",
    "R6": "Header parsing: FHR header lines are UTF-8 without U+0085, U+2028 or "
          "U+2029; bytes outside header lines are not decoded.",
    "R7": "Header parsing: a FASTA/GFA file must not begin with a UTF-8 byte "
          "order mark.",
    "R8": "Header parsing: no duplicate mapping keys, YAML anchors, aliases or "
          "merge keys.",
    "R9": "Header parsing: in microdata the first of repeated attributes applies; "
          "itemtype and itemprop are space-separated token lists.",
    "R10": "Header parsing: FHR lines form the leading header block; a later "
           "FHR line, including one from a concatenated file, is invalid.",
    "M1": "Microdata: exactly one FHR item scope; a nested item scope without "
          "itemprop is a separate item whose properties do not leak.",
    "M2": "Microdata: HTML parsing with implied end tags; values come from the "
          "defining element's value attribute, else its text.",
    "M3": "Microdata: data-fhr-type values must match the declared JSON type; "
          "typed strings are exact; untyped schema numbers and lists are converted.",
    "M4": "Microdata: the extracted metadata must validate against fhr.json; a "
          "repeated property cannot fill a single-valued field.",
    "J1": "JSON-LD: a canonical document has a published FHR context (embedded or a known "
          "URL) and no keyword but @type and a root @id; @context and @type are set aside, "
          "subjectOf is documentation, and export terms are set aside.",
    "J2": "JSON-LD: duplicate object keys are invalid.",
    "J3": "JSON-LD: any other form is read by JSON-LD 1.1 expansion with bundled contexts "
          "only; a context that is not bundled, remote or unknown, is invalid.",
    "J4": "JSON-LD: exactly one top-level node (directly or the only item of @graph); every "
          "property must map to an FHR field in its scope, and unknown terms or a root @id "
          "make the document invalid.",
    "J5": "JSON-LD: IRI fields take @id or a string; dateCreated takes xsd:date or no type, "
          "and no other datatype is allowed; single-valued fields take one value; "
          "commandLineOption comes from @list; a node given only by @id is invalid.",
    "J6": "JSON-LD: the resulting metadata must validate against fhr.json.",
    "J7": "JSON-LD: writers emit the record with an embedded context and typed nodes, "
          "byte for byte as docs/JSONLD.md describes.",
}
NOT_APPLICABLE = {
    "J7": "J7 constrains writers; a reader has no invalid input for it. The valid vectors "
          "that cite J7 are writer output.",
}

PREFIX = {"fasta": b";~", "gfa": b"#~"}
ITEM_TYPE = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json"
COMMENT = {"fasta": b";", "gfa": b"#"}
SUFFIX = {"fasta": ".fhr.fasta", "gfa": ".fhr.gfa", "microdata": ".fhr.html",
          "jsonld": ".fhr.jsonld"}
MARK = b"@CHECKSUM@"
GENOME = "Synthetic FHR conformance genome"
VERSION = "1.0.0"
MASKING = "not-masked"

# Root-level YAML metadata; ``None`` marks the checksum line.
METADATA = [
    "schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
    "schemaVersion: 1.0",
    f"genome: {GENOME}",
    "taxon:",
    "  name: Homo sapiens",
    "  uri: https://identifiers.org/taxonomy:9606",
    f"version: {VERSION}",
    "metadataAuthor:",
    "- name: Synthetic metadata author (placeholder)",
    "assemblyAuthor:",
    "- name: Synthetic assembly author (placeholder)",
    "dateCreated: '2026-10-08'",
    f"masking: {MASKING}",
    "documentation: Synthetic FHR conformance vector; not a real assembly.",
    None,
]
BODY = {
    "fasta": [b">Contig1 synthetic sequence", b"ACGTACGTAC", b"GGTTAACCAT"],
    "gfa": [b"H\tVN:Z:1.0", b"S\tContig1\tACGTACGTACGGTTAACCAT"],
}
EXPECTED_METADATA = {"genome": GENOME, "version": VERSION, "masking": MASKING}


def digest(data):
    return base64.b64encode(hashlib.new("sha512_256", data).digest()).decode("ascii")


class Line:
    """One line without its terminator; ``excluded`` lines are not hashed."""

    def __init__(self, text, excluded=False):
        self.text = text
        self.excluded = excluded


def header(kind, metadata=METADATA, indent="", key="checksum: "):
    """FHR lines for ``metadata``, with the checksum line written as ``key``."""
    prefix = PREFIX[kind]
    lines = []
    for item in metadata:
        if item is None:
            text = prefix + indent.encode() + key.encode() + MARK
            lines.append(Line(text, excluded=True))
        else:
            lines.append(Line(prefix + indent.encode() + item.encode("utf-8")))
    return lines


def body(kind):
    return [Line(text) for text in BODY[kind]]


def assemble(lines, endings=b"\n", final_newline=True, hash_data=None):
    """Join ``lines`` and fill the checksum marker.

    ``endings`` is one terminator or a list cycled over the lines. The checksum
    is computed over the bytes of every line not marked excluded, unless
    ``hash_data`` maps those bytes to the bytes that should be hashed instead.
    """
    if isinstance(endings, bytes):
        endings = [endings]
    pieces = []
    for index, line in enumerate(lines):
        last = index == len(lines) - 1
        ending = b"" if last and not final_newline else endings[index % len(endings)]
        pieces.append((line, line.text + ending))
    covered = b"".join(data for line, data in pieces if not line.excluded)
    value = digest(hash_data(covered) if hash_data else covered).encode("ascii")
    return b"".join(data.replace(MARK, value) for _, data in pieces), value.decode()


def standard(kind, **options):
    return assemble(header(kind) + body(kind), **options)


# Compression: stored deflate blocks keep the bytes independent of zlib builds.

def _stored_deflate(data):
    if not data:
        return b"\x01\x00\x00\xff\xff"
    out = b""
    for start in range(0, len(data), 0xFFFF):
        chunk = data[start:start + 0xFFFF]
        final = start + 0xFFFF >= len(data)
        out += bytes([final]) + struct.pack("<HH", len(chunk), len(chunk) ^ 0xFFFF) + chunk
    return out


def _trailer(data):
    return struct.pack("<II", zlib.crc32(data), len(data) & 0xFFFFFFFF)


def gzip_member(data):
    # ID1 ID2 CM=deflate FLG=0 MTIME=0 XFL=0 OS=unknown: no name, fixed time.
    return b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff" + _stored_deflate(data) + _trailer(data)


BGZF_EOF = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")


def bgzf(data, block_size=96):
    """BGZF: gzip members carrying a BC extra field, then the standard EOF block."""
    out = b""
    for start in range(0, len(data), block_size):
        chunk = data[start:start + block_size]
        deflated = _stored_deflate(chunk)
        block_size_minus_one = 18 + len(deflated) + 8 - 1
        out += (
            b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff"
            + struct.pack("<H", 6) + b"BC" + struct.pack("<HH", 2, block_size_minus_one)
            + deflated + _trailer(chunk)
        )
    return out + BGZF_EOF


def multimember_gzip(data, split):
    return gzip_member(data[:split]) + gzip_member(data[split:])


def decompress(data):
    """Decompress concatenated gzip members (for self-checks)."""
    out = b""
    while data:
        engine = zlib.decompressobj(31)
        out += engine.decompress(data) + engine.flush()
        data = engine.unused_data
    return out


# Reference reading of the rules, used to self-check valid vectors.

def reference_checksum(data, kind):
    """Return (stated value, computed value) or raise ValueError."""
    prefix = PREFIX[kind]
    lines = data.splitlines(keepends=True)
    header_lines, in_block = [], True
    for line in lines:
        if in_block:
            if kind == "fasta" and line.startswith(b">"):
                in_block = False
            elif kind == "gfa" and not line.startswith(b"#") and line.strip():
                in_block = False
        if line.startswith(prefix):
            if not in_block:
                raise ValueError("FHR line after the header block")
            header_lines.append(line)
    contents = [line[len(prefix):].rstrip(b"\r\n") for line in header_lines]
    indents = [
        len(text) - len(text.lstrip(b" \t")) for text in contents
        if text.strip() and not text.lstrip().startswith(b"#")
    ]
    pattern = re.compile(rb"^" + re.escape(prefix) + rb"([ \t]*)checksum[ \t]*:(.*)$", re.S)
    matches = [
        line for line in header_lines
        if (found := pattern.match(line.rstrip(b"\r\n"))) and len(found.group(1)) == min(indents)
    ]
    if len(matches) != 1:
        raise ValueError("expected exactly one root checksum line")
    excluded = matches[0]
    position = data.index(excluded) if lines.count(excluded) == 1 else None
    if position is None:
        raise ValueError("ambiguous checksum line")
    value = pattern.match(excluded.rstrip(b"\r\n")).group(2).strip().strip(b"'\"").decode()
    return value, digest(data[:position] + data[position + len(excluded):])


# The vectors.

VALID = []
INVALID = []


def valid(name, kind, data, value, rules, description, compression=None):
    VALID.append(dict(name=name, kind=kind, data=data, checksum=value, rules=rules,
                      description=description, compression=compression, status="valid"))


def invalid(name, kind, data, rule, reason, compression=None):
    INVALID.append(dict(name=name, kind=kind, data=data, rule=rule, reason=reason,
                        compression=compression, status="invalid"))


def comments_and_blanks(kind):
    comment = COMMENT[kind]
    lines = header(kind)
    lines.insert(0, Line(comment + b" ordinary comment before the FHR lines"))
    lines.insert(1, Line(b""))
    lines.insert(5, Line(comment + b" ordinary comment between FHR lines"))
    lines.insert(6, Line(b""))
    lines.insert(9, Line(PREFIX[kind] + b"# a YAML comment inside the FHR header"))
    lines.insert(len(lines) - 1, Line(comment))
    extra = [Line(b";  legacy FASTA comment after a record")] if kind == "fasta" else []
    return lines + [Line(b"")] + body(kind) + extra


def with_metadata(kind, replacements=(), insert=(), **options):
    metadata = list(METADATA)
    for old, new in replacements:
        metadata[metadata.index(old)] = new
    for anchor, items in insert:
        position = metadata.index(anchor) + 1
        metadata[position:position] = items
    return header(kind, metadata, **options)


def build():
    VALID.clear()
    INVALID.clear()
    plain = {}
    for kind in ("fasta", "gfa"):
        k = kind
        data, value = standard(k)
        plain[k] = (data, value)
        valid(f"{k}-lf", k, data, value, ["R1", "R2", "R3", "R4", "R7", "R10"],
              "LF line endings; the checksum line is the last FHR line.")
        data, value = standard(k, endings=b"\r\n")
        valid(f"{k}-crlf", k, data, value, ["R1", "R3"], "CRLF line endings; CR bytes are hashed.")
        crlf = data
        data, value = standard(k, endings=b"\r")
        valid(f"{k}-cr", k, data, value, ["R1", "R3"], "Lone CR line endings.")
        data, value = standard(k, endings=[b"\n", b"\r\n", b"\r"])
        valid(f"{k}-mixed-endings", k, data, value, ["R1", "R3"],
              "LF, CRLF and CR line endings mixed in one file.")
        data, value = standard(k, final_newline=False)
        valid(f"{k}-no-final-newline", k, data, value, ["R1", "R3"],
              "The last sequence line has no terminator.")
        data, value = assemble(comments_and_blanks(k))
        valid(f"{k}-comments-and-blank-lines", k, data, value, ["R3", "R10"],
              "Ordinary comments, blank lines and a YAML comment before and between "
              "FHR lines; all of them are hashed.")
        data, value = assemble(header(k, indent=" ") + body(k))
        valid(f"{k}-root-indented", k, data, value, ["R2"],
              "Every FHR line, including the checksum line, has root indentation 1.")
        data, value = assemble(header(k, key="checksum  : ") + body(k))
        valid(f"{k}-space-before-colon", k, data, value, ["R2"], "Spaces before the colon.")
        lines = with_metadata(k, insert=[(
            "  uri: https://identifiers.org/taxonomy:9606",
            ["  checksum: nested property, hashed like other metadata"],
        )])
        data, value = assemble(lines + body(k))
        valid(f"{k}-nested-checksum", k, data, value, ["R2", "R3"],
              "A nested taxon.checksum property is ordinary covered metadata.")
        quote = "'" if k == "fasta" else '"'
        lines = header(k)
        lines[-1].text = lines[-1].text.replace(MARK, quote.encode() + MARK + quote.encode())
        data, value = assemble(lines + body(k))
        valid(f"{k}-quoted-value", k, data, value, ["R2", "R5"],
              "The checksum value is a quoted single-line scalar; the key is unquoted.")
        lines = header(k)
        lines[-1].text += b"   "
        data, value = assemble(lines + body(k))
        valid(f"{k}-checksum-trailing-spaces", k, data, value, ["R3", "R5"],
              "Trailing spaces on the checksum line are excluded with it.")
        lines = header(k)
        lines.insert(0, lines.pop())
        data, value = assemble(lines + body(k))
        valid(f"{k}-checksum-first", k, data, value, ["R2", "R3"],
              "The checksum line is the first line of the file.")
        comment = COMMENT[k]
        lines = header(k)
        lines.insert(3, Line(comment + b" ordinary comment, Latin-1 bytes: caf\xe9 \xff\xfe"))
        tail = [Line(b">Contig1 description in Latin-1: caf\xe9 na\xefve"), Line(BODY[k][1]), Line(BODY[k][2])] \
            if k == "fasta" else [Line(BODY[k][0]), Line(BODY[k][1] + b"\tDS:Z:caf\xe9")]
        data, value = assemble(lines + tail)
        valid(f"{k}-non-utf8-outside-header", k, data, value, ["R1", "R6"],
              "Non-UTF-8 bytes in an ordinary comment and a sequence line are hashed, "
              "not decoded.")
        lines = with_metadata(k, replacements=[(
            "documentation: Synthetic FHR conformance vector; not a real assembly.",
            "documentation: 'Synthetic vector, UTF-8 text: café µm — 測試'",
        )])
        data, value = assemble(lines + body(k))
        valid(f"{k}-utf8-metadata", k, data, value, ["R6"],
              "Non-ASCII UTF-8 text in a header value.")
        lines = with_metadata(k, replacements=[(
            "documentation: Synthetic FHR conformance vector; not a real assembly.",
            "documentation: 'Quoted YAML indicators are text: &anchor *alias <<: merge'",
        )])
        data, value = assemble(lines + body(k))
        valid(f"{k}-yaml-indicators-in-strings", k, data, value, ["R8"],
              "Anchor, alias and merge-key characters inside a quoted string are text.")

        # Invalid vectors with otherwise correct checksums unless stated.
        data, _ = standard(k, endings=b"\r\n", hash_data=lambda b: b.replace(b"\r\n", b"\n"))
        assert data != crlf
        invalid(f"{k}-crlf-normalized-checksum", k, data, "R1",
                "CRLF file whose checksum was computed after converting line endings to LF.")
        lines = header(k)[:-1]
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-missing-checksum", k, data, "R2", "No checksum line.")
        lines = header(k)
        lines.insert(2, Line(lines[-1].text, excluded=True))
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-two-checksum-lines", k, data, "R2",
                "Two root-level checksum lines with the same value.")
        quote = "'" if k == "fasta" else '"'
        data, _ = assemble(header(k, key=f"{quote}checksum{quote}: ") + body(k))
        invalid(f"{k}-quoted-key", k, data, "R2", "The checksum key is quoted.")
        lines = with_metadata(k, insert=[("  uri: https://identifiers.org/taxonomy:9606", [None])])
        lines[6].text = lines[6].text.replace(b"checksum: ", b"  checksum: ")
        lines.pop()
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-only-nested-checksum", k, data, "R2",
                "Only a nested taxon.checksum holds the digest; there is no root checksum line.")
        data, value = standard(k)
        data = data.replace(GENOME.encode(), b"Tampered genome name")
        invalid(f"{k}-metadata-tampered", k, data, "R3",
                "Metadata changed after the checksum was computed (checksum mismatch).")
        data, _ = standard(k)
        data = data.replace(b"GGTTAACC", b"GGTTAACG")
        invalid(f"{k}-sequence-tampered", k, data, "R3",
                "Sequence changed after the checksum was computed (checksum mismatch).")
        lines = header(k)
        lines[-1].excluded = False
        data, _ = assemble(lines + body(k), hash_data=lambda b, k=k: b.replace(
            PREFIX[k] + b"checksum: " + MARK + b"\n", b"\n"))
        invalid(f"{k}-checksum-terminator-hashed", k, data, "R3",
                "Checksum computed with the checksum line's terminator still included.")
        data, _ = assemble(comments_and_blanks(k))
        data = data.replace(b"ordinary comment between", b"ordinary comment edited between")
        invalid(f"{k}-comment-tampered", k, data, "R3",
                "An ordinary comment changed after the checksum was computed; comments are covered.")
        data, _ = assemble(header(k) + body(k))
        covered = data.replace(re.search(rb"[;#]~checksum: \S+\n", data).group(), b"")
        wrong = base64.b64encode(hashlib.sha512(covered).digest()[:32])
        data = re.sub(rb"(~checksum: )\S+", lambda m: m.group(1) + wrong, data)
        invalid(f"{k}-truncated-sha512", k, data, "R4",
                "SHA-512 truncated to 32 bytes instead of SHA-512/256.")
        wrong = base64.b64encode(hashlib.sha256(covered).digest())
        data = re.sub(rb"(~checksum: )\S+", lambda m: m.group(1) + wrong, data)
        invalid(f"{k}-sha256", k, data, "R4", "SHA-256 instead of SHA-512/256.")
        lines = header(k, key="checksum: |")
        lines[-1].text = lines[-1].text.replace(MARK, b"")
        lines.append(Line(PREFIX[k] + b"  " + MARK, excluded=True))
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-block-literal-checksum", k, data, "R5",
                "The checksum value is a literal block scalar on the next line.")
        lines = header(k, key="checksum: >-")
        lines[-1].text = lines[-1].text.replace(MARK, b"")
        lines.append(Line(PREFIX[k] + b"  " + MARK, excluded=True))
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-folded-checksum", k, data, "R5",
                "The checksum value is a folded block scalar on the next line.")
        data, value = standard(k)
        head, rest = value[:22], value[22:]
        data = data.replace(value.encode(), f"{head}\n".encode() + PREFIX[k] + f"  {rest}".encode())
        invalid(f"{k}-continued-checksum", k, data, "R5",
                "The plain checksum value continues on a second FHR line.")
        data, value = standard(k)
        data = data.replace(value.encode(), f'"{head}\n'.encode() + PREFIX[k] + f'  {rest}"'.encode())
        invalid(f"{k}-quoted-continued-checksum", k, data, "R5",
                "A double-quoted checksum value continues on a second FHR line.")
        for code, label in (("\u0085", "u0085"), (" ", "u2028"), (" ", "u2029")):
            lines = with_metadata(k, replacements=[(
                "documentation: Synthetic FHR conformance vector; not a real assembly.",
                f"documentation: Synthetic{code}  vector text",
            )])
            data, _ = assemble(lines + body(k))
            invalid(f"{k}-{label}-in-header", k, data, "R6",
                    f"An FHR header line contains U+{label[1:].upper()}, a YAML line break.")
        lines = header(k)
        lines[13].text = lines[13].text.replace(b"Synthetic", b"Synth\xe9tic")
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-non-utf8-header", k, data, "R6", "An FHR header line is not valid UTF-8.")
        data, _ = assemble([Line(b"\xef\xbb\xbf" + line.text, line.excluded) if i == 0 else line
                            for i, line in enumerate(header(k) + body(k))])
        invalid(f"{k}-utf8-bom", k, data, "R7", "The file begins with a UTF-8 byte order mark.")
        lines = with_metadata(k, insert=[(f"genome: {GENOME}", ["genome: Second genome value"])])
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-duplicate-key", k, data, "R8", "The root key genome appears twice.")
        lines = with_metadata(k, replacements=[(f"genome: {GENOME}", f"genome: &name {GENOME}")])
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-yaml-anchor", k, data, "R8", "A YAML anchor on the genome value.")
        lines = with_metadata(k, replacements=[(f"genome: {GENOME}", f"genome: &name {GENOME}")],
                              insert=[(f"genome: &name {GENOME}", ["genomeSynonym:", "- *name"])])
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-yaml-alias", k, data, "R8", "A YAML alias repeats the anchored genome value.")
        lines = with_metadata(k, replacements=[("  name: Homo sapiens", "  <<: {name: Homo sapiens}")])
        data, _ = assemble(lines + body(k))
        invalid(f"{k}-yaml-merge-key", k, data, "R8", "taxon uses a YAML merge key.")
        late = [Line(PREFIX[k] + b"funding: added after the sequence data")]
        data, _ = assemble(header(k) + body(k) + late)
        invalid(f"{k}-fhr-line-after-sequence", k, data, "R10",
                "An FHR line follows the first record; it is hashed, not ignored or merged.")
        second_metadata = [item.replace(GENOME, "Second concatenated genome") if item else item
                           for item in METADATA]
        second, _ = assemble(header(k, second_metadata) + body(k))
        data = plain[k][0] + second
        invalid(f"{k}-concatenated", k, data, "R10",
                "Two complete FHR files concatenated; each part has a correct checksum.")

    for k in ("fasta", "gfa"):
        data, value = plain[k]
        valid(f"{k}-gzip", k, gzip_member(data), value, ["R1"],
              f"{k}-lf compressed as one gzip member; same checksum.", "gzip")
        valid(f"{k}-bgzf", k, bgzf(data), value, ["R1"],
              f"{k}-lf compressed as multi-block BGZF; same checksum.", "bgzf")
        split = data.index(b"checksum: ") + 20
        valid(f"{k}-gzip-multimember", k, multimember_gzip(data, split), value, ["R1"],
              f"{k}-lf as two gzip members split inside the checksum line; same checksum.",
              "gzip")
    data, _ = plain["fasta"]
    invalid("fasta-gzip-sequence-tampered", "fasta",
            gzip_member(data.replace(b"GGTTAACC", b"GGTTAACG")), "R3",
            "Compressed copy of a sequence-tampered file (checksum mismatch).", "gzip")
    MICRODATA_CHECKSUM[0] = plain["fasta"][1]
    build_microdata()
    build_jsonld()

# Microdata vectors. The checksum is an ordinary value here (the fasta-lf
# checksum), so these vectors pin the extracted metadata instead.

MICRODATA_CHECKSUM = [None]
MD_ROOT = f'itemscope itemtype="{ITEM_TYPE}"'
PERSON = "https://schema.org/Person"


def md_base():
    return {
        "schema": ITEM_TYPE,
        "schemaVersion": 1.0,
        "genome": GENOME,
        "taxon": {"name": "Homo sapiens", "uri": "https://identifiers.org/taxonomy:9606"},
        "version": VERSION,
        "metadataAuthor": [{"name": "Synthetic metadata author (placeholder)"}],
        "assemblyAuthor": [{"name": "Synthetic assembly author (placeholder)"}],
        "dateCreated": "2026-10-08",
        "masking": MASKING,
        "documentation": "Synthetic FHR conformance vector; not a real assembly.",
        "checksum": MICRODATA_CHECKSUM[0],
    }


def md_property(key, value):
    """One property in the converter's typed serialization (docs/MICRODATA.md)."""
    prop = escape(key, quote=True)
    if isinstance(value, dict):
        content = "".join(md_property(k, v) for k, v in value.items())
        return f'<span itemprop="{prop}" itemscope data-fhr-type="object">{content}</span>'
    if isinstance(value, list):
        content = "".join(md_property("item", v) for v in value)
        return f'<span itemprop="{prop}" data-fhr-type="array">{content}</span>'
    if isinstance(value, bool):
        kind, text = "boolean", json.dumps(value)
    elif isinstance(value, int):
        kind, text = "integer", json.dumps(value)
    elif isinstance(value, float):
        kind, text = "number", json.dumps(value)
    else:
        kind, text = "string", value
    return f'<span itemprop="{prop}" data-fhr-type="{kind}">{escape(text)}</span>'


def md_content(metadata=None, replace=None, after=None):
    """Typed properties for ``metadata``; ``replace`` maps a key to its own markup
    ("" drops it) and ``after`` maps a key to markup inserted after it."""
    metadata = md_base() if metadata is None else metadata
    replace, after = replace or {}, after or {}
    parts = []
    for key, value in metadata.items():
        parts.append(replace[key] if key in replace else md_property(key, value))
        parts.append(after.get(key, ""))
    return "".join(parts)


def md_page(content, root=MD_ROOT, before="", after="", bom=False):
    text = (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        "<title>FHR conformance vector</title></head><body>\n"
        f"{before}<div {root}>{content}</div>{after}\n</body></html>\n"
    )
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def md_expect(**changes):
    metadata = md_base()
    for key, value in changes.items():
        if value is None:
            metadata.pop(key)
        else:
            metadata[key] = value
    return metadata


def md_valid(name, data, metadata, rules, description):
    VALID.append(dict(name=name, kind="microdata", data=data, metadata=metadata, rules=rules,
                      description=description, compression=None, status="valid"))


def md_invalid(name, data, rule, reason, metadata=None):
    INVALID.append(dict(name=name, kind="microdata", data=data, rule=rule, reason=reason,
                        metadata=metadata, compression=None, status="invalid"))


def build_microdata():
    s = 'data-fhr-type="string"'
    canonical = md_base()
    canonical.update({
        "genomeSynonym": ["synthetic conformance genome"],
        "instrument": [],
        "identifier": ["example:conformance-1"],
        "relatedLink": ["https://example.org/synthetic"],
        "assemblySoftware": [{"name": "synthetic-assembler", "version": "1.2.3",
                              "commandLineOption": ["-t", "2"]}],
        "assemblyProtocol": "https://example.org/protocols/synthetic-assembly",
        "vitalStats": {"N50": 20, "L50": 1, "totalBasePairs": 20, "gcContent": 45.5,
                       "readTechnology": "synthetic"},
    })
    md_valid("microdata-canonical", md_page(md_content(canonical)), canonical,
             ["M1", "M3", "M4"],
             "The converter's typed serialization: nested objects, arrays, an empty "
             "array, integers and numbers.")

    md_valid("microdata-first-attribute-wins", md_page(
        md_content(replace={
            "genome": f'<span itemprop="genome" itemprop="version" {s} '
                      f'data-fhr-type="number">{GENOME}</span>',
            "version": f'<span itemprop="version" {s} data-fhr-type="integer">{VERSION}</span>',
            "dateCreated": '<time itemprop="dateCreated" datetime="2026-10-08" '
                           'datetime="1999-01-01">yesterday</time>',
        }),
        root=f'itemscope itemtype="{ITEM_TYPE}" itemtype="https://schema.org/Dataset"',
    ), md_expect(), ["R9", "M2"],
        "Repeated itemtype, itemprop, data-fhr-type and datetime attributes; the "
        "first of each applies.")

    md_valid("microdata-itemtype-token-list", md_page(
        md_content(),
        root=f'itemscope itemtype="https://schema.org/Dataset\n  {ITEM_TYPE}\t'
             f'https://example.org/types/Genome "',
    ), md_expect(), ["R9", "M1"],
        "The root itemtype lists the FHR type among other types, separated by spaces, "
        "a tab and a newline.")

    author = [{"name": "Synthetic author of metadata and assembly"}]
    md_valid("microdata-itemprop-token-list", md_page(md_content(replace={
        "genome": f'<span itemprop="\tgenome  " {s}>{GENOME}</span>',
        "metadataAuthor": md_property("metadataAuthor", author).replace(
            'itemprop="metadataAuthor"', 'itemprop=" metadataAuthor\tassemblyAuthor\n"'),
        "assemblyAuthor": "",
    })), md_expect(metadataAuthor=author, assemblyAuthor=author), ["R9"],
        "One element supplies both metadataAuthor and assemblyAuthor through an itemprop "
        "token list; another itemprop has surrounding whitespace.")

    md_valid("microdata-implied-end-tags", md_page(md_content(replace={
        "documentation": f'<p itemprop="documentation" {s}>Paragraph closed by the next '
                         "p start tag.<p>Unrelated paragraph closed by the list.",
        "genomeSynonym": "",
        "version": "",
        "masking": "",
        "dateCreated": "",
    }, after={
        "documentation": f'<ul itemprop="genomeSynonym" data-fhr-type="array">'
                         f'<li itemprop="item" {s}>first synonym'
                         f'<li itemprop="item" {s}>second synonym</ul>'
                         f'<table><tr><td itemprop="version" {s}>{VERSION}'
                         f'<td itemprop="masking" {s}>{MASKING}'
                         "<tr><td>unrelated cell<td>another cell</table>"
                         f'<dl><dt>Created<dd itemprop="dateCreated" {s}>2026-10-08'
                         "<dt>Note<dd>unrelated definition</dl>",
    })), md_expect(dateCreated=None, masking=None, version=None, documentation=None) | {
        "documentation": "Paragraph closed by the next p start tag.",
        "genomeSynonym": ["first synonym", "second synonym"],
        "version": VERSION, "masking": MASKING, "dateCreated": "2026-10-08",
    }, ["M2"],
        "Unclosed p, li, td, tr, dt and dd elements inside the FHR scope end where HTML "
        "implies their end tags.")

    md_valid("microdata-nested-unrelated-scope", md_page(
        md_content(after={
            "genome": f'<div itemscope itemtype="{PERSON}"><span itemprop="name">Leaked '
                      'Person</span><span itemprop="genome">Leaked genome</span>'
                      '<span itemprop="version">9.9.9</span></div>',
            "taxon": '<div itemscope><span itemprop="dateCreated">1999-01-01</span>'
                     '<span itemprop="masking">hard-masked</span></div>',
        }),
        before=f'<div itemscope itemtype="{PERSON}"><span itemprop="genome">Genome '
               "outside the FHR scope</span></div>",
    ), md_expect(), ["M1"],
        "Item scopes without itemprop, inside and before the FHR scope, hold genome, "
        "version, dateCreated and masking properties that are not FHR values.")

    links = ["https://example.org/images/synthetic.png", "https://example.org/synthetic"]
    vital = {"N50": 20, "gcContent": 45.5}
    md_valid("microdata-value-attributes", md_page(md_content(replace={
        "dateCreated": '<time itemprop="dateCreated" datetime="2026-10-08">8 October '
                       "2026</time>",
        "version": f'<data itemprop="version" value="{VERSION}">version one</data>',
        "masking": f'<meta itemprop="masking" content="{MASKING}">',
        "taxon": '<span itemprop="taxon" itemscope data-fhr-type="object">'
                 f'<span itemprop="name" {s}>Homo sapiens</span>'
                 '<a itemprop="uri" href="https://identifiers.org/taxonomy:9606">NCBI '
                 "Taxonomy 9606</a></span>",
    }, after={
        "checksum": '<link itemprop="assemblyProtocol" '
                    'href="https://example.org/protocols/synthetic-assembly">'
                    f'<span itemprop="relatedLink" data-fhr-type="array">'
                    f'<img itemprop="item" src="{links[0]}" alt="figure">'
                    f'<a itemprop="item" href="{links[1]}">project page</a></span>'
                    '<span itemprop="vitalStats" itemscope data-fhr-type="object">'
                    '<data itemprop="N50" value="20" data-fhr-type="integer">twenty</data>'
                    '<meter itemprop="gcContent" value="45.5" min="0" max="100" '
                    'data-fhr-type="number">about half</meter></span>',
    })), md_expect(assemblyProtocol="https://example.org/protocols/synthetic-assembly",
                   relatedLink=links, vitalStats=vital), ["M2", "M3"],
        "time[datetime], data[value], meter[value], meta[content], a[href], "
        "link[href] and img[src] supply the value instead of the element text.")

    md_valid("microdata-value-attributes-elsewhere-ignored", md_page(md_content(replace={
        "genome": f'<span itemprop="genome" content="Wrong content" value="Wrong value" '
                  f'{s}>{GENOME}</span>',
        "version": f'<div itemprop="version" value="9.9.9" datetime="2000-01-01">{VERSION}</div>',
        "documentation": '<p itemprop="documentation" href="https://example.org/wrong" '
                         f'src="https://example.org/wrong.png" {s}>'
                         "Synthetic FHR conformance vector; not a real assembly.</p>",
        "masking": f'<b itemprop="masking" content="soft-masked">{MASKING}</b>',
        "dateCreated": '<time itemprop="dateCreated">2026-10-08</time>',
        "taxon": '<span itemprop="taxon" itemscope data-fhr-type="object">'
                 f'<span itemprop="name" datetime="2001-01-01" {s}>Homo sapiens</span>'
                 '<span itemprop="uri" href="https://example.org/wrong" '
                 f'{s}>https://identifiers.org/taxonomy:9606</span></span>',
    })), md_expect(), ["M2"],
        "content, value, datetime, href and src on elements that do not define them "
        "are ignored; a time without datetime uses its text.")

    md_valid("microdata-html-escaping", md_page(md_content(replace={
        "genome": f'<span itemprop="genome" {s}>Synthetic &lt;script&gt;alert(1)'
                  "&lt;/script&gt; &amp; &quot;double&quot; &#39;single&#39; "
                  "&amp;lt;literal&amp;gt;</span>",
        "documentation": '<meta itemprop="documentation" content="Attribute text: a '
                         '&amp; b &lt;c&gt; &quot;d&quot; &#x27;e&#x27;">',
    })), md_expect(
        genome="Synthetic <script>alert(1)</script> & \"double\" 'single' &lt;literal&gt;",
        documentation="Attribute text: a & b <c> \"d\" 'e'",
    ), ["M2", "M3"],
        "Escaped markup, ampersands and quotes in text and in an attribute decode once, "
        "exactly; nothing is executed.")

    unicode_genome = "Synthetic genome café µm — 測試 🧬"
    spaced = "  Leading and trailing spaces,\ta tab and\na newline are kept.  "
    authors = [{"name": "Zoë Ångström 測試"}]
    md_valid("microdata-non-ascii", md_page(md_content(
        replace={
            "genome": md_property("genome", unicode_genome),
            "documentation": md_property("documentation", spaced),
            "metadataAuthor": f'<span itemprop="metadataAuthor" data-fhr-type="array">'
                              f'<span itemprop="item" itemscope data-fhr-type="object">'
                              f'<span itemprop="name" {s}>Zo&euml; &Aring;ngstr&ouml;m '
                              "&#x6E2C;&#35430;</span></span></span>",
        })), md_expect(genome=unicode_genome, documentation=spaced, metadataAuthor=authors),
        ["M2", "M3"],
        "Non-ASCII UTF-8 text and character references; a typed string keeps its "
        "leading, trailing and inner whitespace.")

    md_valid("microdata-utf8-bom", md_page(md_content(), bom=True), md_expect(), ["R7"],
             "HTML metadata beginning with a UTF-8 byte order mark, which is ignored.")

    typed = md_expect(schemaVersion=1.0, version="2")
    typed.update({
        "genomeSynonym": ["2", "true", "null", "1.0"],
        "instrument": [],
        "assemblySoftware": [{"name": "synthetic-assembler", "commandLineOption": ["-k", "31"]}],
        "vitalStats": {"N50": 16, "N90": 0, "totalBasePairs": 16, "gcContent": 37.5,
                       "readTechnology": "100"},
    })
    md_valid("microdata-typed-values", md_page(md_content(typed)), typed, ["M3"],
             "data-fhr-type keeps number-like strings as strings, integers as integers, "
             "numbers as numbers and an empty array as an empty array.")

    untyped = md_expect(schemaVersion=1)
    untyped.update({
        "genomeSynonym": ["only synonym"],
        "identifier": ["example:one", "example:two"],
        "vitalStats": {"N50": 16, "gcContent": 37.5},
    })
    md_valid("microdata-untyped-schema-values", md_page(md_content(untyped, replace={
        "schemaVersion": '<span itemprop="schemaVersion">1</span>',
        "genomeSynonym": '<span itemprop="genomeSynonym">only synonym</span>',
        "identifier": '<span itemprop="identifier">example:one</span>'
                      '<span itemprop="identifier">example:two</span>',
        "vitalStats": '<div itemprop="vitalStats" itemscope><span itemprop="N50">16</span>'
                      '<span itemprop="gcContent">37.5</span></div>',
        "metadataAuthor": '<div itemprop="metadataAuthor" itemscope><span itemprop="name">'
                          "Synthetic metadata author (placeholder)</span></div>",
    })), untyped, ["M3", "M4"],
        "Plain microdata without data-fhr-type: schema numbers are converted, a single "
        "value of a list field becomes a one-item list, repeated values become a list.")

    # Invalid vectors.
    md_invalid("microdata-no-fhr-scope", md_page(
        md_content(), root='itemscope itemtype="https://schema.org/Dataset"'), "M1",
        "The only item scope has a Schema.org type, not the FHR type.")
    md_invalid("microdata-two-fhr-scopes", md_page(md_content(), after=f"<div {MD_ROOT}>"
                                                    f"{md_content()}</div>"), "M1",
               "Two complete FHR item scopes.")
    md_invalid("microdata-genome-only-in-nested-scope", md_page(md_content(replace={
        "genome": f'<div itemscope itemtype="{PERSON}"><span itemprop="genome" {s}>'
                  f"{GENOME}</span></div>"})), "M1",
        "genome appears only inside a nested item scope without itemprop, so the FHR "
        "item has no genome.")
    md_invalid("microdata-itemtype-repeated-attribute", md_page(
        md_content(),
        root=f'itemscope itemtype="https://schema.org/Dataset" itemtype="{ITEM_TYPE}"'), "R9",
        "The FHR type is only in a second itemtype attribute; the first applies, so there "
        "is no FHR item scope.")
    md_invalid("microdata-itemprop-repeated-attribute", md_page(md_content(replace={
        "genome": f'<span itemprop="genomeName" itemprop="genome" {s}>{GENOME}</span>'})),
        "R9", "genome is only in a second itemprop attribute; the first (genomeName, not an "
        "FHR property) applies, so genome is missing.")
    md_invalid("microdata-type-mismatch", md_page(md_content(after={
        "checksum": '<span itemprop="vitalStats" itemscope data-fhr-type="object">'
                    '<span itemprop="gcContent" data-fhr-type="number">abc</span></span>'})),
        "M3", "gcContent is declared a number but its text is abc.")
    md_invalid("microdata-type-mismatch-value-attribute", md_page(md_content(after={
        "checksum": '<span itemprop="vitalStats" itemscope data-fhr-type="object">'
                    '<data itemprop="N50" value="sixteen" data-fhr-type="integer">16</data>'
                    "</span>"})),
        "M3", "N50 is declared an integer; its value comes from data[value], sixteen, not "
        "from the text 16.")
    md_invalid("microdata-value-attribute-applies", md_page(md_content(replace={
        "masking": f'<data itemprop="masking" value="partly">{MASKING}</data>'})), "M2",
        "masking comes from data[value], partly, which fhr.json does not allow; the text "
        f"{MASKING} is not the value.")
    md_invalid("microdata-repeated-single-valued", md_page(md_content(after={
        "genome": f'<span itemprop="genome" {s}>Second genome value</span>'})), "M4",
        "genome has two values; fhr.json allows one string.")
    bad = md_expect()
    bad["vitalStats"] = {"gcContent": 150}
    md_invalid("microdata-schema-invalid", md_page(md_content(bad)), "M4",
               "Well-formed microdata whose gcContent of 150 exceeds the fhr.json maximum "
               "of 100.", metadata=bad)



# JSON-LD vectors (docs/JSONLD.md). The checksum is an ordinary value, as in microdata.

ORCID_EXAMPLE = "https://orcid.org/0000-0002-1825-0097"  # ORCID's documented example iD.
EXPORT_CONTEXT = {
    "id": "https://example.org/datasets/synthetic-conformance",
    "url": "https://example.org/genomes/synthetic-conformance",
    "keywords": ["synthetic", "conformance vector"],
}


def jsonld_record(**changes):
    record = md_base()
    record.update({
        "genomeSynonym": ["synthetic conformance genome"],
        "assemblyAuthor": [{"name": "Josiah Carberry (ORCID example iD)", "uri": ORCID_EXAMPLE}],
        "identifier": ["example:conformance-1"],
        "relatedLink": ["https://example.org/synthetic"],
        "reuseConditions": "CC0-1.0",
        "assemblySoftware": [{"name": "synthetic-assembler", "version": "1.2.3",
                              "commandLineOption": ["-t", "2"]}],
        "vitalStats": {"N50": 20, "L50": 1, "totalBasePairs": 20, "gcContent": 45.5},
    })
    record.update(changes)
    return record


def jsonld_bytes(document):
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def reordered(value):
    """The same JSON value with every object's keys in reverse order."""
    if isinstance(value, dict):
        return {key: reordered(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [reordered(item) for item in value]
    return value


def jsonld_valid(name, document, metadata, rules, description):
    VALID.append(dict(name=name, kind="jsonld", data=jsonld_bytes(document), metadata=metadata,
                      rules=rules, description=description, compression=None, status="valid"))


def jsonld_invalid(name, data, rule, reason, metadata=None):
    INVALID.append(dict(name=name, kind="jsonld", data=data, rule=rule, reason=reason,
                        metadata=metadata, compression=None, status="invalid"))


SDO_IRI = "http://schema.org/"
FHR_IRI = "https://w3id.org/fair-bioheaders/terms#"
XSD_IRI = "http://www.w3.org/2001/XMLSchema#"
VOCAB_CONTEXT = {"@vocab": SDO_IRI, "fhr": FHR_IRI}


def _iri(curie, scope):
    prefix, _, rest = curie.partition(":")
    namespace = scope.get(prefix, {"xsd": XSD_IRI}.get(prefix))
    return namespace + rest if isinstance(namespace, str) else curie


def _scope_of(term):
    return term["@context"][1] if isinstance(term, dict) and "@context" in term else None


def expand_canonical(document):
    """The JSON-LD 1.1 expanded form of a canonical document whose context is the
    embedded FHR context. Covers only what that context uses."""
    root = document["@context"]

    def node(value, scope):
        out = {}
        for key, item in value.items():
            if key == "@context":
                continue
            if key == "@type":
                kinds = item if isinstance(item, list) else [item]
                out["@type"] = [_iri(scope[kind], scope) for kind in kinds]
                continue
            term = scope[key]
            if term == "@id":
                out["@id"] = item
                continue
            items = item if isinstance(item, list) else [item]
            child = _scope_of(term)
            values = []
            for entry in items:
                if child is not None and isinstance(entry, dict):
                    values.append(node(entry, child))
                elif term.get("@type") == "@id":
                    values.append({"@id": entry})
                elif term.get("@type") == "xsd:date":
                    values.append({"@type": XSD_IRI + "date", "@value": entry})
                else:
                    values.append({"@value": entry})
            if term.get("@container") == "@list":
                values = [{"@list": values}]
            out[_iri(term["@id"], scope)] = values
        return out

    return [node(document, root)]


def vocab_compact(expanded):
    """Compact an expanded node against {"@vocab": schema.org, "fhr": ...} only:
    single values unwrapped, untyped values as plain JSON, and typed values,
    IRIs and lists kept as objects."""
    def key(iri):
        if iri.startswith(SDO_IRI):
            return iri[len(SDO_IRI):]
        return "fhr:" + iri[len(FHR_IRI):]

    def value(item):
        if isinstance(item, dict) and set(item) == {"@value"}:
            return item["@value"]
        if isinstance(item, dict) and "@list" in item:
            return {"@list": [value(entry) for entry in item["@list"]]}
        if isinstance(item, dict) and "@value" not in item and set(item) != {"@id"}:
            return node(item)
        return item

    def node(item):
        out = {}
        for name, items in item.items():
            if name == "@id":
                out["@id"] = items
            elif name == "@type":
                kinds = [key(kind) for kind in items]
                out["@type"] = kinds[0] if len(kinds) == 1 else kinds
            else:
                values = [value(entry) for entry in items]
                out[key(name)] = values[0] if len(values) == 1 else values
        return out

    return {"@context": VOCAB_CONTEXT, **node(expanded[0])}


def build_jsonld():
    import make_jsonld

    write = make_jsonld.to_jsonld
    record = jsonld_record()
    jsonld_valid("jsonld-canonical-embedded", write(record), record, ["J1", "J2", "J6", "J7"],
                 "Writer output: the embedded context, @type on the record and on every "
                 "nested node, a name-only author typed Agent and an ORCID author typed Person.")
    by_url = dict(write(record), **{"@context": make_jsonld.RAW_MAIN_CONTEXT_URL})
    jsonld_valid("jsonld-canonical-url", by_url, record, ["J1", "J6"],
                 "The context is referenced by its raw-main URL; nothing is fetched.")
    jsonld_valid("jsonld-keys-reordered", reordered(write(record)), record, ["J1"],
                 "Every object's keys, the root @context and nested @type included, are in "
                 "reverse order.")
    legacy = jsonld_record(assemblySoftware="synthetic-assembler")
    jsonld_valid("jsonld-legacy-software-string", write(legacy), legacy, ["J1", "J7"],
                 "A legacy assemblySoftware string stays a string, with no @type.")
    extra = jsonld_record(taxon={"name": "Homo sapiens",
                                 "uri": "https://identifiers.org/taxonomy:9606",
                                 "checksum": "nested property, not the file checksum"})
    jsonld_valid("jsonld-open-object-extra-key", write(extra), extra, ["J1"],
                 "taxon.checksum has no JSON-LD term; it stays in the document and is kept.")
    versioned = jsonld_record(schema="https://w3id.org/fair-bioheaders/fhr/v0.4.0")
    jsonld_valid("jsonld-schema-versioned-url", write(versioned), versioned, ["J1", "J6"],
                 "The record cites a versioned schema URL, which is kept unchanged.")
    linked = jsonld_record(documentation="https://example.org/synthetic/README")
    jsonld_valid("jsonld-documentation-url", write(linked), linked, ["J1", "J7"],
                 "documentation is an absolute URL, so it is written as subjectOf and read "
                 "back as documentation.")
    jsonld_valid("jsonld-export-terms", write(record, export=EXPORT_CONTEXT), record,
                 ["J1", "J7"],
                 "Export-context terms @id, keywords, url and conformsTo (Bioschemas Dataset "
                 "1.0-RELEASE) are not FHR fields and are set aside.")

    text = jsonld_bytes(write(record)).decode("utf-8")
    duplicate = text.replace(f'  "genome": "{GENOME}",',
                             f'  "genome": "{GENOME}",\n  "genome": "Second genome value",', 1)
    assert duplicate != text
    jsonld_invalid("jsonld-duplicate-key", duplicate.encode("utf-8"), "J2",
                   "The root key genome appears twice.")
    missing = {key: value for key, value in record.items() if key != "checksum"}
    jsonld_invalid("jsonld-missing-checksum", jsonld_bytes(write(missing)), "J6",
                   "A canonical document whose metadata has no checksum, which fhr.json "
                   "requires.", metadata=missing)
    document = write(record)
    document["taxon"]["@type"] = {"@id": "http://schema.org/Taxon"}
    jsonld_invalid("jsonld-type-object", jsonld_bytes(document), "J1",
                   "A @type value is an object, not a string or an array of strings.")
    document = write(record)
    document["subjectOf"] = "https://example.org/synthetic/README"
    jsonld_invalid("jsonld-documentation-and-subjectof", jsonld_bytes(document), "J1",
                   "Both documentation and subjectOf give the documentation value.")
    build_jsonld_general(write, record)


def build_jsonld_general(write, record):
    """Rules J3 to J5: JSON-LD in other forms than the canonical one."""
    expanded = expand_canonical(write(record))
    jsonld_valid("jsonld-expanded", expanded, record, ["J3", "J4", "J5", "J6"],
                 "The canonical document in JSON-LD expanded form: full IRIs, value objects, "
                 "@id for IRI fields, @list for commandLineOption and no context.")
    vocab = vocab_compact(expanded)
    assert isinstance(vocab["dateCreated"], dict)
    jsonld_valid("jsonld-schemaorg-vocab-compaction", vocab, record, ["J3", "J5"],
                 "Compacted with a schema.org @vocab and an fhr prefix instead of the FHR "
                 "context; dateCreated is a value object typed xsd:date.")
    canonical = write(record)
    context = canonical.pop("@context")
    jsonld_valid("jsonld-graph-single-node", {"@context": context, "@graph": [canonical]},
                 record, ["J4"],
                 "The FHR context with the record as the only node of @graph.")
    strings = copy.deepcopy(vocab)
    strings["schemaVersion"] = record["schema"]
    strings["fhr:relatedLink"] = record["relatedLink"][0]
    strings["dateCreated"] = record["dateCreated"]
    jsonld_valid("jsonld-iri-as-string", strings, record, ["J5"],
                 "Under the schema.org @vocab, the IRI fields schema (schema.org schemaVersion) "
                 "and relatedLink, and dateCreated, are plain strings.")

    unknown = dict(copy.deepcopy(vocab), keywords=["synthetic"])
    jsonld_invalid("jsonld-unknown-term", jsonld_bytes(unknown), "J4",
                   "http://schema.org/keywords has no FHR field (it is export metadata only).")
    remote = {"@context": "https://schema.org/", "@type": "Dataset", "name": GENOME}
    jsonld_invalid("jsonld-remote-context", jsonld_bytes(remote), "J3",
                   "The context is a remote URL that is not a bundled FHR context; nothing "
                   "may be fetched.")
    second = dict(copy.deepcopy(canonical), genome="Second synthetic genome")
    jsonld_invalid("jsonld-two-nodes",
                   jsonld_bytes({"@context": context, "@graph": [canonical, second]}), "J4",
                   "@graph holds two records.")
    two = copy.deepcopy(expanded)
    two[0][SDO_IRI + "name"].append({"@value": "Second synthetic genome"})
    jsonld_invalid("jsonld-two-genome-values", jsonld_bytes(two), "J5",
                   "Expanded form with two values for genome (schema.org name), a "
                   "single-valued field.")
    flattened = copy.deepcopy(vocab)
    flattened["about"] = {"@id": record["taxon"]["uri"]}
    jsonld_invalid("jsonld-flattened", jsonld_bytes(flattened), "J5",
                   "The taxon is given only by its @id, as in flattened form; its name is "
                   "not in the document.")
    dated = copy.deepcopy(vocab)
    dated["dateCreated"] = {"@value": record["dateCreated"] + "T00:00:00Z",
                            "@type": XSD_IRI + "dateTime"}
    jsonld_invalid("jsonld-datetime-datecreated", jsonld_bytes(dated), "J5",
                   "dateCreated is typed xsd:dateTime; only xsd:date or no type is allowed.")
    identified = copy.deepcopy(expanded)
    identified[0] = {"@id": EXPORT_CONTEXT["id"], **identified[0]}
    jsonld_invalid("jsonld-root-id", jsonld_bytes(identified), "J4",
                   "Expanded form with a root @id, which no FHR field holds.")


def path_for(entry):
    suffix = SUFFIX[entry["kind"]] + (".gz" if entry["compression"] else "")
    return f"{entry['status']}/{entry['name']}{suffix}"


def self_check():
    names = set()
    for entry in VALID + INVALID:
        assert entry["name"] not in names, entry["name"]
        names.add(entry["name"])
    required = json.loads((ROOT / "fhr.json").read_text())["required"]
    for entry in VALID + INVALID:
        if entry["kind"] == "microdata":
            text = entry["data"].decode("utf-8")
            assert text.count(ITEM_TYPE) >= 1, entry["name"]
        if entry["kind"] in {"microdata", "jsonld"} and entry["status"] == "valid":
            assert set(required) <= entry["metadata"].keys(), entry["name"]
            assert entry["metadata"]["checksum"] == MICRODATA_CHECKSUM[0], entry["name"]
    jsonld_self_check()
    for entry in VALID:
        if entry["kind"] in {"microdata", "jsonld"}:
            continue
        data = decompress(entry["data"]) if entry["compression"] else entry["data"]
        stated, computed = reference_checksum(data, entry["kind"])
        assert stated == computed == entry["checksum"], entry["name"]
    for entry in INVALID:
        if entry["kind"] in {"microdata", "jsonld"}:
            continue
        data = decompress(entry["data"]) if entry["compression"] else entry["data"]
        try:
            stated, computed = reference_checksum(data, entry["kind"])
        except (ValueError, UnicodeDecodeError):
            continue
        if entry["rule"] in {"R1", "R3", "R4"}:
            assert stated != computed, entry["name"]


def jsonld_self_check():
    """Valid JSON-LD vectors read back (rule J1) to their expected metadata."""
    import make_jsonld

    for entry in VALID:
        if entry["kind"] == "jsonld":
            document = json.loads(entry["data"])
            if not any(rule in entry["rules"] for rule in ("J3", "J4", "J5")):
                assert make_jsonld.canonical_record(document) == entry["metadata"], entry["name"]
            else:
                assert not make_jsonld.is_canonical(document), entry["name"]


def manifest():
    covered = {}
    vectors = []
    for entry in VALID + INVALID:
        item = {
            "id": entry["name"],
            "file": path_for(entry),
            "format": entry["kind"],
            "compressed": bool(entry["compression"]),
        }
        if entry["compression"]:
            item["compression"] = entry["compression"]
        if entry["status"] == "valid":
            item.update(expected="valid", rules=entry["rules"], description=entry["description"])
            if entry["kind"] in {"microdata", "jsonld"}:
                item.update(metadata=entry["metadata"])
            else:
                item.update(checksum=entry["checksum"], metadata=EXPECTED_METADATA)
            for rule in entry["rules"]:
                covered.setdefault(rule, set()).add("valid")
        else:
            item.update(expected="invalid", rule=entry["rule"], reason=entry["reason"])
            if entry.get("metadata") is not None:
                item.update(metadata=entry["metadata"])
            covered.setdefault(entry["rule"], set()).add("invalid")
        vectors.append(item)
    for rule in RULES:
        if rule not in NOT_APPLICABLE:
            assert covered.get(rule) == {"valid", "invalid"}, rule
    return {
        "manifestVersion": MANIFEST_VERSION,
        "specification": "docs/FORMAT.md",
        "microdataSpecification": "docs/MICRODATA.md",
        "jsonldSpecification": "docs/JSONLD.md",
        "checksumDefinition": "base64(SHA-512/256) over the (decompressed) file bytes except the "
                    "root-level checksum line and its terminator (FASTA and GFA only; in "
                    "microdata and JSON-LD the checksum is an ordinary metadata value)",
        "rules": {
            rule: {"summary": text, **({"notApplicable": NOT_APPLICABLE[rule]}
                                       if rule in NOT_APPLICABLE else {})}
            for rule, text in RULES.items()
        },
        "vectors": vectors,
    }


def write(output):
    build()
    self_check()
    for status in ("valid", "invalid"):
        directory = output / status
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    for entry in VALID + INVALID:
        (output / path_for(entry)).write_bytes(entry["data"])
    text = json.dumps(manifest(), indent=2, ensure_ascii=True) + "\n"
    (output / "manifest.json").write_bytes(text.encode("ascii"))
    return len(VALID), len(INVALID)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="directory to write (default: conformance/)")
    args = parser.parse_args()
    if "sha512_256" not in hashlib.algorithms_available:
        print("SHA-512/256 is unavailable in this Python build", file=sys.stderr)
        return 1
    valid_count, invalid_count = write(args.output)
    print(f"Wrote {valid_count} valid and {invalid_count} invalid vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
