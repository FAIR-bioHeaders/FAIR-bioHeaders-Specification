# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Load and generate community profile schemas layered on a header type.

A *profile* is a small LinkML schema that imports a published type model
(``fhr_linkml.yml`` first, issue #51) and adds community requirements: a slot
made required, a value constraint, or a naming rule. A profile never edits the
published ``fhr.json``/``fhp.json``/``fhgff3.json`` or the type models; it is a
separate schema that a consumer applies *on top of* the unchanged base
contract. See ``docs/PROFILES.md`` and ``profiles/README.md``.

LinkML resolves an ``imports:`` entry to ``<name>.yaml``, while the published
type models are named ``.yml``. Rather than rename or copy a published file,
this loader reads the imported models into memory and supplies them through a
``SchemaView`` importmap. The profile files stay declarative and the published
bytes are untouched.

The module is usable without the network: it reads only files in this checkout.
"""

import argparse
import json
from pathlib import Path
import sys

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "profiles" / "registry.yaml"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
# The same post-processing json-schema-generator.py applies to the published
# schemas, so a profile's inherited constraints match the base contract.
EXACT_LENGTHS = {"checksum": 44, "seqcol_id": 32}


class UnsupportedProfileError(LookupError):
    """The requested profile is not in the registry of this checkout."""


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_registry(path=REGISTRY_PATH):
    """Return the profile registry, keyed by profile id.

    A profile is a *proposal* until the named community and the maintainers
    review it; the registry records that state and is not a claim of adoption.
    """
    document = load_yaml(path)
    profiles = document.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"{path}: expected a non-empty 'profiles' mapping")
    return profiles


def resolve_profile(name, registry=None):
    """Return the LinkML model path for a profile id.

    A path-like ``name`` is used directly, so tests and reviews can load a
    profile that is not registered yet. An unknown id raises
    :class:`UnsupportedProfileError` instead of silently passing.
    """
    candidate = Path(name)
    if candidate.suffix in {".yaml", ".yml"} and candidate.is_file():
        return candidate
    registry = load_registry() if registry is None else registry
    entry = registry.get(name)
    if entry is None:
        raise UnsupportedProfileError(
            f"profile {name!r} is not in {REGISTRY_PATH.name}; "
            f"known profiles: {', '.join(sorted(registry))}"
        )
    return REGISTRY_PATH.parent / entry["model"]


def _resolve_import(name, importer_dir):
    """Locate an imported model without the ``.yaml`` suffix LinkML assumes."""
    if name.startswith("linkml:"):
        return None
    for base in (importer_dir, ROOT):
        stem = base / name
        for suffix in ("", ".yaml", ".yml"):
            candidate = Path(str(stem) + suffix)
            if candidate.is_file():
                return candidate
    return None


def _import_map(profile_path):
    """Load every local model reachable from a profile as an in-memory schema."""
    importmap = {}
    todo = [(name, profile_path.parent) for name in load_yaml(profile_path)["imports"]]
    while todo:
        name, importer_dir = todo.pop()
        if name in importmap:
            continue
        resolved = _resolve_import(name, importer_dir)
        if resolved is None:
            continue
        schema = load_yaml(resolved)
        importmap[name] = schema
        for child in schema.get("imports", []):
            todo.append((child, resolved.parent))
    return importmap


def load_schema_view(profile):
    """Merge a profile and its imported base models into one schema view."""
    profile_path = resolve_profile(profile) if not isinstance(profile, Path) else profile
    return SchemaView(
        str(profile_path), importmap=_import_map(profile_path), merge_imports=True
    )


def root_class(profile_path):
    """The profile's own ``tree_root`` class (the class the profile constrains)."""
    roots = [
        name
        for name, definition in (load_yaml(profile_path).get("classes") or {}).items()
        if (definition or {}).get("tree_root")
    ]
    if len(roots) != 1:
        raise ValueError(
            f"{profile_path}: a profile must define exactly one tree_root class, "
            f"found {roots or 'none'}"
        )
    return roots[0]


def generate_profile(profile, registry=None):
    """Generate the JSON Schema for a profile, layered on its type's model.

    ``profile`` is a registry id (``agbiodata-fhr``) or a path to a profile
    model. The output is a JSON Schema draft 2020-12 document whose root is the
    profile class; it validates the base contract *and* the community additions.
    """
    path = resolve_profile(profile, registry)
    view = load_schema_view(path)
    generated = json.loads(
        JsonSchemaGenerator(
            view.schema,
            include_null=False,
            not_closed=False,
            top_class=root_class(path),
        ).serialize()
    )
    # Match the published schemas: schemaVersion is an enum so later versions
    # can be listed, and LinkML cannot express the exact digest lengths.
    for node in (generated, *generated.get("$defs", {}).values()):
        properties = node.get("properties", {})
        version = properties.get("schemaVersion", {})
        if "const" in version:
            version["enum"] = [version.pop("const")]
        for name, length in EXACT_LENGTHS.items():
            if name in properties:
                properties[name].update(minLength=length, maxLength=length)
        # LinkML emits a scalar type beside the heterogeneous union; the
        # published fhr.json keeps only the union (json-schema-generator.py).
        if "assemblySoftware" in properties:
            properties["assemblySoftware"].pop("type", None)
    generated["$schema"] = DIALECT
    for key in ("metamodel_version", "version"):
        generated.pop(key, None)
    return generated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("profile", nargs="?", help="profile id or path to a profile model")
    parser.add_argument("--output", type=Path,
                        help="output file (default: <profile>.schema.json)")
    parser.add_argument("--list", action="store_true",
                        help="list registered profiles and exit")
    args = parser.parse_args(argv)
    if args.list:
        for name, entry in sorted(load_registry().items()):
            print(f"{name}\t{entry['header_type']}\t{entry['status']}\t{entry['community']}")
        return 0
    if args.profile is None:
        parser.error("a profile id or path is required (or use --list)")
    try:
        schema = generate_profile(args.profile)
    except UnsupportedProfileError as error:
        print(f"profile_schema: {error}", file=sys.stderr)
        return 2
    output = args.output or Path(f"{Path(args.profile).stem}.schema.json")
    output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
