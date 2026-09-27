# Configuration selection

How Selection rules, Shared patterns, and Cases decide which entries are collected.

This guide explains Selection authoring. Exact pattern grammar and validation are defined in [Selection and Shared patterns](../specification/selection.md), while filesystem-entry boundaries are defined in [Filesystem boundaries and entry types](../specification/filesystem.md). For Target and Case operation, see [Targets and Cases](../cli/targets.md); for the trust boundary, see the [Trust model](../TRUST.md).

## Selection

Directory-Target Pluck, Always sources, and Cases each contain an independent Selection. A Selection uses `must`, `may`, `ignore`, and optionally `allow_empty`; use `description` only when you want to attach a human-readable explanation. File Targets are atomic sources and do not contain a Selection.

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

If a pattern matches nothing, the Selection does not succeed.

### `may`

Candidates that are included when present but whose absence is not an error.

```toml
may = ["generated/*.pdf", "coverage.xml"]
```

`must` and `may` can be used together in one Selection.

### `ignore`

Use `ignore` for entries that should not be plucked from areas already selected as candidates by `must` or `may`. A normal string continues to match a file or directory **name**.

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

For Pluck, `./` means the current Target root. For an Always source, it means that Always source root. A trailing `/` marks a directory path; without the trailing `/`, the reference is a file path. Dirpluck does not infer file-versus-directory meaning from the current filesystem state. Path references must stay inside the Selection root and do not accept `..`, absolute paths, globs, or backslashes.

Name patterns, Shared ignore references, and path references are combined as one set of exclusion conditions. It is valid for several conditions to match the same entry. A directory matching either a directory name ignore or a directory path reference is excluded before traversal, and its contents are not inspected. Evaluation order is not part of the semantics.

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
project = ["src", "pyproject.toml"]

[shared.may]
docs = ["README.md", "docs"]

[shared.ignore]
python-noise = ["__pycache__/", "*.pyc"]
```

A normal string in a Selection array is a direct pattern. In `must` and `may`, a one-element nested array is a Shared reference. In `ignore`, a one-element nested array is a Shared reference when it contains a plain name, or a Selection-relative path reference when the string begins with `./`.

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

Nested arrays such as `[]`, `["a", "b"]`, and `[123]` are invalid references. In `must` and `may`, nested arrays are reserved for Shared references. `ignore` reserves the `./` prefix inside a nested array for path references, without changing the syntax of ordinary direct-string patterns.

See [Specification](../specification/INDEX.md) for name resolution and duplicate validation along a base chain.
## Cases

Use a Case to provide another complete Selection for the same source.

```toml
[pluck]
description = "Normal review."
must = ["documents", "metadata.json"]

[pluck.case.audit]
description = "Audit review."
must = ["documents", "metadata.json", "records"]
```

```console
dirpluck acme --case audit
```

A Case is not a delta applied to the base Selection. Write all required `must`, `may`, `ignore`, Shared references, and `allow_empty` values in the Case itself.

If Pluck and an Always source both have the same Case name, the same CLI `--case` selects the corresponding variation. See [Specification](../specification/INDEX.md) for exact Case semantics, including fallback when an Always source does not define the selected Case.
