<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/recipes/llm_development_environment.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/canonical_documents/` にある日本語 canonical document はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの canonical document を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や canonical document を直接編集するのではなく、正本へ戻って行う。
-->

# Recipe: LLM 開発環境へ project を渡す

このRecipeでは、LLM-assisted developmentへ渡すZIPを1個のConfigurationから再現します。

開発対象repositoryはruntime Targetとして選び、常に必要な作業指示はAlways source、network accessがない環境だけで必要なwheelhouseはExtra sourceとして定義します。LayoutでArchive内の役割を分離し、Always CaseでExtraを有効化します。

特定のLLM製品名ではなく、**handoff先の能力に応じて同じ開発材料を組み替える**ことを主眼にします。

## Workspace

次のworkspaceを使います。

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
│   └── ... target環境で必要なdependency wheel
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

`handoff/DEVELOPMENT.md`はどのhandoffでも必要な作業手順です。`offline_wheels/`はpackage indexへ接続できない環境だけで必要です。`projects/`にはruntimeに選択する開発対象repositoryがあります。

## Goal

目的は次の通りです。

- 開発対象はTargetとしてruntimeに選び、Configurationを作業ごとに書き換えない。
- 常に必要なhandoff guideはAlways sourceとして含める。
- offline wheelhouseはExtraとして定義し、必要なCaseだけで有効化する。
- `support/`、`dependencies/`、`development-targets/`のLayoutに分け、Archiveを受け取った側が役割を把握しやすくする。
- Target / Alwaysの有無に応じた補足をgenerated READMEへ残す。
- 通常は一時的なreview materialを除外し、Pluck Caseを選んだときだけ追加する。

`about.description`とconditional descriptionはSelection semanticsを変更しません。Archiveを受け取った人やLLMへ、今回何が含まれているかを説明するためのmetadataです。

## Configuration

`default.dirpluck`を次のようにします。

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

`[always.handoff]`は定義された時点で有効です。一方、`[extra.offline_wheels]`は定義されただけではsource selectionへ参加せず、`[case.always.offline].add`から追加されたrunだけでAlways相当のfixed sourceとして有効になります。

`[about].always_layout = "support"`はAlways / Extraのdefault Layoutです。`offline_wheels`は個別に`layout = "dependencies"`を指定してdefaultを上書きします。Targetは`targets_layout = "development-targets"`によって別のLayoutへ配置します。

`description_no_targets`、`description_no_always`、`description_empty`はそれぞれresolved sourceの構成に応じてgenerated READMEへ追加されます。通常の`description`は常に表示されます。

## Default handoff

通常のhandoffではAlways Caseを指定しません。Extraはinactiveのままなので、Always sourceのhandoff guideと選択したTargetだけが入ります。

```console
dirpluck projects/service-api/ --preview
dirpluck projects/service-api/
```

概念的には次のArchiveになります。

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

## Offline destination: Extraを有効化する

package indexへ接続できない環境では`.offline` Always Caseを選びます。

```console
dirpluck projects/service-api/ --case .offline --preview
dirpluck projects/service-api/ --case .offline
```

`add = ["offline_wheels"]`は通常のAlways source `handoff`をそのまま維持し、Extra `offline_wheels`だけをこのrunに追加します。`include`は列挙したAlways / Extraだけを残す完全指定なので、「通常のAlwaysへExtraを足す」用途では`add`を使います。

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

## Caseを組み合わせる

`service-api/.tmp/proposed-changes.patch`も評価してほしい場合はPluck CaseとAlways Caseを同時に選べます。

```console
dirpluck projects/service-api/ --case review.offline --preview
dirpluck projects/service-api/ --case review.offline
```

`review.offline`ではPluck軸に`review`、Always軸に`offline`を指定します。これによりTarget Selectionへ`.tmp/`を戻しながら、offline wheelhouseも有効化できます。

`--case .project-only`をTarget付きで実行するとAlways / Extra sourceが0件になるため`description_no_always`がREADMEへ追加されます。Targetを指定せず`--case .project-only`を実行するとresolved sourceが0件になり、`description_empty`を含むREADME-only Archiveになります。

## Related documentation

個々の機能の詳細は次を参照してください。

- [Configuration sources](../configuration/sources.md): Always、Extra、Scope、Layout。
- [Configuration selection](../configuration/selection.md): Selection、Pluck Case、Always Case。
- [CLI Targets and Cases](../cli/targets.md): `review.offline`や`.offline`のようなCase selector。
- [CLI output](../cli/output.md): `--preview`。
- [Configuration output](../configuration/output.md): `[output]`。

このRecipeは一つのcomplete workflowを示すもので、grammarの全組み合わせを列挙するものではありません。厳密な受理grammarとerror条件は[Specification](../specification/INDEX.md)を参照してください。
