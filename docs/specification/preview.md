# Preview

## SPEC_145

`--preview` uses the same base-chain resolution, cycle detection, definition composition, Scope lookup and expansion, Target direct-child resolution and Scope-ignore filtering, Case selection, file selection, and archive planning as a normal run, but does not create or modify output files or directories. It can be used when the Root Configuration has no Output declaration. Because preview does not resolve or write an Output, `--preview` cannot be combined with `--here`, `--output`, `--force`, or `--sequence`. `--archive-mtime` is still validated in preview mode, but no Archive is written, so it does not affect the preview result.

level: MUST

condition: when `--preview` is used

related: [SPEC_028](composition.md#spec_028), [SPEC_037](runtime-targets.md#spec_037), [SPEC_065](selection.md#spec_065), [SPEC_098](archive.md#spec_098), [SPEC_107](output.md#spec_107)

## SPEC_146

A missing ordinary `must` path pattern is displayed as `[missing]`; a missing ordinary `may` path pattern is displayed as `[optional missing]`. A non-path Selection expression such as `{ match = "..." }` is displayed as an opaque unmatched Selection entry rather than being split into path components even when its expression contains `/`. A final Selection containing zero files is displayed as either `empty, allowed` or `empty, would error` according to policy. If an opposite-type entry exists for a `must` or `may` string pattern, preview preserves the normal missing / optional-missing Selection semantics and also records a source-labelled non-fatal type-marker diagnostic. CLI `--preview` prints it as a warning to stderr; Python API `preview=True` returns it in `RunResult.warnings`.

level: MUST

condition: when displaying Selection results in `--preview`

## SPEC_147

Configuration and planning errors remain errors in preview mode, including an invalid base path, base cycle, duplicate effective Scope root, an unavailable Scope root that is actually used, unknown Scope, invalid Target reference, Target outside the direct-child boundary, unresolved Shared reference, invalid source path, Case inconsistency, and Output schema or base-chain write-boundary conflict. An unused named Scope root being currently unavailable is not by itself an error. Base depth itself is not an error or warning.

level: MUST

condition: when `--preview` detects a configuration or planning error
