# Configuration schema

## SPEC_011

The accepted top-level structure is:

```text
[about]
[shared.must]
[shared.may]
[shared.ignore]
[pluck]
[pluck.case.<name>]
[scope]
[scope.<name>]
[namespace.<name>]
[always.<name>]
[always.<name>.case.<name>]
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

Each Configuration layer may contain zero or one Pluck and zero or more named Scopes, Always sources, Shared patterns, and Namespaces. `[scope]` is an optional `ignore` / `namespace` configuration for the always-present default Scope of the Root Configuration; it is not a declaration that creates a Scope. Pluck and Always sources may contain zero or more Cases.

level: MUST

## SPEC_015

Each Configuration may declare zero or one Output. When Output is declared, fixed Output and timestamp Output are mutually exclusive. Output is not required for schema validity, archive planning, or `--preview`. A build that actually writes an Archive requires either the Root Configuration's own Output declaration or Runtime Output. Output from a Base layer is not inherited by the root.

level: MUST

condition: when Output is declared; when a build writes an Archive file

## SPEC_016

A single Configuration layer may have no local source definition. After base composition, the Effective Configuration must contain at least one of Pluck or an Always source. The default Scope always exists for the Root Configuration, so an effective Pluck does not require a separate Scope declaration.

level: MUST

condition: after base composition
