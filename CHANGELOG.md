# dirpluck CHANGELOG

Release history for dirpluck from 0.10.0 onward. Earlier releases are available in the [Changelog Archive](docs/changelog/INDEX.md).

## 0.16.0

0.15.0 was not published. This release folds in the public changes planned for that version and combines the Always / Case / targetless-run contract updates with a substantial reorganization of the internal execution pipeline.

### Added

- Add Always Case as `[case.always.<name>]`. It filters the effective Always-source set with mutually exclusive `include` or `exclude`; `include = []` explicitly selects no Always sources, while `exclude = []` and omitting both fields keep all sources. References use TOML Always identifiers and are validated after effective Base composition.
- Allow positional Target references to be omitted unconditionally and treat a zero-source result as a valid execution. A targetless run does not use Pluck for source selection; it resolves Always sources when present, and otherwise produces a README-only Archive. The CLI reports the zero-source result as ordinary informational output rather than a warning, while the Python API exposes it through `RunResult.archive_entries == ("README.md",)` and the generated README note. A targetless Pluck-only run may select a defined Pluck Case and still produce zero sources; undefined Case names remain errors. This expands previously invalid input into supported use cases and is treated as a backward-compatible feature addition.
- From 0.16.0 through the final pre-1.0 release, compare the valid 0.14.x Always Archive identity with the 0.16.x effective Always name and report public `AlwaysMigrationWarning` only for sources whose Archive root actually changes. The warning includes both the old and new roots. Python API callers receive it through the standard warnings framework, while the CLI renders the same diagnostic to stderr. Always sources whose old and new identities match do not receive a layout warning. Namespace use reports its 1.0 removal independently of the layout comparison. The 0.16 Migration Guide shows before/after examples for the old `path` / Namespace placement and the new Always-name-based placement.

### Changed

- **Compatibility policy:** Withdraw the pre-1.0 policy introduced after 0.10.0 that generally avoided breaking changes to the published surface. Real-world use has shown that core design still needs correction before 1.0, so the remaining 0.x series is a design-convergence period in which necessary breaking changes are permitted. Deprecation, migration warnings, and Migration Guides should be provided where useful, but legacy design will not be frozen solely for compatibility. The stable compatibility contract begins at 1.0.0.
- **Release numbering:** Do not publish 0.15.0. Fold the changes planned for it into 0.16.0. Upgrading from 0.14.x uses `docs/migration/0.16.md`; there is no need to pass through 0.15.0.
- **Internal architecture:** Reorganize execution into three explicit stages: interpretation and normalization of CLI / Configuration / Invocation input, extraction of concrete data from the filesystem, and Archive / message output. Input-language concepts such as Base, Shared, Namespace, Case, and Target grammar are consumed as far as practical during normalization; extraction operates on typed Target / Selection / fixed-source requests and filesystem semantics. Archive planning is separated from ZIP writing so the writer receives only a finalized payload. Canonical CLI / Configuration / Invocation grammar and the selection / Archive semantics not explicitly changed below are preserved.
- **Specification / test structure:** Remove normative Specification text that fixed internal objects, processing phases, or concrete algorithms, and separate public contract, pre-1.0 compatibility, and implementation invariants. Reorganize tests into public-contract, 0.x-compatibility, internal-characterization, and architecture-invariant groups so replacing internals does not accidentally freeze obsolete architecture as public behavior.
- Allow different Scopes to resolve to the same filesystem directory. Scope names provide explicit disambiguation, so duplicate physical roots are no longer Configuration errors by themselves; actual duplicate sources and Archive-path collisions are handled by the normal Target / Archive-planning rules.
- Remove Base-chain validation that rejected a Configuration solely because inactive Output definitions had overlapping write boundaries. Only the root Configuration's Output is active for a run; safety checks apply to that active Output and the actual input / Archive interaction.
- **Breaking:** Make `<name>` in `[always.<name>]` the final Archive directory identity for that Always source. `path` now identifies only the filesystem source directory / Selection root; its basename and its lexical path relative to the Configuration file no longer affect Archive placement. For example, `[always.docs] path = "../external/documentation"` places selected files under `docs/`, preserving only paths relative to the selected source directory beneath that root. Always names are interpreted as TOML keys and then as single Archive directory components; dirpluck does not independently apply host-OS-specific reserved-name or filename rules.
- Treat `[always.<name>].namespace` as pre-1.0 compatibility during the remaining 0.x series starting with 0.16.x. The referenced Namespace name replaces `<name>` as the effective Always name before placement. The former `NAMESPACE/SOURCE_ROOT` prefix behavior for Always sources is not used. Using an Always Namespace reports public `AlwaysMigrationWarning` (and the corresponding CLI warning), stating that the field is removed in 1.0.0 and that the desired Archive directory name should instead be written directly in `[always.<name>]`. Unknown Namespace references remain Configuration errors.
- Treat final Archive roots as destination-region identities. Target/Target and Always/Always roots remain unique under a case-insensitive comparison. A Target and an Always source may share an exactly identical spelling as intentional composition into one destination region, while a case-only mismatch such as Target `App` and Always `app` remains invalid. Actual entry collisions inside a shared region are still detected by the Archive planner.
- Clarify that Always `path` must resolve to a concrete directory and that directory is the Selection boundary. Because Archive identity no longer depends on deriving a source-root name from the source location, remove the old restriction that rejected the filesystem root solely because no source-root name could be derived. Selection traversal rules for link-like and special entries are unchanged.
- **Breaking grammar change with migration path:** Move the canonical Pluck Case syntax from `[pluck.case.<name>]` to `[case.pluck.<name>]`. From 0.16.0 through releases before 1.0.0, legacy `[pluck.case.<name>]` remains accepted with identical semantics and reports public `ConfigurationDeprecationWarning` (rendered by the CLI as a stderr migration notice). Defining the same Case name with both syntaxes in one Configuration document is invalid. Legacy syntax is removed in 1.0.0.
- Change the runtime Case selector to independent Pluck and Always axes. `--case PLUCK` selects only a Pluck Case, `--case .ALWAYS` only an Always Case, and `--case PLUCK.ALWAYS` both. CLI, `dirpluck.run(case=...)`, and the Invocation `case` field share this grammar. A defined Case may validly result in zero sources and a README-only Archive.
- Remove the previous portable-name guarantee for Archive directory identities. dirpluck validates only the Archive structure it owns and does not emulate OS-specific reserved names, trailing-dot rules, Unicode normalization, or similar extraction constraints. Users moving Archives across operating systems or filesystems are responsible for choosing compatible names. Archive directory identities still reject `/` and `\` as path separators and reject ASCII control characters U+0000 through U+001F plus U+007F, because those are Archive-path safety constraints rather than host-OS naming policy.
- Reorganize the generated Archive README. Always sources are listed before all Targets, and each source description now appears before `Files`, `Source`, and overlap metadata. Targets are grouped by Scope; directory Targets are listed under a Pluck group so Scope / Pluck descriptions are not repeated for every Target in the same Scope, while file Targets remain directly under the Scope because they do not use Pluck. The README also explains that `Scope: "..."` identifies only a Target selection range and does not imply priority, importance, or hierarchy; any additional meaning belongs in the Scope `description`. This is a human-facing README presentation/context change and does not change Selection semantics, Archive entry paths, or the machine-readable CLI / Python API contracts.

### Fixed

- Restore rejection of ASCII control characters and backslashes in Archive directory identities. U+0000 through U+001F and U+007F are rejected to prevent ZIP entry-name truncation and broken warning / preview output, and `\` is rejected alongside `/` because it may be interpreted as a path separator. This is an Archive-path safety rule, not an attempt to emulate host-OS reserved-name policy.
- Normalize `OSError` from whole-Scope directory enumeration and from writing generated `README.md` / empty-directory ZIP entries into `SelectionError`, matching other filesystem and Archive I/O failures. The CLI reports these failures as normal `dirpluck: error:` diagnostics instead of tracebacks and leaves no incomplete Output or temporary output behind.

## 0.14.1

Bring the source tree into conformance with the existing Ruff and basedpyright static-analysis policies as a maintenance release. Runtime behavior, the official Python API, CLI, Configuration language, and Archive semantics are unchanged.

### Changed

- Resolve the existing Ruff findings across source, tests, documentation canonical sources, and repository tooling. Normalize blank-line layout and remove unused imports, make the `TargetIgnorePattern` type-annotation import explicit, and place the canonical-document renderer's third-party import in the normal module import block. Also resolve basedpyright error diagnostics, explicitly analyze against Python 3.11, make repository-local test-helper imports package-qualified under `tests.*`, make the recursive archive-tree type and internal builder imports explicit, and narrow Optional / union types in tests while keeping intentional invalid-type runtime-validation cases localized. This is a static-analysis maintenance refactor and does not change runtime behavior, the official Python API, CLI, Configuration language, or Archive semantics.
- Define basedpyright warning policy by repository use case, add `src` to the analysis path, and limit diagnostic overrides to intentional patterns such as the declarative documentation DSL, side-effect-only test calls, and package-internal private helpers. Eliminate the remaining warnings by containing `Any` / `Unknown` at TOML, JSON, and `argparse` boundaries with `object` plus explicit narrowing / casts; modernize deprecated typing imports; make string-literal concatenation and validation-only discarded return values explicit; and annotate test helpers. Remove the unreferenced internal `_resolve_target_both` helper as dead code. These changes clarify typing and repository-local validation only and do not change runtime behavior or the public contract.
- Split the growing CHANGELOG according to the shikumi-devdoc document-collection model. Keep `CHANGELOG.md` at the repository root as the stable public entry point for releases from 0.10.0 onward, and move 0.9.x plus 0.1.0 through 0.8.0 into an archive collection under `docs/changelog/`. Generate the archive `INDEX.md` from each canonical source's `order` / `summary` metadata, and ship the same archive through the public `docs/` tree bundled in the wheel.
- Split the Effective Configuration implementation by processing phase instead of leaving Target resolution, Configuration composition, and final source orchestration in one `_effective.py` module. Move Target / Scope references and selector resolution to `_target_resolution.py`, move base/shared/namespace composition plus Scope-root and Output-boundary validation to `_configuration_composition.py`, and keep request/case/Always handling plus final `ResolvedSource` orchestration in `_effective.py`. The new private modules expose only their cross-module internal interfaces by non-underscore names; this does not expand dirpluck's official Python API or change Target resolution, Configuration composition, or Archive semantics.
- Adopt Ruff formatter as the repository's official Python formatter, using `line-length = 100` and applying formatting to `src/`, `tests/`, and `tools/`. Canonical sources remain outside the formatter scope because they are a documentation DSL whose raw document indentation can be meaningful, while `ruff check .` continues to lint them. CI and the local release check now enforce `ruff format --check src tests tools`, and the formatter version is pinned in the quality dependency group.
- Consolidate the GitHub Actions quality gate in reusable `.github/workflows/checks.yml`. The shared checks run Ruff formatting, Ruff lint, basedpyright, canonical-document drift validation, and the Python 3.11 through 3.14 `unittest` matrix, with Python 3.13 also verifying compatibility with the legacy `discover -s tests` form. Normal CI combines those shared checks with distribution build/metadata/content verification, while the release workflow verifies the release tag against the dynamic package version first, then reuses the same checks against that tag before building, smoke-testing, and publishing the artifact through PyPI Trusted Publishing. `tools/check_release.py` now reproduces the same format/lint/type/test/document gate locally.

### Fixed

- Align repository-local test-helper imports with `tests` being a package by using `tests._temp`, `tests._builder_support`, and `tests._config_support`. Both `python -m unittest discover -s tests` and `python -m unittest discover -s tests -t .` now execute the same suite. Remove the helper-only `[tool.pytest.ini_options] pythonpath = ["tests"]` setting and the corresponding basedpyright `tests` extra path because package-qualified imports no longer require them.

## 0.14.0

Move Selection reference syntax to explicit structured inline tables, while keeping the legacy one-element nested-array forms as deprecated compatibility input.

### Added

- Add `{ shared = "name" }` inline tables for Shared references in `must` and `may`, and use the same form in `ignore`. The containing field continues to determine the reference namespace as `shared.must`, `shared.may`, or `shared.ignore`. Shared-reference resolution timing and rebinding after base composition are unchanged.
- Add `{ path = "relative/path" }` inline tables for concrete Selection-relative paths in `ignore`. `path` is restricted to a relative path from the Selection root; absolute paths, `..`, globs, and backslashes are rejected. A leading `./` and `.` path components are normalized, so `{ path = "foo" }` and `{ path = "./foo" }` identify the same path. Trailing-`/` directory-only semantics and subtree pruning remain the same as for the legacy concrete path reference.
- Add GitHub Actions CI and release workflows. CI runs a Python 3.11 through 3.14 test matrix, canonical-document drift checks, wheel / sdist builds, and distribution metadata / content validation for pushes and pull requests targeting `main`. Publishing a GitHub Release verifies the release tag against the package version, reruns canonical checks and the test suite on Python 3.13, builds and verifies the distributions, smoke-tests the built wheel in an isolated environment, and publishes that same artifact set through PyPI Trusted Publishing. Add a `.[test]` optional dependency so CI and local development can install the same documentation-validation dependency.

### Changed

- Deprecate one-element nested-array Shared references (`["name"]`) and concrete `ignore` path references (`["./path"]`) starting in 0.14.0, and remove them in 1.0.0. From 0.14.0 through releases before 1.0.0, they remain accepted as compatibility input, but the CLI prints one warning to stderr per loaded Configuration file that uses the legacy syntax, including files loaded through the base chain. The warning points to `{ shared = "..." }` / `{ path = "..." }`, states the 1.0.0 removal, and does not change stdout or the exit status.
- The official Python API `dirpluck.run()` now reports deprecated nested-array Configuration syntax through Python's standard warnings framework, emitting one public `ConfigurationDeprecationWarning` (`FutureWarning` subclass) per affected loaded Configuration file, including files from the base chain. The warning is visible under Python's default filters and is attributed to the first caller frame outside the dirpluck package rather than to a fixed `stacklevel`. Configuration-syntax lifecycle warnings remain separate from planning diagnostics and are therefore not included in `RunResult.warnings`. The CLI continues to render the same diagnostic directly to stderr and does not emit an additional Python warning.
- Publish the source repository at `https://github.com/minoru-jp/dirpluck` in package metadata and documentation navigation. Root README documentation links now use absolute URLs to files on the GitHub `main` branch so they also resolve from the PyPI project description. Add Homepage, Documentation, Repository, Issues, and Changelog entries under `[project.urls]`, and update the STATUS distribution note for the public-repository state.

### Fixed

- Add `[tool.pytest.ini_options] pythonpath = ["tests"]` to `pyproject.toml` so running `pytest` directly from an editable-installed source checkout can collect repository-local helpers such as `tests/_temp.py`. The official CI runner remains `unittest`.

## 0.13.1

Migrate the published-document canonical sources to the merge-policy model in shikumi-devdoc 0.3.2, and synchronize the documentation-generation dependency and version snapshot. Runtime behavior, the official Python API, CLI, Configuration language, and Archive semantics are unchanged.

### Changed

- Migrate published-document canonical sources from the deprecated `placeholders` policy to shikumi-devdoc 0.3.2 `merge_policy`. Self-contained documents that must not depend on external context use `merge_policy="local"`, while the CHANGELOG, as a historical snapshot, uses `merge_policy="forbidden"`. This makes the intended merge boundaries explicit without changing document content.
- Update the documentation-generation dependency to `shikumi-devdoc>=0.3.2`, and synchronize `dirpluck.__version__`, the documentation-generation context, and the published README current-version snapshot to `0.13.1`. This release updates repository-local documentation tooling and release metadata only; it makes no functional changes to runtime behavior, the official Python API, CLI, Configuration language, or Archive semantics.

## 0.13.0

Allow a Scope to expose directory and file Targets together, generalize Target selectors across all Target kinds, and add structured full-path regular-expression matching to Selection.

### Added

- Add `target_kind = "both"` to `[scope]` and `[scope.<name>]`. Both mode exposes eligible direct-child regular directories and regular files as Target candidates. Directory Targets use the effective Pluck Selection, while file Targets remain atomic sources. A both-kind Scope may still select files without a Pluck, but resolving any directory Target requires Pluck.
- Add `{ match = "..." }` structured Selection entries to `must`, `may`, `ignore`, and Shared pattern sets. `match` applies a Python-compatible regular expression with full-match semantics to complete root-relative POSIX-style paths below the Selection root. Regular-directory paths carry a trailing `/`, regular-file paths do not, expressions must be non-empty and at most 512 characters, and invalid regular expressions are Configuration errors.
- Structured `must` / `may` matches can select both files and directories; a matching directory behaves like an ordinary directory leaf and collects its subtree. Structured `ignore` matches exclude files and prune matching directory subtrees. If ordinary string patterns, Shared expansion, and structured matches select the same file, the final Selection contains it only once.

### Changed

- Generalize `:[...]` / `SCOPE:[...]` and `:<...>` / `SCOPE:<...>` from file Target selectors to Target selectors available with `target_kind = "directory"`, `"file"`, or `"both"`. List selectors are typed literal Target lists, while regular-expression selectors full-match normalized eligible direct-child Target names: files are `NAME`, directories are `NAME/`.
- Treat `target_kind` as the type filter for direct-child Target candidates. Scope expansion, literal Target resolution, list selectors, and regular-expression selectors share the same type filter, Scope `ignore`, and link-like-entry exclusion. In `both` mode, each resolved Target retains its actual directory/file kind for downstream processing.
- Keep ordinary Selection string patterns as the existing restricted guided-traversal grammar, while structured `match` provides the more expressive full-path regular-expression form. Implementations may scan the Selection root for `match` candidates rather than inferring a guided traversal plan from the regular expression.
- Keep `ignore` intentionally broad: ordinary Selection ignore strings, concrete ignore path references, and Scope ignore patterns without a trailing `/` exclude matching files and directories; a trailing `/` narrows the exclusion to directories only. This preserves the broad exclusion behavior while inclusion-side references become type-explicit. Use structured `{ match = "..." }` when a file-only ignore is required.
- **Breaking:** Make file-versus-directory type explicit for inclusion and Target references. Ordinary `must` / `may` strings, literal Target references, and Target-list items now use no trailing `/` for files and a trailing `/` for directories; dirpluck no longer infers the type from the current filesystem for those references. Migrate directory Selection entries such as `must = ["src"]` to `must = ["src/"]`, and named-Scope directory Targets such as `work/project` to `work/project/`.
- **Breaking:** Add `./NAME/` as the literal form for a default-Scope directory Target because `NAME/` remains reserved for named-Scope expansion. `NAME` / `./NAME` denote default-Scope files. Target lists use `/` both as the item separator and as the directory marker, so a non-final directory item appears as `NAME//NEXT`; three or more consecutive `/` characters are invalid.
- Regular-expression Target selectors now match files as `NAME` and directories as `NAME/`; `/` is therefore allowed in the expression. `<repo>` selects a file, `<repo/>` a directory, and `<repo/?>` can select either. Selector discovery remains limited to direct children of the Scope, so `/` in the expression does not enable recursive traversal.

### Fixed

- Improve strict entry-type migration diagnostics. If a `may` string pattern requests one type but matches only a non-ignored regular entry of the opposite type, it remains optional missing and dirpluck records a source-labelled warning suggesting the relevant trailing-`/` adjustment. A `must` mismatch keeps its normal unsatisfied error during a build, while `--preview` leaves it missing and records the same hint as a warning. The CLI prints these warnings to stderr in normal builds and `--preview`; the official Python API returns the same messages in `RunResult.warnings`. Warnings from different sources remain distinct because they include the source label, and Selection errors now use `source: detail` wording. Existing literal-Target errors keep the same type-marker hint.
- Fix `--preview` rendering for unmatched structured `{ match = "..." }` expressions containing `/`. Such expressions are displayed as opaque unmatched Selection entries instead of being split into a fake directory tree.

## 0.12.0

Add selector syntax to file-kind Scope Target references so direct-child regular files can be selected either by explicit name lists or by regular expressions. Existing literal Target references and whole-Scope expansion keep their previous meanings.

### Added

- Add file Target selectors for Scopes with `target_kind = "file"`. `SCOPE:[name-a/name-b]` / `:[name-a/name-b]` are `/`-separated literal file-name lists, while `SCOPE:<regex>` / `:<regex>` are regular-expression selectors applied to the complete eligible direct-child file name. Selector syntax is valid only for file-kind Scopes; using it with a directory-kind Scope is an error.
- Regular-expression selectors use Python-compatible regular expressions with `fullmatch` semantics. A pattern must be non-empty, contain no `/`, and be at most 512 characters. Invalid regular expressions and zero-match selectors are errors. Selection is applied only after the Scope's `target_kind`, `ignore`, and link-like-entry rules determine the eligible file Targets.

### Changed

- When a file selector overlaps an existing literal Target reference or another selector and resolves the same filesystem entry, that selector overlap is collapsed to one Target. Existing distinct-entry validation is preserved when only literal Target references duplicate the same entry. CLI arguments and `.dirpluck-inv` `targets` use the same selector grammar. Quote selector references in a shell so `[]`, `<>`, and regular-expression metacharacters are not interpreted by the shell.

## 0.11.1

Simplify the generated Archive README by removing auxiliary Namespace / Source-root metadata that can already be inferred from the final Archive path. Namespace placement semantics are unchanged.

### Changed

- Remove the Namespace explanatory paragraph and the per-source `Namespace` / `Source root` metadata from the generated Archive README. Namespaced sources still use their final Archive root as the section heading, and Namespace continues to affect Archive placement exactly as before. This is a human-facing README format change; Configuration, CLI, the official Python API, and Archive-entry path semantics are unchanged. Consumers that parse the README's exact formatting may need to adjust.

## 0.11.0

Add an opt-in Scope mode for treating direct-child regular files as atomic Targets. This supports workflows such as collecting several returned ZIP archives together with existing Always sources without unpacking those archives first, while preserving the directory-only behavior of existing Scopes by default.

### Added

- Add Scope `target_kind = "directory" | "file"`. The default remains `"directory"`, so existing Configurations keep their previous Target discovery and `SCOPE/` expansion behavior. A file-kind Scope exposes only eligible direct-child regular files as Targets; directories, link-like entries, and other special filesystem entries are not file Targets.
- Add optional Scope `description` metadata. For directory Targets, the generated Archive README shows the Scope description before the Pluck description. For file Targets, each atomic file receives its own README section and shows the Scope description without a Pluck description.

### Changed

- Clarify Pluck as content Selection for directory Targets. File Targets bypass Pluck and are included as atomic files, so a Configuration without Pluck may still accept positional Target references from file-kind Scopes. Directory Targets continue to require Pluck.
- Apply the existing Scope Namespace mechanism to file Targets. A file Target uses its file name as the source root, or `NAMESPACE/FILENAME` when the Scope references a Namespace.
- Extend Scope `ignore` and `SCOPE/` expansion according to the active Target kind. Directory mode retains the existing direct-child-directory behavior; file mode applies the same candidate-name policy to direct-child regular files.

## 0.10.2

Clarify the responsibilities of the release artifacts and standardize the build backend on Hatchling. The wheel provides the implementation and the complete published documentation set, while the sdist provides the complete source needed to rebuild and validate the release.

### Changed

- Migrate the build backend from setuptools to Hatchling. `dirpluck.__version__` remains the version source of truth and Hatchling reads it for project metadata. Remove the setuptools-specific `MANIFEST.in` and generated `*.egg-info` from the distribution design.
- Remove the compact documentation channel that existed only for wheels. Delete `src/dirpluck/docs/`, `canonical_sources/package_cli/`, `canonical_sources/package_configuration/`, `canonical_sources/package_trust/`, and the independent `canonical_documents/package/` publication channel so the published documentation no longer has to be maintained in two forms.
- Bundle the repository's published `README.md`, `GLOSSARY.md`, `CHANGELOG.md`, `STATUS.md`, and the complete `docs/` tree under `dirpluck/_docs/` in the wheel, in addition to the implementation. CLI, Configuration, Python API, Trust, Specification, and Glossary documentation can therefore be read from the wheel for the same release.
- Change the sdist from an explicitly enumerated set of directories to the complete release source selected with VCS ignore rules. It includes `tests/`, `tools/`, `devdocs/`, published documentation, and the implementation, while repository-operation-only `.github/` content is excluded.

## 0.10.1

Synchronize release metadata and published documentation for the 0.10.1 release while preserving the runtime behavior and public API / Configuration semantics of 0.10.0.

### Changed

- Update the package version and documentation current-version snapshot to 0.10.1. This release makes no functional changes to runtime behavior, the official Python API, CLI, Configuration language, or Archive semantics.
- Align release-preparation documentation with the current shikumi / shikumi-devdoc baseline, including the STATUS documentation-tooling wording for the release baseline of Shikumi 0.2.0 and shikumi-devdoc 0.3.0.

## 0.10.0

Allow the runtime to choose the Output destination and overwrite policy so a Configuration's extraction definition can be reused while changing where an invocation writes its Archive.

### Added

- Add CLI `--here[=FILENAME]`, `-o PATH` / `--output PATH`, and `-f` / `--force`. `--here` uses the runtime cwd, while `--output` supplies an explicit path resolved from the runtime cwd. A trailing `/` on `--output` selects a directory and generates a timestamp filename. `--here=FILENAME` accepts only a filename directly under the cwd; use `--output` when a path is needed.
- Add `output` and `force` to the official Python `run()` API. `output` follows the same path semantics as CLI `--output`: a trailing `/` generates an automatic timestamp filename in that directory, while a path without trailing `/` is an exact output file path. Relative `output` values are resolved from the API `cwd`.

### Changed

- A build with Runtime Output no longer requires an Output declaration on the Root Configuration. Exact Runtime Output keeps the supplied filename unchanged. Automatic Runtime Output reuses the Root Configuration's `[output.timestamp]` `prefix` / `suffix` naming rule when one is declared; otherwise the default name is `dirpluck-YYYYMMDD-HHMMSS.zip`. The configured output directory or fixed path is not carried into the runtime destination.
- Extend `--sequence N` to automatic timestamp filenames produced by `--here` and trailing-`/` Runtime Output in addition to Configuration timestamp Output. Using a sequence with an exact Runtime Output is an error. Generated-name collisions do not trigger automatic numbering, renaming, or a new timestamp sample.
- Runtime Output defaults to no-overwrite. `--force` / `force=True` makes the effective Output overwriteable and applies to both Runtime Output and Configuration fixed / timestamp Output. Runtime Output paths use `/` separators on every OS, matching Configuration path notation, and reject backslashes.
- Reject `--preview` / `preview=True` when combined with Runtime Output (`--here`, `--output`, or `output=`), overwrite forcing (`--force` / `force=True`), or `--sequence`. Preview does not resolve or write an Output, so these runtime Output modifiers are no longer silently ignored.
- Reorganize the public documentation by moving the end-to-end README example to `docs/GETTING_STARTED.md` and replacing the single `docs/CONFIGURATION.md` with a collection rooted at `docs/configuration/INDEX.md`. The collection separates overview, sources, selection, base composition, Output, and a complete example, while the compact wheel-bundled `dirpluck/docs/CONFIGURATION.md` remains a single quick reference.
- Split the CLI guide from the single `docs/CLI.md` into a collection rooted at `docs/cli/INDEX.md`, separating basic operation, Invocation Templates, Target / Case operation, and preview / runtime Output. Keep the wheel-bundled `dirpluck/docs/CLI.md` as a compact quick reference. Public collection `INDEX.md` files now stay limited to translations of the canonical indexes generated by shikumi-devdoc; explanatory navigation lives in canonical `overview.md` documents instead.
- Remove legacy numbered-section references left over from the former monolithic Specification. Cross-references now name the relevant normative area, such as Filesystem path notation, Runtime Target, Archive planning, or Output. Genuine rule dependencies are retained in `related` metadata where they do not create circular imports, and a regression test rejects reintroduction of numbered section references.
- Synchronize the development-document canonical sources with the current shikumi-devdoc 0.3.0 authoring contract. Nested titles now use `title @= ...` instead of `@title(...)`; every canonical source declares `heading="title"` or `heading="identity"`; document fragments intended for direct verification by ordinary tests use presentation-neutral `test_target_field` values with Markdown fences kept in docstrings; Vocabulary terms are public in the Glossary by default; and the Specification uses identity headings so semantic references remain stable across title and Vocabulary changes.
