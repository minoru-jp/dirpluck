# Configuration examples

A complete Configuration that combines the major authoring features.

This page combines several authoring concerns in one Configuration. Use this collection for field-by-field guidance, the [Specification](../specification/INDEX.md) for the compatibility contract, the [CLI guide](../cli/INDEX.md) for operation, and the [Trust model](../TRUST.md) for filesystem and sharing boundaries.

## Complete example

```toml
[about]
description = "Materials prepared for reviewing the current project."
base = "../common/common.dirpluck"

[shared.ignore]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[pluck]
description = "The project currently under review."
may = ["README.md", "src/", "tests/"]
ignore = [["python-dev"]]
allow_empty = true

[pluck.case.full]
description = "The project with all review material."
may = ["README.md", "src/", "tests/", "docs/"]
ignore = [["python-dev"]]
allow_empty = true

[scope]
ignore = ["archive/"]

[scope.projects]
path = "/srv/projects"
ignore = ["archive/", "tmp-*/"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

```console
dirpluck projects/example/
dirpluck projects/example/ --case full --preview
dirpluck projects/
```

For all CLI options and Configuration / Invocation Template selection, see [CLI guide](../cli/INDEX.md). For the exact way this Configuration is resolved and validated, see [Specification](../specification/INDEX.md).
