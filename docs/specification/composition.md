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

During base resolution, dirpluck keeps each Configuration's selected document location for diagnostics and relative-path resolution, while cycle identity is compared using the physical file path after symbolic-link or junction aliases are resolved. If another document-path alias resolves to the same physical Configuration path already active in the chain, resolution fails with a cycle error and the diagnostic shows the selected document-location chain. Depth alone does not produce an error or warning.

level: MUST

condition: when determining base-chain cycle identity

## SECTION_402

title: Definition composition

### SPEC_028

The deepest layer is used as the initial value, and definitions from each successively outer layer are overlaid to form the Effective Configuration.

level: MUST

### SPEC_029

`[about].description` is searched from the outermost layer inward; the first defined value becomes the effective description. If no layer defines one, there is no effective description. `about.base` is a chain link and is not itself shadowed or merged as an effective value. A `[scope]` written in a Base layer configures the default Scope only when that Configuration itself is the Root; it is not inherited into an outer Root's default Scope.

level: MUST

### SPEC_030

- Pluck: an outer Pluck shadows the entire inner Pluck definition.
- Always source: an outer source shadows the entire same-named inner source; differently named sources remain.
- Named Scope: an outer Scope shadows the entire same-named inner Scope, including `description`, `target_kind`, `path`, `ignore`, and `namespace`; differently named Scopes remain. The default Scope is not composed from the base chain; its root is determined from the Root Configuration location by the default-Scope rule in Runtime Target, Scope, and Case, and only the Root Configuration's `[scope].description` / `target_kind` / `ignore` / `namespace` is used.
- Namespace: an outer Namespace shadows the entire same-named inner Namespace; differently named Namespaces remain. Scope and Always Namespace references are resolved against the effective Namespace set after composition.
- Shared pattern: `must`, `may`, and `ignore` are independent namespaces. Within each namespace, an outer same-named pattern set shadows the entire inner array.

level: MUST

### SPEC_031

Pluck, Always, named-Scope, and Namespace shadowing is not a field-by-field partial merge. Cases belonging to a source definition are replaced together with that source definition.

level: MUST NOT

### SPEC_032

A named-Scope root or Always-source path is resolved from the directory containing the Configuration file in which that definition is written. A definition that remains from a Base Configuration retains the resolution implied by its origin and is not rebased to an outer layer. The default Scope has no `path` field; its root is determined by the default-Scope rule in Runtime Target, Scope, and Case.

level: MUST

related: [SPEC_018](paths.md#spec_018)

### SPEC_033

After composition, no two effective Scopes may resolve and normalize to the same filesystem location. This duplicate check is performed without requiring every named Scope path to exist. The rule also applies between the default Scope and named Scopes. Distinct locations that are merely in an ancestor/descendant relationship are not duplicates under this rule.

level: MUST

condition: when validating effective Scope roots after composition

### SPEC_034

Selection Shared references are resolved against the effective Shared namespace after the entire chain has been overlaid, not against the source's origin layer. An outer layer can therefore provide or shadow a same-named pattern set referenced by an inner source.

level: MUST

## SECTION_403

title: Output and the base chain

### SPEC_035

Output definitions are not composed like source definitions. A Configuration may omit Output and still be used as a Base Configuration that contributes shared definitions. Archive planning and `--preview` do not require Root Output. In a build that actually writes an Archive, only the Output declared directly by the Root Configuration is used, and the build fails if the root has no Output. Output from an inner layer is not inherited by the root.

level: MUST

condition: when a build writes an Archive file

### SPEC_036

Within a base chain, only Configurations that actually declare Output contribute a write-ownership boundary, and the base-chain write-boundary overlap rules in Output validate that those declared write boundaries do not overlap. A layer without Output has no write boundary.

level: MUST
