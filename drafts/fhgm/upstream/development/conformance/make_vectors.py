# SPDX-License-Identifier: MPL-2.0
"""Generate the draft FHGM conformance vectors deterministically.

Companion generator to ``development/examples/model/make_fixtures.py``: it reuses
that pilot's render helpers. Most vectors use the synthetic assembly and
placeholder model IDs. The noncoding scope control instead uses the committed
verbatim RefSeq subset, whose exact source and selection are recorded in
DECISIONS-2026-11-19.md. All vectors are byte-reproducible.

Two rules govern what this file may emit.

* A vector's expected outcome is derived from contract clauses and reviewed
  independently; checker observations are evidence to compare against that
  expectation. ``run_conformance.py --seal`` records only mechanical byte
  digests/checksums and never generates expected outcomes.
* Nothing here gives semantics to split, merge, assembly migration,
  transcript-only contribution or companion-file identity. Those are #204 open
  question Q6, left to curators; the manifest records them as open scope with no
  vectors. A rejection that looks like one of them (the transcript-target vector)
  is labelled as a statement about v0.1's scope only.

Usage: ``python3 make_vectors.py <existing-directory>`` writes
``vectors/valid/`` and ``vectors/invalid/`` under that directory. The runner
regenerates into a temporary directory and compares bytes.
"""

import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "examples" / "revision"))
from check_revision import (  # noqa: E402
    MODELS,
    checksum,
    feature_payload,
    render,
    synthetic_reference,
)

# The ambiguous snapshot whose modelId collides is the committed v0.1 fixture, so
# the vector that points at it reads that file's own checksum line rather than a
# transcribed digest.
FIXTURES = HERE.parents[0] / "examples" / "model"
AMBIGUOUS_SNAPSHOT = FIXTURES / "ambiguous-model-id.fhgff3.gff3"

DATE = "2026-11-14"
AUTHOR = "FHGM conformance vector generator (synthetic)"
REFERENCE = synthetic_reference()
# A synthetic FHR parent binding: the digest is computed over declared synthetic
# bytes, so it is reproducible and is not presented as the checksum of any real
# file.
FHR_PARENT_CHECKSUM = checksum(b"synthetic FHGM conformance FHR parent bytes\n")


def metadata(models, file_version, genome_link=True, **extra):
    header = {
        "schema": "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0",
        "schemaVersion": "1.1",
        "annotation": "Synthetic annotation for the draft FHGM conformance vectors",
        "taxon": {"name": "Synthetic example"},
        "metadataAuthor": [{"name": AUTHOR}],
        "dateCreated": DATE,
        "genomeReference": REFERENCE,
        "version": file_version,
        MODELS: models,
    }
    header.update(extra)
    if not genome_link:
        del header["genomeReference"]
    return header


def fhr_parent_link():
    return {
        "derivedFrom": [
            {
                "headerType": "FHR",
                "checksum": FHR_PARENT_CHECKSUM,
                "relationship": "annotates",
            }
        ]
    }


def record(model_id, model_version, feature="toy-a", **extra):
    model = {
        "modelId": model_id,
        "modelVersion": model_version,
        "featureId": feature,
        "reference": {"genomeReference": REFERENCE},
    }
    model.update(extra)
    return model


def pointer(annotation_checksum, model_id, model_version):
    return {
        "annotationChecksum": annotation_checksum,
        "modelId": model_id,
        "modelVersion": model_version,
    }


def header_checksum(data):
    for line in data.splitlines():
        if line.startswith(b"#~checksum: "):
            return line[len(b"#~checksum: "):].decode()
    raise AssertionError("vector input has no checksum line")


def valid_vectors():
    """Vectors the released base schema and the model-level checker accept."""
    # Real RefSeq antisense gene; only authored metadata is synthetic.
    # Use the actual assembly reference already established by the dmel fixture.
    import yaml
    dmel = (HERE.parent / "examples/dmel4/Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3").read_bytes()
    real_ref = yaml.safe_load(b"\n".join(line[2:] for line in dmel.splitlines()
                                        if line.startswith(b"#~")))["genomeReference"]
    nc = metadata([record("nc-model-a", "A", feature="gene-Dmel_CR45124",
                   reference={"genomeReference": real_ref})], "1", genomeReference=real_ref,
                  annotation="RefSeq antisense gene slice for draft FHGM scope review",
                  taxon={"name": "Drosophila melanogaster"})
    a = render(metadata([record("model-a", "A")], "A"), feature_payload(30))
    b = render(metadata([record("model-a", "B", predecessor=pointer(header_checksum(a), "model-a", "A"))], "B"), feature_payload(31))
    return {
        "noncoding-root-gene": render(nc, (HERE / "noncoding-source.gff3").read_bytes()),
        "opaque-version-a-initial": a,
        "opaque-version-b-successor": b,
        "opaque-version-a-reused": render(metadata([record("model-a", "A",
            predecessor=pointer(header_checksum(b), "model-a", "B"))], "A-again"), feature_payload(32)),
        "competing-model-ids-same-target": render(
            metadata([record("model-a", "A"), record("model-b", "B")], "1"),
            feature_payload(30)),
        "changed-file-local-feature-id": render(
            metadata([record("model-a", "B", feature="renamed-a",
                predecessor=pointer(header_checksum((FIXTURES / "valid-single.fhgff3.gff3").read_bytes()),
                                    "model-a", "1"))], "2"),
            feature_payload(30).replace(b"toy-a", b"renamed-a")),
        # Edge trimming is not a ban on internal whitespace (K2).
        "record-model-id-interior-nbsp": render(
            metadata([record("model-\u00a0a", "1")], "1"), feature_payload(30)),
        # Disposition Q2: file-local identity is the default and needs no minting
        # authority, and a producer-supplied external identifier may occupy the
        # same opaque field. The urn:example: namespace is reserved for
        # documentation, so this claims no registry.
        "supplied-external-model-id": render(
            metadata([record("urn:example:gene-model-7", "deposit-v1")], "1"),
            feature_payload(30),
        ),
        # Rule K5 with the file carrying both released FHGFF3 genome-link forms:
        # one record binds the FHR parent checksum, the other the accession plus
        # supplied SeqCol digest, and each shares a comparable form.
        "both-reference-forms": render(
            metadata(
                [
                    record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM}),
                    record("model-b", "1", feature="toy-b"),
                ],
                "1",
                **fhr_parent_link(),
            ),
            feature_payload(30),
        ),
        # The other FHGFF3 genome-link branch at file scope, with a record bound
        # the same way: no v0.1 fixture used a derivedFrom-only link.
        "file-linked-by-fhr-parent": render(
            metadata(
                [record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM})],
                "1",
                genome_link=False,
                **fhr_parent_link(),
            ),
            feature_payload(30),
        ),
        # Rule K4 compares the percent-decoded feature ID with the record.
        "percent-decoded-feature-target": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy%2Da\n"),
        ),
        # Rule K1, base selection by citation: the v0.6.0 release accepts a
        # record stating schemaVersion 1.1 (shared docs/SCHEMA-VERSIONS.md), so
        # the checker selects the v0.6.0 bytes the URL cites and the overlay's
        # v0.6.0 branch admits 1.1.
        "v0.6.0-citation-stating-1.1": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"),
            feature_payload(30),
        ),
        # Rule K2, positive control for the link host check: user information
        # before a real host, a port, and a bracketed IPv6 host are all
        # accepted in every link field (evidence uri, software uri, protocol).
        "record-links-user-info-before-host": render(
            metadata([record("model-a", "1",
                             evidence=[{"description": "Synthetic evidence statement",
                                        "uri": "https://reader@example.org/evidence"}],
                             methods={
                                 "software": [{"name": "Synthetic curation tool",
                                               "uri": "https://[2001:db8::1]:8443/tool"}],
                                 "protocol": "ftp://anonymous@ftp.example.org/protocol.txt",
                             })], "1"),
            feature_payload(30),
        ),
        # Rule K1: the raw tag URL under the FHR-Specification alias is the
        # same v0.6.0 release (both repository names are recognised). Its 1.2
        # twin keeps this citation, so the alias is exercised under both
        # stated versions.
        "fhr-specification-alias-v0.6.0": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://raw.githubusercontent.com/FAIR-bioHeaders/"
                        "FHR-Specification/v0.6.0/fhgff3.json"),
            feature_payload(30),
        ),
    }


def invalid_vectors():
    """Vectors the model-level checker rejects (or the base schema, where noted)."""
    ambiguous_checksum = header_checksum(AMBIGUOUS_SNAPSHOT.read_bytes())
    valid = valid_vectors()
    both_forms_checksum = header_checksum(valid["both-reference-forms"])
    single_checksum = header_checksum((FIXTURES / "valid-single.fhgff3.gff3").read_bytes())
    external_checksum = header_checksum(valid["supplied-external-model-id"])
    vectors = {
        "feature-inventory-complete-empty": render(
            metadata([record("model-a", "1")], "1"), b""),
        "feature-inventory-no-identifiers": render(
            metadata([record("model-a", "1")], "1"),
            b"toy\tpilot\tgene\t10\t30\t.\t+\t.\t.\n"),
        "feature-target-bare-parent": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy-a;Parent\n")),
        "feature-target-empty-parent": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy-a;Parent=\n")),
        "feature-target-other-so-type": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"\tgene\t", b"\tSO:0001263\t", 1)),
        # Rule K6, assembly-link half: the successor file is linked only by an
        # FHR parent while the supplied predecessor (valid-single) is linked by
        # accession plus SeqCol digest, so the two files share no comparable
        # assembly form. The record reference still matches the prior
        # record's, so only the file-level assembly comparison can refuse it.
        "pointer-assembly-link-differs": render(
            metadata(
                [record("model-a", "2",
                        reference={"genomeReference": REFERENCE,
                                   "annotates": FHR_PARENT_CHECKSUM},
                        predecessor=pointer(single_checksum, "model-a", "1"))],
                "2",
                genome_link=False,
                **fhr_parent_link(),
            ),
            feature_payload(35),
        ),
        # Rule K6, record-reference half: both files carry both genome-link
        # forms, so the assembly links match, but the predecessor record
        # (both-reference-forms, model-a) is bound by the FHR parent checksum
        # and this successor record by accession plus SeqCol digest only.
        "pointer-record-reference-differs": render(
            metadata(
                [record("model-a", "2",
                        predecessor=pointer(both_forms_checksum, "model-a", "1"))],
                "2",
                **fhr_parent_link(),
            ),
            feature_payload(35),
        ),
        # Rule K6: the supplied snapshot exists and passes every snapshot
        # check, but holds no record with this modelId.
        "pointer-snapshot-lacks-model": render(
            metadata(
                [record("model-a", "2",
                        predecessor=pointer(external_checksum, "model-a", "1"))],
                "2",
            ),
            feature_payload(35),
        ),
        # Rule K2: format uri is enforced, not only the scheme. The value has an
        # accepted https scheme and host, and a space no URI may contain.
        "record-evidence-uri-not-a-uri": render(
            metadata([record("model-a", "1", evidence=[{
                "description": "Synthetic evidence statement",
                "uri": "https://example.org/synthetic evidence"}])], "1"),
            feature_payload(30),
        ),
        # Rule K2: link fields accept only the schemes FORMAT.md R14 accepts;
        # javascript: is a well-formed URI that a renderer must never link.
        "record-evidence-uri-javascript-scheme": render(
            metadata([record("model-a", "1", evidence=[{
                "description": "Synthetic evidence statement",
                "uri": "javascript:void(0)"}])], "1"),
            feature_payload(30),
        ),
        # Rule K2: an http, https or ftp link needs a host. User information
        # followed directly by the path leaves the host empty
        # (urlsplit("https://user@/").hostname is None), so each link field
        # rejects it even though format uri accepts the value.
        "record-evidence-uri-user-info-without-host": render(
            metadata([record("model-a", "1", evidence=[{
                "description": "Synthetic evidence statement",
                "uri": "https://user@/"}])], "1"),
            feature_payload(30),
        ),
        "record-software-uri-empty-user-info-and-host": render(
            metadata([record("model-a", "1", methods={"software": [{
                "name": "Synthetic curation tool",
                "uri": "https://@/"}]})], "1"),
            feature_payload(30),
        ),
        "record-methods-protocol-ftp-user-info-without-host": render(
            metadata([record("model-a", "1", methods={
                "protocol": "ftp://user@/"})], "1"),
            feature_payload(30),
        ),
        # Rule K2: opaque text values carry no leading or trailing whitespace,
        # so "model-a " cannot pass for a different identifier than "model-a".
        "record-model-id-trailing-space": render(
            metadata([record("model-a ", "1")], "1"),
            feature_payload(30),
        ),
        # Rule K3 under Unicode normalisation: the two IDs are the NFC and NFD
        # spellings of one string, which print identically.
        "model-ids-equal-under-nfc": render(
            metadata(
                [record("model-caf\u00e9", "1"),
                 record("model-cafe\u0301", "1", feature="toy-b")],
                "1",
            ),
            feature_payload(30),
        ),
        # Rule K3 is checked before any per-record rule (deviation D4): the
        # second record sharing model-a also contradicts the file genome link,
        # and the snapshot is still reported as ambiguous, not as a K5 failure.
        "duplicate-model-id-reported-before-record-checks": render(
            metadata(
                [record("model-a", "1"),
                 record("model-a", "1", feature="toy-b", reference={"genomeReference": dict(
                     REFERENCE, accession="SYNTHETIC_OTHER_ASSEMBLY.1")})],
                "1",
            ),
            feature_payload(30),
        ),
        # Rule K4, the negative percent-decoding control: only decoded IDs are
        # compared, so a record naming the raw spelling toy%2Da does not
        # resolve to the row written ID=toy%2Da (whose ID is toy-a).
        "feature-id-names-percent-encoding": render(
            metadata([record("model-a", "1", feature="toy%2Da")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy%2Da\n"),
        ),
        # Rule K4's type half on a root row: toy-a is written as a root mRNA
        # (no Parent), so only the gene-type requirement can refuse it. A v0.1
        # scope statement, like feature-target-transcript-row: #204 Q6 leaves
        # transcript-only contribution open.
        "feature-target-root-transcript-row": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"\tgene\t10\t30\t", b"\tmRNA\t10\t30\t"),
        ),
        # Rule K4: the target must be a root gene row. Here the gene row toy-a
        # names the toy-b transcript as its Parent.
        "feature-target-gene-with-parent": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy-a;Parent=toy-b-rna\n"),
        ),
        # Rule K2: nested objects are closed. The base schema ignores record
        # contents, so only the record contract can reject this (FORMAT.md R15
        # grants top-level x- keys only, never keys inside a record).
        "record-unknown-key": render(
            metadata([record("model-a", "1", unexpected="synthetic")], "1"),
            feature_payload(30),
        ),
        # Rule K2: modelVersion is an opaque non-empty string, not a number.
        "record-numeric-model-version": render(
            metadata([dict(record("model-a", "1"), modelVersion=2)], "1"),
            feature_payload(30),
        ),
        # Rule K1: the transport array must hold at least one record.
        "empty-model-array": render(metadata([], "1"), feature_payload(30)),
        # Rule K1: FORMAT.md R15 grants extension keys from FHGFF3 1.1 only. This
        # is the one vector the released base schema itself rejects.
        "transport-1-0-extension": render(
            dict(
                metadata([record("model-a", "1")], "1"),
                schema="https://w3id.org/fair-bioheaders/fhgff3/v0.4.0",
                schemaVersion="1.0",
            ),
            feature_payload(30),
        ),
        # Rule K5, the stronger half: nothing contradicts, and the record is still
        # rejected for sharing no comparable form with the file genome link. This
        # is the behaviour the adoption packet's D1 summary under-describes.
        "reference-forms-not-comparable": render(
            metadata([record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM})], "1"),
            feature_payload(30),
        ),
        # Rule K3 reached through the pointer side: the supplied prior snapshot is
        # itself ambiguous, so loading it rejects the run before any verdict for
        # this record's pointer is reported (deviation D4 at snapshot level).
        "pointer-into-ambiguous-history": render(
            metadata(
                [record("model-a", "2", predecessor=pointer(ambiguous_checksum, "model-a", "1"))],
                "2",
            ),
            feature_payload(35),
        ),
        # Rule K4: the target resolves to no local row.
        "feature-target-absent": render(
            metadata([record("model-a", "1", feature="toy-missing")], "1"),
            feature_payload(30),
        ),
        # Rule K4: a transcript row is not a gene row. This is a statement about
        # v0.1 scope only; #204 Q6 leaves transcript-only contribution open.
        "feature-target-transcript-row": render(
            metadata([record("model-a", "1", feature="toy-a-rna")], "1"),
            feature_payload(30),
        ),
        # Rule K4: exactly one row, not two rows sharing the ID.
        "feature-target-duplicate-rows": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30) + b"toy\tpilot\tgene\t1\t5\t.\t+\t.\tID=toy-a\n",
        ),
        # The R15 floor under a registered citation: the v0.5.0 URL stating
        # schemaVersion 1.0. The checker selects the v0.5.0 bytes the URL cites,
        # and those bytes reject the extension key. transport-1-0-extension
        # cites v0.4.0, which no registered base answers to, so it is refused
        # at selection instead; this vector keeps the floor itself observed.
        "transport-1-0-under-v0.5.0-citation": render(
            dict(metadata([record("model-a", "1")], "1"), schemaVersion="1.0"),
            feature_payload(30),
        ),
        # Rule K1, base selection by citation: raw main is a moving contract
        # link, not a release, so no registered base answers to it and the
        # checker refuses rather than evaluating the carrier against bytes it
        # never cited. The released base schema's URL pattern accepts it.
        "carrier-cites-raw-main": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://raw.githubusercontent.com/FAIR-bioHeaders/"
                        "FAIR-bioHeaders-Specification/main/fhgff3.json"),
            feature_payload(30),
        ),
        # Integrity, not a model rule: one byte added after the header makes the
        # file-bound checksum stop covering the file, so the checker refuses
        # before any model verdict. Recorded with checksum outcome "stale", and
        # the one vector this suite does not claim as gap-proof.
        "tampered-record-bytes":
            (FIXTURES / "valid-single.fhgff3.gff3").read_bytes()
            + b"# byte added after the header\n",
    }
    # K2 is already normative: edge whitespace and the explicitly forbidden
    # invisible ranges are rejected. The expected outcomes are derived in
    # TEXT-COVERAGE-2026-11-19.md, not inferred from this checker.
    for vector_id, value in text_rejection_cases().items():
        vectors[vector_id] = render(
            metadata([record(value, "1")], "1"), feature_payload(30))
    for count in (1, 2):
        records = [record("model-a", "1") for _ in range(count)]
        for model in records:
            del model["modelId"]
        vector_id = ("record-model-id-absent" if count == 1
                     else "two-records-model-id-absent")
        vectors[vector_id] = render(metadata(records, "1"), feature_payload(30))
    return vectors


def text_rejection_cases():
    """One case per named whitespace class and invisible-range boundary."""
    return {
        "record-model-id-trailing-nbsp": "model-a\u00a0",
        "record-model-id-leading-line-separator": "\u2028model-a",
        "record-model-id-leading-paragraph-separator": "\u2029model-a",
        "record-model-id-trailing-en-quad": "model-a\u2000",
        "record-model-id-trailing-hair-space": "model-a\u200a",
        "record-model-id-trailing-medium-mathematical-space": "model-a\u205f",
        "record-model-id-trailing-ideographic-space": "model-a\u3000",
        "record-model-id-leading-ogham-space": "\u1680model-a",
        "record-model-id-trailing-narrow-nbsp": "model-a\u202f",
        "record-model-id-zero-width-space": "model-\u200ba",
        "record-model-id-right-to-left-mark": "model-\u200fa",
        "record-model-id-left-to-right-embedding": "model-\u202aa",
        "record-model-id-right-to-left-override": "model-\u202ea",
        "record-model-id-word-joiner": "model-\u2060a",
        "record-model-id-invisible-plus": "model-\u2064a",
        "record-model-id-byte-order-mark": "model-\ufeffa",
    }


def run(output):
    written = 0
    for kind, vectors in (("valid", valid_vectors()), ("invalid", invalid_vectors())):
        target = output / "vectors" / kind
        target.mkdir(parents=True, exist_ok=True)
        for name, data in sorted(vectors.items()):
            path = target / f"{name}.fhgff3.gff3"
            path.write_bytes(data)
            print(f"vectors/{kind}/{name}.fhgff3.gff3  {checksum(path.read_bytes())}")
            written += 1
    if written != len(valid_vectors()) + len(invalid_vectors()):
        raise AssertionError("vector count changed under construction")
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Existing directory for the vectors")
    args = parser.parse_args()
    run(args.output)
