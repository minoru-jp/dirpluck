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

Positional `TARGET` は Scope の `target_kind` に応じて directory、regular file、またはその両方から解決します。Directory Target には effective Pluck selection を独立して適用し、file Target はその file 自体を atomic source として収録します。

Literal Target reference は記法だけで entry type を決めます。末尾 `/` なしは file、末尾 `/` ありは directory で、filesystem の実体型から意味を推測しません。Default Scope では `NAME` / `./NAME` が file、`./NAME/` が directory です。`NAME/` は named Scope expansion と同じ形になるため、default Scope の directory では `./` を明示します。Default Scope は常に root Configuration file の directory を root とします。

```console
dirpluck ./acme/ ./contoso/
```

名前付き Scope では `<scope>/<name>` が file、`<scope>/<name>/` が directory です。

```console
dirpluck work/acme/
```

`work/acme/` は `work` Scope 直下の directory `acme/` だけを Target とします。`work` Scope が未定義なら error で、別の relative path interpretation へ fallback しません。Syntax が要求する型を Scope の `target_kind` が許可しない場合も error です。Literal Target が要求した型と同名の実体型が異なる場合、error diagnostic は末尾 `/` の追加または削除を案内します。

Scope 直下の eligible Target candidate をすべて選ぶには、次の expansion form を使います。

```console
dirpluck /
dirpluck work/
```

`/` は default Scope、`work/` は named Scope `work` を全展開します。`/` は filesystem root ではありません。`target_kind = "directory"` では direct child directory、`target_kind = "file"` では direct child regular file、`target_kind = "both"` ではその両方を展開し、再帰列挙しません。Scope の `ignore` に一致する candidate は除外します。未使用の named Scope の path が現在存在しなくても、別の Scope だけを使う実行は失敗しません。

Target selector はすべての `target_kind` で使えます。`[...]` は typed literal Target list です。Item は末尾 `/` なしなら file、末尾 `/` ありなら directory です。`/` は item separatorにも使うため、途中の directory itemでは `NAME//NEXT` のように2連になります。3連以上は error です。最初の `[` と最後の `]` だけが外郭syntaxで、内部の `[` / `]` などは Target name の通常文字として扱います。

```console
dirpluck 'work:[repo-a//repo-b.zip]'
```

`<...>` は regular-expression selector です。Eligible direct-child file は `NAME`、directory は `NAME/` と正規化し、その文字列全体へ Python-compatible regular expression を full-match します。したがって `<repo>` は file、`<repo/>` は directory、`<repo/?>` は両方を明示できます。Pattern は空にできず、512 character 以下です。Invalid regular expression と0件 match は error です。`/` を含めても再帰探索にはならず、candidate は Scope 直下だけです。

この regular-expression Target selector は、Selection の通常 string pattern とは別の役割です。Selection の通常 string は directory tree の予測可能な traversal / name exclusion を制御し、必要なら `{ match = "..." }` で root-relative path 全体へ regular expression を使えます。一方、`<...>` Target selector は eligible な direct-child Target の normalized name の追加絞り込みだけを行います。Selection 側の pattern と structured `match` は `../configuration/selection.md` を参照してください。

```console
dirpluck 'work:<repo-.*/?>'
```

Default Scope では `:[file-a/dir-b/]` / `:<regex>`、named Scope では `work:[file-a/dir-b/]` / `work:<regex>` のように書きます。Selector は `target_kind = "directory"` / `"file"` / `"both"` のすべてで使用でき、Scope の type filter、`ignore`、link-like exclusion で eligible Target を決めてから適用します。`both` で selector が file と directory の両方を解決した場合も、directory にだけ Pluck を適用し、file は atomic source とします。

Shell から使用する場合、`[]`、`<>`、regular-expression metacharacter が shell 自身に解釈されないよう、selector reference 全体を quote してください。

`./` 単独、`/acme`、`work/team/acme`、absolute filesystem path は Target reference として受理しません。`./acme` と `./acme/` はそれぞれ default Scope の file / directory Target を明示する有効な形式です。

Pluck がない Configuration でも file-capable Scope (`target_kind = "file"` / `"both"`) から file Target は選べます。Directory Target は Pluck を必要とします。Target を指定しない Always-only 実行も従来どおり有効です。

```console
dirpluck --config project-snapshot
```

Scope と `ignore` の定義方法は `configuration/INDEX.md`、Target reference、boundary、archive path の厳密な規則は `specification/INDEX.md` を参照してください。

## Case

名前付きケースを選ぶには `--case NAME` を使います。

```console
dirpluck ./acme/ --case audit
```

1回の実行で指定する Case は1個です。Pluck と Always source が Case をどう選ぶかは `specification/INDEX.md` に定義しています。
