<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    },
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/vocabulary/canonical.py` です。
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

# dirpluck 用語集

dirpluck の文書と実装で共通して使う概念を定義する。ここでは語の意味だけを定め、個数制約、解決順序、path の基準、CLI 文法、validation、error 条件などの仕様は定義しない。

## dirpluck

宣言された抽出意図に従って source から file を選び、ZIP Archive を作成する tool。CLI と最小の Python API を利用入口として持つ。

## 設定ファイル

dirpluck の抽出意図と、その意図に必要な source、selection、output などを TOML syntax で記述し、`.dirpluck` 拡張子で識別する文書。

## 対象

実行時にスコープから選ばれ、pluck の selection が適用される source directory。

## ケース

同じ source に対して base selection とは別の抽出 variation を表す、名前付きの selection。

## 常時ソース

Configuration に source directory を固定し、実行のたびに同じ抽出意図へ参加させる source definition。

## ソース

1回の実行で file selection の対象となる filesystem directory。対象と常時ソースは、source が実行へ参加する方法の違いを表す。

## 選択

source から Archive に含める file を、宣言された pattern と policy に従って決めること、またはそのための定義。

## アーカイブ

dirpluck が selection result から生成する ZIP artifact。

## 出力定義

生成する Archive の書き込み先と命名方法を宣言する Configuration definition。

## アーカイブREADME

Archive の root に生成され、含まれる source と内容を示す index document。

## pluck

今回の実行で選ばれた対象から何を取り出すかを表す selection definition。

## 共有パターン

複数の selection から名前で参照して再利用する pattern set。

## 基底設定ファイル

別の Configuration が自身の基礎として参照し、その definition を引き継いで構成する Configuration file。

## ルート設定ファイル

1回の dirpluck 実行で CLI から選ばれる最外側の Configuration file。

## 実効設定

ルート設定ファイルとその base chain を解決し、1回の実行に使用する形へ構成した Configuration。

## スコープ

実行時に対象を探す filesystem 上の範囲。

## 書き込み境界

ひとつの output definition が Archive を書き込める filesystem 上の範囲として、Configuration から静的に定まる境界。

## ネームスペース

source を Archive 内で区別して配置するために、source root の外側へ追加する Archive 専用の名前空間。

## Invocation Template

Configuration、CLI Target reference、Case などの実行入力を、再利用可能な呼び出しとして保存する `.dirpluck-inv` document。
