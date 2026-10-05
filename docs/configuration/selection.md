# Configuration selection

How Selection rules, Shared patterns, and Cases decide which entries are collected.

This guide explains Selection authoring. Exact pattern grammar and validation are defined in [Selection and Shared patterns](../specification/selection.md), while filesystem-entry boundaries are defined in [Filesystem boundaries and entry types](../specification/filesystem.md). For Target and Case operation, see [Targets and Cases](../cli/targets.md); for the trust boundary, see the [Trust model](../TRUST.md).

## Selection

Directory-Target Pluck, Always sources, and Cases each contain an independent Selection. A Selection uses `must`, `may`, `ignore`, and optionally `allow_empty`; use `description` only when you want to attach a human-readable explanation. File Targets are atomic sources and do not contain a Selection.

Ordinary Selection strings and Scope regular-expression Target selectors intentionally use different pattern languages. Ordinary `must` / `may` strings use restricted path patterns for predictable directory traversal, while ordinary `ignore` strings use restricted name patterns. When a Selection needs more expressive matching, a `{ match = "..." }` inline table can apply a Python-compatible regular expression to a full root-relative path below the Selection root. The Scope `<...>` Target selector also uses a Python-compatible regular expression, but only to filter normalized names of already-eligible direct-child Targets. These differences are intentional. See [Targets and Cases](../cli/targets.md) for Target-selector syntax.

When an inclusion entry reference could denote either a file or a directory, dirpluck does not infer the type from the filesystem. Ordinary `must` / `may` strings use no trailing `/` for a file and a trailing `/` for a directory on the final component. Intermediate components are directories by construction because traversal continues through them. Structured `match` paths are likewise type-explicit: files have no trailing `/`, while directories do.

`ignore` is intentionally broad on the exclusion side. Ordinary ignore strings and structured `{ path = "..." }` entries without a trailing `/` exclude matching files and directories; a trailing `/` narrows the exclusion to directories only. Use structured `match` when an exclusion must be file-only.

### `description`

Describe the role the source plays in the extraction intent. In the generated Archive README, this description explains the meaning of the archive path.

```toml
description = "Reference material used to evaluate the submission."
```

`description` is optional. Omitting it does not change Selection semantics. When present, it must be a non-empty string. An Always source description appears directly below that source heading, before metadata such as the file count. A Pluck description is not duplicated for every directory Target; it appears once in the Pluck group within each Scope. Multi-line descriptions remain section content rather than being compressed into a table cell.

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

When only one concrete location should be excluded, use a `{ path = "..." }` inline table with a concrete relative path from the Selection root.

```toml
ignore = [
    { path = "tests/fixtures/big.bin" },
    { path = "src/generated/" },
]
```

The `path` value is always relative to the Selection root. For Pluck, that root is the current Target root; for an Always source, it is that Always source root. A leading `./` is optional, so `./src/generated/` and `src/generated/` normalize to the same path. Without a trailing `/`, the path excludes either a file or a directory at that location; if it is a directory, its subtree is excluded as well. A trailing `/` narrows the exclusion to a directory only. The path must stay inside the Selection root and does not accept `..`, absolute paths, globs, or backslashes.

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

A normal string in a Selection array is a direct pattern, while `{ match = "..." }` is a direct structured match. Write a Shared reference as a `{ shared = "name" }` inline table, and write a concrete relative path in `ignore` as `{ path = "..." }`. Shared pattern sets may themselves contain direct strings and `{ match = "..." }` entries, but they cannot nest Shared references or path entries.

```toml
[pluck]
description = "The current project."
must = [
    "LICENSE",
    { shared = "project" },
]
may = [
    { shared = "docs" },
]
ignore = [
    ".git/",
    { shared = "python-noise" },
]
```

The referenced namespace is determined by the field containing the reference. `must = [{ shared = "project" }]` refers to `shared.must.project`; references in `may` use `shared.may`; `ignore = [{ shared = "python-noise" }]` refers to `shared.ignore.python-noise`.

From 0.14.0 through releases before 1.0.0, the legacy one-element nested-array forms (`["name"]`, and `["./path"]` inside `ignore`) remain accepted as compatibility input but are deprecated. When the CLI loads a Configuration file that uses the legacy form, it prints one warning for that file to stderr with the replacement syntax and the 1.0.0 removal notice. The official Python API `dirpluck.run()` reports the same condition through Python's warnings framework as the public `ConfigurationDeprecationWarning` (`FutureWarning` subclass), rather than adding it to `RunResult.warnings`. The warning is visible under Python's default filters and is attributed to the first caller outside the dirpluck package. Configuration files loaded through the base chain are covered as well. New Configurations should use `{ shared = "..." }` and `{ path = "..." }`. In 1.0.0, the legacy nested-array references become invalid Configuration syntax. Nested arrays that were already invalid, such as `[]`, `["a", "b"]`, and `[123]`, remain errors throughout the compatibility period.

See [Specification](../specification/INDEX.md) for name resolution and duplicate validation along a base chain.
## Cases

Cases have different jobs for Pluck and Always. A Pluck Case is another complete Selection. An Always Case filters which Always sources participate.

```toml
[pluck]
description = "Normal review."
must = ["documents/", "metadata.json"]

[case.pluck.audit]
description = "Audit review."
must = ["documents/", "metadata.json", "records/"]

[always.guidelines]
path = "review-guidelines"
must = ["*.md"]

[always.license]
path = "legal"
must = ["LICENSE"]

[case.always.release]
include = ["guidelines", "license"]
```

```console
dirpluck ./acme/ --case audit
dirpluck --case .release
dirpluck ./acme/ --case audit.release
```

`[case.pluck.audit]` is not a delta from `[pluck]`. Write every required `must`, `may`, `ignore`, Shared reference, and `allow_empty` value in the Case itself. From 0.16.x through releases before 1.0.0, legacy `[pluck.case.audit]` remains accepted as compatibility input, reports a migration notice, and is removed in 1.0.0.

`[case.always.release]` does not change any Always source Selection. It filters the effective Always-source set. `include` and `exclude` are mutually exclusive. `include = []` explicitly selects no Always sources; `exclude = []` excludes none; omitting both includes every Always source.

The runtime selector has two independent axes. `--case audit` selects only the Pluck Case, `--case .release` selects only the Always Case, and `--case audit.release` selects both. A defined Case may validly result in zero sources. See [Specification](../specification/INDEX.md) for the normative Case rules.
