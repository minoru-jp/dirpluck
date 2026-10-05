# Recipe: Select the projects you need from a workspace

This recipe registers a workspace containing multiple projects as a named Scope, then switches what is collected by changing only the CLI Target reference while keeping the same Configuration.

Instead of memorizing the Target grammar as a list, compare the forms by purpose: **select one project, select several explicitly, select by a naming pattern, or select the whole Scope**.

## Workspace

Use the following workspace.

```text
workspace/
├── default.dirpluck
└── projects/
    ├── service-api/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── src/
    │   └── tests/
    ├── web-console/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── src/
    │   └── tests/
    ├── worker-jobs/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── src/
    │   └── tests/
    └── scratch/
        └── notes.txt
```

Treat the direct-child directories under `projects/` as project candidates. `scratch/` is temporary working material, so exclude it from Target candidates with Scope `ignore`.

## Goal

The goals are:

- apply the same Selection rule to every project;
- normally select one project, but collect several together when needed;
- use a regex selector when project names follow a known pattern;
- collect the whole Scope when appropriate; and
- organize projects under `repositories/` in the Archive independently of where they are found in the workspace.

Create the Configuration once, then change only the CLI Target.

## Configuration

Write `default.dirpluck` as follows.

```toml
[about]
description = """
This archive contains one or more projects selected from the workspace.

Each selected project keeps the same review-oriented file selection. The CLI Target controls which projects participate; the Configuration controls what is collected from each selected project.
"""

[namespace.repositories]

[scope.projects]
description = "Projects available in this workspace."
path = "projects"
target_kind = "directory"
namespace = "repositories"
ignore = ["scratch/"]

[pluck]
description = "Review material selected from each chosen project."
must = ["README.md", "src/"]
may = ["pyproject.toml", "tests/"]
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[output]
path = "selected-projects.zip"
overwrite = true
```

`[scope.projects]` registers `projects/` as the named Scope `projects`. Because `target_kind = "directory"`, only eligible direct-child directories become Target candidates.

`ignore = ["scratch/"]` removes `scratch/` from Target candidates. This ignore does not control file selection inside a project. It controls **which direct children of the Scope are exposed as project Targets**.

`namespace = "repositories"` does not change where dirpluck searches. It only places each selected project's Archive root under `repositories/<project>/`.

`[pluck]` is the common Selection applied to every selected project directory. It requires `README.md` and `src/`, and includes `pyproject.toml` and `tests/` when they exist.

## Pattern 1: Select one project

When you need only one project, specify its name as a literal Target.

```console
dirpluck projects/service-api/ --preview
dirpluck projects/service-api/
```

The trailing `/` means a directory Target. `projects` is the Scope name; the CLI is not directly spelling a filesystem path.

Because the Scope uses `namespace = "repositories"`, the conceptual Archive looks like this.

```text
selected-projects.zip
├── README.md
└── repositories/
    └── service-api/
        ├── README.md
        ├── pyproject.toml
        ├── src/
        └── tests/
```

## Pattern 2: Select several projects

There are several ways to select multiple projects. Choose the form that is easiest to read for the task.

**List several Targets directly:**

```console
dirpluck projects/service-api/ projects/web-console/ --preview
dirpluck 'projects:[service-api//web-console/]' --preview
dirpluck 'projects:<.*-(api|console)/>' --preview
```

The first command supplies two literal Targets separately. This is usually the clearest form when the set is small and the names should be explicit.

The second command uses a literal list selector. The trailing `/` of a directory item and the `/` item separator appear next to each other, producing `service-api//web-console/`. It means "the directory item `service-api/`, followed by `/` that separates the next item."

The third command uses a regular-expression selector. Directory candidates are matched as normalized names with a trailing `/`, so `.*-(api|console)/` selects `service-api/` and `web-console/` in this workspace.

With every form, dirpluck first determines eligible candidates using the Scope's `target_kind`, `ignore`, and link-like-entry exclusion, then applies the Target selection.

## Pattern 3: Select the whole Scope

Use Scope expansion when you want every eligible project in the Scope.

```console
dirpluck projects/ --preview
dirpluck projects/
```

In this workspace, `service-api/`, `web-console/`, and `worker-jobs/` are selected. `scratch/` is excluded from Target candidates by `ignore = ["scratch/"]`, so it is not included by Scope expansion either.

The conceptual Archive roots are:

```text
repositories/
├── service-api/
├── web-console/
└── worker-jobs/
```

Scope expansion is not recursive traversal. It expands the eligible direct children of `projects/` into Targets, then applies `[pluck]` Selection inside each selected directory.

## How the responsibilities are divided

This recipe keeps Configuration and CLI responsibilities separate.

- Scope defines where Target candidates come from.
- Scope `ignore` defines which direct children are removed from Target candidates.
- The CLI Target decides which projects participate in this run.
- Pluck Selection defines what is collected from each selected directory.
- Namespace defines where the collected projects are placed in the Archive.

With this separation in mind, you do not need to memorize the Target grammar as a feature list. You can choose the form that matches the current task.

## Related documentation

See these documents for the detailed rules.

- [CLI Targets and Cases](../cli/targets.md): literal Targets, Scope expansion, list selectors, and regex selectors.
- [Configuration Sources](../configuration/sources.md): Scope, `target_kind`, Scope `ignore`, and Namespace.
- [Configuration Selection](../configuration/selection.md): Pluck Selection.
- [Runtime Targets Specification](../specification/runtime-targets.md): the exact Target-resolution contract.

This recipe prioritizes comparing useful forms against the same workspace, so it does not cover every Target-grammar error condition.
