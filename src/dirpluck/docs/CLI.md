# dirpluck CLI Quick Reference

This is the compact CLI reference included in the wheel.

```text
dirpluck [TARGET ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
dirpluck --configs
dirpluck --version
```

- Supply one or more positional `TARGET` arguments when the Effective Configuration has a Target. Supply none when it has no Target.
- `project` resolves as `cwd/project`; `work/project` resolves from the named `work` location when that location exists. `./work/project` explicitly requests cwd-relative resolution.
- `work/` expands all direct child directories of the named `work` location into Targets. If that location is undefined, the command fails instead of falling back to cwd.
- `--config NAME` selects a Configuration filename from the current working directory or `./dirpluck/`; `.toml` may be omitted.
- `--case NAME` selects one named Case.
- `--dry-run` prints the planned ZIP contents without writing an archive.
- `--paths` adds resolved source filesystem paths to the generated Archive README. Paths are omitted by default.
- `--sequence N` supplies an explicit positive sequence number for a generated output name. It is not automatic numbering.
- `--configs` lists Configurations discoverable from the current working directory and exits.

```console
dirpluck projects/example --dry-run
dirpluck work/example --case audit
dirpluck work/
dirpluck --config snapshot
```

For the compact TOML reference, see the bundled `CONFIGURATION.md`; for the trust model, see the bundled `TRUST.md`. For detailed CLI semantics, the Configuration guide, the Glossary, and the Specification, see `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, and `docs/SPECIFICATION.md` in the source distribution for the same release.
