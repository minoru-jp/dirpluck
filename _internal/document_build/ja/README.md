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

バックアップのように周辺をすべて複製するのではなく、レビュー、引き渡し、調査、定例作業、LLM と扱う作業コンテキストなど、明示した目的に必要な範囲だけをまとめることを目的とします。

## 何に使うか

### 固定された複数の資料をひとつにまとめる

必要な資料が別々のディレクトリに置かれていても、それらが同じ目的に属するなら、コンパニオンとして設定ファイルへ固定できます。Companion の source directory は Configuration の近くに置く必要はなく、filesystem 上の別の場所を直接参照できます。

たとえば提案資料、調査結果、法務資料をひとつのレビュー用パッケージにしたり、週次作業で毎回同じ種類の資料を集めたりできます。実行時に変わる対象がない用途では、Companion だけでもアーカイブを作れます。

### 実行ごとに変わる対象へ固定資料を付ける

異なるプロジェクト、提出物、案件などへ毎回同じ選択規則を適用したい場合は、対象を使います。Target の選択規則は Configuration に残し、実際の対象ディレクトリは実行時に選びます。

通常は cwd 直下の directory を Target として選べます。Configuration workspace と Target の実体を別の場所で管理したい場合は、ターゲットロケーションに filesystem 上の起点を名前付きで定義し、`work/project` のように location 直下の directory を選べます。`work/` と指定すれば、その location 直下の eligible directory を一括して Target にできます。Target は cwd または location の直下に限定し、Target の中に別の Target candidate を再帰的に設けません。

固定ガイドライン、テンプレート、参照資料などは Companion として同じアーカイブへ加えられます。これにより、Configuration の置き場所、実行時の Target、固定資料を互いに独立して配置できます。

### 別の Configuration が表す抽出意図を再利用する

関連するプロジェクトに既に設定ファイルがある場合は、設定インポートでその定義を内側の layer として利用できます。親側で同じ情報をコピーする必要はありません。

Import の解決順序、shadowing、filesystem boundary などの厳密な規則は `docs/SPECIFICATION.md` にまとめています。Configuration を書くために必要な形だけを知りたい場合は `docs/CONFIGURATION.md` を参照してください。

## 宣言として残す理由

一度きりなら手作業で ZIP を作る方が簡単です。dirpluck が役立つのは、同じ種類の判断を後でもう一度行うときです。

Configuration に残しておけば、何を含めるか、何を任意扱いにするか、何を除外するか、どの固定資料を伴わせるかを、シェル履歴や会話履歴、人間の記憶へ依存せず確認できます。`--dry-run` を使えば、出力を書き込む前に現在の filesystem に対する解決結果を確認できます。

LLM と扱う作業でも、dirpluck の役割はローカル filesystem から必要な材料を選んで Archive を用意するところまでです。非ローカルの対話型 LLM にはその Archive をアップロードし、ローカル agent 型の LLM では workspace へ配置する受け渡し物として使えます。LLM が dirpluck を操作することを前提としません。

## Configuration と filesystem の信頼境界

外部へ渡す Archive を作る場合は、作成前に selection を確認してください。dirpluck はどの file が機密かを推論しないため、含めるべきでないものは `exclude` で明示します。たとえば次のように書けます。

```toml
exclude = [".git/", ".env*", "*.pem", "*.key"]
```

これは一例であり、project 固有の機密情報は別の名前や場所に存在し得ます。Configuration をどのような入力として扱うか、absolute path、overwrite、外部へ渡す Archive の確認責任などは `docs/TRUST.md` にまとめています。

## 小さな例

次の Configuration は、実行時の Target と固定ガイドラインをひとつのアーカイブへまとめます。

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
skip = ["archive", "tmp-*"]
if_empty = "allow"

[target.location.work]
path = "/srv/projects"
skip = ["archive"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck work/example --dry-run
dirpluck work/example
```

TOML の各 field とより大きな例は `docs/CONFIGURATION.md`、CLI option と Configuration discovery は `docs/CLI.md` を参照してください。

## インストール

Python 3.11 以降を使用します。現在のリリースは `0.8.0` です。

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
- `docs/TRUST.md`: Configuration と filesystem 操作の信頼境界、確認すべき責任範囲。
- `CHANGELOG.md`: リリース履歴。

wheel には、インストール後すぐ Configuration を書いて CLI を実行できるよう、簡潔な `dirpluck/docs/CONFIGURATION.md` と `dirpluck/docs/CLI.md` に加えて、同じ trust model を説明する `dirpluck/docs/TRUST.md` を同梱します。より詳しい説明が必要な場合は、sdist またはリポジトリに含まれる上記文書を参照してください。

## 公開インターフェース

互換性を保証する公開面は `dirpluck` CLI と TOML Configuration 形式です。パッケージ内の Python モジュールは、明示的に公開 API とされない限り内部実装として扱います。
