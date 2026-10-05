# Recipe: Build task-specific packages from shared team settings

This recipe keeps team-wide Selection rules and team guidelines in a Base Configuration, then inherits them from a project-specific Root Configuration.

The default run creates a focused review package. The `full` Pluck Case expands the same project to include documentation and runnable examples. Instead of learning Base, Shared, and Case as isolated features, treat them as one workflow: **define common policy once, then switch the package for the current task**.

## Workspace

Use this workspace.

```text
workspace/
├── default.dirpluck
├── common/
│   ├── common.dirpluck
│   └── team_guidelines/
│       ├── REVIEW.md
│       └── SECURITY.md
└── project/
    ├── README.md
    ├── pyproject.toml
    ├── src/
    ├── tests/
    ├── docs/
    ├── examples/
    ├── .git/
    └── .venv/
```

`common/common.dirpluck` is the team policy. The workspace-root `default.dirpluck` is the Root Configuration for this project. `common/team_guidelines/` contains team material that should accompany every package.

## Goal

The goals are:

- require `README.md`, `pyproject.toml`, and `src/` for every project;
- include `tests/` in the ordinary review package when it exists;
- ignore `.git/`, `.venv/`, `__pycache__/`, and `*.pyc` everywhere;
- include the team guidelines on every run;
- leave `docs/` and `examples/` out of the ordinary review package, but add them for a `full` review; and
- keep the Output location and current-task explanation in the Root Configuration.

Shared patterns let the default Pluck and the `full` Case reuse the same pattern sets instead of copying the lists.

## 1. Team Base Configuration

Write the shared policy in `common/common.dirpluck`.

```toml
[shared.must]
project_core = ["README.md", "pyproject.toml", "src/"]

[shared.may]
review_extra = ["tests/"]
full_extra = ["tests/", "docs/", "examples/"]

[shared.ignore]
python_noise = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[pluck]
description = "Default review package with the project core and tests when present."
must = [{ shared = "project_core" }]
may = [{ shared = "review_extra" }]
ignore = [{ shared = "python_noise" }]

[always.team_guidelines]
description = "Team review and security guidelines that accompany every package."
path = "team_guidelines"
must = ["*.md"]
```

The Base Configuration deliberately has no Output. Where the ZIP should be written belongs to the Root Configuration that is actually run.

`[shared.must]`, `[shared.may]`, and `[shared.ignore]` define reusable pattern sets. The default `[pluck]` uses those sets for the ordinary review package.

The relative `path = "team_guidelines"` under `[always.team_guidelines]` is anchored to the directory containing `common/common.dirpluck`. Inheriting the Always source from the outer `default.dirpluck` does not rebase that path to the workspace root.

## 2. Project Root Configuration

At the workspace root, make `default.dirpluck` inherit the Base Configuration and add the current project context, the `full` Case, and Output.

```toml
[about]
base = "common/common.dirpluck"
description = """
Package prepared for review of the current project.

Use the default selection for an ordinary code review. Use the `full` Case when documentation and runnable examples are also part of the review scope.
"""

[case.pluck.full]
description = "Full review package including documentation and examples."
must = [{ shared = "project_core" }]
may = [{ shared = "full_extra" }]
ignore = [{ shared = "python_noise" }]

[output]
path = "project-package.zip"
overwrite = true
```

`[case.pluck.full]` is not a delta from `[pluck]`; it is a complete independent Selection. That is why it writes `must`, `may`, and `ignore` again. The actual pattern lists are still not duplicated because both Selections refer to Shared patterns.

The Root Configuration's `about.description` appears at the beginning of the generated Archive README, so the recipient can immediately see which package mode to use and why.

## Pattern 1: Ordinary review

Do not select a Case for the ordinary code-review package.

```console
dirpluck ./project/ --preview
dirpluck ./project/
```

The default Pluck is used. Conceptually, the Archive looks like this:

```text
project-package.zip
├── README.md
├── project/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   └── tests/
└── team_guidelines/
    ├── REVIEW.md
    └── SECURITY.md
```

`docs/` and `examples/` are intentionally absent from the ordinary review package.

## Pattern 2: Full review

When documentation and examples are also part of the review, select the `full` Pluck Case.

```console
dirpluck ./project/ --case full --preview
dirpluck ./project/ --case full
```

The `full` Case uses `shared.may.full_extra`, so `docs/` and `examples/` join `tests/` as optional review material.

```text
project-package.zip
├── README.md
├── project/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   ├── tests/
│   ├── docs/
│   └── examples/
└── team_guidelines/
    ├── REVIEW.md
    └── SECURITY.md
```

Always sources are independent of the Pluck Case, so `team_guidelines/` is included in both the ordinary and full review packages.

## How the responsibilities are divided

This recipe gives each layer a distinct job.

- Base Configuration: team-wide Selection policy and fixed review material.
- Shared: pattern sets reused by multiple Selections.
- Root Configuration: the current task description, task-specific Cases, and Output.
- Pluck Case: a complete Selection that changes the collection scope for the same Target.
- CLI: chooses which Case applies to this run.

The purpose of Base Configuration is not merely to shorten a file. Thinking in terms of **different ownership and change frequency** makes it easier to decide which Configuration should contain each rule.

## Related documentation

See these documents for the detailed rules.

- [Configuration composition](../configuration/composition.md): Base Configuration and path anchoring.
- [Configuration selection](../configuration/selection.md): Shared patterns and Pluck Cases.
- [Configuration sources](../configuration/sources.md): Always sources.
- [CLI Targets and Cases](../cli/targets.md): `--case full`.
- [Base chain and composition Specification](../specification/composition.md): the exact composition contract.

This recipe emphasizes one reusable team workflow rather than listing the complete grammar for Base, Shared, and Case.
