#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Verify the immutable FHT candidate closure; no released contract is changed."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parent
REPOSITORY = "FAIR-bioHeaders/FHT-Specification"
COMMIT = "0f6eb7763aa88d05a42fa69b02cf3f89f5cc3b00"
EXCLUDED = {"AGENTS.md"}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def verify(root=ROOT, upstream=None):
    manifest = json.loads((root / "source.json").read_text())
    if manifest["repository"] != REPOSITORY or manifest["commit"] != COMMIT:
        raise ValueError("candidate must retain its reviewed source repository and commit")
    if manifest["selection"]["trackedFiles"] != "all" or set(manifest["selection"]["excluded"]) != EXCLUDED:
        raise ValueError("candidate source selection changed")
    entries = {}
    for entry in manifest["files"]:
        source = PurePosixPath(entry["source"])
        if (source.is_absolute() or ".." in source.parts or str(source) in EXCLUDED
                or entry["local"] != "upstream/" + str(source)
                or str(source) in entries):
            raise ValueError("unsafe, excluded or duplicate candidate path")
        target = root / entry["local"]
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"missing/nonregular candidate file: {source}")
        if entry["mode"] not in ("100644", "100755") or bool(target.stat().st_mode & 0o111) != (entry["mode"] == "100755"):
            raise ValueError(f"candidate executable mode differs: {source}")
        raw = target.read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError(f"candidate byte parity failed: {source}")
        entries[str(source)] = entry
    actual = {str(p.relative_to(root / "upstream"))
              for p in (root / "upstream").rglob("*") if p.is_file()
              and "__pycache__" not in p.parts}
    if actual != set(entries):
        raise ValueError(f"candidate file inventory differs: {sorted(actual ^ set(entries))}")
    if upstream is not None:
        upstream = Path(upstream)
        if git(upstream, "rev-parse", "HEAD").decode().strip() != COMMIT:
            raise ValueError("upstream checkout HEAD is not the reviewed source commit")
        remote = git(upstream, "remote", "get-url", "origin").decode().strip()
        if remote not in (f"https://github.com/{REPOSITORY}",
                          f"https://github.com/{REPOSITORY}.git",
                          f"git@github.com:{REPOSITORY}.git"):
            raise ValueError("upstream remote is not the owning repository")
        source_tree = {}
        for line in git(upstream, "ls-tree", "-r", COMMIT).decode().splitlines():
            meta, name = line.split("\t")
            mode, kind, _ = meta.split()
            if name in EXCLUDED:
                continue
            if kind != "blob" or mode not in ("100644", "100755"):
                raise ValueError(f"unsupported owning source entry: {name}")
            source_tree[name] = mode
        if set(source_tree) != set(entries):
            raise ValueError("independently selected owning file set differs from candidate")
        for name, mode in source_tree.items():
            raw = git(upstream, "show", f"{COMMIT}:{name}")
            if entries[name]["mode"] != mode or raw != (root / entries[name]["local"]).read_bytes():
                raise ValueError(f"immutable owning blob differs: {name}")
        # Units execute this worktree, not git-show output. Check every tracked
        # file (including excluded guidance) and reject extra discoverable code.
        tracked = set(git(upstream, "ls-tree", "-r", "--name-only", COMMIT).decode().splitlines())
        actual_worktree = set()
        for folder, dirs, names in os.walk(upstream):
            if any((Path(folder) / name).is_symlink() for name in dirs):
                raise ValueError("executed owning worktree contains a symlink directory")
            dirs[:] = [name for name in dirs if not (Path(folder) == upstream and name == ".git")]
            for name in names:
                target = Path(folder) / name
                relative = str(target.relative_to(upstream))
                if ("__pycache__" in target.relative_to(upstream).parts
                        and not target.is_symlink()
                        and re.fullmatch(r".+\.cpython-\d+(?:\.opt-[12])?\.pyc", name)):
                    continue  # Inert cache only; the unit runner uses a fresh cache root.
                if relative != ".git":
                    actual_worktree.add(relative)
        if actual_worktree != tracked:
            raise ValueError(f"executed owning worktree inventory differs: {sorted(actual_worktree ^ tracked)}")
        for name in tracked:
            target = upstream / name
            if target.is_symlink() or target.read_bytes() != git(upstream, "show", f"{COMMIT}:{name}"):
                raise ValueError(f"executed owning worktree bytes differ: {name}")
    schema = json.loads((root / "upstream/fht.json").read_text())
    expected_citation = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
    for node in (schema, schema["$defs"]["FHT"]):
        if node["properties"]["schema"].get("const") != expected_citation:
            raise ValueError("candidate must retain owning draft selector, not a release form")
    vectors = json.loads((root / "upstream/conformance/manifest.json").read_text())["vectors"]
    if len(vectors) != 93 or sum(v["expected"] == "valid" for v in vectors) != 34:
        raise ValueError("candidate must retain the accepted 93-vector inventory")
    print(f"FHT candidate parity: {len(entries)} byte-exact files; 93 vectors (34 valid/59 invalid); "
          + ("immutable owning git blobs verified" if upstream else "offline digest baseline verified"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, help="independent owning checkout at the exact source commit")
    args = parser.parse_args()
    verify(upstream=args.upstream)


if __name__ == "__main__":
    main()
