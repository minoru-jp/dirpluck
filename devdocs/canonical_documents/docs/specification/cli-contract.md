<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/cli_contract.py` です。
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

# CLI contract

## SPEC_148

CLI が受理する主な form は次とする。

```console
dirpluck TARGET [TARGET ...]
dirpluck --config PATH
dirpluck TARGET [TARGET ...] --case CASE
dirpluck --config PATH --case CASE
dirpluck -i PATH [-e NAME] [--case CASE]
dirpluck --invocation-template PATH [--entry NAME] [--case CASE]
dirpluck ... --preview
dirpluck ... --paths
dirpluck ... --sequence N
dirpluck ... --archive-mtime VALUE
dirpluck ... --here[=FILENAME]
dirpluck ... -o PATH
dirpluck ... --output PATH
dirpluck ... -f
dirpluck ... --force
dirpluck --version
```

level: MUST

## SPEC_149

Positional argument は Runtime Target, Scope, and Case の CLI Target reference rules で解決する。Positional Target reference は常に0個以上を受理する。0個の場合は Pluck を source selection に使用せず、Always source があればそれらだけを解決し、Always source もなければ resolved source 0件の README-only Archive として正常に実行する。Target reference を指定した場合、Pluck がない Configuration でも `target_kind = "file"` / `"both"` の Scope から file Target reference は受理するが、directory Target は受理しない。

level: MUST

condition: positional Target reference を0個または1個以上指定する場合

related: [SPEC_037](runtime-targets.md#spec_037)

## SPEC_150

`--case`、`--sequence`、`--archive-mtime`、`--here`、`-o` / `--output`、`-i` / `--invocation-template`、`-e` / `--entry` はそれぞれ最大1回だけ指定できる。`-e` / `--entry` は Invocation Template と一緒にだけ使用できる。Invocation Template を指定した場合は positional `TARGET` と `--config` を受理しない。`--case` は Invocation Template と併用でき、指定時は選択した Invocation の `case` を上書きする。`--archive-mtime VALUE` も Invocation Template と併用でき、指定時は選択した Invocation の `archive_mtime` を上書きする。`VALUE` は Output の Archive entry timestamp grammar に従う。`--here` と `--output` は相互排他とし、`--here` の optional filename は `--here=FILENAME` の form でだけ指定する。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--sequence` は1以上の integer を受理し、automatic timestamp filename の effective Output でだけ使用する。`-f` / `--force` は effective overwrite policy を true にする。`--here` / `--output` / `--force`、`--preview`、`--sequence`、`--archive-mtime`、`--paths` は Invocation Template と併用できる。`--paths` は通常 build で生成するアーカイブREADMEの各 source section へ `Source` metadata を追加する。`--preview` と組み合わせても Archive は生成されないため、表示 tree に source filesystem path を追加しない。

level: MUST

related: [SPEC_009](document-selection.md#spec_009), [SPEC_122](output.md#spec_122), [SPEC_129](output.md#spec_129), [SPEC_131](output.md#spec_131), [SPEC_132](output.md#spec_132), [SPEC_145](preview.md#spec_145)

## SPEC_151

Argument parse error と dirpluck の Configuration / build error は status 2 で終了する。Successful build と informational command は status 0 とする。通常 build の成功時は final output path を標準出力から取得できるようにする。Resolved source が0件なら、通常 build / `--preview` のどちらでも `README.md` だけの Archive plan になったことを informational output として扱い、warning semantics は与えない。Field を1つも持たない Invocation を選択した成功実行では、保存済み実行入力がなく CLI runtime value と normal defaults を使うことを informational note として示す。これらの人間向け文言と表示順序の細部は互換性契約に含めない。

level: MUST

condition: CLI execution が終了する場合

## SPEC_152

Base chain 用の追加 CLI path や layer ごとの Case option は提供しない。Base chain は TOML の `about.base`、Case は composition 後の実効設定へ適用する。

level: MUST NOT

related: [SPEC_025](composition.md#spec_025), [SPEC_030](composition.md#spec_030)
