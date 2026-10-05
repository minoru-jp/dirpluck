<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/recipes/workspace_project_selection.py` です。
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

# Recipe: workspace から必要な project を選ぶ

このRecipeでは、複数projectを含むworkspaceをnamed Scopeとして登録し、Configurationは変えずにCLI Target referenceだけを変えて収集対象を切り替えます。

Target grammarを文法一覧として暗記するのではなく、**1 projectだけ選ぶ、複数を明示的に選ぶ、名前patternで選ぶ、Scope全体を選ぶ**という目的別に比較します。

## Workspace

次のworkspaceを使います。

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

`projects/`直下のdirectoryをproject候補として扱います。`scratch/`は一時作業用なのでScope `ignore`でTarget候補から除外します。

## Goal

目的は次の通りです。

- すべてのprojectへ同じSelection ruleを適用する。
- 普段は1 projectだけ選び、必要なら複数をまとめる。
- project名の規則が分かっているときはregex selectorを使う。
- 必要ならScope全体を選ぶ。
- workspace上の場所とは独立して、Archiveでは`repositories/`配下へ整理する。

Configurationは一度だけ作り、runごとにCLI Targetだけ変えます。

## Configuration

`default.dirpluck`を次のようにします。

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

`[scope.projects]`は`projects/`をnamed Scope `projects`として登録します。`target_kind = "directory"`なのでeligibleなdirect-child directoryだけがTarget候補です。

`ignore = ["scratch/"]`は`projects/`内部のfile selectionではなく、**Scopeから公開するTarget候補**を制御します。

`namespace = "repositories"`は検索場所を変えず、選択projectのArchive rootを`repositories/<project>/`にします。

`[pluck]`は選ばれた各project directoryへ共通で適用されます。

## Pattern 1: 1 projectを選ぶ

1 projectだけ必要ならliteral Targetを指定します。

```console
dirpluck projects/service-api/ --preview
dirpluck projects/service-api/
```

末尾`/`はdirectory Targetを意味します。`projects`はScope名であり、CLIがfilesystem pathを直接書いているわけではありません。

Namespaceによって概念的なArchiveは次のようになります。

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

## Pattern 2: 複数projectを選ぶ

複数projectを選ぶ方法はいくつかあります。taskに対して一番読みやすい形を使います。

```console
dirpluck projects/service-api/ projects/web-console/ --preview
dirpluck 'projects:[service-api//web-console/]' --preview
dirpluck 'projects:<.*-(api|console)/>' --preview
```

最初は2つのliteral Targetを別々のargumentとして渡します。小さい集合を明示したいときに最も読みやすい形です。

2つ目はliteral list selectorです。directory itemの末尾`/`とitem separatorの`/`が隣接するため`service-api//web-console/`となります。

3つ目はregular-expression selectorです。directory candidateは末尾`/`を付けたnormalized nameに対してfull-matchされます。

どの形式でも、dirpluckは最初にScopeの`target_kind`、`ignore`、link-like entry exclusionでeligible candidateを決め、その後Target selectionを適用します。

## Pattern 3: Scope全体を選ぶ

Scope内のeligible projectをすべて選ぶときはScope expansionを使います。

```console
dirpluck projects/ --preview
dirpluck projects/
```

このworkspaceでは`service-api/`、`web-console/`、`worker-jobs/`が選ばれ、`scratch/`はScope ignoreによって候補から除外されます。

```text
repositories/
├── service-api/
├── web-console/
└── worker-jobs/
```

Scope expansionはrecursive traversalではありません。`projects/`のeligibleなdirect childをTargetへ展開し、その各directory内部へ`[pluck]` Selectionを適用します。

## 責務の分け方

このRecipeでは責務を次のように分けています。

- Scope: Target候補をどこから得るか。
- Scope `ignore`: direct childのどれをTarget候補から外すか。
- CLI Target: 今回どのprojectをrunへ参加させるか。
- Pluck Selection: 選んだprojectから何を収集するか。
- Namespace: Archive内のどこへ配置するか。

この分離を理解すると、Target grammarを機能一覧として暗記せず、taskに合う形式を選べます。

## Related documentation

詳細は次を参照してください。

- [CLI Targets and Cases](../cli/targets.md): literal Target、Scope expansion、list selector、regex selector。
- [Configuration Sources](../configuration/sources.md): Scope、`target_kind`、Scope `ignore`、Namespace。
- [Configuration Selection](../configuration/selection.md): Pluck Selection。
- [Runtime Targets Specification](../specification/runtime-targets.md): Target resolutionの厳密な契約。

このRecipeは同じworkspaceに対して実用的な形式を比較することを優先し、すべてのTarget grammar error conditionは扱いません。
