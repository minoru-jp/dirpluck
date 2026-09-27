# Selection and Shared patterns

## SPEC_065

A base or Case Selection for Pluck or an Always source requires at least one candidate across `must` and `may`. A candidate may be a direct pattern or a Shared reference. `description` is optional; when present, it must be a non-empty string.

level: MUST

## SPEC_066

Each item in `must` or `may` is either a direct pattern string or a one-element Shared-reference array.

```text
"foo"       direct pattern
["foo"]     Shared reference
```

level: MUST

## SPEC_067

A direct string in `ignore` is a name pattern. A one-element nested array is a reference marker: if its string begins with `./`, it is a Selection-relative path reference; otherwise it is a `shared.ignore` Shared reference.

```text
"*.pyc"                         direct name pattern
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

A Shared pattern definition value is a non-empty array of direct patterns. Shared references and path references cannot be nested inside Shared pattern definitions.

level: MUST

## SPEC_071

Shared references are resolved against the effective Shared namespace after base composition. An unknown Shared reference is a Configuration error. Shared references are expanded in Selection-array order into their referenced pattern sets. A path reference does not use the Shared namespace; it is interpreted from that Selection's source root.

level: MUST

related: [SPEC_034](composition.md#spec_034)

## SPEC_072

Duplicate identical pattern/reference declarations within expanded `must`, `may`, or `ignore`, and duplicate include patterns across `must` and `may`, are Configuration errors. By contrast, semantic overlap where different ignore conditions match the same filesystem entry is valid; the effective exclusion is the union of all ignore conditions.

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
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

level: MUST

### SPEC_076

A `must` pattern must match one or more **non-ignored selectable entries** or the Selection fails. A `may` pattern may match zero candidates. If a pattern matches several candidates, only those remaining after `ignore` become Selection candidates.

level: MUST

condition: when evaluating a `must` / `may` pattern

### SPEC_077

If the final matched entity is a regular file, that file is selected. If it is a regular directory, regular files below it are collected recursively subject to `ignore`. `ignore` takes precedence over diagnostics based on filesystem-entry type: ignored entries do not count as selectable matches, link-only or special-entry-only matches, or skipped-link entries. Recognized **non-ignored** symbolic links or Windows directory junctions are not selectable. If a pattern matches only such non-ignored link-like entries, `must` raises an explanatory error that distinguishes this case from an ordinary missing match, while `may` records it as optional missing.

level: MUST

condition: when an include pattern matches a link-like entry

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

Selection `ignore` has two forms: name patterns and concrete Selection-relative path references.

level: MUST

### SPEC_081

A direct string matches one entity name case-sensitively. A pattern ending in `/` applies to a directory name; a pattern without `/` applies to a file name. Supported forms are:

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

level: MUST

### SPEC_082

A directory name pattern appends `/` to that body:

```text
.git/
__pycache__/
tmp-*/
```

level: MUST

### SPEC_083

A Selection-relative path reference is a one-element nested array whose string begins with `./`. For Pluck, the Selection root is the Target directory. For an Always source, it is the resolved Always-source directory. A trailing `/` denotes a concrete directory path; without the trailing `/`, the reference denotes a concrete file path. Dirpluck does not infer file-versus-directory meaning from current filesystem state.

```text
["./tests/fixtures/big.bin"]   exact file path
["./tests/fixtures/"]          exact directory path and its subtree
```

level: MUST

### SPEC_084

A path reference must stay inside the Selection root. Bare `./`, `..` components, absolute paths, globs, and backslashes are rejected; `/` is the separator. A matching directory path reference prunes that directory before subtree traversal. A file path reference excludes only the exact file path.

level: MUST

### SPEC_085

Name patterns, expanded Shared ignores, and path references are applied as a union of exclusion conditions. Several different conditions may match the same entry without error, and evaluation order is not observable semantics. Implementations may prune a subtree as soon as a directory exclusion matches.

level: MUST

### SPEC_086

`ignore` takes precedence over link-like and special-entry diagnostics. Ignored entries are not Selection candidates, do not cause link-only or special-entry-only errors, and are not included in the skipped-link count. Entries inside an ignored subtree are not enumerated or subjected to traversal-time validation. A name pattern without a trailing `/` also applies to a special filesystem entry with the same name. If a path reference matches a link-like entry itself, that entry is likewise treated as ignored.

level: MUST

### SPEC_087

For name patterns, a bare `*`, `*/`, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, `!`, backslash, and a path separator inside the body are rejected. Path references have no wildcard syntax.

level: MUST NOT
