# Base chain and composition

## SPEC_025

A Base Configuration is declared as `[about].base`. `base` is a concrete Configuration file path; empty strings and globs are rejected. A relative path is resolved from the current Configuration file's directory according to the Filesystem path notation rules, while an absolute path refers directly to a file on the host filesystem. The path must end in `.dirpluck`, follows the host OS's normal filesystem semantics, and must resolve to an existing regular file whose contents are a valid TOML Configuration schema.

level: MUST

related: [SPEC_003](document-selection.md#spec_003), [SPEC_018](paths.md#spec_018)

## SPEC_026

Each Configuration may reference zero or one base. If the Base Configuration has another `base`, the result is a linear chain. There is no fixed depth limit.

level: MUST

## SECTION_401

title: Cycle detection

### SPEC_027

If a base chain contains a reference that returns to the same Configuration file, the chain is invalid with a cycle error. Reaching the same physical Configuration file through a different document-path alias, including a symbolic link or Windows junction, is also a cycle.

level: MUST

condition: when determining a base-chain cycle

## SECTION_402

title: Definition composition

### SPEC_029

`[about].description`, `description_no_targets`, `description_no_always`, `description_empty`, `always_layout`, and `targets_layout` are each searched independently from the Root Configuration through its base chain; for each field, the first defined value becomes the effective value. If no Configuration in the chain defines a field, that effective value does not exist. `about.base` is a chain link and is not inherited as a value. A `[scope]` written in a Base Configuration configures the default Scope only when that Configuration itself is the Root; it is not inherited into an outer Root's default Scope.

level: MUST

### SPEC_030

- Pluck default Selection: when more than one Configuration in the base chain defines a default Selection, the `[pluck]` from the Configuration closest to the Root takes precedence. A Configuration that defines only Cases does not hide a Base default Selection.
- Pluck Case: `[case.pluck.<name>]` definitions are combined by Case name. For the same name, the complete Selection definition from the Configuration closest to the Root is used; differently named Cases all remain.
- Always source: for the same source name, the complete definition from the Configuration closest to the Root is used; differently named sources all remain.
- Always Case: `[case.always.<name>]` definitions are combined by Case name. For the same name, the complete definition, including `description`, `include`, and `exclude`, from the Configuration closest to the Root is used; differently named Cases all remain.
- Named Scope: for the same Scope name, the complete definition from the Configuration closest to the Root is used, including `description`, `target_kind`, `path`, `ignore`, `layout`, and `namespace`; differently named Scopes all remain. The default Scope is not inherited from a Base Configuration. Its root follows the default-Scope rule in Runtime Target, Scope, and Case, and only the Root Configuration's `[scope].description` / `target_kind` / `ignore` / `layout` / `namespace` applies.
- Layout: for the same Layout name, the complete definition from the Configuration closest to the Root is used; differently named Layouts all remain. Effective Layout names after composition must be unique under a case-insensitive comparison. `[about].always_layout`, `[about].targets_layout`, and per-source `layout` references are resolved against the effective Layout set after Base composition.
- Namespace: for the same Namespace name, the definition from the Configuration closest to the Root is used; differently named Namespaces all remain. Scope Namespace references are resolved against the effective Namespace set after Base composition.
- Shared pattern: `must`, `may`, and `ignore` are independent namespaces. Within each namespace, the complete array from the Configuration closest to the Root is used for a same-named pattern set.

level: MUST

### SPEC_034

Selection Shared references are resolved against the effective Shared namespace after Base composition. A Configuration closer to the Root can therefore add or replace a same-named pattern set referenced by a source definition from a Base Configuration.

level: MUST

## SECTION_403

title: Output and the base chain

### SPEC_035

A Configuration may omit Output and still be used as a Base Configuration that contributes shared definitions. Output from a Base Configuration is not inherited by the Root Configuration. Archive planning and `--preview` do not require Root Output. In a build that actually writes an Archive, only the Output declared directly by the Root Configuration is used, and the build fails if the Root has no Output.

level: MUST

condition: when a build writes an Archive file

