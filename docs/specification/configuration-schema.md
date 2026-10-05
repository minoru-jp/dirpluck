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
[namespace.<name>]
[always.<name>]
[output]
[output.timestamp]
```

level: MUST

## SPEC_012

Unknown keys are errors.

level: MUST

## SPEC_013

`[about]` is optional and may contain only `description` and `base`. Each field is independently optional, but if `[about]` is present, at least one must be present. `description` is a non-empty string. `base` is one Configuration file path.

level: MUST

condition: when `[about]` is defined

## SPEC_014

Each Configuration in a Base chain may contain zero or one Pluck and zero or more named Scopes, Always sources, Shared patterns, and Namespaces. `[scope]` configures the optional `description` / `target_kind` / `ignore` / `namespace` fields of the always-present default Scope in the Root Configuration; it is not a declaration that creates a Scope. A named Scope has a required `path` and the same optional fields. `target_kind` is `"directory"`, `"file"`, or `"both"` and defaults to `"directory"`. A canonical `[always.<name>]` has required `path` plus Selection fields only; `namespace` is not part of the 1.0 schema. Case definitions live under the top-level `[case]` namespace. `[case.pluck.<name>]` is a complete Pluck Selection, while `[case.always.<name>]` filters membership in the effective Always-source set. Therefore `case` is not reserved as an Always-source name and `[always.case]` remains a normal Always source definition.

level: MUST

## SPEC_015

Each Configuration may declare zero or one Output. When Output is declared, fixed Output and timestamp Output are mutually exclusive. Standalone schema validity and Archive planning / `--preview` do not require Output. A build that writes an Archive file requires either an Output declaration on the Root Configuration itself or a runtime Output. Output declared by a Base Configuration is not inherited by the Root Configuration.

level: MUST

condition: when Output is declared; when a build writes an Archive file

## SPEC_016

Each Configuration, and the effective configuration after Base composition, may contain no source definitions. Pluck, Always sources, and named Scopes are all optional, and an Effective Configuration containing only the always-present default Scope is valid. If a runtime request resolves zero sources, build / preview still succeeds and the Archive may contain only the generated `README.md`.

level: MUST

condition: after Base composition

