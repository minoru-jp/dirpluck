# dirpluck Glossary

Terms used with a common meaning in the design, implementation, and use of dirpluck.

## dirpluck

The name of this library. It follows the extraction intent declared by a Root Configuration, applies an optional CLI-bound Target definition to one or more runtime directories, selects from fixed Companions, and may also select files from Companions declared by explicitly imported Configurations or added by the Root Configuration inside an import root before creating one ZIP Archive. A run may be composed only of Companions and Configuration imports, without a local Target.

## Configuration file

A TOML file that declares a dirpluck extraction intent. It contains zero or one Target definition, zero or more Companions, zero or more named Shared patterns, zero or more Configuration imports, and one Output definition. A Configuration selected directly by the CLI becomes the Root Configuration, uses the process cwd as the execution root for its own sources, and owns the final Output. Import `root` paths are resolved relative to the directory containing the Root Configuration file itself. A Configuration loaded through a Configuration import uses the resolved import `root` as its execution root. Its declared Companions may be reused, and the Root Configuration may add more Companions under `[import.<name>.companion.<name>]` within the same import root; the imported Target and Output definition are not used. At most one flat Case name may be selected within a Configuration: for a Root Configuration it can switch Target and Companion selections, while for an import it can switch Companion selections only. Shared patterns are reused by explicit references within the same Configuration and do not provide Case inheritance or implicit merging. Root Configuration discovery is limited to cwd and the immediate `./dirpluck/` directory; duplicate names are ambiguous and rejected.

## Target

An optional runtime-bound source definition. Default extraction settings may be written directly in `[target]`, with independent named alternatives under `[target.case.<name>]`. A Target never has a fixed `path` in the Configuration, and each Configuration still defines at most one Target rule. Only when the Configuration is run as the Root Configuration does it receive one or more directories from CLI `DIRECTORY` values, and the same selected Target rule is applied to all of them. If that Configuration is imported by another Configuration, its Target definition is not used. A Root Configuration without a Target cannot be bound to Target directories.

## Case

A flat named extraction variation selected zero or one time for a Configuration. When a Root Configuration has a Target, `[target.case.<name>]` defines that Case, and each Companion uses `[companion.<name>.case.<name>]` when present or falls back to its base selection. When a Root Configuration has no Target, or when a Case is selected for a Configuration import, at least one relevant Companion must define that Case. Imported Target Cases are not used. Case definitions are complete selections rather than differences from or inheritance of the base selection. They do not add or remove sources, change Companion paths, or change Output definitions. Cases are not combined or nested.

## Companion

A fixed source associated with a Configuration's extraction intent. It may accompany a Target or belong to an intent with no Target. Ordinary `[companion.<name>]` tables declare a fixed `path` relative to their Configuration execution root, a purpose description, and a base selection. A Root Configuration may also declare `[import.<import-name>.companion.<name>]` to add a Companion inside an import root without turning that source into a Target. Optional matching `.case.<case-name>` tables provide complete alternative selections; when the selected Case is absent, the Companion falls back to its base selection.

## Source directory

An actual directory from which extraction is performed. A Root Configuration receives one or more Target directories from the CLI when it defines a Target. Companion directories are determined from fixed `path` values in the Root Configuration, an imported Configuration, or a Root-defined Companion under an import namespace. Every used source directory must exist and resolve within the execution root assigned to the Configuration that resolves that source, and symbolic-link escapes are rejected. A Root Target may be the process cwd itself via `.`, in which case the cwd's actual directory name is still preserved in the Archive.

## Extraction

The process of determining which files from Targets or Companions belong in the Archive and combining the Root Configuration's own Target and Companions with Companion results from each import namespace, whether those Companions come from the imported Configuration or were added by the Root Configuration, into one Archive plan. `include` lists required relative paths, `include_if_exists` lists optional candidates added only when present, and `exclude` applies limited name filters inside selected areas. These patterns may be written directly or added by explicitly referencing Shared include or exclude patterns from the same Configuration. Shared include patterns are referenced with `include_pattern_refs` or `include_if_exists_pattern_refs`, Shared excludes with `exclude_pattern_refs`, and the referring selection decides whether a Shared include is required or optional. At least one direct or Shared `include` / `include_if_exists` equivalent candidate is required. `if_empty = "allow"` is valid only when there are no required candidates.

## Archive

The ZIP output generated by dirpluck. A selected file keeps its actual path relative to the execution root of the Configuration that selected it, and a generated `README.md` is written at the Archive root. If multiple sources or Configuration imports select the same real file for the same Archive path, it is written once. If one Archive path maps to different real files, or one real file maps to different Archive paths, the plan is ambiguous and rejected.

## Output definition

The required `[output]` settings. Only the Root Configuration's Output definition is used as the final Output for a run; Output definitions belonging to imported Configurations are ignored at execution time. Fixed output declares a cwd-relative `path` plus `if_exists = "error" | "overwrite"`. Generated output declares `directory`, `timestamp = true`, and optional `prefix` / `suffix`; it creates a timestamped ZIP name, rejects an already-existing destination during normal execution, and may accept an explicit CLI `--sequence N` after the timestamp. dirpluck does not auto-number generated outputs, coordinate concurrent writes to the same path, or temporarily override the Output form from the CLI.

## Archive README

The purpose-neutral index document generated as the Archive-root `README.md`. It records the Root Configuration, Configuration imports, selected Cases, the execution root assigned to each Configuration, included directories, Target descriptions or logically named Companion descriptions, selected Configuration locations, directory binding methods, selected-file counts, and empty-result policies when relevant. Its fixed wording does not name the generating tool or prescribe a downstream use; concrete purpose comes from the configured descriptions. If multiple roles resolve to the same actual directory, that directory is indexed once and each role is recorded separately.

## Shared pattern

A named pattern set explicitly reused by multiple selections inside the same Configuration. Include sets are defined under `[shared.include_patterns]`, exclude sets under `[shared.exclude_patterns]`, each as `name = [...]`, and each is validated with the corresponding pattern grammar. Selections reference Shared patterns with `include_pattern_refs`, `include_if_exists_pattern_refs`, or `exclude_pattern_refs` and add them to directly written patterns. Unreferenced Shared patterns are not applied. Shared patterns do not provide Case inheritance, implicit merging, or automatic application across sources.

## Configuration import

A mechanism by which a Root Configuration explicitly loads another dirpluck Configuration under a name and combines Companion extraction results in the same Archive plan. `[import.<name>]` declares an import execution `root` as a relative path from the directory containing the Root Configuration file itself, the `configuration` file within that root, an optional `case`, and optionally Root-owned `[import.<name>.companion.<companion-name>]` tables. The import name is a logical namespace, so Companions under it are named `<import>.<companion>` regardless of their origin; duplicate names within one import are rejected. Absolute roots are not accepted. Imported-Configuration Companions resolve Shared patterns in the imported Configuration, while Root-defined import Companions resolve them in the Root Configuration. The imported Target and `[output]` are not used. Each import namespace must contain at least one Companion from either origin. In 0.3.0, only the Root Configuration may declare Configuration imports, and an imported Configuration may not recursively import another Configuration.

## Root Configuration

The Configuration that starts one dirpluck run. It is selected through normal CLI discovery or `--config NAME`, uses the process cwd as the execution root for its own sources, and binds CLI `DIRECTORY` and `--case` values to its own Target and Companions. Import `root` values are resolved relative to the directory containing this Configuration file itself, not relative to the process cwd. It may declare zero or more Configuration imports to reuse Companions from other Configurations and to add Root-owned Companions inside those import roots, and it owns the final `[output]` used by the run. It does not implicitly inherit or propagate an imported Configuration's Target, Output definition, or Case.
