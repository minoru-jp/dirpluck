# Namespace

## SPEC_061

A Namespace is defined as a named `[namespace.<name>]` table. In the current schema the table must be empty and accepts no fields. A bare empty parent `[namespace]` does not define a Namespace and is an error.

level: MUST

## SPEC_062

The Namespace name itself becomes one directory component in the ZIP. Empty names, `.`, `..`, `/`, backslash, control characters, and `< > : " | ? *` are rejected. A Namespace is not a filesystem path; it is exactly one Archive-path component.

level: MUST

## SPEC_063

A Scope or Always `namespace` field references an effective Namespace name. For a source that references a Namespace, the final Archive root is `NAMESPACE/SOURCE_ROOT`. The prefix is always applied, regardless of whether another source would otherwise collide. A source without a Namespace keeps `SOURCE_ROOT` as its final Archive root.

level: MUST

## SPEC_064

Several sources may reference the same Namespace. A Namespace is not an automatic collision resolver; uniqueness of final Archive roots is validated by the final-archive-root uniqueness rule in Archive planning.

level: MAY
