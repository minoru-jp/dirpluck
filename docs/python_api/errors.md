# DirpluckError

Catch `DirpluckError` when one caller wants to handle expected dirpluck failures uniformly.

```python
import dirpluck

try:
    result = dirpluck.run("example", preview=True)
except dirpluck.DirpluckError as exc:
    print(exc)
```

Invalid Configurations, Target or Selection resolution failures, Invocation Template failures, and incompatible `run()` argument combinations raise a `DirpluckError` subclass. CLI status 2 and the `dirpluck: error:` prefix are presentation details of the CLI adapter and are not part of the Python API contract.
