from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} CLI Guide")
class TITLE_1:
    r'''この文書は `dirpluck` CLI の使い方を説明します。TOML の書き方は `CONFIGURATION.md`、解決や validation の厳密な意味論は `SPECIFICATION.md` を参照してください。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("基本形")
    class TITLE_2:
        r'''```text
{{TERM_1}} [DIRECTORY ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
{{TERM_1}} --configs
{{TERM_1}} --version
```

選択した{{TERM_15}}に{{TERM_3}}がある場合は、1個以上の `DIRECTORY` を指定します。Target がない場合は positional directory を指定しません。

```console
{{TERM_1}} projects/example
{{TERM_1}} projects/a projects/b
{{TERM_1}} --config snapshot
```

Target definition が import 先から来た場合でも、実際の Target directory は同じく CLI `DIRECTORY` から与えます。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_3, terms.TERM_15)

    @title("Configuration を選ぶ")
    class TITLE_3:
        r'''既定では `dirpluck.toml` を使用します。別名の Configuration は `--config NAME` で選びます。`.toml` は省略できます。

```console
{{TERM_1}} projects/example --config review
```

{{TERM_14}}の discovery は cwd と `./dirpluck/` の直下だけを対象にします。同じ filename が両方にある場合は ambiguous として扱います。

検出できる Configuration は次で確認できます。

```console
{{TERM_1}} --configs
```

`--configs` は一覧表示だけを行い、build option や `DIRECTORY` とは組み合わせません。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_14)

    @title("Target directory")
    class TITLE_4:
        r'''Target がある Configuration では、各 `DIRECTORY` に同じ Target selection が独立して適用されます。

```console
{{TERM_1}} submissions/acme submissions/contoso
```

Target がない Configuration は Companion など固定 source だけで実行できます。

```console
{{TERM_1}} --config project-snapshot
```

許可される path と filesystem boundary の厳密な規則は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Case")
    class TITLE_5:
        r'''名前付き{{TERM_4}}を選ぶには `--case NAME` を使います。

```console
{{TERM_1}} projects/example --case audit
```

1回の実行で指定する Case は1個です。Target と Companion が Case をどう選ぶかは `SPECIFICATION.md` に定義しています。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_4)

    @title("Dry run")
    class TITLE_6:
        r'''`--dry-run` は archive file を作らず、解決した ZIP contents を tree として表示します。

```console
{{TERM_1}} projects/example --dry-run
```

Configuration や workspace を変更した後、実際に archive を書き込む前の確認に使えます。通常実行との差分は書き込みだけで、planning に使う主要な解決処理は共通です。正確な dry-run semantics は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Archive index の source path")
    class TITLE_65:
        r'''生成される{{TERM_10}}は、既定では archive path、`description`、選択 file 数だけを示す簡潔な索引です。Target / Companion、Configuration、Case など dirpluck 固有の内部情報や、source filesystem path は記録しません。

Source filesystem path も索引へ含めたい場合だけ `--paths` を指定します。

```console
{{TERM_1}} projects/example --paths
```

`--paths` は各索引行に解決済み source directory を追加します。Absolute path を含むローカル filesystem 情報を archive に残し得るため、外部へ配布する archive では必要性を確認して使用してください。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_10)

    @title("Generated output の sequence")
    class TITLE_7:
        r'''Generated output を使う Configuration で、同じ秒に複数 run を意図的に区別したい場合は正の整数 `--sequence N` を指定できます。

```console
{{TERM_1}} --config project-snapshot --sequence 2
```

`--sequence` は自動採番ではありません。Fixed output では使えません。Filename の正確な配置と collision rules は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Help と version")
    class TITLE_8:
        r'''```console
{{TERM_1}} --help
{{TERM_1}} --version
```'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("終了とエラー")
    class TITLE_9:
        r'''正常終了は status 0 です。CLI argument error や dirpluck の validation / build error は status 2 で終了し、`dirpluck: error:` に続けて理由を表示します。

Archive を生成する通常実行では、成功すると出力 path を標準出力へ表示します。'''

    @title("次に読む文書")
    class TITLE_10:
        r'''- Configuration を新しく書く、または変更する: `CONFIGURATION.md`
- 用語の意味を確認する: `../GLOSSARY.md`
- Configuration と filesystem 操作の信頼境界を確認する: `TRUST.md`
- import resolution、matching、filesystem boundary、Archive README、output collision などを正確に確認する: `SPECIFICATION.md`'''
