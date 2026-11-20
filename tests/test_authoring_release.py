"""Authoring pins must name the exact independently tagged generator inputs."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import make_cedar


class AuthoringAuthorityTests(unittest.TestCase):
    def test_tag_authority_positive_and_refusal_controls(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            def git(*args):
                return subprocess.run(['git', '-C', work, *args], check=True, capture_output=True)
            git('init', '-q')
            schema = root / 'fhr.json'
            schema.write_text('{"type":"object"}\n')
            git('add', 'fhr.json')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.org',
                'commit', '-qm', 'Independent temporary authority')
            git('tag', 'v1.0.0')
            registry = {'current':'v1.0.1', 'preRelease':'v1.0.1',
                        'authoringRelease':'v1.0.0', 'files':{'FHR':'fhr.json'},
                        'w3id':{'FHR':'fhr'},
                        'releases':{'v1.0.0':{'FHR':'2.1'}, 'v1.0.1':{'FHR':'2.1'}}}
            record = root / 'versions.json'
            def write(): record.write_text(json.dumps(registry))
            write()
            with patch.object(make_cedar, 'ROOT', root), patch.object(make_cedar, 'VERSIONS_PATH', record), patch.object(make_cedar, 'TYPES', {'FHR':'fhr'}):
                self.assertEqual(make_cedar.load_registry()['fhr']['release'], 'v1.0.0')
                schema.write_text('{"type":"string"}\n')
                with self.assertRaisesRegex(ValueError, 'bytes differ'):
                    make_cedar.load_registry()
                schema.write_text('{"type":"object"}\n')
                registry['authoringRelease'] = 'v1.0.1'; write()
                with self.assertRaisesRegex(ValueError, 'unpublished candidate'):
                    make_cedar.load_registry()
                registry['preRelease'] = None; write()
                with self.assertRaisesRegex(ValueError, 'existing complete release tag'):
                    make_cedar.load_registry()
                registry['authoringRelease'] = 'v9.9.9'; write()
                with self.assertRaisesRegex(ValueError, 'Unregistered'):
                    make_cedar.load_registry()
