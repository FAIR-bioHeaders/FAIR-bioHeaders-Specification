# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The GitHub Pages site for the JSON-LD files (scripts/build_pages.py)."""

from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_pages  # noqa: E402


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.hrefs.append(attrs["href"])


def parse(path):
    parser = Ids()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class BuildPagesTests(unittest.TestCase):
    def build(self, tags=(), files=None):
        site = Path(self.enterContext(tempfile.TemporaryDirectory())) / "site"
        with mock.patch.object(build_pages, "release_tags", return_value=list(tags)), \
                mock.patch.object(build_pages, "tag_file",
                                  side_effect=lambda tag, name: (files or {}).get((tag, name))):
            versions = build_pages.build(site)
        return site, versions

    def synthetic_root(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "repo"
        (root / "docs").mkdir(parents=True)
        shutil.copyfile(ROOT / "docs/TERMS.md", root / "docs/TERMS.md")
        shutil.copytree(ROOT / "jsonld", root / "jsonld")
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "docs", "jsonld"], check=True)
        return root.resolve()

    def test_checkout_and_ancestor_outputs_are_refused_before_deletion(self):
        root = self.synthetic_root()
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            for target in (root, root / ".", root.parent):
                with self.subTest(target=target):
                    with self.assertRaisesRegex(ValueError, "this checkout or its ancestor"):
                        build_pages.build(target)
                    remove.assert_not_called()
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_case_aliases_of_metadata_and_indexed_source_are_refused(self):
        root = self.synthetic_root()
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            for target, reason in [(root / ".GIT", "Git metadata"),
                                   (root / "DOCS", "tracked source")]:
                with self.subTest(target=target), self.assertRaisesRegex(ValueError, reason):
                    build_pages.build(target)
                remove.assert_not_called()
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_physical_root_alias_protects_tracked_source(self):
        root = self.synthetic_root()
        alias = root.with_name("REPO")
        original = Path.samefile
        def samefile(first, second):
            if first == alias and second == root:
                return True
            return original(first, second)
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(Path, "samefile", samefile), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            with self.assertRaisesRegex(ValueError, "tracked source"):
                build_pages.build(alias / "docs")
            remove.assert_not_called()
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_real_case_insensitive_root_and_ancestor_aliases(self):
        root = self.synthetic_root()
        alias = root.with_name("REPO")
        if not alias.exists() or not alias.samefile(root):
            self.skipTest("filesystem is case-sensitive; physical alias logic tested separately")
        ancestor_alias = root.parent.with_name(root.parent.name.swapcase())
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            for target in (alias, ancestor_alias):
                with self.subTest(target=target), self.assertRaisesRegex(ValueError, "this checkout or its ancestor"):
                    build_pages.build(target)
                remove.assert_not_called()
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_unicode_and_case_alias_of_tracked_source_is_refused(self):
        root = self.synthetic_root()
        folder = root / "données"
        folder.mkdir()
        (folder / "keep").write_text("tracked")
        subprocess.run(["git", "-C", str(root), "add", "données/keep"], check=True)
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            with self.assertRaisesRegex(ValueError, "tracked source"):
                build_pages.build(root / "DONNE\u0301ES")
            remove.assert_not_called()
        self.assertEqual((folder / "keep").read_text(), "tracked")

    def test_unknown_filesystem_identity_is_refused_before_deletion(self):
        root = self.synthetic_root()
        output = root / "scratch"
        output.mkdir()
        (output / "keep").write_text("user work")
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(Path, "samefile", side_effect=PermissionError("unreadable identity")), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            with self.assertRaisesRegex(ValueError, "cannot establish output filesystem identity"):
                build_pages.build(output)
            remove.assert_not_called()
        self.assertEqual((output / "keep").read_text(), "user work")

    def test_untracked_literal_glob_filename_does_not_match_indexed_source(self):
        root = self.synthetic_root()
        output = root / "[docs]"
        output.mkdir()
        (output / "old-output").write_text("disposable")
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages, "release_tags", return_value=[]):
            build_pages.build(output)
        self.assertTrue((output / "terms/index.html").is_file())
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_other_git_worktree_is_not_deleted(self):
        target = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (target / ".git").write_text("gitdir: /some/worktree/metadata\n")
        sentinel = target / "keep.txt"
        sentinel.write_text("user work")
        with self.assertRaisesRegex(ValueError, "another repository or worktree"):
            build_pages.build(target)
        self.assertEqual(sentinel.read_text(), "user work")

    def test_tracked_source_directory_is_refused_before_deletion(self):
        root = self.synthetic_root()
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            with self.assertRaisesRegex(ValueError, "tracked source"):
                build_pages.build(root / "docs")
            remove.assert_not_called()
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_unknown_tracking_state_is_refused_before_deletion(self):
        root = self.synthetic_root()
        output = root / "scratch"
        output.mkdir()
        (output / "keep").write_text("user work")
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages.subprocess, "run", side_effect=OSError("git unavailable")), \
                mock.patch.object(build_pages.shutil, "rmtree") as remove:
            with self.assertRaisesRegex(ValueError, "cannot establish"):
                build_pages.build(output)
            remove.assert_not_called()
        self.assertEqual((output / "keep").read_text(), "user work")

    def test_untracked_scratch_inside_checkout_can_be_replaced(self):
        root = self.synthetic_root()
        output = root / "scratch"
        output.mkdir()
        (output / "old-output").write_text("disposable")
        with mock.patch.object(build_pages, "ROOT", root), \
                mock.patch.object(build_pages, "release_tags", return_value=[]):
            build_pages.build(output)
        self.assertFalse((output / "old-output").exists())
        self.assertTrue((output / "terms/index.html").is_file())
        self.assertTrue((root / "docs/TERMS.md").is_file())

    def test_git_metadata_output_is_not_deleted(self):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        metadata = folder / ".git" / "objects"
        metadata.mkdir(parents=True)
        sentinel = metadata / "keep"
        sentinel.write_text("git object")
        with self.assertRaisesRegex(ValueError, "Git metadata"):
            build_pages.build(metadata)
        self.assertEqual(sentinel.read_text(), "git object")

    def test_symlink_output_does_not_delete_its_target(self):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        target = folder / "user-work"
        target.mkdir()
        (target / "keep.txt").write_text("keep")
        output = folder / "site-link"
        output.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_pages.build(output)
        self.assertEqual((target / "keep.txt").read_text(), "keep")

    def test_site_layout(self):
        site, versions = self.build()
        self.assertEqual(versions, ["main"])
        for path in ("index.html", ".nojekyll", "terms/index.html", "terms/terms.ttl",
                     "terms/terms.jsonld", "fhr/main/jsonld/fhr.context.jsonld",
                     "fhr/main/jsonld/terms.ttl", "fhr/main/jsonld/terms.jsonld"):
            self.assertTrue((site / path).is_file(), path)
        self.assertEqual((site / "terms/terms.ttl").read_bytes(),
                         (ROOT / "jsonld/terms.ttl").read_bytes())

    def test_every_term_has_an_anchor(self):
        site, _ = self.build()
        terms = re.findall(r"^### (.+)$", (ROOT / "docs/TERMS.md").read_text(), flags=re.M)
        page = parse(site / "terms/index.html")
        self.assertTrue(terms)
        for name in terms:
            self.assertEqual(page.ids.count(name), 1, name)
        self.assertEqual(len(page.ids), len(set(page.ids)))
        for href in page.hrefs:
            self.assertTrue(href.startswith(("https://", "#")), href)
            self.assertNotIn("..", href)

    def test_release_copies_skip_tags_without_jsonld(self):
        files = {("v0.4.0", "fhr.context.jsonld"): b"{}\n", ("v0.4.0", "terms.ttl"): b"# t\n"}
        site, versions = self.build(["v0.3.1", "v0.4.0"], files)
        self.assertEqual(versions, ["v0.4.0", "main"])
        self.assertFalse((site / "fhr/v0.3.1").exists())
        self.assertEqual((site / "fhr/v0.4.0/jsonld/fhr.context.jsonld").read_bytes(), b"{}\n")
        self.assertFalse((site / "fhr/v0.4.0/jsonld/terms.jsonld").exists())
        self.assertIn("fhr/v0.4.0/jsonld/fhr.context.jsonld",
                      parse(site / "index.html").hrefs)

    def test_unsupported_markdown_is_an_error(self):
        for text in ("| a | b |\n", "```\ncode\n```\n", "#### deep\n", "- item\nloose\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                build_pages.render_markdown(text, "docs/TERMS.md")

    def test_markdown_escaping_and_links(self):
        out = build_pages.render_markdown(
            "### a<b\n\nSee [x](../jsonld/terms.ttl) and `<c>`.\n", "docs/TERMS.md")
        self.assertIn('<h3 id="a&lt;b">a&lt;b</h3>', out)
        self.assertIn(build_pages.BLOB + "jsonld/terms.ttl", out)
        self.assertIn("<code>&lt;c&gt;</code>", out)


if __name__ == "__main__":
    unittest.main()
