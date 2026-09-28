# Package surface

The official package-root exports for 0.13.x are exactly:

```python
from dirpluck import DirpluckError, RunResult, __version__, run
```

`dirpluck.builder`, `dirpluck.config`, `dirpluck.invocation`, underscore-prefixed modules, and models or helpers importable from those modules are not official API. Code that depends on them may need changes as internal refactoring continues during Beta.

Keeping the official surface deliberately small provides the same high-level capability as the CLI while preserving room to change Configuration models and archive-planning internals later.

## What to read next

In the repository or source distribution, use these published documents:

- CLI arguments and human-readable output: `docs/cli/INDEX.md`
- Writing Configurations: `docs/configuration/INDEX.md`
- Exact Configuration, Target, Case, traversal, Archive, and Output semantics: `docs/specification/INDEX.md`
- Trust boundaries for filesystem operations and distribution: `docs/TRUST.md`
- Term meanings: `GLOSSARY.md`

The wheel also bundles the same complete published documentation set under `dirpluck/_docs/`. An installed wheel therefore provides the README, Glossary, CLI / Configuration / Python API guides, Trust model, Specification, CHANGELOG, and STATUS for that release.
