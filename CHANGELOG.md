# dirpluck CHANGELOG

Release-by-release changes for dirpluck.

## 0.1.0

First public release.

### Added

- Rework `README.md` around concrete use cases and the value of repeatable file sets, move TOML authoring guidance into `CONFIGURATION.md`, and keep exact operational semantics in `SPECIFICATION.md`.
- Keep the Archive-root `README.md` as a purpose-neutral index: fixed wording does not identify the generating tool or prescribe downstream use, while Target and Companion `description` values carry concrete purpose.
- Add fixed and generated Output forms. Generated Output uses `directory`, `timestamp = true`, optional `prefix` / `suffix`, and optional CLI `--sequence N` to produce `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip`; existing destinations are rejected during normal execution, with no auto-numbering, auto-renaming, or overwrite mode. Asynchronous and parallel invocations are not coordinated, so callers must avoid concurrent writes to the same output path.
- Clarify in `README.md` and `CONFIGURATION.md` that selecting a directory recursively collects its contents and that dirpluck does not infer or automatically exclude secret-like files such as `.env`, private keys, or `.git`; broad selections require explicit exclusions appropriate to the workspace.
- Define the CLI as the supported public interface; package-internal Python modules and functions are not yet a compatibility-guaranteed public API.
- Treat one Configuration file as one extraction intent, producing a ZIP Archive from an optional runtime-bound Target definition and/or one or more fixed Companions, plus one required Output definition. When a Target is defined, one or more CLI directory arguments may instantiate that same Target rule in one run; TOML still defines only one Target rule. A Configuration with no Target runs without positional directories, while supplying any to such a Configuration is an error.
- Generalize Case as one flat, Configuration-wide selection variation. Target and Companion Case selections are complete alternatives with no inheritance or merge. When a Target exists it must define the selected Case; Companions with the same Case use it and other Companions fall back to base. Without a Target, a Case is valid when at least one Companion defines it. Cases cannot be combined or nested, and they never change source membership, Companion paths, or Output policy.
- Select fixed-depth relative paths with `include` and `include_if_exists`, allowing at most one `*` per path element. `include` requires at least one match per pattern, while `include_if_exists` permits zero matches. Recursive-anywhere `**` search is not provided.
- Filter selected file or directory names with `exclude` using limited exact, prefix, suffix, and contains matching.
- Default `if_empty` to `error`, while allowing optional-only Target or Companion selections to use `if_empty = "allow"`. Allowed empty selections can be preserved as explicit empty directories in the Archive.
- Preview planned Archive contents with `--dry-run`. Missing required includes are shown as `[missing]`, optional misses as `[optional missing]`, and empty-result policy is reported without creating a ZIP.
- Restrict processing to the current working directory, reject symbolic-link escapes, and allow the Target to be the cwd itself while still preserving the cwd's actual directory name in the Archive.
- Require `description` on every Target or Companion selection, including named Cases, and generate an Archive-root README. When multiple purposes resolve to the same actual directory, files are unioned by real path and the README records each declared purpose.
- Support Python 3.11 and later, distribute dirpluck under the MIT License, and keep runtime third-party dependencies at zero.
- Define PyPI distribution boundaries explicitly: the wheel ships executable code plus the public `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md`, while the sdist additionally includes tests and public source documents. `_internal/` and `.github/` remain repository-only development infrastructure.
- Simplify the normal CLI form to `dirpluck DIRECTORY [DIRECTORY ...]` and remove the `build` subcommand. Discover Configurations only from the cwd and `./dirpluck/`: the default searches for `dirpluck.toml`, while `--config NAME` searches for the same named TOML in both locations. Multiple matches are rejected as ambiguous, and `--configs` lists discoverable candidates and conflicts.
