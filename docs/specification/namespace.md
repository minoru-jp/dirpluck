# Namespace

## SPEC_061

A Namespace is defined as a named `[namespace.<name>]` table. In the current schema the table must be empty and accepts no fields. A bare empty parent `[namespace]` does not define a Namespace and is an error.

level: MUST

## SPEC_062

After it has been parsed as a TOML key, a Namespace name is validated as one Archive directory component. Empty names, `.`, `..`, path separators `/` and `\`, ASCII control characters U+0000 through U+001F, and U+007F are rejected. These are structural Archive-name constraints rather than host-OS filename rules. dirpluck does not independently apply host-OS reserved-name, trailing-dot, or other filesystem-specific naming rules. A Namespace is not a filesystem path; it is a named Configuration concept that assists a source's logical Archive identity.

level: MUST

## SPEC_063

A Scope `namespace` field references an effective Namespace name and retains the existing Target behavior: `NAMESPACE/` is prefixed to the Target's final Archive root. The Scope root, Target discovery, and Target entry name are unchanged. An unknown Namespace reference is a Configuration error.

level: MUST

## SPEC_168

Multiple Scopes may reference the same Namespace definition. Namespace definition names are unique under case-insensitive comparison. Final Archive roots after applying a Scope Namespace follow the ordinary Archive identity and collision rules. The spelling written to the Archive preserves the Configuration / Target spelling.

level: MAY

## SPEC_169

dirpluck does not emulate host-OS or filesystem-specific reserved names, trailing-dot rules, Unicode normalization, or similar naming behavior to guarantee cross-platform extraction compatibility. When an Archive will be moved to another OS or filesystem, Configuration authors are responsible for choosing names that are valid and remain distinct there. Case-insensitive uniqueness is a dirpluck Archive-identity rule and applies to the complete set of resolved source final Archive roots independently of those host-specific rules.

level: MUST
