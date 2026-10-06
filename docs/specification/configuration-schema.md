# Configuration schema

## SPEC_011

The accepted top-level structure is:

```text
[about]
[shared.must]
[shared.may]
[shared.ignore]
[pluck]
[case.pluck.<name>]
[case.always.<name>]
[scope]
[scope.<name>]
[layout.<name>]
[namespace.<name>]
[always.<name>]
[extra.<name>]
[output]
[output.timestamp]
```

level: MUST

## SPEC_012

Unknown keys are errors.

level: MUST

## SPEC_013

`[about]` is optional and may contain `description`, `description_no_targets`, `description_no_always`, `description_empty`, `always_layout`, `targets_layout`, and `base`. Each field is optional, but if `[about]` is present at least one field must be present. All four description fields are non-empty strings. `always_layout` and `targets_layout` are Layout-name references valid as one Archive directory component, and `base` is one Configuration file path.

level: MUST

condition: when `[about]` is defined

## SPEC_014

Each Configuration in a Base chain may contain zero or one Pluck and zero or more named Scopes, Layouts, Always sources, Extra sources, Shared patterns, and Namespaces. `[scope]` configures the optional `description` / `target_kind` / `ignore` / `layout` / `namespace` fields of the always-present default Scope in the Root Configuration; it is not a declaration that creates a Scope. A named Scope has a required `path` and the same optional fields. `target_kind` is `"directory"`, `"file"`, or `"both"` and defaults to `"directory"`. `[layout.<name>]` is a named declaration for a top-level Archive directory and may contain only optional `description`; omitting `description` and leaving the table empty is valid, while a bare parent `[layout]` with no named Layouts is an error. After TOML key parsing, a Layout name is validated as one Archive directory component and must be unique within a Configuration under a case-insensitive comparison. Canonical `[always.<name>]` and `[extra.<name>]` use the same source schema: required `path`, Selection fields, and optional `layout`; `namespace` is not part of the 1.0 schema. Always definitions normally participate, while Extra definitions are inactive until referenced by the complete `include` mode or delta `add` mode of `[case.always.<name>]`, at which point they participate with the same fixed-source role as Always. Case definitions live under the top-level `[case]` namespace. `[case.pluck.<name>]` is a complete Pluck Selection, while `[case.always.<name>]` defines participation rules over effective Always and Extra sources. Therefore `case` is not reserved as an Always-source name and `[always.case]` remains a normal Always source definition.

level: MUST

## SPEC_015

Each Configuration may declare zero or one Output. When Output is declared, fixed Output and timestamp Output are mutually exclusive. Standalone schema validity and Archive planning / `--preview` do not require Output. A build that writes an Archive file requires either an Output declaration on the Root Configuration itself or a runtime Output. Output declared by a Base Configuration is not inherited by the Root Configuration.

level: MUST

condition: when Output is declared; when a build writes an Archive file

## SPEC_016

Each Configuration, and the effective configuration after Base composition, may contain no source definitions. Pluck, Always sources, Extra sources, and named Scopes are all optional, and an Effective Configuration containing only the always-present default Scope is valid. If a runtime request resolves zero sources, build / preview still succeeds and the Archive may contain only the generated `README.md`.

level: MUST

condition: after Base composition

