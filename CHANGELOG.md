# dirpluck CHANGELOG

Release history for dirpluck.

## 0.5.2

Reorganize the public documentation by purpose, make the glossary the conceptual foundation of the documentation set, and keep only the minimal runtime references in the wheel.

### Changed

- Organize the public documentation as `README.md`, `GLOSSARY.md`, and `CHANGELOG.md` at the repository root, with `docs/CLI.md`, `docs/CONFIGURATION.md`, and `docs/SPECIFICATION.md` for detailed reference. Remove the former `USAGE.md` and split CLI operation from TOML Configuration authoring. README now focuses on use cases and adoption, the Glossary on concepts, and the `docs/` documents on details read as needed.
- Remove specification details such as cardinality constraints, shadowing rules, path rules, and validation behavior from `GLOSSARY.md`, leaving it as the shared conceptual vocabulary for the documentation set. Exact behavior is concentrated in `docs/SPECIFICATION.md`; the CLI and Configuration guides explain only what is needed for their tasks and point to the specification when more detail is required.
- Replace the wheel's single `dirpluck/docs/USAGE.md` with two compact references: `dirpluck/docs/CLI.md` and `dirpluck/docs/CONFIGURATION.md`. The full Glossary, detailed guides, Specification, canonical documentation sources, and Japanese intermediate documents remain available from the sdist, separating lightweight runtime reference from deeper investigation.

## 0.5.1

Fix Target binding in the 0.5.0 effective-Configuration model so runtime directories always come from CLI input, independent of the layer that defined the Target.

### Fixed

- When the effective Configuration contains a Target, require one or more CLI `DIRECTORY` arguments whether the Target was defined by the Root Configuration or by an imported layer. Remove the 0.5.0 rule that inferred an imported Target's project directory from Configuration placement and rejected CLI `DIRECTORY`. Target Selection still resolves through the Configuration chain, while runtime Target directories always resolve inside the Root Configuration's execution root.

## 0.5.0

Configuration import is generalized into one linear layering model so that Target, Companion, and Shared-pattern definitions can be composed under the same name-resolution rules from imported Configuration to importing Configuration.

### Changed

- Each Configuration may define at most one `[import.<name>]`, while an imported Configuration may itself import one more. Import-chain depth is unlimited; a repeated Configuration file on the active chain is rejected as a cycle.
- The Configuration chain is resolved from the deepest layer outward into one effective Configuration. Target uses the singleton name `target`; Companions and Shared patterns resolve by their own names. An outer same-named definition shadows the inner definition as a whole. Shared-pattern references are resolved against the final effective namespace, and 0.5.0 no longer requires `<import>.<pattern>` qualification as the name-resolution model.
- A Target that survives from an imported Configuration may now be executed. A Root-owned effective Target still receives CLI `DIRECTORY` values. An imported effective Target is bound to the project directory inferred from `<project>/dirpluck.toml` or `<project>/dirpluck/<name>.toml`. An outer Target shadows the inner Target and all of its Cases.
- Case selection is moved from per-import settings to one Case applied to the effective Configuration. `[import.<name>].case` is no longer used. Shadowing a source also replaces its Case definitions.
- Only the Root Configuration's `[output]` is still executed. Recursive-import version-specific wording is removed; cycles are reported with version-independent Configuration errors that identify the import chain.

## 0.4.1

The current package version is centralized in `dirpluck.__version__`, and document generation uses an external JSON context generated from it.

### Changed

- Stop storing the current release number as glossary vocabulary. Generate the external document-context JSON from `dirpluck.__version__`, and use its `version` value in documents that need the current version. CHANGELOG release labels remain literal historical data in the canonical source.

## 0.4.0

Allow the Root Configuration to explicitly reuse Shared include and exclude patterns from imported Configurations under the import namespace.

### Added

- Expose `[shared.include_patterns]` and `[shared.exclude_patterns]` from an imported Configuration to the Root side under qualified names of the form `<import-name>.<pattern-name>`. Root-local Shared patterns keep their existing local names, and include/exclude namespaces remain distinct.
- Allow qualified imported Shared patterns to be referenced from Root-owned Target, Root Companion, and `[import.<name>.companion.<name>]` base/Case selections. Companions declared by the imported Configuration continue to resolve their own Shared patterns locally inside that Configuration; their references are not rebound into the Root namespace.
- Reject an ambiguous Root-visible Shared-pattern name when a Root-local name collides with the qualified name of an imported Shared pattern of the same kind. Shared-pattern tables are still not merged or applied automatically; every Selection must name the Shared pattern it uses explicitly.

## 0.3.0

Allow a Root Configuration to explicitly import Companions declared by another dirpluck Configuration from a different filesystem root while preserving a separate boundary for each Configuration.

### Added

- Add Configuration imports. A Root Configuration may declare `root`, `configuration`, and optional `case` under `[import.<name>]` to combine the extraction results of Companions declared by another dirpluck Configuration into the same Archive plan. A Root Configuration may also consist only of imports with no local Target or Companion.
- Define import `root` as the only path that may explicitly cross the Root Configuration's cwd boundary. The root is restricted to a relative path from the directory containing the Root Configuration file itself; POSIX, Windows, and UNC absolute forms are rejected regardless of the host OS. After the import root is resolved, `configuration`, imported Companions, and selected files are confined inside that root again so every Configuration keeps an independent filesystem boundary.
- Keep runtime binding explicit across Configuration boundaries: Root CLI `DIRECTORY` and `--case` values do not propagate into imports, imported Targets are not used, and import `case` applies independently only to the imported Companion group. Imported `[output]` definitions are schema-validated but not executed; the Root Configuration's `[output]` remains the only final Output. In 0.3.0, imported Configurations may not recursively import another Configuration.
- Build Archive paths relative to the execution root of the Configuration that selected each file. The same real file selected for the same Archive path is written once; different real files colliding on one Archive path, or one real file resolving to different Archive paths, are rejected as ambiguous. The Archive README records used Configuration imports and their execution roots.
- Allow a Root Configuration to declare `[import.<name>.companion.<companion-name>]` and add sources inside an import root as Companions rather than Targets. Companions under an import use logical names `<import>.<companion>` regardless of whether they come from the imported Configuration or the Root Configuration, and duplicate logical names within one import are rejected. Root-defined import Companions use Root Shared patterns, imported-Configuration Companions keep the imported Shared-pattern namespace, and `path = "."` may select the import root itself.

## 0.2.0

Introduce Shared patterns so extraction conditions can be reused explicitly across Cases and sources.

### Added

- Add Shared patterns. Define named pattern sets as `name = [...]` under `[shared.include_patterns]` and `[shared.exclude_patterns]`, then reference them explicitly from Target or Companion base/Case selections with `include_pattern_refs`, `include_if_exists_pattern_refs`, and `exclude_pattern_refs`. Shared patterns are added only to selections that reference them; they do not inherit from base to Case, merge implicitly, or apply automatically across sources.
- Validate Shared include patterns with the include grammar and Shared exclude patterns with the exclude grammar. A Shared include set may be referenced as required candidates through `include_pattern_refs` or optional candidates through `include_if_exists_pattern_refs`; Shared excludes use `exclude_pattern_refs`. All three forms may be combined with directly written `include`, `include_if_exists`, or `exclude` patterns.
- Expand the sdist as a source distribution suitable for rebuilding and validating a release. In addition to the existing tests and public documents, it now includes the canonical documentation sources and Japanese intermediate documents under `_internal/`, plus the synchronization and distribution-verification tools under `tools/`. `_internal/`, `tools/`, tests, and `.github/` remain excluded from wheels.
- Add a public `USAGE.md` that provides a compact reference for the operational rules needed at use time. Manage it through the existing canonical → Japanese intermediate document → English publication flow, and include it at the repository root, in the sdist, and as `dirpluck/docs/USAGE.md` in the wheel. The wheel now packages `USAGE.md` as its only documentation file; `README.md`, `CONFIGURATION.md`, `GLOSSARY.md`, and `SPECIFICATION.md` remain available from the sdist or repository.

## 0.1.0

First public release.

### Added

- Treat one Configuration file as one extraction intent, producing a ZIP Archive from an optional runtime-bound Target definition and/or one or more fixed Companions, plus one required Output definition. When a Target is defined, one or more CLI directory arguments may instantiate that same Target rule in one run; TOML still defines only one Target rule. A Configuration with no Target runs without positional directories, while supplying any to such a Configuration is an error. Extraction conditions are written directly on each source; there are no named shared extraction rules or bundle references.
- Generalize Case as one flat, Configuration-wide selection variation. When a Target exists it must define the selected Case; Companions with the same Case use it and other Companions fall back to base. Without a Target, a Case is valid when at least one Companion defines it. Case selections are complete alternatives with no inheritance or merge, source membership, Companion paths, and Output policy do not change, and Cases cannot be combined or nested.
- Select fixed-depth relative paths with `include` and `include_if_exists`, allowing at most one `*` per path element. `include` requires at least one match per pattern, while `include_if_exists` permits zero matches. Recursive-anywhere `**` search is not provided.
- Filter selected file or directory names with `exclude` using limited exact, prefix, suffix, and contains matching.
- Default `if_empty` to `error`, while allowing optional-only Target or Companion selections to use `if_empty = "allow"`. Allowed empty selections can be preserved as explicit empty directories in the Archive.
- Preview planned Archive contents with `--dry-run`. Missing required includes are shown as `[missing]`, optional misses as `[optional missing]`, and empty-result policy is reported without creating a ZIP.
- Restrict processing to the current working directory, reject symbolic-link escapes, and allow the Target to be the cwd itself while still preserving the cwd's actual directory name in the Archive.
- Require `description` on every Target or Companion selection, including named Cases, and generate an Archive-root README. When multiple purposes resolve to the same actual directory, files are unioned by real path and the README records each declared purpose.
- Support Python 3.11 and later, distribute dirpluck under the MIT License, and keep runtime third-party dependencies at zero.
- Define PyPI distribution boundaries explicitly: the wheel ships executable code plus the public `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md`, while the sdist additionally includes tests and public source documents. `_internal/` and `.github/` remain repository-only development infrastructure.
- Simplify the normal CLI form to `dirpluck DIRECTORY [DIRECTORY ...]` and remove the `build` subcommand. Discover Configurations only from the cwd and `./dirpluck/`: the default searches for `dirpluck.toml`, while `--config NAME` searches for the same named TOML in both locations. Multiple matches are rejected as ambiguous, and `--configs` lists discoverable candidates and conflicts.
- Rework `README.md` around concrete use cases and the value of repeatable file sets, move TOML authoring guidance into `CONFIGURATION.md`, and keep exact operational semantics in `SPECIFICATION.md`.
- Keep the Archive-root `README.md` as a purpose-neutral index: fixed wording does not identify the generating tool or prescribe downstream use, while Target and Companion `description` values carry concrete purpose.
- Add fixed and generated Output forms. Generated Output uses `directory`, `timestamp = true`, optional `prefix` / `suffix`, and optional CLI `--sequence N` to produce `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip`; existing destinations are rejected during normal execution, with no auto-numbering, auto-renaming, or overwrite mode. Asynchronous and parallel invocations are not coordinated, so callers must avoid concurrent writes to the same output path.
- Clarify in `README.md` and `CONFIGURATION.md` that selecting a directory recursively collects its contents and that dirpluck does not infer or automatically exclude secret-like files such as `.env`, private keys, or `.git`; broad selections require explicit exclusions appropriate to the workspace.
