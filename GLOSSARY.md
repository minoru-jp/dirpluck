# dirpluck Glossary

Terms used consistently across dirpluck design, implementation, and operation.

## dirpluck

The library itself. dirpluck resolves an optional single Configuration-import chain, composes definitions from the inner layer outward into one effective Configuration, then selects files from the effective Target and Companions and packages them into a ZIP Archive.

## Configuration file

A TOML file that describes a dirpluck extraction intent. Each file may define zero or one Target, named Companions, named Shared patterns, zero or one Configuration import, and one Output definition. When an import exists, the imported Configuration is resolved first and outer same-named definitions shadow inner definitions. Import depth is unlimited; cycles are rejected.

## Target

The main source definition, with at most one Target per Configuration. A Target has a base selection and optional named Cases but no fixed path. Across a Configuration chain, an outer Target shadows the inner Target as a whole. Whenever an effective Target exists, one or more CLI `DIRECTORY` values bind its runtime source regardless of which Configuration layer defined it.

## Case

A single flat named selection variation applied to the effective Configuration. Cases are complete selections, not deltas from base. Shadowing a Target or Companion replaces that source together with all of its Cases. One CLI `--case` is applied after Configuration layering.

## Companion

A fixed source associated with the extraction intent. An ordinary `[companion.<name>]` uses a path relative to the execution root of the layer that defines it. Across a Configuration chain, an outer same-named Companion shadows the inner definition as a whole. `[import.<name>.companion.<name>]` defines a Companion overlay anchored to the immediate import root and participates in the same name resolution.

## Source directory

The actual directory from which files are extracted. Whenever an effective Target exists, one or more CLI directories are resolved inside the Root Configuration execution root regardless of the Target definition's origin layer. Companion directories come from the fixed path and execution-root context associated with their effective definition. Every source directory must stay inside its corresponding filesystem boundary.

## Extraction

The process of resolving files from the effective Target and Companions. `include` defines required candidates, `include_if_exists` optional candidates, and `exclude` filters names inside selected ranges. Shared-pattern references resolve against the effective include/exclude namespaces after the whole Configuration chain has been layered.

## Archive

The ZIP artifact produced by dirpluck. Target-selected files retain paths relative to the Root Configuration execution root; Companion-selected files retain paths relative to the execution root associated with the effective Companion definition. Identical physical files at the same Archive path are written once; path collisions between different files and ambiguous multiple Archive paths for the same physical file are rejected.

## Output definition

The `[output]` configuration. Only the outermost Root Configuration's Output is used in a run; inner Output definitions are not executed. Fixed output uses a cwd-relative `path` and `if_exists`; generated output uses `directory`, `timestamp = true`, and optional `prefix` / `suffix`.

## Archive README

The neutral index document generated as `README.md` at the Archive root. It records the resolved Configuration chain, execution roots, effective source definitions, selected Case, descriptions, and selection counts.

## Shared pattern

A named reusable pattern array. Include patterns live under `[shared.include_patterns]`; exclude patterns under `[shared.exclude_patterns]`. The two namespaces resolve independently from inner to outer, with an outer same-named pattern shadowing the inner one. Selections reference ordinary names, and those references are resolved against the final effective namespace.

## Configuration import

The mechanism for loading one other dirpluck Configuration as the next inner layer. Each Configuration may declare zero or one `[import.<name>]`. `root` is relative to the Configuration file that declares the import, and `configuration` is a relative TOML path inside that root. Imported Configurations may import again without a depth limit; re-entering a Configuration already on the active chain is a cycle error.

## Root Configuration

The outermost Configuration that starts one dirpluck run. It is selected by normal CLI discovery or `--config NAME`, uses the process cwd as its execution root, may import zero or one inner Configuration, owns the final Output, and resolves CLI `DIRECTORY` values inside its execution root whenever the effective Configuration contains a Target.

## Effective Configuration

The one-run Configuration produced by resolving the import chain from the deepest layer outward and shadowing same-named definitions with outer definitions. It contains at most one Target, at most one Companion per name, and at most one Shared include/exclude pattern per name in their respective namespaces. Output is not layered; the Root Configuration's Output is used.
