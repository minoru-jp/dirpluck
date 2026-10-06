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

何を含め、何を除外し、どの固定資料を常に添え、どの追加資料を Case に応じて有効化するかを TOML の設定ファイルとして残せます。たとえば LLM に repository を渡して開発作業を依頼するときに、今回の開発対象、作業手順、必要時だけ使う local wheel などを、同じ rule から再現可能な Archive にまとめられます。

## インストール

現在の version は **0.18.0** です。

Python 3.11 以降を使用します。

```console
pip install dirpluck
dirpluck --version
```

dirpluck には runtime third-party dependency はありません。

0.16.x から upgrade する場合は、Target / Always の final Archive root 一意性と Layout への移行を `docs/migration/0.17.md` で確認してください。0.14.x 以前から upgrade する場合は、先に `docs/migration/0.16.md` の Always Archive identity 変更も確認してください。

## 例: LLM に開発 handoff Archive を渡す

代表例として、LLM-assisted developmentへ渡すhandoff Archiveを作ります。完全版は [LLM development environment Recipe](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/llm-development-environment.md) にあり、ここでは主要な構造だけを抜粋します。

次のようなworkspaceを考えます。

```text
workspace/
├── default.dirpluck
├── handoff/
│   └── DEVELOPMENT.md
├── offline_wheels/
│   └── ...
└── projects/
    ├── service-api/
    └── worker-jobs/
```

Workspace rootの`default.dirpluck`を次のようにします。

```toml
[about]
description = "LLM-assisted development向けのhandoff Archive。"
description_no_targets = "開発対象Targetは選択されていません。"
description_no_always = "support sourceは有効ではありません。"
description_empty = "sourceは選択されておらず、generated READMEだけを収録します。"
always_layout = "support"
targets_layout = "development-targets"

[layout.support]
description = "開発時に参照する作業指示。"

[layout.dependencies]
description = "offline環境で使用する開発dependency。"

[layout.development-targets]
description = "今回の開発対象として選択されたrepository。"

[always.handoff]
description = "どの通常handoffにも添える開発手順。"
path = "handoff"
must = ["DEVELOPMENT.md"]

[extra.offline_wheels]
description = "package indexを利用できない環境向けのwheelhouse。"
path = "offline_wheels"
must = ["*.whl"]
layout = "dependencies"

[scope.projects]
description = "開発対象として選択できるrepository。"
path = "projects"

[pluck]
description = "LLMへ渡す通常のproject file。"
may = ["*", "*/"]
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pyc",
]

[case.always.offline]
description = "package indexへ接続できないhandoff先。"
add = ["offline_wheels"]

[output]
path = "develop-target.zip"
overwrite = true
```

この例では、常に必要な作業指示を`always`、offline環境だけで必要なwheelhouseを`extra`として定義します。Extraは定義しただけではinactiveで、`.offline` Always Caseからaddされたrunだけで有効になります。

Layoutはsupport material、dependency、development TargetをArchive内で分離します。`description_no_targets`などのconditional descriptionはsourceの有無に応じた補足をgenerated READMEへ追加し、通常の`description`は常に表示されます。

### Preview と Build

通常のhandoffはExtraを有効化せずpreviewします。

```console
dirpluck projects/service-api/ --preview
```

package indexへ接続できないhandoff先では`.offline` Always Caseを選びます。

```console
dirpluck projects/service-api/ --case .offline --preview
```

概念的には次のArchiveになります。

```text
develop-target.zip
├── README.md
├── support/
│   └── handoff/
│       └── DEVELOPMENT.md
├── dependencies/
│   └── offline_wheels/
│       └── ...
└── development-targets/
    └── service-api/
        └── ...
```

内容に問題がなければ`--preview`を外してbuildします。Pluck Caseとの組み合わせやREADME-only Archiveを含む完全な例は [Recipe](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/llm-development-environment.md) を参照してください。

### Filesystem の注意

自動的な Target discovery と Selection traversal で見つかった symbolic link や認識済み Windows directory junction は追跡せず、Archive にも含めません。詳細な filesystem boundary は [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) を参照してください。

## Archive を共有する前に

dirpluck は、file の名前や内容から「これは秘密情報なので共有してはいけない」と判断しません。

上の例にある `.git/`、`.venv/`、`.env*`、`*.pem`、`*.key` などの ignore は有用ですが、**security boundary ではありません**。Project 固有の credential、秘密鍵、個人情報、顧客 data、local 設定、test fixture などは別の名前や場所に存在する可能性があります。

外部の相手や non-local の LLM に Archive を渡す場合は、共有前に `--preview` で選択内容を確認してください。

設定ファイル自体も filesystem 操作の指示です。Named Scope / Always / Extra source は local filesystem の location を参照でき、Output は書き込み先を指定します。第三者から受け取った Configuration や内容を確認していない Configuration はそのまま実行せず、参照 source、Base Configuration、Selection、Output を確認してください。

生成される Archive README は source filesystem path を default では記録しません。`--paths` を指定すると resolved source path が追加され、absolute path など local environment の情報を含む可能性があります。

詳しい trust boundary と共有時の確認事項は [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) を参照してください。

## なぜ dirpluck を使うのか

一度だけ ZIP を作るなら、手作業の方が簡単な場合もあります。

dirpluck が役立つのは、「今回どの file を渡すか」という判断を次回も再利用したい場合です。設定ファイルに rule を残しておけば、shell history、過去の会話、人間の記憶に依存せず、同じ意図から Archive を再構成できます。

Target だけを入れ替えたり、複数 Target をまとめたり、固定資料を `always` で添えたり、追加資料を `extra` と Always Case で必要な run だけ有効化したり、Layout で Archive 内の役割を分けたりできます。

## 文書

この README は、ひとつの利用例を通して基本的な使い方だけを紹介しています。

- [Getting Started](https://github.com/minoru-jp/dirpluck/blob/main/docs/GETTING_STARTED.md): 最小 Configuration から preview / build までの短い walkthrough。
- [Recipes](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/INDEX.md): 実際の workspace と目的から TOML / CLI の組み合わせを学ぶ use-case guide。
- [Glossary](https://github.com/minoru-jp/dirpluck/blob/main/GLOSSARY.md): 文書全体で使う概念の意味。
- [Configuration Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/configuration/INDEX.md): Scope、Always、Extra、Layout、Shared、Case、Base Configuration など Configuration authoring の guide。
- [CLI Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/cli/INDEX.md): Target 指定、CLI option、Invocation Template の guide。
- [Python API](https://github.com/minoru-jp/dirpluck/blob/main/docs/python_api/INDEX.md): CLI と同じ execution model を Python から使う最小の公式 API。
- [Specification](https://github.com/minoru-jp/dirpluck/blob/main/docs/specification/INDEX.md): Configuration composition、resolution、matching、filesystem traversal、Archive、Output、validation の厳密な規則。
- [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md): Configuration、filesystem、外部共有に関する trust boundary。
- [Changelog](https://github.com/minoru-jp/dirpluck/blob/main/CHANGELOG.md): release history。
- [Status](https://github.com/minoru-jp/dirpluck/blob/main/STATUS.md): 現在の開発段階、互換性方針、公開形態。

## ライセンス

dirpluck は MIT License のもとで公開されています。

詳細は [LICENSE](https://github.com/minoru-jp/dirpluck/blob/main/LICENSE) を参照してください。
