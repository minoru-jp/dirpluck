<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/recipes/team_shared_configuration.py` です。
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

# Recipe: チーム共通設定から用途別 package を作る

この Recipe では、チーム全体で再利用する Selection と team guidelines を Base Configuration に置き、個別 project の Root Configuration からそれを継承します。

通常の run は review に必要な最小限の file を集め、`full` Pluck Case を選んだときだけ docs と examples まで含めます。Base、Shared、Case を単独の機能として覚えるのではなく、**共通 policy を一度定義し、用途ごとに package を切り替える** workflow として見ます。

## Workspace

次の workspace を使います。

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

`common/common.dirpluck` はチーム共通の policy、workspace root の `default.dirpluck` はこの project の Root Configuration です。`common/team_guidelines/` はどの package にも含めるチーム共通資料です。

## Goal

目的は次の通りです。

- `README.md`、`pyproject.toml`、`src/` を全projectで共通の必須対象にする。
- `tests/` は通常レビューでも含めるが、存在しなくてもよい。
- `.git/`、`.venv/`、`__pycache__/`、`*.pyc` は共通で除外する。
- team guidelines は常に Archive に含める。
- 通常レビューでは docs/examples を省き、`full` Caseでだけ追加する。
- Output pathや今回の作業説明はRoot Configuration側に置く。

共通patternをSharedにすることで、default Pluckと`full` Caseは同じpattern listをコピーせず再利用できます。

## 1. チーム共通の Base Configuration

`common/common.dirpluck` にチーム共通設定を書きます。

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

Base ConfigurationにはOutputを置いていません。どこへ書き出すかは、実際にrunするRoot Configurationの責務にします。

`[shared.must]` / `[shared.may]` / `[shared.ignore]` は、複数Selectionから再利用するpattern setです。`[pluck]` は通常レビューのdefault Selectionです。

`[always.team_guidelines]` の `path = "team_guidelines"` は、Base Configuration自身がある`common/` directoryを基準に解決されます。外側の`default.dirpluck`から継承されてもworkspace rootへrebaseされません。

## 2. Project 用の Root Configuration

workspace rootの`default.dirpluck`はBaseを継承し、このproject固有の説明、`full` Case、Outputを追加します。

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

`[case.pluck.full]` は `[pluck]` への差分ではなく、独立した完全Selectionです。そのため `must`、`may`、`ignore` をすべて書きます。ただし実際のpattern listはShared参照なので、default Selectionと同じ内容を複製する必要はありません。

Root Configurationの`about.description`は生成Archive READMEの先頭に入り、このpackageが何のために作られたかを受け取り側へ伝えます。

## Pattern 1: 通常レビュー

通常レビューではCaseを指定しません。

```console
dirpluck ./project/ --preview
dirpluck ./project/
```

default Pluckが使われ、概念的には次の内容になります。

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

`docs/` と `examples/` は通常レビューには入りません。

## Pattern 2: Full review

docsやexamplesまで含めて確認したいときは`full` Pluck Caseを選びます。

```console
dirpluck ./project/ --case full --preview
dirpluck ./project/ --case full
```

`full` Caseでは`shared.may.full_extra`を使うため、`tests/`に加えて`docs/`と`examples/`も対象になります。

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

Always sourceはPluck Caseとは独立しているため、`team_guidelines/`は通常レビューでもfullレビューでも含まれます。

## 責務の分け方

このRecipeでは責務を次のように分けています。

- Base Configuration: チーム共通のSelection policyと固定資料。
- Shared: 複数Selectionで再利用するpattern set。
- Root Configuration: 今回の作業説明、用途別Case、Output。
- Pluck Case: 同じTargetに対して収集範囲を切り替える完全Selection。
- CLI: 今回どのCaseでrunするかを選ぶ。

Baseを使う目的は設定fileを短くすることだけではありません。**変更頻度と所有者が違う設定を分ける**と考えると、どこに何を書くかを判断しやすくなります。

## Related documentation

詳細な規則は次の文書を参照してください。

- [Configuration composition](../configuration/composition.md): Base Configurationとpath anchoring。
- [Configuration selection](../configuration/selection.md): SharedとPluck Case。
- [Configuration sources](../configuration/sources.md): Always source。
- [CLI Targets and Cases](../cli/targets.md): `--case full`。
- [Base chain and composition Specification](../specification/composition.md): compositionの厳密な契約。

このRecipeは、Base / Shared / Caseの完全なgrammar一覧ではなく、チーム共通policyを再利用する一つのworkflowを優先して説明しています。
