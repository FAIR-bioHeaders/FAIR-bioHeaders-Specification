# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Installed-toolkit CEDAR binding evidence, separate from live workbench upload.

Set CEDAR_TOOLKIT to an installed bioheaders executable of the release pinned
in conformance/toolkit-pin.json (the pin the CI workflow installs). Optional CEDAR_FHGM_ROOT
selects the owning repository's checker; absent means that test is explicitly
not run, never a model-conformance pass. No source contract or pin is rewritten.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from test_cedar import (
    ROOT, TYPES, FHT_FIXTURE, FHGM_FIXTURE_MINIMAL, contract_path, contract_schema,
    load_example, load_template, make_cedar, wrap_export,
)


# One pin shared with the workflow's install step: the toolkit version and the
# SHA-256 of the FHT draft that release bundles.
TOOLKIT_PIN = json.loads((ROOT / "conformance" / "toolkit-pin.json").read_text(encoding="utf-8"))


class CedarInstalledToolkitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        selected = os.environ.get("CEDAR_TOOLKIT")
        if not selected:
            raise unittest.SkipTest("not run: set CEDAR_TOOLKIT to installed bioheaders "
                                    + TOOLKIT_PIN["version"])
        cls.cli = Path(selected).resolve()
        cls.python = cls.cli.with_name("python")
        cls.env = {k: v for k, v in os.environ.items()
                   if k not in {"PYTHONPATH", "BIOHEADERS_EXPERIMENTAL_FHT"}}
        cls.scratch = tempfile.TemporaryDirectory(prefix="cedar-installed-")
        cls.directory = Path(cls.scratch.name)
        result = cls.invoke([str(cls.python), "-c", (
            "import importlib.metadata,json,bioheaders; "
            "from importlib.resources import files; import hashlib; "
            "print(json.dumps({'version':importlib.metadata.version('fair-bioheaders'),"
            "'module':bioheaders.__file__,'fhtSha256':hashlib.sha256("
            "files('bioheaders').joinpath('schemas/fht-draft.json').read_bytes()).hexdigest()}))"
        )])
        cls.installed = json.loads(result.stdout)
        if cls.installed["version"] != TOOLKIT_PIN["version"]:
            raise AssertionError(f"requires the pinned published toolkit "
                                 f"{TOOLKIT_PIN['version']}, got {cls.installed}")
        if "site-packages" not in Path(cls.installed["module"]).parts:
            raise AssertionError(f"installed artifact required, got {cls.installed}")

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    @classmethod
    def invoke(cls, command, expected=0, draft=False):
        env = dict(cls.env)
        if draft:
            env["BIOHEADERS_EXPERIMENTAL_FHT"] = "1"
        result = subprocess.run(command, capture_output=True, text=True,
                                cwd=cls.directory, env=env)
        if result.returncode != expected:
            raise AssertionError(f"{command}: exit {result.returncode}, expected {expected}: "
                                 f"{result.stdout}\n{result.stderr}")
        return result

    def same_typed_values(self, actual, expected):
        self.assertIs(type(actual), type(expected))
        if isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected))
            for key in expected:
                self.same_typed_values(actual[key], expected[key])
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected))
            for left, right in zip(actual, expected):
                self.same_typed_values(left, right)
        else:
            self.assertEqual(actual, expected)

    def flattened(self, stem, record):
        artifact = wrap_export(record, load_template(stem), root=True)
        flat = make_cedar.flatten_export(artifact)
        expected = copy.deepcopy(record)
        if expected.get("checksum", object()) is None:
            expected.pop("checksum")
        self.same_typed_values(flat, expected)
        return flat

    def bind(self, stem, metadata, payload, suffix, draft=False):
        source = self.directory / (stem + ".json")
        sequence = self.directory / (stem + suffix)
        bound = self.directory / (stem + ".bound" + suffix)
        converted = self.directory / (stem + ".readback.json")
        stripped = self.directory / (stem + ".stripped" + suffix)
        source.write_text(json.dumps(metadata), encoding="utf-8")
        sequence.write_bytes(payload)
        first = self.invoke([str(self.cli), "combine", str(source), str(sequence), "-o", str(bound)], draft=draft)
        self.invoke([str(self.cli), "validate", str(bound)], draft=draft)
        self.invoke([str(self.cli), "verify", str(bound)], draft=draft)
        self.invoke([str(self.cli), "convert", str(bound), str(converted)], draft=draft)
        self.invoke([str(self.cli), "strip", str(bound), str(stripped)], draft=draft)
        result = json.loads(converted.read_bytes())
        self.assertIn("checksum", result)
        result.pop("checksum")
        self.same_typed_values(result, metadata)
        self.assertEqual(stripped.read_bytes(), payload)
        second = self.directory / (stem + ".again" + suffix)
        self.invoke([str(self.cli), "combine", str(source), str(sequence), "-o", str(second)], draft=draft)
        self.assertEqual(second.read_bytes(), bound.read_bytes())
        return bound, first

    def test_released_exports_bind_and_read_back_without_value_or_type_loss(self):
        for stem, (_, example, fmt) in TYPES.items():
            with self.subTest(stem=stem):
                record = load_example(example, fmt)
                record["checksum"] = None
                flat = self.flattened(stem, record)
                # flatten_export deliberately omits empty root checksums.
                flat.pop("checksum", None)
                payload = b"##gff-version 3\nctg\tfixture\tgene\t1\t4\t.\t+\t.\tID=gene-fixture\n" if stem == "fhgff3" else b">synthetic\nACGT\n"
                self.bind(stem, flat, payload, ".gff3" if stem == "fhgff3" else ".fa")

    def test_fht_is_default_off_then_binds_in_the_v7_lane(self):
        record = copy.deepcopy(FHT_FIXTURE)
        record.pop("checksum")
        flat = self.flattened("fht", record)
        source = self.directory / "fht-default.json"
        sequence = self.directory / "fht-default.fa"
        source.write_text(json.dumps(flat), encoding="utf-8")
        sequence.write_bytes(b">synthetic\nACGT\n")
        refused = self.directory / "fht-default.bound.fa"
        self.invoke([str(self.cli), "combine", str(source), str(sequence), "-o", str(refused)], expected=1)
        self.assertFalse(refused.exists())
        _, result = self.bind("fht", flat, sequence.read_bytes(), ".fa", draft=True)
        self.assertIn("draft", result.stderr.lower())
        self.assertEqual(type(flat["vitalStats"]["averageTranscriptLength"]), float)
        self.assertEqual(type(flat["vitalStats"]["N50"]), int)
        self.assertEqual(flat["derivedFrom"], record["derivedFrom"])

    def test_fht_draft_pin_and_dotted_lineage_follow_the_bundled_bytes(self):
        # The installed bundle must be the one the pin records; whether it can
        # bind a dotted lineage then follows from whether those bytes are the
        # CEDAR snapshot's (which accepts it) or an older draft (which does not).
        self.assertEqual(self.installed["fhtSha256"], TOOLKIT_PIN["fhtDraftSha256"])
        snapshot = hashlib.sha256(contract_path("fht").read_bytes()).hexdigest()
        record = copy.deepcopy(FHT_FIXTURE)
        record["completeness"]["lineageDataset"] = "diptera_odb10.1"
        Draft202012Validator(contract_schema("fht"), format_checker=FormatChecker()).validate(record)
        source = self.directory / "fht-dotted.json"
        source.write_text(json.dumps(record), encoding="utf-8")
        if TOOLKIT_PIN["fhtDraftSha256"] == snapshot:
            self.invoke([str(self.cli), "validate", str(source)], expected=0, draft=True)
        else:
            rejected = self.invoke([str(self.cli), "validate", str(source)], expected=1, draft=True)
            self.assertIn("lineageDataset", rejected.stderr)

    def carriers(self):
        model = self.flattened("fhgm", copy.deepcopy(FHGM_FIXTURE_MINIMAL))
        Draft202012Validator(contract_schema("fhgm"), format_checker=FormatChecker()).validate(model)
        record = load_example(TYPES["fhgff3"][1], "yaml")
        record.pop("checksum")
        record.pop("derivedFrom")
        record["genomeReference"] = copy.deepcopy(model["reference"]["genomeReference"])
        record["x-fhgm-models"] = [model]
        payload = b"##gff-version 3\nctg\tfixture\tgene\t1\t100\t.\t+\t.\tID=gene-EXAMPLE-1\n"
        for version, tag in (("1.1", "v0.5.0"), ("1.2", "v0.6.0")):
            record["schema"] = f"https://w3id.org/fair-bioheaders/fhgff3/{tag}"
            record["schemaVersion"] = version
            bound, _ = self.bind("fhgm-carrier-" + version, record, payload, ".gff3")
            yield version, bound

    def test_fhgm_records_travel_in_both_released_carriers(self):
        self.assertEqual(len(list(self.carriers())), 2)
        # This proves base validation, checksum and preservation, not model resolution.

    def test_owning_fhgm_checker_resolves_each_declared_base(self):
        selected = os.environ.get("CEDAR_FHGM_ROOT")
        if not selected:
            self.skipTest("not run: owning FHGM model resolution requires CEDAR_FHGM_ROOT; carrier success is not model conformance")
        owner = Path(selected).resolve()
        model_dir = owner / "development/model"
        self.assertEqual((model_dir / "fhgm-model.schema.json").read_bytes(), (ROOT / "templates/cedar/drafts/fhgm-model.schema.json").read_bytes())
        registry = json.loads((model_dir / "base-schemas.json").read_bytes())
        candidates = []
        for base in registry["bases"]:
            raw = subprocess.check_output(["git", "show", base["ref"] + ":" + base["path"]], cwd=ROOT)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), base["sha256"])
            candidate = self.directory / (base["ref"] + ".json")
            candidate.write_bytes(raw)
            candidates += ["--base-schema", str(candidate)]
        checker = model_dir / "validate_fhgm.py"
        for version, bound in self.carriers():
            result = self.invoke([str(self.python), str(checker), *candidates, str(bound)])
            tag = "v0.5.0" if version == "1.1" else "v0.6.0"
            self.assertIn(f"carrier declares schemaVersion '{version}'", result.stdout)
            self.assertIn(f"FAIR-bioHeaders/FAIR-bioHeaders-Specification@{tag} fhgff3.json", result.stdout)
            self.assertIn("exact match on the declared schemaVersion", result.stdout)
            self.assertIn("Passed FHGFF3 header, checksum and draft FHGM checks", result.stdout)
        # Base validation/checksum can succeed while model target resolution fails.
        invalid = json.loads((self.directory / "fhgm-carrier-1.2.readback.json").read_bytes())
        invalid.pop("checksum")
        invalid["x-fhgm-models"][0]["featureId"] = "missing-gene"
        payload = b"##gff-version 3\nctg\tfixture\tgene\t1\t100\t.\t+\t.\tID=gene-EXAMPLE-1\n"
        bound, _ = self.bind("fhgm-wrong-target", invalid, payload, ".gff3")
        result = self.invoke([str(self.python), str(checker), *candidates, str(bound)], expected=1)
        self.assertIn("missing-gene", result.stderr)
        # The absence of full feature/biology, reference sequence and curator
        # assessment is deliberate; this CEDAR workflow does not perform them.


if __name__ == "__main__":
    unittest.main()
