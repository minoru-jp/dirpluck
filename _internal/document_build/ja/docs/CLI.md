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
正本は `dirpluck_docs/cli/canonical.py` です。
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

# dirpluck CLI Guide

この文書は `dirpluck` CLI の使い方を説明します。TOML の書き方は `CONFIGURATION.md`、解決や validation の厳密な意味論は `SPECIFICATION.md` を参照してください。

## 基本形

```text
dirpluck [DIRECTORY ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
dirpluck --configs
dirpluck --version
```

選択した実効設定に対象がある場合は、1個以上の `DIRECTORY` を指定します。Target がない場合は positional directory を指定しません。

```console
dirpluck projects/example
dirpluck projects/a projects/b
dirpluck --config snapshot
```

Target definition が import 先から来た場合でも、実際の Target directory は同じく CLI `DIRECTORY` から与えます。

## Configuration を選ぶ

既定では `dirpluck.toml` を使用します。別名の Configuration は `--config NAME` で選びます。`.toml` は省略できます。

```console
dirpluck projects/example --config review
```

ルート設定ファイルの discovery は cwd と `./dirpluck/` の直下だけを対象にします。同じ filename が両方にある場合は ambiguous として扱います。

検出できる Configuration は次で確認できます。

```console
dirpluck --configs
```

`--configs` は一覧表示だけを行い、build option や `DIRECTORY` とは組み合わせません。

## Target directory

Target がある Configuration では、各 `DIRECTORY` に同じ Target selection が独立して適用されます。

```console
dirpluck submissions/acme submissions/contoso
```

Target がない Configuration は Companion など固定 source だけで実行できます。

```console
dirpluck --config project-snapshot
```

許可される path と filesystem boundary の厳密な規則は `SPECIFICATION.md` を参照してください。

## Case

名前付きケースを選ぶには `--case NAME` を使います。

```console
dirpluck projects/example --case audit
```

1回の実行で指定する Case は1個です。Target と Companion が Case をどう選ぶかは `SPECIFICATION.md` に定義しています。

## Dry run

`--dry-run` は archive file を作らず、解決した ZIP contents を tree として表示します。

```console
dirpluck projects/example --dry-run
```

Configuration や workspace を変更した後、実際に archive を書き込む前の確認に使えます。通常実行との差分は書き込みだけで、planning に使う主要な解決処理は共通です。正確な dry-run semantics は `SPECIFICATION.md` を参照してください。

## Archive index の source path

生成されるアーカイブREADMEは、既定では archive path、`description`、選択 file 数だけを示す簡潔な索引です。Target / Companion、Configuration、Case など dirpluck 固有の内部情報や、source filesystem path は記録しません。

Source filesystem path も索引へ含めたい場合だけ `--paths` を指定します。

```console
dirpluck projects/example --paths
```

`--paths` は各索引行に解決済み source directory を追加します。Absolute path を含むローカル filesystem 情報を archive に残し得るため、外部へ配布する archive では必要性を確認して使用してください。

## Generated output の sequence

Generated output を使う Configuration で、同じ秒に複数 run を意図的に区別したい場合は正の整数 `--sequence N` を指定できます。

```console
dirpluck --config project-snapshot --sequence 2
```

`--sequence` は自動採番ではありません。Fixed output では使えません。Filename の正確な配置と collision rules は `SPECIFICATION.md` を参照してください。

## Help と version

```console
dirpluck --help
dirpluck --version
```

## 終了とエラー

正常終了は status 0 です。CLI argument error や dirpluck の validation / build error は status 2 で終了し、`dirpluck: error:` に続けて理由を表示します。

Archive を生成する通常実行では、成功すると出力 path を標準出力へ表示します。

## 次に読む文書

- Configuration を新しく書く、または変更する: `CONFIGURATION.md`
- 用語の意味を確認する: `../GLOSSARY.md`
- Configuration と filesystem 操作の信頼境界を確認する: `TRUST.md`
- import resolution、matching、filesystem boundary、Archive README、output collision などを正確に確認する: `SPECIFICATION.md`
