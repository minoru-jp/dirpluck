# Recipe: Hand a project to an LLM development environment

This recipe builds a ZIP handoff for LLM-assisted development from a single Configuration.

Development repositories are selected at runtime as Targets. Working instructions that are always needed are defined as an Always source, while the wheelhouse needed only when network access is unavailable is defined as an Extra source. Layouts separate their roles inside the Archive, and an Always Case activates the Extra source when needed.

The important idea is not a particular LLM product name, but **reassembling the same development material according to the capabilities of the handoff destination**.

## Workspace

Use this workspace:

```text
workspace/
├── default.dirpluck
├── handoff/
│   └── DEVELOPMENT.md
├── offline_wheels/
│   ├── shikumi-0.2.4-py3-none-any.whl
│   ├── shikumi_devdoc-0.3.5-py3-none-any.whl
│   ├── basedpyright-1.40.1-py3-none-any.whl
│   ├── ruff-0.16.10-...whl
│   └── ... dependency wheels required by the target environment
└── projects/
    ├── service-api/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── src/
    │   ├── tests/
    │   └── .tmp/
    │       └── proposed-changes.patch
    └── worker-jobs/
```

`handoff/DEVELOPMENT.md` contains working instructions needed for every handoff. `offline_wheels/` is needed only when the destination cannot reach a package index. `projects/` contains the repositories that can be selected as runtime development Targets.

## Goal

The goal is to:

- select the development target at runtime instead of rewriting the Configuration for each task;
- include a handoff guide that is always required as an Always source;
- declare the offline wheelhouse as Extra and activate it only for the Case that needs it;
- separate `support/`, `dependencies/`, and `development-targets/` with Layouts so the recipient can see each role clearly;
- leave additional context in the generated README according to whether Targets and Always-side sources are present; and
- exclude temporary review material normally, then add it only when a Pluck Case is selected.

`about.description` and the conditional descriptions do not change Selection semantics. They are metadata for explaining to the receiving person or LLM what the current Archive contains.

## Configuration

Create `default.dirpluck` as follows:

```toml
[about]
description = """
This archive is a development handoff package for LLM-assisted work.
Read the generated README and `support/handoff/DEVELOPMENT.md` before changing code.
Run the existing tests before and after modifying the selected project.
"""
description_no_targets = "No development target was selected; this archive contains support material only."
description_no_always = "No support source is active; this archive contains only selected development targets."
description_empty = "No development target or support source is active; this archive contains only its generated README."
always_layout = "support"
targets_layout = "development-targets"

[layout.support]
description = "Instructions and other material that accompany every normal handoff."

[layout.dependencies]
description = "Offline installation artifacts used when the destination cannot access a package index."

[layout.development-targets]
description = "Repositories selected for the current development task."

[always.handoff]
description = "Development instructions that should accompany every normal handoff."
path = "handoff"
must = ["DEVELOPMENT.md"]

[extra.offline_wheels]
description = "Offline wheelhouse for the development tools required by this project."
path = "offline_wheels"
must = ["*.whl"]
layout = "dependencies"

[scope.projects]
description = "Repositories that can be selected as development targets."
path = "projects"
ignore = ["archive/", "scratch/"]

[shared.ignore]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]

[pluck]
description = "The project files required for normal implementation and testing."
may = ["*", "*/"]
ignore = [
    { shared = "python-dev" },
    { path = ".tmp/" },
]

[case.pluck.review]
description = "Include temporary review material such as a proposed patch."
may = ["*", "*/"]
ignore = [{ shared = "python-dev" }]

[case.always.offline]
description = "The destination cannot install development tools from a package index."
add = ["offline_wheels"]

[case.always.project-only]
description = "Package only runtime-selected development targets without support sources."
include = []

[output]
path = "develop-target.zip"
overwrite = true
```

`[always.handoff]` is active as soon as it is defined. By contrast, `[extra.offline_wheels]` does not participate in source selection merely because it exists. It becomes an Always-side fixed source only for runs where `[case.always.offline].include` selects it.

`[about].always_layout = "support"` is the default Layout for Always and Extra sources. `offline_wheels` overrides that default with `layout = "dependencies"`. Targets are placed separately by `targets_layout = "development-targets"`.

`description_no_targets`, `description_no_always`, and `description_empty` are added to the generated README according to the resolved source composition. The ordinary `description` is always shown.

## Default handoff

For a normal handoff, do not specify an Always Case. Extra remains inactive, so only the Always handoff guide and the selected Target are included.

```console
dirpluck projects/service-api/ --preview
dirpluck projects/service-api/
```

Conceptually, the Archive looks like this:

```text
develop-target.zip
├── README.md
├── support/
│   └── handoff/
│       └── DEVELOPMENT.md
└── development-targets/
    └── service-api/
        └── ...
```

## Offline destination: activate Extra

When the destination cannot reach a package index, select the `.offline` Always Case:

```console
dirpluck projects/service-api/ --case .offline --preview
dirpluck projects/service-api/ --case .offline
```

`add = ["offline_wheels"]` keeps the normal Always source `handoff` unchanged and adds the Extra source `offline_wheels` only for this run. `include` is the complete-enumeration mode that keeps only the listed Always / Extra sources, so use `add` when the intent is simply to add Extra material to the normal Always set.

```text
develop-target.zip
├── README.md
├── support/
│   └── handoff/
│       └── DEVELOPMENT.md
├── dependencies/
│   └── offline_wheels/
│       ├── shikumi-0.2.4-py3-none-any.whl
│       └── ...
└── development-targets/
    └── service-api/
        └── ...
```

## Combine Cases

If `service-api/.tmp/proposed-changes.patch` should also be reviewed, select a Pluck Case and an Always Case together:

```console
dirpluck projects/service-api/ --case review.offline --preview
dirpluck projects/service-api/ --case review.offline
```

`review.offline` selects `review` on the Pluck axis and `offline` on the Always axis. This restores `.tmp/` to the Target Selection while also activating the offline wheelhouse.

Running `--case .project-only` with a Target selects zero Always / Extra sources, so `description_no_always` is added to the README. Running `--case .project-only` with no Target resolves zero sources and produces a README-only Archive containing `description_empty`.

## Related documentation

For the individual features used in this recipe, see:

- [Configuration sources](../configuration/sources.md): Always, Extra, Scope, and Layout.
- [Configuration selection](../configuration/selection.md): Selection, Pluck Cases, and Always Cases.
- [CLI Targets and Cases](../cli/targets.md): Case selectors such as `review.offline` and `.offline`.
- [CLI output](../cli/output.md): `--preview`.
- [Configuration output](../configuration/output.md): `[output]`.

This recipe presents one complete workflow rather than enumerating every grammar combination. See the [Specification](../specification/INDEX.md) for the exact accepted grammar and error conditions.
