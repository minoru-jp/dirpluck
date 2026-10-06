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
正本は `devdocs/canonical_sources/configuration/composition.py` です。
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

# Configuration composition

この文書は、`[about].base` を使った Base Configuration の再利用と filesystem anchor の考え方を説明します。

この guide は Base Configuration の authoring を説明し、base chain、shadowing、cycle detection の厳密な契約は `../specification/composition.md`、relative path anchor は `../specification/paths.md` が定義します。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。

## Base Configuration

既存の Configuration を基礎として再利用するときは、`[about]` の `base` で基底設定ファイルを参照します。

```toml
[about]
base = "../common/common.dirpluck"
```

`base` は1個の Configuration file を参照します。参照先がさらに `base` を持つ場合は linear base chain になります。Base chain の深さに固定上限はありません。

各 Configuration に書かれた relative filesystem path は、常にその Configuration file 自身の directory を基準に解決します。Base Configuration から継承した named Scope や Always / Extra source の path を、外側 Configuration の位置へ rebase しません。Default Scope も同じ Configuration-directory model に従い、Root Configuration file の directory をそのまま root とします。

Pluck、Always、Extra、Scope、Layout、Shared pattern の composition、`[about]` の description / default Layout resolution、cycle detection、Output の扱いは `../specification/INDEX.md` に定義します。Layout definition は名前ごとに合成し、外側の同名 definition が内側を置き換えます。Layout reference は composition 後の effective Layout 集合に対して解決します。Base Configuration は Output を省略できます。Output を持たない root Configuration も `--preview` に使用でき、通常 build でも CLI `--here` / `--output` または Python API `output=` で runtime Output を与えれば実行できます。Runtime Output を使わない build では root 自身の fixed または timestamp Output を直接宣言します。
