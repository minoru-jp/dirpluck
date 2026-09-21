from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Python API")
class TITLE_1:
    r'''この文書は、{{TERM_1}} 0.9.x の公式 Python API を説明します。API は CLI と同じ実行 model を Python から利用するための最小 surface として定義し、Configuration parser や builder pipeline の低 level object を一般用途の互換性契約には含めません。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("位置づけ")
    class TITLE_2:
        r'''公式 API の中心は `dirpluck.run()` です。CLI が受け取る Target、Configuration、Case、Invocation Template、Entry、preview、output modifier を Python argument として渡し、同じ application layer で実行します。

CLI は人間向けの argument parsing、help、exit status、stdout / stderr formatting を担当します。Python API は `SystemExit` を通常の制御手段にせず、結果を `RunResult` で返し、期待される dirpluck error を `DirpluckError` として raise します。

0.9.x では、package root から明示的に export する名前だけを公式 Python API とします。低 level module や underscore 名は implementation detail であり、Beta 中の互換性保証対象には含めません。'''

    @title("基本形")
    class TITLE_3:
        r'''```python
import dirpluck

result = dirpluck.run("example")
print(result.output_path)
```

これは概念的に次の CLI invocation と同じです。

```console
{{TERM_1}} example
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

この `config` は `/work/project/configs/review.dirpluck` を選びます。`cwd` は Configuration 内の relative source path の基準を変更しません。それらは通常どおり各 Configuration document location を基準に解決します。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("run()")
    class TITLE_4:
        r'''公式 high-level entry point は次の形です。

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
cwd           Python API only: relative control-document path の runtime anchor
```

`invocation` を使う場合は positional `targets` と `config` を同時に指定しません。`entry` は `invocation` と一緒にだけ使用します。`preview=True` と `sequence` は組み合わせません。`sequence` は 1 以上の integer とします。

Invocation Template を選択した場合、`case` argument は保存された Case、`archive_mtime` argument は保存された `archive_mtime` を CLI と同じ規則で上書きします。Invocation の `config` が未指定なら `cwd/default.dirpluck`、`targets` が未指定なら Target なし、`case` が未指定なら通常の default Case semantics、`archive_mtime` が未指定なら従来の entry timestamp semantics を使います。'''

    @title("Invocation Template")
    class TITLE_5:
        r'''Named Invocation も CLI と同じ形で選択できます。

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
{{TERM_1}} -i calls/release -e review --case audit --preview
```

Field を持たない Invocation も有効です。その場合、`RunResult.invocation_empty` が `True` になります。CLI はこれを human-readable note として表示しますが、Python API は状態を field で返します。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Archive entry の mtime")
    class TITLE_55:
        r'''`archive_mtime` は CLI `--archive-mtime VALUE` と同じ runtime policy です。

```python
result = dirpluck.run(
    "example",
    archive_mtime="zip-epoch",
)
```

受理する値は `YYYY-MM-DDTHH:MM:SS`、`"now"`、`"zip-epoch"` です。明示 timestamp は ZIP の 1980-01-01T00:00:00 から 2107-12-31T23:59:59 の範囲とし、timezone conversion は行いません。`now` は1回の `run()` で local current time を1度だけ取得します。ZIP timestamp の2秒粒度に合わせ、奇数秒は直前の偶数秒へ切り下げます。

値を指定すると generated `README.md`、empty directory entry、source file の全 ZIP entry に同じ timestamp を適用します。省略時は source file の filesystem mtime と generated entry の生成時刻を使う従来動作を維持します。固定値は entry timestamp による byte 差を取り除き、reproducible な Archive を作る一助になります。ただし source file の permission bits など他の filesystem metadata は正規化せず、Archive 全体の byte-for-byte reproducibility は保証しません。Timestamp output filename の時刻にも影響しません。`preview=True` でも argument 自体は受理しますが、Archive を書かないため結果には影響しません。'''

    @title("Preview と RunResult")
    class TITLE_6:
        r'''`preview=True` は Archive file を書き込まず、CLI `--preview` と同じ planning semantics を実行します。

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

通常 build でも `preview_text` と `archive_readme` は実際に使用した plan から返します。そのため、呼び出し側は CLI output を parse せず、生成結果と plan の主要な public information を取得できます。'''

    @title("エラー")
    class TITLE_7:
        r'''Python API から期待される dirpluck error をまとめて扱う場合は `DirpluckError` を catch します。

```python
import dirpluck

try:
    result = dirpluck.run("example", preview=True)
except dirpluck.DirpluckError as exc:
    print(exc)
```

Invalid Configuration、Target / Selection resolution、Invocation Template、または `run()` の互換でない argument combination は `DirpluckError` の subclass を raise します。CLI の status 2 や `dirpluck: error:` prefix は CLI adapter の presentation であり、Python API contract には含めません。'''

    @title("公式 surface と互換性")
    class TITLE_8:
        r'''0.9.x の公式 package-root export は次の4名です。

```python
from dirpluck import DirpluckError, RunResult, __version__, run
```

`dirpluck.builder`、`dirpluck.config`、`dirpluck.invocation`、underscore module、そこから import できる model / helper は実装上利用されていても公式 API ではありません。これらへ直接依存する code は Beta 中の内部 refactor で変更される可能性があります。

公式 surface を意図的に小さく保つことで、CLI と同じ高 level capability を Python へ提供しつつ、Configuration model や archive-planning internals を将来整理する余地を残します。'''

    @title("次に読む文書")
    class TITLE_9:
        r'''- CLI argument と human-readable output: `CLI.md`
- Configuration の書き方: `CONFIGURATION.md`
- Configuration / Target / Case / traversal / Archive / Output の厳密な意味論: `SPECIFICATION.md`
- filesystem 操作と配布時の trust boundary: `TRUST.md`
- 用語の意味: `../GLOSSARY.md`'''
