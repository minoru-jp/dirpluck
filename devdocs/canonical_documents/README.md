<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/readme/canonical.py` です。
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

# dirpluck

dirpluck は、複数の場所にある file から必要なものを選び、ひとつの ZIP Archive にまとめるための CLI tool です。

何を含め、何を除外し、どの固定資料を常に添えるかを TOML の設定ファイルとして残せます。たとえば LLM に repository を渡して開発作業を依頼するときに、今回の開発対象、共通 framework、作業に必要な local wheel、関連 repository を、同じ rule から再現可能な Archive にまとめられます。

## インストール

現在の version は **0.17.0** です。

Python 3.11 以降を使用します。

```console
pip install dirpluck
dirpluck --version
```

dirpluck には runtime third-party dependency はありません。

0.16.x から upgrade する場合は、Target / Always の final Archive root 一意性と Layout への移行を `docs/migration/0.17.md` で確認してください。0.14.x 以前から upgrade する場合は、先に `docs/migration/0.16.md` の Always Archive identity 変更も確認してください。

## 例: LLM に開発 context を渡す

次のような workspace を考えます。

```text
workspace/
├── default.dirpluck
├── framework-core/
│   └── dist/
│       └── framework_core-2.4.0-py3-none-any.whl
├── docs-builder/
│   └── dist/
│       └── docs_builder-1.6.0-py3-none-any.whl
└── repositories/
    ├── service-api/
    │   ├── src/
    │   └── .tmp/
    │       └── proposed-changes.patch
    ├── worker-jobs/
    └── web-console/
```

`repositories/` には同じ基盤を利用する複数の repository があり、今回は `service-api` と `web-console` を LLM に渡す開発対象とします。`framework-core` と `docs-builder` の wheel は、どの Target を選んでも作業に必要なので常に Archive へ含めます。`service-api/.tmp/` には、別の作業で取得した評価対象の差分が置かれています。

Workspace root の `default.dirpluck` を次のようにします。

```toml
[about]
description = "LLMによる開発作業のためのリポジトリと実行依存物。"
description_no_targets = "今回は開発対象リポジトリを含まず、固定資料だけを収録しています。"
targets_layout = "repositories"

[layout.repositories]
description = "今回の開発対象として選択されたリポジトリ。"

[always.dependencies]
description = "対象リポジトリが利用する基盤フレームワーク。"
path = "framework-core/dist"
must = ["*.whl"]

[always.tools]
description = "開発文書を構成するためのツール。"
path = "docs-builder/dist"
must = ["*.whl"]

[scope.projects]
description = "開発対象として選択できるリポジトリ。"
path = "repositories"
ignore = ["archive/", "scratch/"]

[shared.ignore]
repository-noise = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]

[pluck]
description = "今回LLMに渡す開発対象のリポジトリ。"
may = ["*", "*/"]
ignore = [
    { shared = "repository-noise" },
    { path = "private/local-notes/" },
    { path = ".tmp/" },
]

[case.pluck.diff]
description = "開発対象のリポジトリ。.tmp/ に評価してほしい差分が含まれています。"
may = ["*", "*/"]
ignore = [
    { shared = "repository-noise" },
    { path = "private/local-notes/" },
]

[output]
path = "develop-target.zip"
overwrite = true
```

`always` は Target に関係なく固定資料を加えます。`scope.projects` は runtime に選べる repository の場所を定め、`pluck` は選ばれた directory Target へ同じ Selection を適用します。`targets_layout = "repositories"` は選択した Target を宣言済み `repositories/` Layout の下へ配置します。通常は `.tmp/` を除外し、`diff` Case のときだけ評価対象の差分を含めます。`description` は選択 semantics を変えませんが、生成される Archive README に役割を残すため、受け取った人や LLM が開発対象・基盤・補助 tool を区別できます。

### Preview

Archive を作る前に、まず内容を確認します。この例では workspace root を runtime current working directory として実行するため、`default.dirpluck` が自動的に使われます。

```console
dirpluck projects/service-api/ projects/web-console/ --preview
```

`--preview` は ZIP をまだ書き込まず、現在の filesystem から何が選択されるかを表示します。想定していない file が含まれていないか、必要な file が欠けていないかを確認します。

### Case で差分を追加する

通常の Selection では `.tmp/` を除外しています。`service-api/.tmp/proposed-changes.patch` も一緒に渡して差分を評価するときは、`diff` Case を選びます。

```console
dirpluck projects/service-api/ --case diff --preview
```

`--case diff` は `[case.pluck.diff]` の Selection を使用するため、この場合だけ `.tmp/` も Archive の対象になります。生成される Archive README には Case 側の `description` も反映されます。確認後は同じ command から `--preview` を外して build できます。

### Build

内容に問題がなければ、同じ Target で Archive を作成します。

```console
dirpluck projects/service-api/ projects/web-console/
```

概念的には、次のような Archive が得られます。

```text
develop-target.zip
├── README.md
├── dependencies/
│   └── framework_core-2.4.0-py3-none-any.whl
├── repositories/
│   ├── service-api/
│   │   └── ...
│   └── web-console/
│       └── ...
└── tools/
    └── docs_builder-1.6.0-py3-none-any.whl
```

別の作業では Target だけを変えます。

```console
dirpluck projects/worker-jobs/ --preview
```

設定ファイルに残した収集 rule と固定資料はそのまま再利用できます。

### Filesystem の注意

自動的な Target discovery と Selection traversal で見つかった symbolic link や認識済み Windows directory junction は追跡せず、Archive にも含めません。詳細な filesystem boundary は [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) を参照してください。

## Archive を共有する前に

dirpluck は、file の名前や内容から「これは秘密情報なので共有してはいけない」と判断しません。

上の例にある `.git/`、`.venv/`、`.env*`、`*.pem`、`*.key` などの ignore は有用ですが、**security boundary ではありません**。Project 固有の credential、秘密鍵、個人情報、顧客 data、local 設定、test fixture などは別の名前や場所に存在する可能性があります。

外部の相手や non-local の LLM に Archive を渡す場合は、共有前に `--preview` で選択内容を確認してください。

設定ファイル自体も filesystem 操作の指示です。Named Scope / Always source は local filesystem の location を参照でき、Output は書き込み先を指定します。第三者から受け取った Configuration や内容を確認していない Configuration はそのまま実行せず、参照 source、Base Configuration、Selection、Output を確認してください。

生成される Archive README は source filesystem path を default では記録しません。`--paths` を指定すると resolved source path が追加され、absolute path など local environment の情報を含む可能性があります。

詳しい trust boundary と共有時の確認事項は [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) を参照してください。

## なぜ dirpluck を使うのか

一度だけ ZIP を作るなら、手作業の方が簡単な場合もあります。

dirpluck が役立つのは、「今回どの file を渡すか」という判断を次回も再利用したい場合です。設定ファイルに rule を残しておけば、shell history、過去の会話、人間の記憶に依存せず、同じ意図から Archive を再構成できます。

Target だけを入れ替えたり、複数 Target をまとめたり、固定資料を `always` で添えたりできます。

## 文書

この README は、ひとつの利用例を通して基本的な使い方だけを紹介しています。

- [Getting Started](https://github.com/minoru-jp/dirpluck/blob/main/docs/GETTING_STARTED.md): 最小 Configuration から preview / build までの短い walkthrough。
- [Recipes](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/INDEX.md): 実際の workspace と目的から TOML / CLI の組み合わせを学ぶ use-case guide。
- [Glossary](https://github.com/minoru-jp/dirpluck/blob/main/GLOSSARY.md): 文書全体で使う概念の意味。
- [Configuration Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/configuration/INDEX.md): Scope、Always、Shared、Case、Base Configuration など Configuration authoring の guide。
- [CLI Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/cli/INDEX.md): Target 指定、CLI option、Invocation Template の guide。
- [Python API](https://github.com/minoru-jp/dirpluck/blob/main/docs/python_api/INDEX.md): CLI と同じ execution model を Python から使う最小の公式 API。
- [Specification](https://github.com/minoru-jp/dirpluck/blob/main/docs/specification/INDEX.md): Configuration composition、resolution、matching、filesystem traversal、Archive、Output、validation の厳密な規則。
- [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md): Configuration、filesystem、外部共有に関する trust boundary。
- [Changelog](https://github.com/minoru-jp/dirpluck/blob/main/CHANGELOG.md): release history。
- [Status](https://github.com/minoru-jp/dirpluck/blob/main/STATUS.md): 現在の開発段階、互換性方針、公開形態。

## ライセンス

dirpluck は MIT License のもとで公開されています。

詳細は [LICENSE](https://github.com/minoru-jp/dirpluck/blob/main/LICENSE) を参照してください。
