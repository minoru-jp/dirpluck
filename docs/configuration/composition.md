# Configuration composition

How one Configuration reuses another through `[about].base`, including filesystem anchoring.

This guide explains Base Configuration authoring. Exact base-chain, shadowing, and cycle rules are defined in [Base chain and composition](../specification/composition.md), and relative-path anchors are defined in [Filesystem path notation](../specification/paths.md). For operation, see the [CLI guide](../cli/INDEX.md); for the trust boundary, see the [Trust model](../TRUST.md).

## Base Configuration

Reference a Base Configuration with `base` in `[about]` when reusing an existing Configuration as the foundation of another.

```toml
[about]
base = "../common/common.dirpluck"
```

`base` references one Configuration file. If that Configuration has another `base`, the result is a linear base chain. There is no fixed maximum base-chain depth.

Relative filesystem paths in each Configuration are always resolved from the directory containing that Configuration file itself. A Scope or Always-source path inherited from a Base Configuration is not rebased to the location of an outer Configuration. The default Scope has no relative-path field and always uses the Root Configuration file's directory as its root.

[Specification](../specification/INDEX.md) defines composition of Pluck, Always, Scope, and Shared patterns, description resolution, cycle detection, and Output handling. A Base Configuration may omit Output. A Root Configuration used with `--preview` or Runtime Output may also omit it; a normal build without Runtime Output must declare its own fixed or timestamp Output directly.
