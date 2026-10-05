# Pre-1.0 compatibility

The rules in this document define only compatibility inputs and behaviors for the current 0.x series. They are not canonical input semantics; they exist to provide a migration period to the stated replacements, and all are removed in 1.0.0.

## SECTION_1301

title: Deprecated Selection references

### SPEC_068

From 0.14.0 until 1.0.0, the legacy one-element nested-array Shared reference (`["name"]`) and the one-element nested-array path reference beginning with `./` in `ignore` (`["./path"]`) are accepted as compatibility inputs but are deprecated. New Configurations use `{ shared = "..." }` / `{ path = "..." }`. For the CLI, each loaded Configuration file that contains one or more valid deprecated nested-array references produces one warning on stderr for that file, stating that the syntax is removed in 1.0.0 and naming the replacement syntax. The official Python API `dirpluck.run()` reports the same diagnostic once per loaded Configuration file through Python's warnings framework as the public `ConfigurationDeprecationWarning` (`FutureWarning` subclass), and does not include it in `RunResult.warnings`. The warning is visible under Python's default filters, and its location is attributed to the first caller frame outside the dirpluck package rather than to a fixed `stacklevel`. Base-chain Configurations count as loaded Configurations in the same way. Because the CLI collects the same diagnostic for stderr display, it does not additionally emit `ConfigurationDeprecationWarning`. These warnings do not change CLI stdout or exit status. In 1.0.0, deprecated nested-array references are removed from Configuration syntax and become invalid. During the compatibility period, a nested array is recognized only when it contains exactly one non-empty string; `[]`, `["foo", "bar"]`, and `[123]` are errors.

level: MUST

## SECTION_1302

title: Legacy Pluck Case syntax

### SPEC_170

From 0.16.0 until 1.0.0, legacy `[pluck.case.<name>]` is accepted as a compatibility form of canonical `[case.pluck.<name>]`, with identical Base-composition and runtime Case semantics. A `ConfigurationDeprecationWarning` directs users to `[case.pluck.<name>]`. If the same Case name is defined in both legacy and canonical form in one Configuration document, there is no precedence rule and the Configuration is an error. The legacy syntax is removed in 1.0.0. Always Case has no legacy alias and is accepted only as `[case.always.<name>]`.

level: MUST

## SECTION_1303

title: Always Namespace compatibility

### SPEC_064

From 0.16.0 until 1.0.0, an optional `namespace` field on an Always source is accepted as pre-1.0 compatibility and references an effective `[namespace.<name>]`. It does not use Scope prefix semantics. Instead, the Namespace name replaces the `<name>` from `[always.<name>]` as the effective Always name used for the final Archive root. The source filesystem path and Selection boundary are unchanged. An unknown Namespace reference is a Configuration error, and the resulting final Archive root follows the ordinary Archive identity and collision rules. The canonical replacement is to write the required Archive directory name directly as the `<name>` in `[always.<name>]`. In 1.0.0, the `namespace` field is removed from the Always-source schema and a Configuration that specifies it is invalid.

level: MUST

### SPEC_167

From 0.16.0 until 1.0.0, a Configuration that uses Always `namespace` reports `AlwaysMigrationWarning`, explaining that the field is removed in 1.0.0 and that the replacement is to write the Archive directory name directly in `[always.<name>]`. This warning is reported independently of any layout-migration warning. In 1.0.0, both acceptance of Always `namespace` and this migration warning are removed.

level: MUST
