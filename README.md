# dirpluck

dirpluck turns a declared file-extraction intent into a reproducible ZIP archive. It is useful when “which files belong together” is a repeatable decision rather than a one-off manual choice: the files may live in one directory or several, some may change from run to run, others may be fixed references that should always travel with the same purpose, and some may already be declared by another Configuration that you want to reuse explicitly.

Instead of reconstructing that set from memory, shell history, chat history, or local convention, you describe it once in TOML. A later run resolves the same declared sources and applies the same selection rules. The result is not a backup of everything nearby; it is a package assembled for a stated purpose.

## Where dirpluck fits

### Gather related material scattered across directories

A useful package is often not stored under one root. A proposal may need documents from `sales/`, supporting research from `research/`, and legal material from `legal/`. A recurring meeting pack may draw from notes, reports, and reference material maintained by different parts of a workspace.

dirpluck can describe those locations as fixed Companions and build the package without requiring a runtime Target at all:

```toml
[companion.proposal]
path = "sales/proposal"
description = "The proposal being prepared for delivery."
include = ["*.pdf"]

[companion.research]
path = "research"
description = "Research material supporting the proposal."
include = ["*.md", "data/*.csv"]

[output]
path = "artifacts/proposal-package.zip"
if_exists = "overwrite"
```

```console
dirpluck --config proposal-package
```

The Configuration records why those directories belong together. The directories do not need to share a parent beyond the current working-directory boundary, and no single one has to be treated as the “main” directory.

### Rebuild a recurring working set

Some file sets are useful precisely because they recur. A weekly review, editorial cycle, research pass, reporting task, or other repeated workflow may need the same categories of material every time even though the file contents change.

A Configuration turns that recurring choice into a named artifact of the workflow. The next run does not have to rediscover which folders, reports, or references were used last time. `--dry-run` can show the resolved plan before the Archive is written, so the declared set can be checked when the workspace changes.

### Prepare a focused review or handoff package

Sharing an entire repository or working directory is often unnecessary. A review may need the current document, supporting evidence, and a checklist; a handoff may need the deliverable, operating notes, and selected reference material; a code review may need source, tests, and a dependent library.

dirpluck lets the package describe that boundary explicitly. Required material can be declared with `include`, while known optional material can be declared separately with `include_if_exists`. A missing required item therefore fails instead of silently producing a package that only appears complete.

### Preserve a meaningful snapshot

A snapshot does not always mean “copy everything as it exists now.” For research, writing, investigations, design work, or release preparation, the useful snapshot may be the subset that explains the state of the work: the current documents, selected source data, decisions, and any generated artifacts that happen to exist.

A Companion-only Configuration works well for this. Fixed sources describe the parts that constitute the snapshot, and optional selections can include generated material when present without turning its absence into an error. Running the same Configuration later reproduces the same definition of the snapshot, even though its contents may have changed.

For snapshots meant to accumulate, the Configuration can use timestamp-based generated output instead of repeatedly updating one fixed path:

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

Each run creates a name such as `project-YYYYMMDD-HHMMSS.zip`. If that generated name already exists when the run checks its destination, the run fails. If a script deliberately starts multiple runs in the same second, the caller can add `--sequence N` to distinguish them. dirpluck does not infer the next number or silently rename an existing output.

dirpluck does not coordinate asynchronous or parallel invocations. If multiple runs may overlap, the caller is responsible for giving them distinct output paths; for generated output, explicit `--sequence N` values are one way to do that. Concurrent writes to the same output path are unsupported.

### Combine changing subjects with stable references

Other workflows have one or more subjects of the same kind that change from run to run. You may review different projects against the same guidelines, inspect several case directories alongside the same reference corpus, or package a batch of submissions with the same templates and instructions.

That distinction is represented directly: one `[target]` definition describes the shared selection rule, and the CLI supplies one or more Target directories for that run. Companions remain fixed in the Configuration. This does not add multiple Target definitions to TOML; the same Target rule is applied independently to every supplied directory.

```toml
[target]
description = "The submission currently being reviewed."
include = ["documents", "metadata.json"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck submissions/acme
```

The same rule can also be applied to several runtime Targets in one Archive:

```console
dirpluck submissions/acme submissions/contoso submissions/globex
```

Each Root Target keeps its directory path relative to cwd in the Archive and uses the same Target selection. The same Configuration can therefore be reused for one subject or a batch without duplicating the TOML definition.

### Import Companion definitions from another Configuration

When a related project lives in another directory and already manages its Companions in a dirpluck Configuration, you do not need to duplicate those paths and patterns in the parent Configuration. A Root Configuration can import that Configuration explicitly and reuse its Companion definitions and, when needed, a Companion Case. The imported Target is not used.

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

Companions under an import use logical names of the form `<import>.<companion>` regardless of whether they come from the imported Configuration or are added by the Root Configuration. The same Companion name cannot be defined twice within one import. Logical names are not Archive-path prefixes.

Only `root` is allowed to cross the parent cwd boundary explicitly. It is resolved as a relative path from the directory containing the Root Configuration file itself, so if the Configuration is stored under `./dirpluck/`, that location is the reference point even when the process cwd is unchanged. Absolute paths are not accepted. Once the import root is resolved, it becomes the imported Configuration's filesystem boundary, and the Companions used by the import and their selected files are confined to it again. The parent CLI `--case` and `DIRECTORY` values do not propagate implicitly, and the imported Configuration's Target and `[output]` are not used.

This lets a parent reuse Companion definitions already declared for another project without copying that project's Companion paths and selection rules into a second Configuration, while still allowing parent-specific extra sources to remain Companions instead of becoming Targets. Shared patterns from an imported Configuration are available to Root-owned selections under qualified names such as `<import>.<pattern>`. Imported-Configuration Companions continue to resolve their own local Shared-pattern names inside the imported Configuration; importing them does not rewrite those references. Imports remain one level deep: an imported Configuration cannot import another Configuration.

### Keep LLM-assisted work reproducible

LLM-assisted work is one important instance of the same problem. During a long-running task, a human and an LLM may repeatedly need the same source material, reference documents, generated outputs, or related projects. If that set exists only in conversation history, each new session has to reconstruct it and may reconstruct it differently.

A Configuration gives both sides an inspectable statement of what belongs together. An LLM can read the file, explain why each source is present, help revise it, and use `--dry-run` to check the resulting plan. The durable decision remains in TOML rather than in the model’s memory of an earlier conversation.

## Broad directory selections require explicit exclusions

When `include` or `include_if_exists` selects a directory, files below that directory are collected recursively. dirpluck does not treat hidden files, repository metadata, environment files, credentials, or private keys as special cases. A broad selection such as `include = ["src"]` or `include = ["*"]` therefore includes content under selected directories unless an `exclude` rule removes it.

Before sharing an Archive or sending it outside the workspace, review broad selections and add exclusions appropriate to that workspace. `.git/`, `.env*`, `*.pem`, and `*.key` are common examples, but no example list can identify every sensitive file. dirpluck deliberately does not infer which files are secrets or exclude them automatically.

When the same exclusion list is needed by the base selection and several Cases, or by several sources, define it once as a **Shared pattern**. What is shared is only the pattern array, not a complete selection; every selection that uses it names the shared set explicitly. Shared patterns from an imported Configuration can also be reused by the Root Configuration through qualified names such as `<import>.<pattern>`. For example, a normal development selection and an “almost everything” Case can reuse the same exclusions.

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
    "*.pyc",
    ".DS_Store",
]

[target]
description = "The current development target."
include_if_exists = ["src", "tests", "README.md"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[target.case.all]
description = "All target files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Cases do not inherit from the base selection, so `exclude_pattern_refs` must be written explicitly on every selection that needs it. This preserves the rule that a Case is a complete replacement while allowing long pattern arrays to be reused.

## Why the model is intentionally narrow

The examples above are different uses of the same claim: **one Root Configuration represents one final Archive intent**. dirpluck keeps extraction decisions local and explicit instead of turning Configuration into a general-purpose search language or a hierarchy of inherited profiles. Within one Configuration, named include/exclude pattern arrays can be reused. Companion definitions owned by another Configuration can be reused explicitly through a Configuration import. Neither mechanism provides implicit inheritance or merging.

dirpluck therefore does not infer which files are important, select the newest artifact, search arbitrary directory depth, or invent relationships between sources. Those decisions stay visible in Configuration. When another Configuration is used, dirpluck does not open arbitrary paths outside cwd for individual sources; `[import.<name>]` explicitly names both the Configuration and the execution root being reused.

A Case is intentionally smaller than a profile system. One run may select at most one flat Case name. That Case can switch complete selections for the Target and for Companions that define the same name; Companions without that Case continue with their base selection. A Case does not add or remove sources, change Companion paths, or replace Output policy.

Required and optional material are also kept separate. `include` means a match is necessary for the declared intent; `include_if_exists` means absence is expected and acceptable. This lets a Configuration distinguish “not present today” from “the package is incomplete.”

## The model in brief

A **Root Configuration** contains at least one local source or Configuration import and exactly one Output definition. A **Target** is an optional runtime-bound source definition that receives one or more directories from the CLI only when the Configuration is run as the Root Configuration. The same Target selection is applied to every supplied directory. An imported Configuration's Target is not used. Each Configuration still contains at most one `[target]` definition. A **Companion** is a fixed source whose path is relative to the execution root assigned to that Configuration, and its definition can be reused through a Configuration import.

A **Case** is one flat selection variation within a Configuration. When a Target exists, it must define the selected Case; each Companion may define the same Case and otherwise falls back to its base selection. Without a Target, a Case is valid when at least one Companion defines it. Cases do not propagate between the Root Configuration and imports.

Selections describe required and optional entries inside each source. Repeated pattern sets may be given Shared pattern names and referenced explicitly from the selections that need them. To reuse Companions or Shared patterns from another Configuration, use a **Configuration import** and explicitly declare its execution root, Configuration file, and, when needed, a Companion Case. Imported Shared patterns are referenced from Root-owned selections as `<import>.<pattern>`. Only the Root Configuration owns the final Output; an imported Configuration's Target and `[output]` are not used.

For the complete TOML authoring guide, including Target and Companion forms, Cases, selection fields, and full examples, see [CONFIGURATION.md](CONFIGURATION.md). For exact matching, discovery, filesystem-boundary, Archive, Output, dry-run, and error semantics, see [SPECIFICATION.md](SPECIFICATION.md).

## CLI

The supported public interface is the CLI.

When the selected Configuration defines a Target, supply one or more directories. Every directory uses the same `[target]` selection:

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

A Configuration made only of Companions needs no positional directory:

```console
dirpluck --config snapshot
```

Use one named Case with `--case`:

```console
dirpluck DIRECTORY [DIRECTORY ...] --case review
```

For a Companion-only Configuration:

```console
dirpluck --config snapshot --case archive
```

Use another Configuration with `--config NAME`. `NAME` is a filename, not an arbitrary path; the `.toml` suffix is optional.

```console
dirpluck DIRECTORY [DIRECTORY ...] --config review
```

List Configurations discoverable from the current working directory:

```console
dirpluck --configs
```

Preview the same Archive plan without creating or modifying the output:

```console
dirpluck DIRECTORY [DIRECTORY ...] --case review --dry-run
```

For a Configuration that uses generated output, supply a positive sequence number only when same-second runs need an explicit distinction:

```console
dirpluck --config snapshot --sequence 2
```

There are intentionally no CLI options that temporarily replace selection rules or the Output form. Those decisions belong to the Configuration so the invocation remains explainable from the same declared intent. `--sequence` does not replace the naming rule; it only fills the optional runtime number slot declared by generated output.

## Installation

Python 3.11 or later is required. Current release: `0.4.0`.

```console
pip install dirpluck
```

After installation:

```console
dirpluck --version
```

dirpluck has no third-party runtime dependencies.

## Public interface and documentation

The CLI is dirpluck's compatibility-supported public interface. Python modules and functions inside the package remain importable for implementation structure and testing, but they are not currently a compatibility-guaranteed public Python API.

The documentation is split by purpose:

- **README.md** explains what dirpluck is useful for, how its model maps to those uses, and the main design boundaries.
- **USAGE.md** is a compact operational reference for the positive-use rules needed when running dirpluck.
- **CONFIGURATION.md** explains how to write the TOML Configuration and provides complete authoring examples.
- **SPECIFICATION.md** defines exact matching, discovery, boundary, Archive, Output, dry-run, and error semantics.
- **GLOSSARY.md** provides compact definitions of the domain terms used across the project.

The wheel includes only `USAGE.md` under `dirpluck/docs/`, keeping the information needed at use time alongside the installed CLI. README, CONFIGURATION, SPECIFICATION, GLOSSARY, CHANGELOG, and the document-generation infrastructure are available from the sdist or repository.
