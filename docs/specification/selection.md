# Selection and Shared patterns

## SPEC_065

A Pluck base Selection, a Pluck Case Selection, or an Always source base Selection requires at least one candidate across `must` and `may`. A candidate may be a direct string pattern, a structured `match` entry, or a Shared reference. `description` is optional; when present, it must be a non-empty string. An Always Case is not a Selection; it is a membership filter over the effective Always-source set and therefore does not use this Selection grammar.

level: MUST

## SPEC_066

Each item in `must` or `may` is a direct pattern string, a `{ match = "..." }` inline table, or a `{ shared = "..." }` inline table.

```text
"foo"                         direct pattern
{ match = 'src/.*\.py' }    structured match
{ shared = "foo" }            Shared reference
```

level: MUST

## SPEC_067

A direct string in `ignore` is a name pattern. Structured entries use `{ match = "..." }` for a regular-expression match over a root-relative path, `{ shared = "..." }` for a `shared.ignore` reference, and `{ path = "..." }` for a concrete Selection-relative path.

```text
"*.pyc"                              direct name pattern
{ match = 'build/' }                 structured match
{ shared = "python-noise" }          Shared ignore reference
{ path = "tests/fixtures/big.bin" }  file/directory path
{ path = "tests/fixtures/" }         directory path
```

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

Shared references are resolved against the effective Shared namespace after Base composition. An unknown Shared reference is a Configuration error. A Shared reference has the same Selection meaning as the effective pattern set that it names. A path reference does not use the Shared namespace; it is interpreted from that Selection's source root.

level: MUST

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

Selection `ignore` supports direct name patterns, structured `{ path = "..." }` concrete paths, structured `{ match = "..." }` entries, and Shared-ignore expansion through `{ shared = "..." }`.

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

A Selection-relative concrete path is written as a `{ path = STRING }` inline table in `ignore`. For Pluck, the Selection root is the Target directory. For an Always source, it is the resolved Always-source directory. `path` is relative to the Selection root, and an initial `./` is optional and normalized. Without a trailing `/`, the concrete path excludes either a file or a directory at that path. Appending `/` narrows the exclusion to a directory only.

```text
{ path = "tests/fixtures/big.bin" }   exact entry path (file or directory)
{ path = "tests/fixtures/" }          exact directory path and its subtree
{ path = "./tests/fixtures/" }        same path after normalization
```

level: MUST

### SPEC_084

If an `ignore` path pattern denotes a directory, that directory and its entire subtree are excluded from Selection.

level: MUST

### SPEC_085

All `ignore` entries collectively define exclusions from the Selection result. An `ignore` entry that matches nothing is not an error.

level: MUST

### SPEC_086

Entries excluded by `ignore`, including entries within an ignored directory subtree, do not produce missing-pattern or type-mismatch diagnostics and do not contribute selected files.

level: MUST

### SPEC_087

For name patterns, a bare `*`, `*/`, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, `!`, backslash, and a path separator inside the body are rejected. Structured `path` entries have no wildcard syntax.

level: MUST NOT

## SECTION_603

title: Structured path match (`{ match = "..." }`)

### SPEC_159

`must`, `may`, `ignore`, and Shared pattern sets accept `{ match = STRING }` inline tables as direct Selection entries. The inline table may contain no key other than `match`, and `match` must be a non-empty string.

level: MUST

### SPEC_160

A regex Selection `{ match = "..." }` contains a non-empty Python-compatible regular expression of at most 512 characters. The expression is applied with full-match semantics to normalized relative source paths. Invalid regular expressions are Configuration errors.

level: MUST

### SPEC_161

A structured `match` is evaluated against the complete root-relative POSIX-style path of descendant regular files and regular directories below the Selection root; the Selection root itself is not a candidate. `/` is the path separator on every OS. A regular file path has no trailing `/`, while a regular directory path is normalized with a trailing `/`, such as `src/` or `src/pkg/`.

level: MUST

### SPEC_162

A structured `match` in `must` must match at least one selectable entry after `ignore` or the Selection fails. A structured `match` in `may` may match zero entries. If one structured match selects several entries, all matching entries become Selection candidates. A matching regular file selects that file; a matching regular directory behaves like an ordinary selected directory leaf and recursively collects regular files below it subject to `ignore`.

level: MUST

### SPEC_163

If multiple Selection expressions match the same file, that file contributes one Archive candidate. Distinct `must` expressions are nevertheless satisfied independently: each required expression must have at least one match.

level: MUST

### SPEC_164

When an ignore rule denotes a directory, the directory and its entire subtree are excluded from matching and Selection results.

level: MUST

### SPEC_165

Ignored entries do not contribute Selection matches, selected files, missing-pattern diagnostics, type-mismatch diagnostics, or skipped-link diagnostics.

level: MUST

