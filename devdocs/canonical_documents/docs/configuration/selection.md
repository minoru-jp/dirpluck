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
正本は `devdocs/canonical_sources/configuration/selection.py` です。
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

# Configuration selection

この文書は、各 source から何を収集するかを定義する Selection、再利用可能な Shared patterns、Case variation を説明します。

この guide は Selection authoring を説明し、pattern grammar と validation の厳密な契約は `../specification/selection.md`、filesystem entry の boundary は `../specification/filesystem.md` が定義します。CLI からの Target / Case 操作は `../cli/targets.md`、trust boundary は `../TRUST.md` を参照してください。

## Selection

Directory Target の Pluck、Always source、Case はそれぞれ独立した選択を持ちます。Selection では `must` / `may` / `ignore`、必要に応じて `allow_empty` を記述し、人間向けの説明を添えたい場合だけ `description` を使います。File Target は atomic source なので Selection を持ちません。

Selection pattern と file-kind Scope の regular-expression selector は、意図的に同じ pattern language にはしていません。`must` / `may` / `ignore` は directory tree を予測可能に探索・除外するための制限された path / name pattern を使います。一方、file-kind Scope の `<...>` selector は、すでに eligible と判定された direct-child file の basename をさらに絞り込む補助的な手段として Python-compatible regular expression を使います。Regular-expression selector の使い方は `../cli/targets.md` を参照してください。

### `description`

その source が抽出意図の中で果たす役割を書きます。生成されるアーカイブREADMEでは、この description が archive path の意味を説明するために使われます。

```toml
description = "Reference material used to evaluate the submission."
```

`description` は任意です。省略しても selection の抽出意味論は変わりません。記述する場合は空でない string とし、生成される Archive README ではその source の見出しと file 数に続く本文として使われます。複数行の説明も table cell へ圧縮せず、そのまま section body として表示します。

### `must`

存在を要求し、存在するものを selection に含める candidate です。

```toml
must = ["report.pdf", "data/*.csv"]
```

Pattern が1件も一致しなければ selection は成立しません。

### `may`

存在する場合だけ selection に含め、不在を error にしない candidate です。

```toml
may = ["generated/*.pdf", "coverage.xml"]
```

`must` と `may` は同じ selection で併用できます。

### `ignore`

既に `must` / `may` から選択候補になった範囲で、pluck しない entry を指定します。通常の string は従来どおり file / directory **name** を照合します。

```toml
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

特定の場所だけを除外したい場合は、1要素 nested array の中を `./` で始めて Selection root からの concrete relative path を指定できます。

```toml
ignore = [
    ["./tests/fixtures/big.bin"],
    ["./src/generated/"],
]
```

Pluck では `./` は現在の Target root、Always source ではその Always source root を表します。末尾 `/` は directory path、末尾 `/` なしは file path として扱い、filesystem の現在状態から種類を推測しません。Path reference は Selection root の内側に限定し、`..`、absolute path、glob、backslash を受理しません。

Name pattern、Shared ignore reference、path reference はすべて除外条件の和として扱います。同じ entry に複数の条件が一致しても error にはなりません。Directory ignore または directory path reference に一致した directory はその時点で除外し、内部を走査しません。評価順序は意味論に含めません。

`ignore` は entry の種類による診断より優先し、一致した entry は selection 対象から外した時点で処理済みとします。そのため ignored entry は symbolic link / Windows directory junction や特殊 filesystem entry であっても、その種類を理由とする runtime diagnostic の根拠にしません。`must` が ignored entry にしか一致しない場合は通常の unsatisfied `must` として扱います。

認識した非 ignored symbolic link / Windows directory junction は `must` / `may` の選択対象にも再帰走査の対象にもならず、Archive へも含めません。FIFO、socket、device など regular file / regular directory ではない非 ignored filesystem entry も Archive 対象にしません。`must` がそのような特殊 entry だけに一致した場合は selectable でない理由を示す error とし、`may` では optional missing として扱います。Selection には内容や名前に基づく暗黙の ignore を加えません。Configuration を実行するときの trust boundary と広い selection の扱いは `../TRUST.md` を参照してください。

### `allow_empty`

`may` だけの selection で、最終的に0 file でも正常としたい場合に使います。

```toml
may = ["generated/*.pdf"]
allow_empty = true
```

既定は `false` です。`allow_empty = true` と `must` は同時に使えません。

## Shared patterns

同じ pattern set を複数 selection で使う場合は共有パターンとして名前を付けます。Selection と同じ `must` / `may` / `ignore` の3 namespace を使います。

```toml
[shared.must]
project = ["src", "pyproject.toml"]

[shared.may]
docs = ["README.md", "docs"]

[shared.ignore]
python-noise = ["__pycache__/", "*.pyc"]
```

Selection array の通常の string は direct pattern です。`must` / `may` の1要素 nested array は Shared reference、`ignore` の1要素 nested arrayは plain name なら Shared reference、`./` で始まる string なら Selection-relative path reference として解釈します。

```toml
[pluck]
description = "The current project."
must = [
    "LICENSE",
    ["project"],
]
may = [
    ["docs"],
]
ignore = [
    ".git/",
    ["python-noise"],
]
```

参照先 namespace は、その reference を書いた field から決まります。`must = [["project"]]` は `shared.must.project`、`may` は `shared.may`、`ignore = [["python-noise"]]` は `shared.ignore.python-noise` を参照します。`ignore = [["./tests/fixtures/"]]` のように `./` で始めた場合だけ Shared namespace ではなく Selection-relative path を表します。

`[]`、`["a", "b"]`、`[123]` のような nested array は reference として無効です。`must` / `may` では nested array は Shared reference 専用です。`ignore` では `./` を path reference marker に予約しますが、通常の direct string pattern の表現は変えません。

Base chain での name resolution と duplicate validation は `../specification/INDEX.md` を参照してください。

## Cases

ケースは、同じ source に別の完全な selection を用意するときに使います。

```toml
[pluck]
description = "Normal review."
must = ["documents", "metadata.json"]

[pluck.case.audit]
description = "Audit review."
must = ["documents", "metadata.json", "records"]
```

```console
dirpluck acme --case audit
```

Case は base selection への差分ではありません。必要な `must` / `may` / `ignore` / Shared reference / `allow_empty` は Case 自身へ書きます。

Pluck と Always source が同じ Case 名を持てば、同じ CLI `--case` で対応する variation を選べます。Always source に同名 Case がない場合の fallback など、正確な Case semantics は `../specification/INDEX.md` を参照してください。
