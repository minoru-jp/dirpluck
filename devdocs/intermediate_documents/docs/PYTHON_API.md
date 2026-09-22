<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `devdocs/canonical_documents/python_api/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/intermediate_documents/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck Python API

この文書は、dirpluck 0.10.x の公式 Python API を説明します。API は CLI と同じ実行 model を Python から利用するための最小 surface として定義し、Configuration parser や builder pipeline の低 level object を一般用途の互換性契約には含めません。

## 位置づけ

公式 API の中心は `dirpluck.run()` です。CLI が受け取る Target、Configuration、Case、Invocation Template、Entry、preview、output modifier を Python argument として渡し、同じ application layer で実行します。

CLI は人間向けの argument parsing、help、exit status、stdout / stderr formatting を担当します。Python API は `SystemExit` を通常の制御手段にせず、結果を `RunResult` で返し、期待される dirpluck error を `DirpluckError` として raise します。

0.10.x では、package root から明示的に export する名前だけを公式 Python API とします。低 level module や underscore 名は implementation detail であり、Beta 中の互換性保証対象には含めません。

## 基本形

```python
import dirpluck

result = dirpluck.run("example")
print(result.output_path)
```

これは概念的に次の CLI invocation と同じです。

```console
dirpluck example
```

`config` を省略した場合は runtime cwd の `default.dirpluck` を使います。Python API では process cwd を変更せずに relative document path の基準だけを指定したい場合、API 専用の `cwd` argument を使えます。

```python
from pathlib import Path
import dirpluck

result = dirpluck.run(
    "example",
    config="configs/review",
    cwd=Path("/work/project"),
)
```

この `config` は `/work/project/configs/review.dirpluck` を選びます。`cwd` は Configuration 内の relative source path の基準を変更しません。それらは通常どおり各 Configuration document location を基準に解決します。

## run()

公式 high-level entry point は次の形です。

```python
run(
    *targets,
    config=None,
    case=None,
    sequence=None,
    invocation=None,
    entry=None,
    preview=False,
    paths=False,
    archive_mtime=None,
    output=None,
    force=False,
    cwd=None,
)
```

各 argument は CLI の次の入力に対応します。

```text
targets       positional TARGET
config        --config PATH
case          --case NAME
sequence      --sequence N
invocation    -i / --invocation-template PATH
entry         -e / --entry NAME
preview       --preview
paths         --paths
archive_mtime --archive-mtime VALUE
output        --output PATH
force         --force
cwd           Python API only: relative control-document path の runtime anchor
```

`invocation` を使う場合は positional `targets` と `config` を同時に指定しません。`entry` は `invocation` と一緒にだけ使用します。`preview=True` は Output を解決・書き込みしないため `sequence`、`output`、`force=True` とは組み合わせません。`sequence` は 1 以上の integer とします。`output` は CLI `--output` と同じ `/` separator の path syntax を使い、relative path は `cwd` を基準にします。`force` は boolean です。

Invocation Template を選択した場合、`case` argument は保存された Case、`archive_mtime` argument は保存された `archive_mtime` を CLI と同じ規則で上書きします。Invocation の `config` が未指定なら `cwd/default.dirpluck`、`targets` が未指定なら Target なし、`case` が未指定なら通常の default Case semantics、`archive_mtime` が未指定なら従来の entry timestamp semantics を使います。

## Runtime Output

`output` は Configuration の Output destination を invocation 単位で置き換える runtime argument です。

```python
result = dirpluck.run(
    "example",
    output="artifacts/context.zip",
)
```

末尾 `/` がない `output` は exact output file path です。末尾 `/` がある場合は directory として扱い、その directory 直下へ automatic timestamp filename を生成します。

```python
result = dirpluck.run(
    "example",
    output="artifacts/snapshots/",
)
```

Automatic filename は、root Configuration が `[output.timestamp]` を持つ場合にその `prefix` / `suffix` naming rule を再利用します。Configured output directory は再利用しません。Root に timestamp Output がなければ `dirpluck-YYYYMMDD-HHMMSS.zip` を使います。`sequence` は automatic timestamp filename にだけ指定できます。

`output` を指定した build は root Configuration に Output declaration がなくても実行できます。Runtime Output の overwrite は既定で無効です。既存 destination を置き換える場合は `force=True` を指定します。`force=True` は Configuration の fixed / timestamp Output を使う build にも適用できます。

CLI `--here` は Python API に専用 argumentを持たず、`output="./"` が同じ cwd + automatic filename、`output="context.zip"` が cwd + explicit filename に相当します。`output` path は OS にかかわらず `/` separator を使い、backslash を受理しません。

## Invocation Template

Named Invocation も CLI と同じ形で選択できます。

```python
import dirpluck

result = dirpluck.run(
    invocation="calls/release",
    entry="review",
    case="audit",
    preview=True,
)
```

概念的には次と同じです。

```console
dirpluck -i calls/release -e review --case audit --preview
```

Field を持たない Invocation も有効です。その場合、`RunResult.invocation_empty` が `True` になります。CLI はこれを human-readable note として表示しますが、Python API は状態を field で返します。

## Archive entry の mtime

`archive_mtime` は CLI `--archive-mtime VALUE` と同じ runtime policy です。

```python
result = dirpluck.run(
    "example",
    archive_mtime="zip-epoch",
)
```

受理する値は `YYYY-MM-DDTHH:MM:SS`、`"now"`、`"zip-epoch"` です。明示 timestamp は ZIP の 1980-01-01T00:00:00 から 2107-12-31T23:59:59 の範囲とし、timezone conversion は行いません。`now` は1回の `run()` で local current time を1度だけ取得します。ZIP timestamp の2秒粒度に合わせ、奇数秒は直前の偶数秒へ切り下げます。

値を指定すると generated `README.md`、empty directory entry、source file の全 ZIP entry に同じ timestamp を適用します。省略時は source file の filesystem mtime と generated entry の生成時刻を使う従来動作を維持します。固定値は entry timestamp による byte 差を取り除き、reproducible な Archive を作る一助になります。ただし source file の permission bits など他の filesystem metadata は正規化せず、Archive 全体の byte-for-byte reproducibility は保証しません。Timestamp output filename の時刻にも影響しません。`preview=True` でも argument 自体は受理しますが、Archive を書かないため結果には影響しません。

## Preview と RunResult

`preview=True` は Archive file を書き込まず、CLI `--preview` と同じ planning semantics を実行します。Output を解決・書き込みしないため、`output`、`force=True`、`sequence` とは組み合わせません。

```python
result = dirpluck.run("example", preview=True)
print(result.preview_text)
```

`RunResult` は次の public field を持ちます。

```text
output_path         build で生成した ZIP path。preview では None
preview_text        CLI --preview と同じ tree representation
archive_entries     実際に Archive へ入る final entry path の tuple
archive_readme      root README.md として生成する Markdown
skipped_link_count  automatic traversal で除外した link-like entry 数
invocation_empty    選択した Invocation が config / targets / case / archive_mtime を持たなかったか
```

通常 build でも `preview_text` と `archive_readme` は実際に使用した plan から返します。そのため、呼び出し側は CLI output を parse せず、生成結果と plan の主要な public information を取得できます。

## エラー

Python API から期待される dirpluck error をまとめて扱う場合は `DirpluckError` を catch します。

```python
import dirpluck

try:
    result = dirpluck.run("example", preview=True)
except dirpluck.DirpluckError as exc:
    print(exc)
```

Invalid Configuration、Target / Selection resolution、Invocation Template、または `run()` の互換でない argument combination は `DirpluckError` の subclass を raise します。CLI の status 2 や `dirpluck: error:` prefix は CLI adapter の presentation であり、Python API contract には含めません。

## 公式 surface と互換性

0.10.x の公式 package-root export は次の4名です。

```python
from dirpluck import DirpluckError, RunResult, __version__, run
```

`dirpluck.builder`、`dirpluck.config`、`dirpluck.invocation`、underscore module、そこから import できる model / helper は実装上利用されていても公式 API ではありません。これらへ直接依存する code は Beta 中の内部 refactor で変更される可能性があります。

公式 surface を意図的に小さく保つことで、CLI と同じ高 level capability を Python へ提供しつつ、Configuration model や archive-planning internals を将来整理する余地を残します。

## 次に読む文書

- CLI argument と human-readable output: `CLI.md`
- Configuration の書き方: `CONFIGURATION.md`
- Configuration / Target / Case / traversal / Archive / Output の厳密な意味論: `SPECIFICATION.md`
- filesystem 操作と配布時の trust boundary: `TRUST.md`
- 用語の意味: `../GLOSSARY.md`
