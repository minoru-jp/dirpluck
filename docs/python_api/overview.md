# Python API overview

This document describes the official Python API for dirpluck 0.12.x. The API is intentionally small: it exposes the same execution model as the CLI without making the Configuration parser or builder pipeline part of the general compatibility contract.

See [`run()`](run.md) for arguments and runtime modifiers, [`RunResult`](result.md) for return values, [`DirpluckError`](errors.md) for the public error boundary, and [Package surface](surface.md) for compatibility-supported package-root exports. Configuration, Target, Case, and Archive execution semantics are shared with the [Specification](../specification/INDEX.md).

## Positioning

The center of the official API is `dirpluck.run()`. It accepts the same kinds of runtime inputs as the CLI: Targets, Configuration, Case, Invocation Template, Entry, preview, and Output modifiers, and executes them through the same application layer.

The CLI remains responsible for human-facing argument parsing, help, exit status, and stdout / stderr formatting. The Python API does not use `SystemExit` as its normal control flow. It returns a `RunResult` and raises expected dirpluck failures as `DirpluckError` subclasses.

For 0.12.x, only names explicitly exported from the package root are official Python API. Lower-level modules and underscore-prefixed names are implementation details and are not compatibility-supported during Beta.

## Basic form

```python
import dirpluck

result = dirpluck.run("example")
print(result.output_path)
```

This is conceptually equivalent to:

```console
dirpluck example
```

When `config` is omitted, dirpluck uses `default.dirpluck` in the runtime cwd. The Python API also provides an API-only `cwd` argument when you want to choose the anchor for relative control-document paths without changing the process working directory.

```python
from pathlib import Path
import dirpluck

result = dirpluck.run(
    "example",
    config="configs/review",
    cwd=Path("/work/project"),
)
```

Here, `config` selects `/work/project/configs/review.dirpluck`. The `cwd` argument does not rebase relative source paths written inside a Configuration; those continue to resolve from the location of the Configuration document that contains them.
