# dirpluck Usage Guide

This document lists only the operational rules needed when using dirpluck.

## Basics

- The supported public interfaces are the CLI and TOML Configuration.
- Check a new or changed Configuration with `--dry-run` before a normal run.
- The default Root Configuration is `dirpluck.toml` in cwd or `./dirpluck/`.
- `--config NAME` selects the Root Configuration from cwd or `./dirpluck/`. The `.toml` suffix may be omitted.
- Pass one or more `DIRECTORY` arguments whenever the effective Configuration contains a Target, regardless of which Configuration layer defined it.
- When the effective Configuration has no Target, pass no `DIRECTORY`.

```console
dirpluck PROJECT --dry-run
dirpluck PROJECT
dirpluck PROJECT --config review --dry-run
dirpluck --config snapshot --dry-run
```

When using a Case:

```console
dirpluck PROJECT --case all --dry-run
```

## Target

Items that must exist:

```toml
[target]
description = "The current project."
include = [
    "pyproject.toml",
    "src",
]
```

Items to collect only when they exist:

```toml
[target]
description = "The current project."
include_if_exists = [
    "README.md",
    "tests",
    "docs",
]
if_empty = "allow"
```

To collect the entire Target while allowing it to be empty:

```toml
[target]
description = "The current project."
include_if_exists = ["*"]
if_empty = "allow"
```

When an include matches a directory, files under that directory are collected recursively.

## Exclusions

```toml
exclude = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

When using a broad include, explicitly add the exclusions required for the intended use.

## Shared patterns

Shared exclusions:

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

Reference them from a Selection:

```toml
[target]
description = "The current project."
include_if_exists = ["src", "tests"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Shared includes:

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]
```

Reference them as required candidates:

```toml
include_pattern_refs = ["project-core"]
```

Reference them as optional candidates:

```toml
include_if_exists_pattern_refs = ["project-core"]
```

Defining a shared pattern does not apply it automatically. Reference it explicitly from each Selection that uses it.

Across a Configuration chain, Shared-pattern names are resolved from the inner layer outward. Reference the ordinary name; an outer same-named definition shadows the inner one.

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"

[shared.exclude_patterns]
python-dev = [".git/", ".venv/", "__pycache__/", "*.pyc"]

[target]
description = "The current project."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Even when a Selection comes from an inner Configuration, `python-dev` resolves in the final effective Shared-pattern namespace. An outer layer may provide or override that name.

## Case

```toml
[target.case.all]
description = "All target files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

A Case does not inherit the base Selection. Declare the required `include`, `include_if_exists`, `exclude`, and shared-pattern references in the Case itself.

## Companion

```toml
[companion.tool]
path = "tool-project"
description = "A related project used with the target."
include = ["dist/tool-*.whl"]
```

If a Companion defines a Case with the selected Case name, that Case is used. Otherwise the Companion uses its base Selection.

## Configuration import

Import another Configuration:

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

- Each Configuration may contain zero or one `[import.<name>]`.
- The imported Configuration may import one more Configuration; there is no chain-depth limit.
- Re-entering a Configuration file already on the active chain is a cycle error.
- `root` is relative to the Configuration file that declares the import. Use `/`; `..` is allowed. Absolute paths are not.
- `configuration` is a relative TOML file path inside the import root. No discovery is performed.
- Resolve names from the deepest layer outward. Outer same-named Target, Companion, or Shared pattern definitions shadow inner definitions.
- The import name identifies the link; it is not an automatic prefix for Companion or Shared-pattern names.
- Do not use `[import.<name>.case]`. One CLI `--case` applies to the effective Configuration.
- Inner `[output]` definitions are not executed. Only the Root Configuration's `[output]` is used.

To add or override a Companion whose path is relative to the immediate import root:

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

This participates in normal Companion-name resolution under `project`. `path = "."` selects the import root itself.

If an imported Target survives into the effective Configuration, apply that Target selection to the runtime directory supplied with CLI `DIRECTORY`. dirpluck does not infer a Target directory from the imported Configuration file's location. If the Root layer defines its own Target, that outer Target shadows the imported Target and all of its Cases.

## Output

Fixed name:

```toml
[output]
path = "output.zip"
if_exists = "overwrite"
```

Use `if_exists = "error"` to reject an existing output file.

Timestamp-based generated name:

```toml
[output]
directory = "dist"
prefix = "context"
timestamp = true
suffix = "dev"
```

Specify a positive sequence only when needed.

```console
dirpluck PROJECT --sequence 2
```

## Operation

- Check the selection with `--dry-run` before a normal run.
- Treat `[missing]` as an unmatched required `include` and investigate it.
- Treat `[optional missing]` as an unmatched `include_if_exists` and verify that the result is intentional.
- Treat cwd as the Root Configuration boundary; every import layer uses its resolved `root` as its boundary.
- After changing imports, use `--dry-run` to inspect the chain, shadowing result, Target directory, and Companions.
- When symlinks are present, use `--dry-run` to check the resolved selection.

## Common mistakes

- `include` is required. Use `include_if_exists` for candidates whose absence is normal.
- `include = ["*"]` on an empty Target fails because the required pattern has no match. To allow an empty Target, use `include_if_exists = ["*"]` with `if_empty = "allow"`.
- `if_empty = "allow"` cannot be used by a Selection that has required `include` patterns.
- A Case does not inherit base selection fields or shared-pattern references.
- Shared patterns are not applied automatically.
- Define include and exclude shared patterns separately.
- Do not define more than one `[import.<name>]` in one Configuration.
- Import depth is unlimited, but cycles are not allowed.
- Do not treat the import name as a Companion or Shared-pattern prefix.
- If a Target is effective, pass CLI `DIRECTORY` even when that Target definition came from an imported Configuration.
- Inner `[output]` definitions are not executed.
- Do not use `..` on ordinary Targets or Companions to widen the boundary. Use `[import.<name>]` when another Configuration should be used.
- Do not use internal Python modules as a public API.

## Details

If an sdist or repository checkout is available, consult these documents as needed:

- `CONFIGURATION.md`: detailed TOML Configuration authoring
- `SPECIFICATION.md`: exact operational semantics
- `GLOSSARY.md`: terminology
- `README.md`: overall library description
