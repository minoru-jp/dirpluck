# Recipe: Hand a project to an LLM development environment

This recipe shows how to hand the same Python project to different LLM sandboxes while switching an offline wheelhouse according to whether the environment can reach the Python package index.

Using the author's October 2026 workflow as the concrete example, the default assumes a ChatGPT sandbox that cannot reach the package index and includes `shikumi`, `shikumi-devdoc`, `basedpyright`, `ruff`, and the dependency wheels they require. The `.claude` Always Case treats the Claude environment as able to install from the package index and omits the wheelhouse.

The durable idea is not the product names but the distinction between an **offline environment and an online environment**. If the capabilities of the sandbox you use change, rename the Case or invert the default to match the real environment.

## Workspace

Use this workspace:

```text
workspace/
├── default.dirpluck
├── offline_wheels/
│   ├── shikumi-0.2.4-py3-none-any.whl
│   ├── shikumi_devdoc-0.3.5-py3-none-any.whl
│   ├── basedpyright-1.40.1-py3-none-any.whl
│   ├── ruff-0.16.10-...whl
│   └── ... dependency wheels required by the target environment
└── project/
    ├── README.md
    ├── pyproject.toml
    ├── src/
    └── tests/
```

`project/` is the development target to hand to the LLM. Prepare `offline_wheels/` in advance with every wheel needed for offline installation. Include not only the four direct dependencies shown here, but also any transitive dependency wheels they require in the target environment.

## Goal

The goal is:

- Make the default Archive usable in a sandbox that cannot reach the package index.
- Put the environment-setup and verification instructions that the LLM should follow first at the top of the Archive README.
- Omit the unnecessary wheelhouse in an environment that can use the package index.
- Keep the project Selection identical in both environments.

`about.description` does not affect Selection semantics, but it is inserted at the beginning of the generated Archive `README.md`. This makes it useful for more than a short label: it can contain a multi-line set of working instructions for the receiving LLM.

## Configuration

Create `default.dirpluck` as follows:

```toml
[about]
description = """
This archive contains a Python project prepared for LLM-assisted development.

Before changing the project:
1. Read `project/README.md` and the project documentation.
2. Prepare the development environment with `shikumi`, `shikumi-devdoc`, `basedpyright`, and `ruff`.
3. If the Python package index is unavailable, install from the bundled `offline_wheels/` directory, for example:
   `python -m pip install --no-index --find-links offline_wheels shikumi shikumi-devdoc basedpyright ruff`
4. Run the existing test suite before and after modifying the implementation.

Treat the bundled wheels as an offline installation fallback; use the package index when the environment provides normal network access.
"""

[always.offline_wheels]
description = "Offline wheelhouse for the development tools required by this project."
path = "offline_wheels"
must = ["*.whl"]

[case.always.claude]
description = "The environment can install development tools from the package index, so the offline wheelhouse is not needed."
exclude = ["offline_wheels"]

[pluck]
description = "The Python project to modify and test."
may = ["*", "*/"]
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[output]
path = "develop-target.zip"
overwrite = true
```

`[always.offline_wheels]` adds the wheelhouse regardless of the selected Target. Because the Always-source identifier is `offline_wheels`, its Archive root is also `offline_wheels/`.

`[case.always.claude]` does not change the Selection of any individual Always source. It removes `offline_wheels` from the participating Always-source set. `.claude` is a Case selector that selects only the Always Case.

The `about.description` naturally tells the receiving environment to read the project README first, install the development tools, fall back to the bundled wheels when the package index is unavailable, and run the test suite before and after changing the project.

## Offline sandbox: default

For a sandbox that cannot use the package index, do not specify a Case. Without an Always Case, every effective Always source participates, so `offline_wheels/` is included in the Archive.

Preview first, then build:

```console
dirpluck ./project/ --preview
dirpluck ./project/
```

The first command lets you inspect the selection. If it looks correct, the second command writes the ZIP.

Conceptually, the Archive looks like this:

```text
develop-target.zip
├── README.md
├── offline_wheels/
│   ├── shikumi-0.2.4-py3-none-any.whl
│   ├── shikumi_devdoc-0.3.5-py3-none-any.whl
│   ├── basedpyright-1.40.1-py3-none-any.whl
│   ├── ruff-0.16.10-...whl
│   └── ...
└── project/
    └── ...
```

Because the Archive `README.md` begins with `about.description`, a sandbox with network restrictions can immediately see that it should use the bundled wheels.

## Online sandbox: `.claude`

In a Claude environment that can reach the package index, select the `.claude` Always Case:

```console
dirpluck ./project/ --case .claude --preview
dirpluck ./project/ --case .claude
```

`.claude` does not select a Pluck Case. It selects only the Always Case named `claude`. `exclude = ["offline_wheels"]` therefore leaves the project collection rules unchanged and removes only the wheelhouse.

The resulting Archive looks like this:

```text
develop-target.zip
├── README.md
└── project/
    └── ...
```

If you do not want provider names in the Configuration, use the same pattern with a capability-oriented name such as `[case.always.online]`.

## Related documentation

For the individual features used in this recipe, see:

- [Configuration sources](../configuration/sources.md): Always sources.
- [Configuration selection](../configuration/selection.md): Selection and Always Cases.
- [CLI Targets and Cases](../cli/targets.md): Case selectors such as `.claude`.
- [CLI output](../cli/output.md): `--preview`.
- [Configuration output](../configuration/output.md): `[output]`.

This recipe favors one concrete workflow over a complete grammar reference. See the [Specification](../specification/INDEX.md) for the exact accepted grammar and error conditions.
