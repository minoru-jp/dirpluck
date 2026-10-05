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
正本は `devdocs/canonical_sources/cli/overview.py` です。
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

# CLI overview

この文書は `dirpluck` CLI の基本的な呼び出し方、Configuration の選択、help / version、終了 status を説明します。

Target / Case は `targets.md`、Invocation Template は `invocation-templates.md`、preview と Output runtime option は `output.md` を参照してください。厳密な document selection は `../specification/document-selection.md`、CLI option の組み合わせと終了契約は `../specification/cli-contract.md` に定義されています。

## 基本形

```text
dirpluck [TARGET ...] [--config PATH] [--case CASE] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck -i PATH [-e NAME] [--case CASE] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck --version
```

選択した実効設定に Always source が1個以上あれば、Pluck も定義されている Configuration でも `TARGET` reference を省略し、Always source だけを Archive にできます。Target を指定した場合は従来どおり Pluck を directory Target に適用します。Pluck がなくても `target_kind = "file"` / `"both"` の Scope から file Target は positional argument で選択できます。Directory Target は Pluck を必要とします。

```console
dirpluck ./example/
dirpluck work/project-a/ work/project-b/
dirpluck --config snapshot
```

Target reference は literal reference、Scope expansion、Target selector を使えます。Literal reference は末尾 `/` なしを file、末尾 `/` ありを directory とし、default Scope の directory は `./NAME/`、named Scope では `SCOPE/NAME/` と書きます。`/` / `SCOPE/` は Scope expansion、`:[...]` / `SCOPE:[...]` は typed literal list selector、`:<...>` / `SCOPE:<...>` は regular-expression selector です。どの形式もスコープから対象を選びます。

## Configuration を選ぶ

Configuration document は TOML syntax を使用しますが、filename extension は `.dirpluck` です。`--config` を省略した場合だけ、runtime cwd の `default.dirpluck` を自動的に使用します。これは CLI が暗黙に探す唯一の Configuration です。

別の Configuration は `--config PATH` で明示します。`PATH` は filesystem location と同じ `/` separator の表記を使い、relative path は runtime cwd、absolute path は host filesystem を基準にします。末尾が `.dirpluck` でなければ suffix を付加するため、dot を含む document name もそのまま使えます。Windows でも CLI path separator には `\` ではなく `/` を使います。

```console
dirpluck ./example/ --config review
dirpluck ./example/ --config configs/release-1.2
dirpluck ./example/ --config ../shared/review.dirpluck
```

`--config` を指定した場合は、その path が表す1個の Configuration document だけを使用し、別 directory の同名 file を探索しません。Directory 自体を指定してその中の `default.dirpluck` を補うこともありません。Configuration document path は host OS の通常の filesystem semantics に従って解決し、symbolic link / Windows directory junction を含む path も control document の選択では特別に拒否しません。dirpluck は選択した path の absolute な表記を document location として保持し、その document 内の relative path はその location の directory を基準にします。dirpluck は file 内容から Configuration らしさを推論したり、任意の `*.dirpluck` file を自動選択・列挙したりしません。`.toml` file を Configuration として扱う互換 fallback もありません。

Output は `--preview` には不要です。通常 build では root Configuration 自身の Output declaration、または CLI の runtime Output (`--here` / `--output`) のどちらかを使います。Configuration が `about.base` で参照する Base Configuration は CLI の自動選択対象ではありません。

## Help と version

```console
dirpluck --help
dirpluck --version
```

## 終了とエラー

正常終了は status 0 です。CLI argument error や dirpluck の validation / build error は status 2 で終了し、`dirpluck: error:` に続けて理由を表示します。

Archive を生成する通常実行では、成功すると output path を標準出力へ表示します。Selection traversal で symbolic link / Windows directory junction として認識した entry を除外していた場合は、除外件数も informational note として表示します。この runtime note は Archive 内の README には書き込みません。
