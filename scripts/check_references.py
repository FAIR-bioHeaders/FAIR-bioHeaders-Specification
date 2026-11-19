#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Advisory audit of declared cross-repository references; never changes a pin.

A missing declaration/confirmed missing file is ABSENT. A failed query is
QUERY_FAILED, and an unperformed local comparison is reported separately.
"""
import argparse
import concurrent.futures
import hashlib
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CLASSES = {'released-contract', 'draft-contract', 'conformance-suite',
           'base-carrier', 'copied-tree'}
CONTROL = '__fair_bioheaders_reference_404_control_7f0817__.json'


class QueryFailed(Exception):
    pass


class Missing(Exception):
    pass


class Github:
    """Resolve tag -> commit first; read content-addressed bytes, never raw main."""
    def __init__(self):
        self._requests = {}
        self._lock = threading.Lock()

    def get(self, route, raw=False):
        key = (route, raw)
        with self._lock:
            future = self._requests.get(key)
            owner = future is None
            if owner:
                future = concurrent.futures.Future()
                self._requests[key] = future
        if owner:
            try:
                future.set_result(self._fetch(route, raw))
            except Exception as exc:
                future.set_exception(exc)
        return future.result()

    def _fetch(self, route, raw=False):
        req = urllib.request.Request('https://api.github.com/repos/' + route,
            headers={'Accept': 'application/vnd.github.raw+json' if raw else
                     'application/vnd.github+json', 'User-Agent': 'fair-bioheaders-reference-audit'})
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            req.add_header('Authorization', 'Bearer ' + token)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise Missing(route) from exc
            raise QueryFailed(f'{route}: HTTP {exc.code}') from exc
        except (OSError, urllib.error.URLError) as exc:
            raise QueryFailed(f'{route}: {exc}') from exc
        if not body:
            raise QueryFailed(f'{route}: empty response')
        if raw:
            return body
        try:
            return json.loads(body)
        except (ValueError, UnicodeError) as exc:
            raise QueryFailed(f'{route}: invalid JSON') from exc

    def revision(self, repo, ref, kind):
        # The commits endpoint dereferences annotated tags; it also accepts
        # branches, so verify tag existence separately before using it.
        if kind == 'tag':
            tag = self.get(f'{repo}/git/ref/tags/{urllib.parse.quote(ref, safe="")}')
            if not isinstance(tag, dict) or tag.get('ref') != 'refs/tags/' + ref:
                raise QueryFailed(f'{repo}@{ref}: malformed tag-ref response')
        data = self.get(f'{repo}/commits/{urllib.parse.quote(ref, safe="")}')
        sha = data.get('sha', '') if isinstance(data, dict) else ''
        if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha):
            raise QueryFailed(f'{repo}@{ref}: no full commit measurement')
        return sha

    def accessible_revision(self, repo):
        """Positive content access, independent of a possibly missing named ref."""
        try:
            metadata = self.get(repo)
            branch = metadata.get('default_branch') if isinstance(metadata, dict) else None
            if not isinstance(branch, str) or not branch:
                raise QueryFailed(f'{repo}: repository accessibility was not established')
            commit = self.revision(repo, branch, 'branch')
            # A metadata-only token may see repository metadata while lacking
            # content access. Require a successful, shaped content-tree read too.
            self.paths(repo, commit)
            return commit
        except Missing as exc:
            raise QueryFailed(f'{repo}: repository/content access is ambiguous (HTTP 404)') from exc

    def read(self, repo, commit, name):
        return self.get(f'{repo}/contents/{urllib.parse.quote(name, safe="/")}?ref={commit}', True)

    def paths(self, repo, commit):
        tree = self.get(f'{repo}/git/trees/{commit}?recursive=1')
        if not isinstance(tree, dict) or not isinstance(tree.get('tree'), list):
            raise QueryFailed(f'{repo}@{commit}: malformed authority tree response')
        if tree.get('truncated'):
            raise QueryFailed('Truncated authority tree cannot establish a complete set')
        paths = set()
        for row in tree['tree']:
            if not isinstance(row, dict) or not isinstance(row.get('path'), str) or not row['path'] or not isinstance(row.get('type'), str) or row['type'] not in {'blob', 'tree', 'commit'}:
                raise QueryFailed(f'{repo}@{commit}: malformed authority tree entry')
            if row['type'] == 'blob':
                paths.add(row['path'])
        return paths


class Checkouts:
    """Offline authority resolver; missing objects are query failures, not absence."""
    def __init__(self, mapping):
        self.mapping = mapping

    def git(self, repo, *args):
        if repo not in self.mapping:
            raise QueryFailed(f'No checkout mapped for {repo}')
        try:
            result = subprocess.run(['git', '-C', str(self.mapping[repo]), *args],
                capture_output=True, timeout=30,
                env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0',
                     'GIT_NO_REPLACE_OBJECTS': '1'})
        except subprocess.TimeoutExpired as exc:
            raise QueryFailed(f'{repo}: local git query timed out') from exc
        if result.returncode:
            raise QueryFailed(result.stderr.decode(errors='replace').strip())
        return result.stdout

    def revision(self, repo, ref, kind):
        target = 'refs/tags/' + ref if kind == 'tag' else ref
        return self.git(repo, 'rev-parse', '--verify', target + '^{commit}').decode().strip()

    def accessible_revision(self, repo):
        return self.revision(repo, 'HEAD', 'commit')

    def read(self, repo, commit, name):
        # Validate the commit independently so a missing object cannot masquerade
        # as the expected missing-path negative control.
        self.git(repo, 'cat-file', '-e', commit + '^{commit}')
        listing = self.git(repo, 'ls-tree', '-z', commit, '--', name)
        if not listing:
            raise Missing(name)
        return self.git(repo, 'show', commit + ':' + name)

    def paths(self, repo, commit):
        return set(self.git(repo, 'ls-tree', '-r', '--name-only', commit).decode().splitlines())


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def audit(row, resolver, local=None):
    result = {'id': row['id'], 'class': row['class'], 'consumer': row['consumer'],
              'verdict': 'ABSENT', 'localComparison': 'not-run', 'files': []}
    if row['class'] not in CLASSES:
        raise ValueError('Unknown reference class')
    ref, kind = row.get('revision'), row.get('revisionKind')
    files = row.get('files', [])
    if not ref or not files or any(not f.get('path') or not f.get('sha256') for f in files):
        result['reason'] = 'Incomplete recorded reference; no authoritative comparison claimed'
        return result
    if kind not in {'tag', 'commit'}:
        result.update(verdict='DRIFT', reason='Unsupported/floating revision kind')
        return result
    if row['class'] == 'draft-contract' and kind != 'commit':
        result.update(verdict='DRIFT', reason='Draft contracts require an owning full commit')
        return result
    if row['class'] == 'copied-tree':
        status = row.get('materialStatus')
        if status not in {'released', 'draft', 'historical'}:
            result.update(verdict='DRIFT', reason='Copied tree requires explicit material classification')
            return result
        if (status == 'released' and kind != 'tag') or (status == 'draft' and kind != 'commit'):
            result.update(verdict='DRIFT', reason='Released mirrors require tags; draft snapshots require full commits')
            return result
    if row['class'] in {'released-contract', 'base-carrier'} and kind != 'tag':
        result.update(verdict='DRIFT', reason='Released material must name a tag')
        return result
    if kind == 'commit' and not re.fullmatch('[0-9a-f]{40}', ref):
        result.update(verdict='DRIFT', reason='A commit reference must be a full immutable commit')
        return result
    recorded_commit = row.get('commit', ref if kind == 'commit' else None)
    if recorded_commit is None or recorded_commit == '':
        result['reason'] = 'Incomplete recorded reference: dereferenced commit is absent'
        return result
    if not isinstance(recorded_commit, str) or not re.fullmatch('[0-9a-f]{40}', recorded_commit):
        result.update(verdict='DRIFT', reason='Recorded commit must be a full immutable commit')
        return result
    exclusions = row.get('sourceExclusions', [])
    if (not isinstance(exclusions, list) or any(not isinstance(p, str) or not p for p in exclusions)
            or len(set(exclusions)) != len(exclusions)
            or (exclusions and not row.get('sourcePatterns'))):
        result.update(verdict='DRIFT', reason='Source exclusions require unique exact paths and a declared source scope')
        return result
    if len({f.get('local') or f['path'] for f in files}) != len(files):
        result.update(verdict='DRIFT', reason='Duplicate paths in declared reference set')
        return result
    try:
        commit = resolver.revision(row['repository'], ref, kind)
        result['resolvedCommit'] = commit
        try:
            resolver.read(row['repository'], commit, CONTROL)
        except Missing:
            result['negativeControl'] = 'confirmed-missing'
        else:
            raise QueryFailed('Negative control unexpectedly returned bytes')
        if recorded_commit != commit:
            result.update(verdict='DRIFT', reason='Tag/recorded commit disagree')
            return result
        result['verdict'] = 'FRESH'
        absent_authority = set()
        for f in files:
            item = {'path': f['path'], 'local': f.get('local')}
            try:
                data = resolver.read(row['repository'], commit, f['path'])
            except Missing:
                item['verdict'] = 'ABSENT'
                absent_authority.add(f['path'])
            else:
                if not data:
                    raise QueryFailed(f'{f["path"]}: empty authority measurement')
                item['authoritySha256'] = sha256(data)
                expected = f.get('upstreamSha256', f['sha256'])
                item['verdict'] = 'FRESH' if item['authoritySha256'] == expected else 'DRIFT'
                if local is not None and f.get('local'):
                    dest = (local / f['local']).resolve()
                    if not dest.is_relative_to(local.resolve()):
                        raise ValueError('Local path escapes consumer checkout')
                    if not dest.is_file():
                        item['verdict'] = 'ABSENT'
                    else:
                        item['localSha256'] = sha256(dest.read_bytes())
                        if item['localSha256'] != f['sha256']:
                            item['verdict'] = 'DRIFT'
                    result['localComparison'] = 'performed'
            result['files'].append(item)
        verdicts = {i['verdict'] for i in result['files']}
        result['verdict'] = 'DRIFT' if 'DRIFT' in verdicts else 'ABSENT' if 'ABSENT' in verdicts else 'FRESH'
        result['declaredPaths'] = len(files)
        if row.get('sourcePatterns'):
            source = {p for p in resolver.paths(row['repository'], commit)
                      if any(fnmatch.fnmatchcase(p, pattern) for pattern in row['sourcePatterns'])}
            unused_exclusions = set(exclusions) - source
            if exclusions:
                result['excludedAuthorityPaths'] = sorted(source & set(exclusions))
                result['unusedSourceExclusions'] = sorted(unused_exclusions)
                source -= set(exclusions)
            recorded = {f['path'] for f in files}
            result['onlyAuthority'] = sorted(source - recorded)
            result['onlyRecord'] = sorted(recorded - source)
            result['sourceSetComparison'] = 'performed'
            if (source - recorded or (recorded - source) - absent_authority or unused_exclusions):
                result['verdict'] = 'DRIFT'
            elif recorded - source and result['verdict'] != 'DRIFT':
                result['verdict'] = 'ABSENT'
        else:
            result['sourceSetComparison'] = 'not-run: selected file references; no complete source scope declared'
        if row.get('localTree') and local is not None:
            present = {p.relative_to(local).as_posix() for p in (local / row['localTree']).rglob('*') if p.is_file()}
            recorded = {f['local'] for f in files if f.get('local')}
            exclusions = set(row.get('localExclusions', []))
            result['onlyLocal'] = sorted(present - recorded - exclusions)
            result['missingLocal'] = sorted(recorded - present)
            if result['onlyLocal']:
                result['verdict'] = 'DRIFT'
            elif result['missingLocal'] and result['verdict'] != 'DRIFT':
                result['verdict'] = 'ABSENT'
    except Missing as exc:
        # A revision-stage HTTP 404 can conceal an inaccessible private repo.
        # Establish independent positive content access and a negative control
        # at a known existing revision before calling the named ref absent.
        try:
            witness = resolver.accessible_revision(row['repository'])
            try:
                resolver.read(row['repository'], witness, CONTROL)
            except Missing:
                result.update(verdict='ABSENT', reason=f'Confirmed missing authority: {exc}',
                              accessibilityCommit=witness,
                              negativeControl='confirmed-missing-at-accessible-revision')
            else:
                raise QueryFailed('Accessibility negative control unexpectedly returned bytes')
        except (QueryFailed, Missing, AttributeError) as error:
            result.update(verdict='QUERY_FAILED', reason=f'Cannot establish authority accessibility: {error}')
    except QueryFailed as exc:
        result.update(verdict='QUERY_FAILED', reason=str(exc))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=ROOT / 'references/inventory.json')
    parser.add_argument('--consumer', help='Exact owner/repository to select')
    parser.add_argument('--consumer-root', type=Path, help='Checkout of the selected consumer; compare its bytes too')
    parser.add_argument('--checkout', action='append', default=[], metavar='OWNER/REPO=PATH', help='Offline authority mapping (repeatable); no network when provided')
    parser.add_argument('--exit-on-findings', action='store_true')
    args = parser.parse_args(argv)
    if args.consumer_root and not args.consumer:
        parser.error('--consumer-root requires --consumer')
    table = json.loads(args.inventory.read_text())
    rows = [r for r in table['references'] if not args.consumer or r['consumer'] == args.consumer]
    if not rows:
        parser.error('No declared references selected')
    resolver = Checkouts(dict(x.split('=', 1) for x in args.checkout)) if args.checkout else Github()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda r: audit(r, resolver, args.consumer_root), rows))
    report = {'inventoryVersion': table['inventoryVersion'], 'advisory': True, 'wrote': [],
              'references': results, 'coverageGaps': table.get('coverageGaps', [])}
    print(json.dumps(report, indent=2))
    return int(args.exit_on_findings and any(r['verdict'] != 'FRESH' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
