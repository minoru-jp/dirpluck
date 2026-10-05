# Test suite structure during the 1.0 refactor

The active suite is deliberately split by *test stability*, not only by feature area.
This keeps the public 1.0 contract separate from tests that are allowed to be rewritten
when the internal parser/compiler/resolver architecture changes.

- `contract/` contains tests that exercise the supported public surfaces directly:
  the `dirpluck` CLI and the package-root Python API. These tests are the stable 1.0
  contract baseline. Their implementation should normally survive the internal rewrite.
- `characterization/` contains canonical behavior that is still important, but the test
  code currently reaches private modules, private models, or other current implementation
  boundaries. Preserve the represented behavior unless the canonical specification says
  otherwise, but freely rewrite these tests as the new typed parser/compiler/resolver
  boundaries replace the current architecture.
- `compatibility/` contains pre-1.0 behavior explicitly scheduled for removal in 1.0.0.
  It remains active during 0.x and is intended to disappear as a unit when those
  compatibility paths are removed.
- `architecture/` contains internal layering invariants for the refactor itself. These are
  not public product contracts; they prevent the normalize → extract → output dependency
  direction from regressing while implementation details continue to change.

Helpers shared by these groups remain directly under `tests/`.

Run the complete active 0.x suite with:

```console
python -m unittest discover -s tests -t . -v
```

The public-contract baseline alone can be run with:

```console
python -m unittest discover -s tests/contract -t . -v
```

Current-implementation characterization alone can be run with:

```console
python -m unittest discover -s tests/characterization -t . -v
```

Pre-1.0 compatibility alone can be run with:

```console
python -m unittest discover -s tests/compatibility -t . -v
```

Layering invariants alone can be run with:

```console
python -m unittest discover -s tests/architecture -t . -v
```

Tests intentionally excluded from normal discovery live under `tests_deferred/`.
`legacy_behavior/` preserves behavior deliberately removed from the 1.0 contract;
`generated_docs/` is paused while only canonical document sources are retained.
