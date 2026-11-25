"""CI regression for the NPP projection fixtures (#249, round NPP-2 on #292).

Asserts the full green state: the source fixture validates against this
repository's own fhr.json, the fixture file's checksum recomputes exactly
(FORMAT.md R2-R4), the three outputs are byte-deterministic rebuilds, the XML
parses with entity resolution left off (stdlib ElementTree default), and every
negative fixture fails with exactly its expected codes. A missing SHA-512/256
implementation is reported as a failure, never a silent pass.
"""
import unittest

from scripts import npp_projection


class NppProjectionFixtures(unittest.TestCase):
    def test_fixtures_are_consistent(self):
        errors = npp_projection.check()
        self.assertEqual(errors, [], "fixture harness reported: " + "; ".join(errors))


if __name__ == "__main__":
    unittest.main()
