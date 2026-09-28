# Selection and Shared patterns

## SPEC_065

A base or Case Selection for Pluck or an Always source requires at least one candidate across `must` and `may`. A candidate may be a direct string pattern, a structured `match` entry, or a Shared reference. `description` is optional; when present, it must be a non-empty string.

level: MUST

## SPEC_066

Each item in `must` or `may` is a direct pattern string, a `{ match = "..." }` inline table, or a one-element Shared-reference array.

```text
"foo"                         direct pattern
{ match = 'src/.*\.py' }    structured match
["foo"]                       Shared reference
```

level: MUST

## SPEC_067

A direct string in `ignore` is a name pattern. A `{ match = "..." }` inline table is a structured path match. A one-element nested array is a reference marker: if its string begins with `./`, it is a Selection-relative path reference; otherwise it is a `shared.ignore` Shared reference.

```text
"*.pyc"                         direct name pattern
{ match = 'build/' }            structured match
["python-noise"]               Shared ignore reference
["./tests/fixtures/big.bin"]   file path reference
["./tests/fixtures/"]          directory path reference
```

level: MUST

## SPEC_068

A nested array must contain exactly one non-empty string. `[]`, `["foo", "bar"]`, and `[123]` are errors. In `must` and `may`, nested arrays are reserved for Shared references.

level: MUST

## SPEC_069

The Shared-reference namespace is determined uniquely by the containing field:

```text
must   -> shared.must
may    -> shared.may
ignore -> shared.ignore
```

level: MUST

## SPEC_070

A Shared pattern definition value is a non-empty array of direct string patterns or `{ match = "..." }` inline tables. Shared references and path references cannot be nested inside Shared pattern definitions.

level: MUST

## SPEC_071

Shared references are resolved against the effective Shared namespace after base composition. An unknown Shared reference is a Configuration error. Shared references are expanded in Selection-array order into their referenced pattern sets. A path reference does not use the Shared namespace; it is interpreted from that Selection's source root.

level: MUST

related: [SPEC_034](composition.md#spec_034)

## SPEC_072

Duplicate identical pattern, structured-match, or reference declarations within expanded `must`, `may`, or `ignore`, and identical include entries across `must` and `may`, are Configuration errors. By contrast, semantic overlap where different Selection entries ultimately select the same filesystem entry is valid; the final Selection includes the same file only once. Semantic overlap where different ignore conditions match the same filesystem entry is also valid; the effective exclusion is the union of all ignore conditions.

level: MUST

## SPEC_073

`allow_empty` is a boolean with default `false`. `allow_empty = true` may be specified only for a Selection that has no `must` patterns after Shared-reference expansion.

level: MUST

condition: when `allow_empty = true` is specified

## SECTION_601

title: Include pattern grammar (`must` / `may`)

### SPEC_074

A direct or expanded pattern in `must` or `may` is a `/`-separated relative path from the source directory. Absolute paths, escaping through `.` or `..`, and backslashes are rejected.

level: MUST

### SPEC_075

Each path element may contain at most one `*`. `*` matches zero or more characters within one concrete name and never crosses a path separator, so the path hierarchy depth written in the Configuration remains fixed.

```text
src/
README.md
dist/package-*.whl
packages/*/dist/
```

level: MUST

### SPEC_076

A `must` pattern must match one or more **non-ignored selectable entries** or the Selection fails. A `may` pattern may match zero candidates. If a pattern matches several candidates, only those remaining after `ignore` become Selection candidates.

level: MUST

condition: when evaluating a `must` / `may` pattern

### SPEC_077

A direct `must` / `may` string pattern declares the expected type with the **final component's trailing `/` only**. No trailing `/` requires a regular file; a trailing `/` requires a regular directory. Dirpluck does not infer this meaning from the current filesystem. Intermediate components are traversal points and are therefore directories by construction. A matching directory leaf recursively collects regular files below it subject to `ignore`. A type mismatch is not a selectable match. When there is no selectable match of the requested type but the same string pattern matches a non-ignored regular entry of the opposite type, `must` remains an unsatisfied-must error in a normal build and includes a trailing-`/` adjustment hint; during preview planning it remains missing and the same hint is recorded as a non-fatal diagnostic. `may` remains optional missing and records the same type hint as a non-fatal diagnostic. Each diagnostic includes the affected source label. The CLI prints it as a warning to stderr, while the Python API returns it in `RunResult.warnings`. These diagnostics do not change `must` / `may` Selection semantics. `ignore` takes precedence over entry-type diagnostics: ignored entries are not selectable matches, link-only or special-entry-only matches, or skipped-link counts. A recognized **non-ignored** symbolic link or Windows directory junction is not selectable. If a pattern matches only such non-ignored link-like entries, `must` reports a reasoned error distinct from ordinary absence, while `may` treats the result as optional missing.

level: MUST

condition: when evaluating an include pattern

### SPEC_078

A **non-ignored** filesystem entry that is neither a regular file nor a regular directory, such as a FIFO, socket, or device, is also not selectable and is not included in the Archive. If `may` matches only such entries, they are treated as optional missing. If `must` matches only such entries, it raises an explanatory error stating that only unsupported special filesystem entries matched. Special entries encountered while recursively collecting a regular directory are silently excluded rather than traversed or archived. No implicit ignore is inferred from contents or filename meaning.

level: MUST NOT

condition: when an include pattern matches a special filesystem entry

### SPEC_079

Matching is case-sensitive independently of the OS. `**`, `?`, character classes (`[]`), and `!` are unsupported. Multiple matches are not ranked by version, mtime, or other metadata.

level: MUST

## SECTION_602

title: Ignore grammar

### SPEC_080

Selection `ignore` has three forms: name patterns, concrete Selection-relative path references, and structured `match` entries.

level: MUST

### SPEC_081

A direct string matches one entity name case-sensitively. A pattern without a trailing `/` applies to matching file and directory names, while a pattern ending in `/` narrows the exclusion to directory names only. Supported forms are:

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

level: MUST

### SPEC_082

To narrow a name pattern to directories only, append `/` to that body. The same body without the trailing `/` applies to both files and directories:

```text
.git/
__pycache__/
tmp-*/
```

level: MUST

### SPEC_083

A Selection-relative path reference is a one-element nested array whose string begins with `./`. For Pluck, the Selection root is the Target directory. For an Always source, it is the resolved Always-source directory. Without a trailing `/`, the concrete path excludes either a file or a directory at that path. Appending `/` narrows the exclusion to a directory only.

```text
["./tests/fixtures/big.bin"]   exact entry path (file or directory)
["./tests/fixtures/"]          exact directory path and its subtree
```

level: MUST

### SPEC_084

A path reference must stay inside the Selection root. Bare `./`, `..` components, absolute paths, globs, and backslashes are rejected; `/` is the separator. If the matched entry is a directory, its subtree is pruned before traversal whether or not the spelling had a trailing `/`. A spelling without a trailing `/` may also match a regular file at the same path, while a spelling with a trailing `/` does not match a regular file.

level: MUST

### SPEC_085

Name patterns, expanded Shared ignores, path references, and structured `match` entries are applied as a union of exclusion conditions. Several different conditions may match the same entry without error, and evaluation order is not observable semantics. Implementations may prune a subtree as soon as a directory exclusion matches.

level: MUST

### SPEC_086

`ignore` takes precedence over link-like and special-entry diagnostics. Ignored entries are not Selection candidates, do not cause link-only or special-entry-only errors, and are not included in the skipped-link count. Entries inside an ignored subtree are not enumerated or subjected to traversal-time validation. A name pattern without a trailing `/` applies to matching file and directory names and also to a special filesystem entry with the same name. If a path reference matches a link-like entry itself, that entry is likewise treated as ignored.

level: MUST

### SPEC_087

For name patterns, a bare `*`, `*/`, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, `!`, backslash, and a path separator inside the body are rejected. Path references have no wildcard syntax.

level: MUST NOT

## SECTION_603

title: Structured path match (`{ match = "..." }`)

### SPEC_159

`must`, `may`, `ignore`, and Shared pattern sets accept `{ match = STRING }` inline tables as direct Selection entries. The inline table may contain no key other than `match`, and `match` must be a non-empty string.

level: MUST

### SPEC_160

The `match` value is compiled as a Python-compatible regular expression and must be no longer than 512 characters. An invalid regular expression is a Configuration error. Matching uses full-match semantics equivalent to `re.fullmatch()`.

level: MUST

### SPEC_161

A structured `match` is evaluated against the complete root-relative POSIX-style path of descendant regular files and regular directories below the Selection root; the Selection root itself is not a candidate. `/` is the path separator on every OS. A regular file path has no trailing `/`, while a regular directory path is normalized with a trailing `/`, such as `src/` or `src/pkg/`.

level: MUST

### SPEC_162

A structured `match` in `must` must match at least one selectable entry after `ignore` or the Selection fails. A structured `match` in `may` may match zero entries. If one structured match selects several entries, all matching entries become Selection candidates. A matching regular file selects that file; a matching regular directory behaves like an ordinary selected directory leaf and recursively collects regular files below it subject to `ignore`.

level: MUST

### SPEC_163

If ordinary string patterns, Shared expansion, or structured matches ultimately select the same regular file more than once, the final Selection is deduplicated by root-relative path and includes that file only once as an Archive candidate. Satisfaction of each `must` entry is evaluated independently before this deduplication.

level: MUST

### SPEC_164

A structured `match` in `ignore` has the same precedence as other ignore conditions. Matching a regular file path excludes that file. Matching a regular directory path prunes that directory and its subtree before traversal. A descendant whose ancestor directory path matches a structured ignore is part of that excluded subtree.

level: MUST

### SPEC_165

Structured `match` does not change the existing filesystem-safety boundary. Ignored entries are excluded before type diagnostics. Non-ignored symbolic links, Windows junctions, FIFOs, sockets, devices, and other unsupported entries are not selectable; if a `must` structured match matches only such entries, the existing link-only or special-entry-only diagnostic semantics apply.

level: MUST

### SPEC_166

An implementation may scan entries below the Selection root and test their candidate paths against a structured `match`; it is not required to infer a guided traversal plan equivalent to ordinary string patterns from the regular expression. A structured match may therefore traverse a broader portion of the filesystem tree than an ordinary string pattern.

level: MUST

