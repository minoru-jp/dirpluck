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
正本は `devdocs/canonical_sources/cli/targets.py` です。
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

# Targets and Cases

この文書は positional Target reference、Scope expansion、Case selection を CLI から指定する方法を説明します。

Scope / Namespace の authoring は `../configuration/sources.md`、Case の authoring は `../configuration/selection.md`、厳密な Target / Case semantics は `../specification/runtime-targets.md` に定義されています。

## Target の指定

Positional `TARGET` は Scope の `target_kind` に応じて directory または regular file を解決します。Directory Target には effective Pluck selection を独立して適用し、file Target はその file 自体を atomic source として収録します。

常設の default Scope から1 Target を選ぶ場合は direct-child name だけを指定します。Default Scope は常に root Configuration file の directory を root とします。Configuration を別 directory に置けば default Scope もその directory に移るため、別の Target root が必要な場合は named Scope を定義します。

```console
dirpluck acme contoso
```

名前付き Scope から選ぶ場合は `<scope>/<name>` を使います。

```console
dirpluck work/acme
```

`work/acme` は `work` Scope 直下の `acme` だけを Target とします。`work` Scope が未定義なら error で、別の relative path interpretation へ fallback しません。

Scope 直下の eligible Target candidate をすべて選ぶには、次の expansion form を使います。

```console
dirpluck /
dirpluck work/
```

`/` は default Scope、`work/` は named Scope `work` を全展開します。`/` は filesystem root ではありません。`target_kind = "directory"` では direct child directory、`target_kind = "file"` では direct child regular file だけを展開し、再帰列挙しません。Scope の `ignore` に一致する candidate は除外します。未使用の named Scope の path が現在存在しなくても、別の Scope だけを使う実行は失敗しません。

`./`、`./acme`、`/acme`、`work/team/acme`、absolute filesystem path は Target reference として受理しません。

Pluck がない Configuration でも file-kind Scope の Target reference は使用できます。Directory Target は Pluck を必要とします。Target を指定しない Always-only 実行も従来どおり有効です。

```console
dirpluck --config project-snapshot
```

Scope と `ignore` の定義方法は `configuration/INDEX.md`、Target reference、boundary、archive path の厳密な規則は `specification/INDEX.md` を参照してください。

## Case

名前付きケースを選ぶには `--case NAME` を使います。

```console
dirpluck acme --case audit
```

1回の実行で指定する Case は1個です。Pluck と Always source が Case をどう選ぶかは `specification/INDEX.md` に定義しています。
