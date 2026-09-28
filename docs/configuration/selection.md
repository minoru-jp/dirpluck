# Configuration selection

How Selection rules, Shared patterns, and Cases decide which entries are collected.

This guide explains Selection authoring. Exact pattern grammar and validation are defined in [Selection and Shared patterns](../specification/selection.md), while filesystem-entry boundaries are defined in [Filesystem boundaries and entry types](../specification/filesystem.md). For Target and Case operation, see [Targets and Cases](../cli/targets.md); for the trust boundary, see the [Trust model](../TRUST.md).

## Selection

Directory-Target Pluck, Always sources, and Cases each contain an independent Selection. A Selection uses `must`, `may`, `ignore`, and optionally `allow_empty`; use `description` only when you want to attach a human-readable explanation. File Targets are atomic sources and do not contain a Selection.

Ordinary Selection strings and Scope regular-expression Target selectors intentionally use different pattern languages. Ordinary `must` / `may` strings use restricted path patterns for predictable directory traversal, while ordinary `ignore` strings use restricted name patterns. When a Selection needs more expressive matching, a `{ match = "..." }` inline table can apply a Python-compatible regular expression to a full root-relative path below the Selection root. The Scope `<...>` Target selector also uses a Python-compatible regular expression, but only to filter normalized names of already-eligible direct-child Targets. These differences are intentional. See [Targets and Cases](../cli/targets.md) for Target-selector syntax.

When an inclusion entry reference could denote either a file or a directory, dirpluck does not infer the type from the filesystem. Ordinary `must` / `may` strings use no trailing `/` for a file and a trailing `/` for a directory on the final component. Intermediate components are directories by construction because traversal continues through them. Structured `match` paths are likewise type-explicit: files have no trailing `/`, while directories do.

`ignore` is intentionally broad on the exclusion side. Ordinary ignore strings and concrete path references without a trailing `/` exclude matching files and directories; a trailing `/` narrows the exclusion to directories only. Use structured `match` when an exclusion must be file-only.

### `description`

Describe the role the source plays in the extraction intent. In the generated Archive README, this description explains the meaning of the archive path.

```toml
description = "Reference material used to evaluate the submission."
```

`description` is optional. Omitting it does not change Selection semantics. When present, it must be a non-empty string and appears as the body of that source's section in the generated Archive README, after the source heading and file count. Multi-line descriptions are kept as section content rather than being compressed into a table cell.

### `must`

Candidates that are required to exist and are included when present.

```toml
must = ["report.pdf", "data/*.csv"]
```

If a pattern matches nothing, the Selection does not succeed. The final component without a trailing `/` requires a file; a trailing `/` requires a directory. For example, write `src/` when selecting that directory.

### `may`

Candidates that are included when present but whose absence is not an error.

```toml
may = ["generated/*.pdf", "coverage.xml"]
```

`must` and `may` can be used together in one Selection. The final-component type notation is the same as for `must`. If a `may` entry has no match of the requested type but the same pattern matches an entry of the opposite type, it remains optional missing rather than becoming an error. Dirpluck records a source-labelled non-fatal diagnostic suggesting the relevant trailing-`/` adjustment; the CLI prints it as a warning in both normal builds and `--preview`, and the Python API returns it in `RunResult.warnings`. The diagnostic does not change `may` semantics. The same mismatch on `must` remains an unsatisfied error in a normal build, while `--preview` keeps it missing and also reports the type-marker hint as a warning.

### `{ match = "..." }`

When ordinary string patterns are not expressive enough, `must`, `may`, and `ignore` can contain a `{ match = "..." }` inline table. Its value is a Python-compatible regular expression applied with full-match semantics to the **entire root-relative path** of entries below the Selection root.

```toml
must = [
    "src/",
    { match = 'packages/(core|ui)/dist/.*\.whl' },
]
```

Paths always use `/` as the separator, regardless of the host OS. A regular file is matched as a path such as `src/main.py`; a regular directory is matched as `src/package/`, with a trailing `/` only for directories. This lets the regular expression distinguish files from directories or deliberately match both, for example with a suffix such as `/?`. The Selection root itself is not a `match` candidate.

A `must` match must find at least one non-ignored selectable entry; a `may` match may find none. If one expression matches several entries, all of them are selected. Matching a directory has the same meaning as selecting a directory with an ordinary pattern: its subtree is collected subject to `ignore`. If ordinary patterns and `match` entries ultimately select the same file, the Archive still contains that file only once.

The same form is available in `ignore`. Matching a directory path there prunes that directory subtree.

```toml
ignore = [
    { match = 'build/' },
    { match = 'src/.*\.tmp' },
]
```

A structured `match` may scan a broad portion of the Selection root to test candidate paths. Dirpluck does not need to infer an optimized traversal route from the regular expression. Ordinary string patterns remain the simpler choice for straightforward path selection; use `match` when its added expressiveness is useful. A `match` expression must be non-empty, no longer than 512 characters, and valid as a Python-compatible regular expression.

### `ignore`

Use `ignore` for entries that should not be plucked from areas already selected as candidates by `must` or `may`. A normal string continues to match a file or directory **name**. To exclude by a regular expression over a full root-relative path, use the structured `{ match = "..." }` form described above.

```toml
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

When only one concrete location should be excluded, use a one-element nested array whose string begins with `./`. This is a path reference relative to the Selection root.

```toml
ignore = [
    ["./tests/fixtures/big.bin"],
    ["./src/generated/"],
]
```

For Pluck, `./` means the current Target root. For an Always source, it means that Always source root. Without a trailing `/`, a concrete path reference excludes either a file or a directory at that path; if it is a directory, its subtree is excluded as well. A trailing `/` narrows the exclusion to a directory only. Path references must stay inside the Selection root and do not accept `..`, absolute paths, globs, or backslashes.

Ordinary name patterns follow the same broad-exclusion rule: without a trailing `/` they exclude matching files and directories, while a trailing `/` narrows the exclusion to directories. Name patterns, Shared ignore references, path references, and structured `match` entries are combined as one set of exclusion conditions. It is valid for several conditions to match the same entry. Any name ignore, path reference, or structured `match` that matches a directory excludes that directory before traversal, and its contents are not inspected. Evaluation order is not part of the semantics.

`ignore` takes precedence over diagnostics based on an entry's filesystem type: once an entry is ignored, it is treated as handled rather than as evidence for a symbolic-link, Windows-junction, or special-entry diagnostic. A `must` pattern that matches only ignored entries therefore fails as an ordinary unsatisfied `must`.

Recognized non-ignored symbolic links or Windows directory junctions are neither `must` / `may` selection candidates nor recursive traversal targets and are not included in the Archive. Other non-ignored filesystem entries that are neither regular files nor regular directories, such as FIFOs, sockets, and devices, are also not archived. If `must` matches only such special entries, the error explains that those entries are not selectable; `may` treats them as optional missing. Selections do not add implicit ignores based on content or names. See [TRUST.md](../TRUST.md) for the trust boundary when running Configurations and for handling broad selections.

### `allow_empty`

Use this for a Selection containing only `may` candidates when zero final files should still be valid.

```toml
may = ["generated/*.pdf"]
allow_empty = true
```

The default is `false`. `allow_empty = true` cannot be combined with `must`.
## Shared patterns

When the same pattern set is used by multiple Selections, define it as a named Shared pattern. Shared patterns use the same three namespaces as Selections: `must`, `may`, and `ignore`.

```toml
[shared.must]
project = ["src/", "pyproject.toml"]

[shared.may]
docs = ["README.md", "docs/"]

[shared.ignore]
python-noise = ["__pycache__/", "*.pyc"]
```

A normal string in a Selection array is a direct pattern, while `{ match = "..." }` is a direct structured match. In `must` and `may`, a one-element nested array is a Shared reference. In `ignore`, a one-element nested array is a Shared reference when it contains a plain name, or a Selection-relative path reference when the string begins with `./`. Shared pattern sets may themselves contain direct strings and `{ match = "..." }` entries, but they cannot nest Shared references or path references.

```toml
[pluck]
description = "The current project."
must = [
    "LICENSE",
    ["project"],
]
may = [
    ["docs"],
]
ignore = [
    ".git/",
    ["python-noise"],
]
```

The referenced namespace is determined by the field containing the reference. `must = [["project"]]` refers to `shared.must.project`; references in `may` use `shared.may`; `ignore = [["python-noise"]]` refers to `shared.ignore.python-noise`. Only an `ignore` nested-array string beginning with `./`, such as `ignore = [["./tests/fixtures/"]]`, refers to a Selection-relative path instead of the Shared namespace.

Nested arrays such as `[]`, `["a", "b"]`, and `[123]` are invalid references. In `must` and `may`, nested arrays are reserved for Shared references. `ignore` reserves the `./` prefix inside a nested array for path references, without changing the syntax of ordinary direct-string patterns or structured `match` entries.

See [Specification](../specification/INDEX.md) for name resolution and duplicate validation along a base chain.
## Cases

Use a Case to provide another complete Selection for the same source.

```toml
[pluck]
description = "Normal review."
must = ["documents/", "metadata.json"]

[pluck.case.audit]
description = "Audit review."
must = ["documents/", "metadata.json", "records/"]
```

```console
dirpluck ./acme/ --case audit
```

A Case is not a delta applied to the base Selection. Write all required `must`, `may`, `ignore`, Shared references, and `allow_empty` values in the Case itself.

If Pluck and an Always source both have the same Case name, the same CLI `--case` selects the corresponding variation. See [Specification](../specification/INDEX.md) for exact Case semantics, including fallback when an Always source does not define the selected Case.
