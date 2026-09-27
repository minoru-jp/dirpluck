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
正本は `devdocs/canonical_sources/configuration/output.py` です。
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

# Configuration output

この文書は、Configuration が宣言する Output、fixed / timestamp mode、書き込み境界を説明します。

この guide は Configuration 側の Output authoring を説明し、fixed / timestamp / runtime Output と書き込み境界の厳密な契約は `../specification/output.md` が定義します。CLI runtime Output は `../cli/output.md`、trust boundary は `../TRUST.md` を参照してください。

## Output

出力定義は optional です。共通 definition を提供する Base Configurationだけでなく、`--preview` や runtime Output を使う root Configuration でも Output を省略できます。Runtime Output を指定しない通常 build では、root Configuration 自身に fixed mode または timestamp mode のどちらか一方を直接宣言します。Base の Output は継承されません。

### Fixed output

```toml
[output]
path = "artifacts/review.zip"
overwrite = false
```

`path` は filename まで含む具体的な output file path です。Relative path はこの `[output]` を記述した Configuration file の directory を基準に解決します。

`overwrite` は existing output を置き換えてよいかを表し、既定は `false` です。Output file は毎回通常の新規 file creation と同じ permission semantics で作られ、POSIX では process `umask` が適用されます。`overwrite = true` でも置き換える前の file mode は継承しません。`prefix` / `suffix` は fixed mode では使いません。

### Timestamp output

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` は output directory を指定し、末尾 `/` で directory path であることを表します。Relative path はこの definition を記述した Configuration file の directory を基準に解決します。

Filename は次の形で生成します。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

`prefix` と `suffix` は timestamp mode 専用です。同じ秒に複数 run を意図的に区別したい場合は CLI `--sequence N` を使えます。CLI `--here` や末尾 `/` の `--output PATH`、Python API の末尾 `/` の `output=` で runtime directory Output を指定した場合も、root Configuration が `[output.timestamp]` を持てば `prefix` / `suffix` は automatic filename の naming rule として再利用されます。Configured `path` は runtime destination には使いません。ZIP entry 自体の mtime を統一する policy は Configuration field ではなく、CLI / Invocation Template の `--archive-mtime` / `archive_mtime` で指定します。

### Writable destination

Output は、Configuration だけから書き込み境界を静的に確定できる形に限定します。Fixed output では指定した完全 file path、timestamp output では指定した directory tree が書き込み境界です。

Base chain 上の Output definitions は互いの書き込み境界へ介入できません。Fixed / timestamp の組み合わせごとの overlap 判定は `../specification/INDEX.md` を参照してください。
