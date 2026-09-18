# dirpluck Usage Guide

This document lists only the operational rules needed when using dirpluck.

## Basics

- The supported public interfaces are the CLI and TOML Configuration.
- Check a new or changed Configuration with `--dry-run` before a normal run.
- The default Root Configuration is `dirpluck.toml` in cwd or `./dirpluck/`.
- `--config NAME` selects the Root Configuration from cwd or `./dirpluck/`. The `.toml` suffix may be omitted.
- A Configuration with `[target]` requires one or more `DIRECTORY` arguments.
- A Companion-only Configuration takes no `DIRECTORY` argument.

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

To use a Shared pattern from an imported Configuration, reference it as `<import>.<pattern>`:

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"

[target]
description = "The current project."
include_if_exists = ["*"]
exclude_pattern_refs = ["shikumi.python-dev"]
if_empty = "allow"
```

Root Targets, Root Companions, and `[import.<name>.companion.<name>]` selections may use qualified imported Shared patterns. Companions declared by the imported Configuration continue to use that Configuration's own `[shared.*]` names locally.


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

To reuse Companions from another Configuration:

```toml
[import.shikumi-stack]
root = ".."
configuration = "shikumi/dirpluck.toml"
case = "distribution"

[import.shikumi-stack.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

- `root` is relative to the directory containing the Root Configuration file itself. Use `/` separators; `..` is allowed, but absolute paths are not.
- `configuration` is a relative TOML file path inside the import root. No discovery is performed.
- Only Companions are used from the imported Configuration. Its Target is not used.
- Add `[import.<name>.companion.<name>]` when the Root Configuration should define another Companion inside the import root.
- Companion logical names under an import are `<import>.<companion>`. Do not define the same Companion name from both the imported Configuration and the Root Configuration within one import.
- Root-defined import Companion `path` values are relative to the import root. `path = "."` selects the import root itself. Do not use absolute paths or `..`.
- Shared patterns from an imported Configuration are available to Root-owned selections as `<import>.<pattern>`.
- Companions declared by the imported Configuration continue to use the imported Configuration's own `[shared.*]` names locally; importing them does not rewrite those references.
- The imported and Root-defined Companions together must provide at least one Companion.
- `case` applies to the whole import Companion namespace. At least one Companion must define that Case. Root `--case` does not propagate.
- The imported `[output]` is not used. Only the Root Configuration's `[output]` is the final Output.
- Do not import from an imported Configuration. Imports are one level deep.

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
- Treat cwd as the Root Configuration boundary; each import uses its own `root` as its boundary.
- After adding or changing an import, use `--dry-run` to verify the resolved root, Configuration, and Companions.
- When symlinks are present, use `--dry-run` to check the resolved selection.

## Common mistakes

- `include` is required. Use `include_if_exists` for candidates whose absence is normal.
- `include = ["*"]` on an empty Target fails because the required pattern has no match. To allow an empty Target, use `include_if_exists = ["*"]` with `if_empty = "allow"`.
- `if_empty = "allow"` cannot be used by a Selection that has required `include` patterns.
- A Case does not inherit base selection fields or shared-pattern references.
- Shared patterns are not applied automatically.
- Imported Shared patterns use qualified names of the form `<import>.<pattern>` from Root-owned selections.
- Define include and exclude shared patterns separately.
- Root CLI `DIRECTORY` and `--case` values do not propagate into imports.
- An imported `[output]` is not executed.
- Do not put `[import.<name>]` inside an imported Configuration.
- Do not use `..` on ordinary Targets or Companions to widen the boundary. Use `[import.<name>]` when another Configuration should be used.
- Do not use internal Python modules as a public API.

## Details

If an sdist or repository checkout is available, consult these documents as needed:

- `CONFIGURATION.md`: detailed TOML Configuration authoring
- `SPECIFICATION.md`: exact operational semantics
- `GLOSSARY.md`: terminology
- `README.md`: overall library description
