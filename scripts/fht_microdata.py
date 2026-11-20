# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Shared v0.7.0 publication-candidate typed HTML reference; not toolkit support.

DOM and typed-container code derives from FHP-Specification tests/fhp_microdata.py
at bc7110fedb6f05b52b1d2348b5b14a79b91b0637. See docs/FHT-MICRODATA.md (proposed shared F1-F7 clauses).
Adapted from immutable FHT owning4ddda69/b62c4e2 source. No network or sequence checksum verification. Proposed release selectors remain gated.
"""

import hashlib
import json
import math
import re
import subprocess
import sys
import warnings
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fht_semantics import completeness_errors  # noqa: E402
FHT_ITEMTYPE = 'https://w3id.org/fair-bioheaders/fht/v0.7.0'
from check_conformance import select_schema, RAW_SCHEMA, W3ID_SCHEMA, TYPE_NAMES, schema_validator  # noqa: E402
OTHER_FAMILY_TYPES = {
    "https://raw.githubusercontent.com/FAIR-bioHeaders/"
    + repo
    + "/main/"
    + kind
    + ".json"
    for repo in ["FAIR-bioHeaders-Specification", "FHR-Specification"]
    for kind in ["fhr", "fhp", "fhgff3"]
}

# Elements whose end tag HTML implies (shared MICRODATA.md M2). The values are
# the ancestors a start tag closes, and the scope its search must not cross.
_VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_BASE_SCOPE = {
    "applet",
    "caption",
    "html",
    "marquee",
    "object",
    "table",
    "td",
    "th",
    "template",
}
_BUTTON_SCOPE = _BASE_SCOPE | {"button"}
_LIST_SCOPE = _BASE_SCOPE | {"ol", "ul"}
_TABLE_SCOPE = {"html", "table", "template"}

# Start tags that close an open p in button scope.
_P_CLOSERS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "details",
    "dialog",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "hr",
    "main",
    "menu",
    "nav",
    "ol",
    "p",
    "pre",
    "search",
    "section",
    "table",
    "ul",
    "li",
    "dt",
    "dd",
    "tr",
    "td",
    "th",
    "tbody",
    "thead",
    "tfoot",
}
_IMPLIED_BY_START = {
    "li": ({"li"}, _LIST_SCOPE),
    "dt": ({"dt", "dd"}, _BASE_SCOPE),
    "dd": ({"dt", "dd"}, _BASE_SCOPE),
    "option": ({"option"}, _BASE_SCOPE | {"select", "datalist"}),
    "optgroup": ({"option", "optgroup"}, _BASE_SCOPE | {"select"}),
    "tr": ({"tr"}, _TABLE_SCOPE),
    "td": ({"td", "th"}, _TABLE_SCOPE),
    "th": ({"td", "th"}, _TABLE_SCOPE),
    "tbody": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "thead": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "tfoot": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "colgroup": ({"colgroup"}, _TABLE_SCOPE),
}
# Elements whose defining attribute is the property value (shared MICRODATA.md M2).
_VALUE_ATTRIBUTE = {
    "meta": "content",
    "a": "href",
    "area": "href",
    "link": "href",
    "audio": "src",
    "embed": "src",
    "iframe": "src",
    "img": "src",
    "source": "src",
    "track": "src",
    "video": "src",
    "object": "data",
    "data": "value",
    "meter": "value",
    "time": "datetime",
}
_TYPED = {"string", "integer", "number", "boolean", "null"}

# Subtrees whose contents are inert in HTML: they create no item scopes or
# properties and contribute no scalar text (docs/FHT-MICRODATA.md F7).
_INERT_CONTENT = {"script", "template"}

# Visible values only (docs/FHT-MICRODATA.md, "Visible values"). The binding's
# promise is that the embedded data is the readable value, so a property a
# reader of the page cannot see is an error, not metadata.
# Elements whose contents are never rendered in the page body.
_UNRENDERED = {"head", "title", "style", "noscript", "meta", "link"}
_CONCEALING_STYLE = re.compile(
    r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)"
    r"|content-visibility\s*:\s*hidden)\s*(?:!\s*important\s*)?(?:;|$)",
    re.IGNORECASE,
)
_CSS_COMMENT = re.compile(r"/\*[\s\S]*?(?:\*/|$)")


def _style_hides_or_is_unsupported(style):
    """Check a bounded inline-style subset, not a CSS cascade or layout engine."""
    # Quotes may contain comment-looking text; escapes can spell both property
    # names and values. Refuse these forms instead of guessing their CSS tokens.
    if any(character in style for character in ("\\", "\"", "'")):
        return True
    # CSS comments separate tokens, rather than joining split identifiers. This
    # also handles an EOF-terminated comment after an otherwise complete value.
    normalized = _CSS_COMMENT.sub(" ", style)
    return "*/" in normalized or bool(_CONCEALING_STYLE.search(normalized))


# Elements whose value would come from an attribute with no visible text.
_ATTRIBUTE_ONLY = {"meta", "link", "img", "audio", "video", "source", "track",
                   "embed", "iframe", "object"}
# Elements whose value attribute must equal the text the page shows.
_SHOWN_ATTRIBUTE = {"data", "meter", "time"}
# FORMAT.md R14: the link schemes a validator accepts without a warning. An
# href is an active link in the rendered page, so other schemes are refused.
_R14_SCHEMES = {"http", "https", "ftp", "urn", "doi", "info"}
_SCHEME = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
def _supports_rcdata():
    """Probe parser behavior, including backports, rather than a version number."""
    events = []

    class Probe(HTMLParser):
        def handle_starttag(self, tag, attrs):
            events.append(("start", tag))

        def handle_endtag(self, tag):
            events.append(("end", tag))

        def handle_data(self, data):
            events.append(("data", data))

    parser = Probe(convert_charrefs=True)
    parser.feed("<title>a<b>c</b>&amp;</title>"
                "<textarea>x<i>y</i>&amp;</textarea>")
    parser.close()
    return events == [
        ("start", "title"), ("data", "a<b>c</b>&"), ("end", "title"),
        ("start", "textarea"), ("data", "x<i>y</i>&"), ("end", "textarea"),
    ]


def _conceals(tag, attrs):
    return (tag in _UNRENDERED or "hidden" in attrs
            or _style_hides_or_is_unsupported(attrs.get("style", "")))


class MicrodataError(ValueError):
    """The document is not valid FHT microdata."""


class _Node:
    __slots__ = (
        "tag",
        "attrs",
        "children",
        "itemscope",
        "itemtype",
        "itemprop",
        "datatype",
        "concealed",
    )

    def __init__(self, tag, attrs, concealed=False):
        self.tag = tag
        self.concealed = concealed or _conceals(tag, attrs)
        self.attrs = attrs
        self.children = []
        self.itemscope = "itemscope" in attrs
        self.itemtype = attrs.get("itemtype", "").split()
        self.itemprop = attrs.get("itemprop", "").split()
        self.datatype = attrs.get("data-fhr-type")


def _first_wins(attrs):
    """R9: the first of repeated attributes applies."""
    result = {}
    for name, value in attrs:
        if name not in result:
            result[name] = "" if value is None else value
    return result


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document", {})
        self.stack = [self.root]

    def _pop_through(self, targets, boundaries):
        """Close the nearest target ancestor and everything above it.

        The search skips inline descendants but stops at the scope boundary
        the HTML rule names, so an open span does not hide the p or table cell
        that the start tag has to close (shared MICRODATA.md M2).
        """
        for index in range(len(self.stack) - 1, 0, -1):
            node = self.stack[index]
            if node.tag in targets:
                del self.stack[index:]
                return True
            if node.tag in boundaries:
                return False
        return False

    def _close_implied(self, tag):
        if tag in _P_CLOSERS:
            self._pop_through({"p"}, _BUTTON_SCOPE)
        rule = _IMPLIED_BY_START.get(tag)
        if rule:
            self._pop_through(*rule)

    def handle_starttag(self, tag, attrs):
        self._close_implied(tag)
        node = _Node(tag, _first_wins(attrs), self.stack[-1].concealed)
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        # HTML ignores a self-closing slash on non-void elements.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return
            if self.stack[index].tag == "template":
                return  # Inert fragment end tags cannot close an outer scope.

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _nodes(node):
    for child in node.children:
        if isinstance(child, _Node):
            if child.tag in _INERT_CONTENT:
                continue
            yield child
            yield from _nodes(child)


def _text(node):
    parts = []
    for child in node.children:
        if isinstance(child, str):
            if child and node.concealed:
                _check_visible(node)
            parts.append(child)
        elif child.tag not in _INERT_CONTENT:
            parts.append(_text(child))
    return "".join(parts)


def _value_of(element):
    _check_visible(element)
    if element.tag in _ATTRIBUTE_ONLY:
        raise MicrodataError(
            f"<{element.tag}> property value is not visible text in the page"
        )
    attribute = _VALUE_ATTRIBUTE.get(element.tag)
    if attribute and attribute in element.attrs:
        value = element.attrs[attribute]
        if element.tag in _SHOWN_ATTRIBUTE and value != _text(element):
            raise MicrodataError(
                f"<{element.tag} {attribute}> differs from the text the page shows"
            )
        if attribute == "href":
            scheme = _SCHEME.match(value.strip())
            if not scheme or scheme.group(1).lower() not in _R14_SCHEMES:
                raise MicrodataError(
                    f"href {value!r} is an active link outside the R14 schemes "
                    "(http, https, ftp, urn, doi, info)"
                )
        return value
    return _text(element)


def _check_visible(element):
    """Visible values: no concealed property, itemref or multi-token itemprop."""
    if element.concealed:
        raise MicrodataError(
            f"property {' '.join(element.itemprop) or element.tag!r} is not "
            "visible or has unsupported inline CSS (hidden, display:none or an unrendered element)"
        )
    if "itemref" in element.attrs:
        raise MicrodataError("itemref is not supported: properties must be in the item")
    if len(element.itemprop) > 1:
        raise MicrodataError(
            "one element names several properties (itemprop "
            f"{' '.join(element.itemprop)!r}); write one property per element"
        )


def _resolve(root, subschema):
    while isinstance(subschema, dict) and "$ref" in subschema:
        reference = subschema["$ref"]
        if not reference.startswith("#/$defs/"):
            raise MicrodataError(f"unsupported $ref {reference!r}")
        subschema = root["$defs"][reference.rsplit("/", 1)[-1]]
    return subschema


def _json_type(root, subschema):
    resolved = _resolve(root, subschema)
    if "type" in resolved:
        return resolved["type"]
    branches = resolved.get("anyOf") or resolved.get("oneOf")
    if branches:
        types = {_json_type(root, branch) for branch in branches}
        if len(types) == 1:
            return types.pop()
    return None


def _subschema(root, parent, name):
    return _resolve(root, parent).get("properties", {}).get(name, {})


def _parse_typed(raw, datatype):
    if datatype == "string":
        return raw
    try:
        value = json.loads(raw)
    except ValueError as error:
        raise MicrodataError(f"{datatype} value is not JSON: {raw!r}") from error
    if datatype == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise MicrodataError(f"integer value is not an integer: {raw!r}")
    elif datatype == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MicrodataError(f"number value is not a number: {raw!r}")
    elif datatype == "boolean":
        if not isinstance(value, bool):
            raise MicrodataError(f"boolean value is not a boolean: {raw!r}")
    elif datatype == "null":
        if value is not None:
            raise MicrodataError(f"null value is not null: {raw!r}")
    else:
        raise MicrodataError(f"unknown data-fhr-type {datatype!r}")
    return value


def _convert_untyped(raw, root, subschema):
    kind = _json_type(root, subschema)
    if kind in ("integer", "number", "boolean"):
        return _parse_typed(raw, kind)
    return raw


def _property_elements(scope):
    """Yield (element, property name) for the item's own properties (M1)."""

    def walk(node):
        for child in node.children:
            if not isinstance(child, _Node):
                continue
            if child.tag in _INERT_CONTENT:
                continue  # Script and template contents never contribute metadata.
            if child.itemprop or child.itemscope:
                _check_visible(child)
            if child.datatype in ("array", "object"):
                # A typed container's children are the container's own values,
                # not properties of the enclosing item.
                if child.itemprop:
                    for name in child.itemprop:
                        yield child, name
                continue
            if child.itemprop:
                for name in child.itemprop:
                    yield child, name
                if child.itemscope:
                    continue  # A nested item; its properties are not the parent's.
                # An ordinary property element can contain further properties;
                # they still belong to the enclosing item (M1).
                yield from walk(child)
            elif child.itemscope:
                continue  # A separate item; its properties are not the parent's.
            else:
                yield from walk(child)

    yield from walk(scope)


def _item_subschema(root, subschema):
    """The schema for one occurrence of a field, using an array's items."""
    resolved = _resolve(root, subschema)
    if _json_type(root, subschema) == "array":
        return resolved.get("items", {})
    return subschema


def _read_value(element, root, subschema):
    # Recursive array items bypass _property_elements(), including attribute-
    # valued links and nested containers. Apply the same gate at every value.
    _check_visible(element)
    datatype = element.datatype
    if datatype == "array":
        items = []
        for child in element.children:
            if isinstance(child, str):
                if child.strip():
                    raise MicrodataError("array container has stray text")
                continue
            if child.tag in _INERT_CONTENT:
                continue
            if "item" not in child.itemprop:
                raise MicrodataError("array container child is not itemprop=item")
            items.append(
                _read_value(child, root, _resolve(root, subschema).get("items", {}))
            )
        return items
    # An array field may also appear as an ordinary occurrence (an untyped
    # item scope, or an explicitly typed object scope). Read it against the
    # item schema, not the array schema (M3).
    item_schema = _item_subschema(root, subschema)
    if datatype == "object":
        if not element.itemscope:
            raise MicrodataError("data-fhr-type=object without itemscope")
        return _read_scope(element, root, item_schema)
    if datatype in _TYPED:
        return _parse_typed(_value_of(element), datatype)
    if datatype is not None:
        raise MicrodataError(f"unknown data-fhr-type {datatype!r}")
    if element.itemscope:
        return _read_scope(element, root, item_schema)
    return _convert_untyped(_value_of(element), root, item_schema)


def _read_scope(scope, root, subschema):
    occurrences = {}
    for element, name in _property_elements(scope):
        value = _read_value(element, root, _subschema(root, subschema, name))
        occurrences.setdefault(name, []).append(value)
    record = {}
    for name, values in occurrences.items():
        field = _subschema(root, subschema, name)
        if _json_type(root, field) == "array":
            if len(values) == 1 and isinstance(values[0], list):
                # A single array container is unwrapped. Repeated containers
                # stay as nested lists, so schema validation rejects them
                # (docs/FHT-MICRODATA.md "Repeated properties").
                record[name] = values[0]
            else:
                # Ordinary repeated properties form one flat list (M4).
                record[name] = values
        elif len(values) == 1:
            record[name] = values[0]
        else:
            record[name] = values  # M4: a repeated property becomes a list.
    return record


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise MicrodataError("non-finite numbers are not metadata values (R13)")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def _html_text(value):
    # Check only emitted/extracted text, not values omitted under M5.
    if isinstance(value, str) and any(
        char == "\x00" or 0xD800 <= ord(char) <= 0xDFFF for char in value
    ):
        raise MicrodataError("text is not losslessly representable in HTML")
    if isinstance(value, dict):
        for key, item in value.items():
            _html_text(key)
            _html_text(item)
    elif isinstance(value, list):
        for item in value:
            _html_text(item)


def resolve_schema(selection, schema):
    """Resolve the proposed shared registry, never substitute unknown releases."""
    kind, release, name = select_schema(selection)
    if kind != 'FHT' or name != 'fht.json' or release not in ('main', 'v0.7.0'):
        raise MicrodataError(f'unsupported candidate FHT schema selection: {selection!r}')
    return schema


def _validate(record, schema):
    _finite(record)
    if record.get("schemaVersion") != "1.0":
        raise MicrodataError("unsupported FHT schemaVersion")
    errors = list(
        schema_validator(schema).iter_errors(record)
    )
    if errors:
        raise MicrodataError(
            "schema-invalid metadata: " + "; ".join(error.message for error in errors)
        )
    from reader_policy import canonical, checksum_values
    if not all(canonical(value) for _, value in checksum_values(record)):
        raise MicrodataError('R4: noncanonical standard checksum encoding')
    semantic = completeness_errors(record)
    if semantic:
        raise MicrodataError("contract-invalid metadata: " + "; ".join(semantic))


def _candidate_schema(allow_candidate, schema):
    registry = json.loads((ROOT / 'schemas/versions.json').read_text())
    current = registry.get('current')
    releases = registry.get('releases', {})
    if (releases.get('v0.7.0', {}).get('FHT') != '1.0' or
            releases.get(current, {}).get('FHT') != '1.0'):
        raise MicrodataError('This binding requires the registered FHT 1.0 contract')
    if registry.get('preRelease') not in (None, current):
        raise MicrodataError('Invalid FHT preRelease guard')
    raw = (ROOT / 'fht.json').read_bytes()
    mode = 'publication-candidate'
    if registry.get('preRelease') == 'v0.7.0':
        if not allow_candidate:
            raise MicrodataError('Unpublished binding requires allow_candidate=True; no release is claimed')
    else:
        immutable = subprocess.run(['git', '--no-replace-objects', '-C', str(ROOT), 'show', 'v0.7.0:fht.json'], capture_output=True)
        if immutable.returncode or immutable.stdout != raw:
            raise MicrodataError('Tag-reference binding requires actual byte-matching v0.7.0 tag; no fallback to candidate')
        mode = 'tag-verified-reference'
    local = json.loads(raw)
    if schema is not None and schema != local:
        raise MicrodataError('custom schema must match the shared candidate')
    Draft202012Validator.check_schema(local)
    return local, mode


def read_page(text, schema=None, *, allow_candidate=False, warn=None):
    """Extract and schema-check one draft FHT record; never verify sequence bytes."""
    if not _supports_rcdata():
        raise MicrodataError(
            "the FHT HTML reader requires RCDATA-capable html.parser behavior: "
            "<title>/<textarea> markup must stay text with references decoded"
        )
    schema, mode = _candidate_schema(allow_candidate, schema)
    builder = _TreeBuilder()
    # HTML preprocessing normalizes literal line endings before tokenization;
    # character references such as &#13; are decoded later and stay intact.
    builder.feed(text.replace("\r\n", "\n").replace("\r", "\n"))
    builder.close()
    scopes = [node for node in _nodes(builder.root) if node.itemscope]
    def family_kind(value):
        raw, w3id = RAW_SCHEMA.fullmatch(value), W3ID_SCHEMA.fullmatch(value)
        if raw:
            return TYPE_NAMES[raw.group(2)]
        if w3id:
            return TYPE_NAMES[w3id.group(1)]
        if value == 'https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json':
            return 'FHT-draft'
        return None
    family = [node for node in scopes if any(family_kind(value) for value in node.itemtype)]
    if len(family) != 1 or not any(family_kind(value) == 'FHT' for value in family[0].itemtype):
        raise MicrodataError('expected exactly one candidate FHT scope and no conflicting family scope')
    if any(family_kind(value) not in (None, 'FHT') for value in family[0].itemtype):
        raise MicrodataError('mixed family itemtype identity')
    for value in family[0].itemtype:
        if family_kind(value) == 'FHT':
            resolve_schema(value, schema)
    scope = family[0]
    _check_visible(scope)
    selectors = [
        element for element, name in _property_elements(scope) if name == "schema"
    ]
    if len(selectors) != 1:
        raise MicrodataError("FHT scope requires exactly one schema property")
    selected = resolve_schema(_value_of(selectors[0]), schema)
    record = _read_scope(scope, selected, selected)
    if any(key.startswith("x-") for key in record):
        raise MicrodataError("extension fields are not permitted in microdata (M5)")
    _validate(record, selected)
    _html_text(record)
    message = ('Unpublished FHT v0.7.0 publication-candidate reference; released=false'
               if mode == 'publication-candidate' else
               'FHT v0.7.0 tag-verified reference; exact tag bytes verified; GitHub Release and publication not verified')
    if warn is None:
        warnings.warn_explicit(message, UserWarning, __file__, 0, registry={})
    else:
        warn(message)
    return record


def _rows(record):
    return "".join(
        '<tr><th scope="row">'
        + escape(name)
        + "</th><td>"
        + _write_property(name, value)
        + "</td></tr>"
        for name, value in record.items()
    )


def _write_property(name, value):
    prop = escape(name, quote=True)
    if isinstance(value, dict):
        content = (
            "<table><caption>Object: "
            + prop
            + "</caption><tbody>"
            + _rows(value)
            + "</tbody></table>"
        )
        tag = "li" if name == "item" else "div"
        return f'<{tag} itemprop="{prop}" itemscope data-fhr-type="object">{content}</{tag}>'
    if isinstance(value, list):
        return (
            f'<ol itemprop="{prop}" data-fhr-type="array">'
            + "".join(_write_property("item", item) for item in value)
            + "</ol>"
        )
    if isinstance(value, bool):
        datatype, text = "boolean", json.dumps(value)
    elif isinstance(value, int):
        datatype, text = "integer", json.dumps(value)
    elif isinstance(value, float):
        datatype, text = "number", json.dumps(value, allow_nan=False)
    else:
        datatype, text = "string", value
    tag = "li" if name == "item" else "span"
    return f'<{tag} itemprop="{prop}" data-fhr-type="{datatype}">{escape(text).replace(chr(13), "&#13;")}</{tag}>'


def write_page(
    record, schema=None, *, allow_candidate=False, title=None, warn=None,
    _reference_example=False
):
    """Write one visible typed table; omit M5 extension fields with an explicit warning."""
    schema, mode = _candidate_schema(allow_candidate, schema)
    if title is None:
        title = 'FHT publication-candidate metadata' if mode == 'publication-candidate' else 'FHT tag-verified reference metadata'
    selected = resolve_schema(record.get("schema"), schema)
    _validate(record, selected)
    keys = [name for name in record if name.startswith("x-")]
    if keys:
        message = "microdata extension fields omitted (M5): " + ", ".join(keys)
        if warn is None:
            warnings.warn(message, stacklevel=2)
        else:
            warn(message)
    omission = (
        (
            "<p>Extension fields omitted from HTML (M5): <code>"
            + escape(", ".join(keys))
            + "</code>. Retain the original JSON/YAML record.</p>"
        )
        if keys
        else ""
    )
    emitted = {
        name: value for name, value in record.items() if not name.startswith("x-")
    }
    _html_text(emitted)
    _html_text(title)
    # Stored synthetic examples have stable presentation across publication.
    # This changes no validation/tag guard or runtime read diagnostic.
    status = ('FHT v0.7.0 synthetic reference example; publication is not established by this page.'
              if _reference_example else
              'Unreleased FHT draft binding example.' if mode == 'publication-candidate' else
              'FHT reference checked against the exact v0.7.0 tag; GitHub Release and publication have not been verified.')
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex"><title>' + escape(title) + "</title>"
        "<style>body{font-family:system-ui;max-width:75em;margin:2em auto;padding:0 1em}"
        "table{border-collapse:collapse;max-width:100%}th,td{border:1px solid;padding:.4em;"
        "text-align:left;vertical-align:top;overflow-wrap:anywhere}span,li[data-fhr-type=string]{white-space:pre-wrap}"
        "ol{margin:0;padding-left:1.5em}</style></head><body><h1>"
        + escape(title)
        + "</h1>"
        + '<p>' + status + ' Structural validation is not file, parent or biological verification.</p>'
        + omission
        + f'<table itemscope itemtype="{FHT_ITEMTYPE}"><caption>FHT metadata record</caption><tbody>'
        + _rows(emitted)
        + "</tbody></table></body></html>\n"
    )
