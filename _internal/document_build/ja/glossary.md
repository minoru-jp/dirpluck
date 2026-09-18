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
正本は `dirpluck_docs/vocabulary/canonical.py` です。
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

# dirpluck 用語集

dirpluck の文書と実装で共通して使う概念を定義する。ここでは語の意味だけを定め、個数制約、解決順序、エラー条件などの仕様は定義しない。

## dirpluck

宣言された抽出意図に従って source からファイルを選び、ZIP アーカイブを作成する CLI ツール。

## 設定ファイル

dirpluck の抽出意図を TOML で記述した文書。

## 対象

実行時に与える source directory へ共通の選択規則を適用するための source 定義。

## ケース

base とは別の抽出 variation として名前を付けた選択定義。

## コンパニオン

設定ファイルに source directory を固定し、同じ抽出意図へ付随させる source 定義。

## 対象ディレクトリ

対象またはコンパニオンに対応し、実際にファイルを抽出するディレクトリ。

## 抽出

source directory からアーカイブへ含めるファイルを選択規則に従って確定する処理。

## アーカイブ

dirpluck が抽出結果から生成する ZIP 成果物。

## 出力定義

生成するアーカイブの出力先と命名方針を記述する設定。

## アーカイブREADME

アーカイブのルートに生成され、解決済みの抽出計画と含まれる source を示す索引文書。

## 共有パターン

選択定義から参照して再利用する、名前付きの include または exclude パターン集合。

## 設定インポート

別の設定ファイルを内側の layer として取り込み、定義を組み合わせる仕組み。

## ルート設定ファイル

1回の dirpluck 実行を開始する最外側の設定ファイル。

## 実効設定

ルート設定ファイルと設定インポートを解決し、1回の実行に使用する形へ構成した設定。
