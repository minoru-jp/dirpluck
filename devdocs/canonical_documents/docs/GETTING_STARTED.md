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
正本は `devdocs/canonical_sources/getting_started/canonical.py` です。
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

# Getting started with dirpluck

この文書では、最小構成から dirpluck を試し、preview で内容を確認してから Archive を生成するまでを通して説明します。

Configuration field の詳細は `configuration/INDEX.md`、CLI option と Invocation Template は `cli/INDEX.md`、trust boundary は `TRUST.md` を参照してください。

## 1. Configuration を作る

`--config` を指定しない場合、dirpluck は runtime cwd の `default.dirpluck` を使用します。まずは次の内容を `default.dirpluck` として保存します。

```toml
[about]
description = "Review package for the example project."

[pluck]
description = "Project files selected for review."
must = ["README.md", "src/", "tests/"]
ignore = [".git/", "__pycache__/", "*.pyc"]

[always.guidelines]
path = "review-guidelines"
description = "Review guidelines shared across projects."
must = ["*.md"]

[output]
path = "review.zip"
```

`pluck` は実行時に選ぶ Target から収集する内容、`always.guidelines` は毎回一緒に収集する固定 source、`output` は生成先を定義しています。

## 2. 対象を用意する

同じ directory に、たとえば次の file があるとします。

```text
.
├── default.dirpluck
├── example/
│   ├── README.md
│   ├── src/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
└── review-guidelines/
    └── review.md
```

`example/` が実行時に選ぶ 対象、`review-guidelines/` が Configuration に固定した Always source です。

## 3. Preview で確認する

Archive を書き込む前に `--preview` で contents plan を確認します。

```console
dirpluck ./example/ --preview
```

この例では次のように表示されます。

```text
├── README.md
├── example/
│   ├── README.md
│   ├── src/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
└── review-guidelines/
    └── review.md
```

先頭の `README.md` は、dirpluck が Archive の内容を説明するために生成する file です。

## 4. Archive を作る

Preview に問題がなければ、同じ Target で Archive を作成します。

```console
dirpluck ./example/
```

`[output]` に従って `review.zip` が作成され、preview で確認した file と生成された `README.md` が入ります。この例の Archive README は次の内容です。

```markdown
# Archive contents

Review package for the example project.

## `example/`

Files: 3

Project files selected for review.

## `review-guidelines/`

Files: 1

Review guidelines shared across projects.
```

## 次に読む

Configuration の `description` は抽出意味論を変えず、生成される Archive README に人間向けの context を追加します。Scope、Namespace、Case、Shared patterns、Base Configuration、Output の詳細は `configuration/INDEX.md` に分けています。

同じ Configuration / Target / Case の組み合わせを繰り返す場合は `.dirpluck-inv` Invocation Template に呼び出しを保存できます。詳しくは `cli/INDEX.md` を参照してください。

外部へ渡す Archive を扱う場合は、広い selection や機密 file の扱いを `TRUST.md` で確認してください。
