<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `dirpluck_docs/readme/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `_internal/document_build/ja/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck

dirpluck は、繰り返し現れる「どのファイルを一緒に扱うか」という判断を TOML に残し、同じ意図から ZIP アーカイブを組み立てる CLI ツールです。

バックアップのように周辺をすべて複製するのではなく、レビュー、引き渡し、調査、定例作業、LLM と扱う作業コンテキストなど、明示した目的に必要な範囲だけを再現可能にまとめることを目的とします。

## 何に使うか

### 固定された複数の資料をひとつにまとめる

必要な資料が別々のディレクトリに置かれていても、それらが同じ目的に属するなら、コンパニオンとして設定ファイルへ固定できます。Companion の source directory は Configuration の近くに置く必要はなく、filesystem 上の別の場所を直接参照できます。

たとえば提案資料、調査結果、法務資料をひとつのレビュー用パッケージにしたり、週次作業で毎回同じ種類の資料を集めたりできます。実行時に変わる対象がない用途では、Companion だけでもアーカイブを作れます。

### 実行ごとに変わる対象へ固定資料を付ける

異なるプロジェクト、提出物、案件などへ毎回同じ選択規則を適用したい場合は、対象を使います。Target の選択規則は Configuration に残し、実際の対象ディレクトリは実行時に与えます。

固定ガイドライン、テンプレート、参照資料などは Companion として同じアーカイブへ加えられます。これにより、対象だけを変えながら同じ抽出意図を繰り返せます。

### 別の Configuration が表す抽出意図を再利用する

関連するプロジェクトに既に設定ファイルがある場合は、設定インポートでその定義を内側の layer として利用できます。親側で同じ情報をコピーする必要はありません。

Import の解決順序、shadowing、filesystem boundary などの厳密な規則は `docs/SPECIFICATION.md` にまとめています。Configuration を書くために必要な形だけを知りたい場合は `docs/CONFIGURATION.md` を参照してください。

## 宣言として残す理由

一度きりなら手作業で ZIP を作る方が簡単です。dirpluck が役立つのは、同じ種類の判断を後でもう一度行うときです。

Configuration に残しておけば、何を含めるか、何を任意扱いにするか、何を除外するか、どの固定資料を伴わせるかを、シェル履歴や会話履歴、人間の記憶へ依存せず確認できます。`--dry-run` を使えば、出力を書き込む前に現在の filesystem に対する解決結果を確認できます。

LLM と継続して作業する場合も同じです。必要な source の集合を会話の中だけに保持するのではなく Configuration として残せば、人間と LLM が同じ宣言を読み、同じ対象範囲を再構成できます。

## 選択は明示的です

dirpluck は「重要そうなファイル」「最新らしい成果物」「秘密情報らしいファイル」を推論しません。Configuration に書かれた選択規則を適用します。

特にディレクトリ全体や `*` のような広い範囲を含める場合、その配下にある `.git/`、環境ファイル、秘密鍵なども、明示的に除外しない限り候補になります。外部へ渡すアーカイブでは、対象 workspace に応じた除外を Configuration で確認してください。

この狭いモデルにより、「何を一緒に扱うか」という判断そのものを Configuration 上へ残します。

## 小さな例

次の Configuration は、実行時の Target と固定ガイドラインをひとつのアーカイブへまとめます。

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck projects/example --dry-run
dirpluck projects/example
```

TOML の各 field とより大きな例は `docs/CONFIGURATION.md`、CLI option と Configuration discovery は `docs/CLI.md` を参照してください。

## インストール

Python 3.11 以降を使用します。現在のリリースは `0.6.0` です。

```console
pip install dirpluck
dirpluck --version
```

実行時のサードパーティ依存はありません。

## 文書

文書は読む目的で分けています。

- `GLOSSARY.md`: 文書全体で使う概念の意味。
- `docs/CONFIGURATION.md`: TOML Configuration を書くためのガイド。
- `docs/CLI.md`: CLI を実行するためのガイド。
- `docs/SPECIFICATION.md`: 解決、matching、filesystem、archive、output、validation の厳密な規則。
- `CHANGELOG.md`: リリース履歴。

wheel には、インストール後すぐ Configuration を書いて CLI を実行できるよう、簡潔な `dirpluck/docs/CONFIGURATION.md` と `dirpluck/docs/CLI.md` だけを同梱します。より詳しい説明が必要な場合は、sdist またはリポジトリに含まれる上記文書を参照してください。

## 公開インターフェース

互換性を保証する公開面は `dirpluck` CLI と TOML Configuration 形式です。パッケージ内の Python モジュールは、明示的に公開 API とされない限り内部実装として扱います。
