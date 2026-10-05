<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/python_api/surface.py` です。
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

# Package surface

0.16.x の公式 package-root export は次の6名です。

```python
from dirpluck import (
    AlwaysMigrationWarning,
    ConfigurationDeprecationWarning,
    DirpluckError,
    RunResult,
    __version__,
    run,
)
```

`ConfigurationDeprecationWarning` は deprecated Configuration syntax、`AlwaysMigrationWarning` は 0.16.x の Always layout / Namespace transition を filter / error 化するための公開 `FutureWarning` subclass です。

`dirpluck.builder`、`dirpluck.invocation`、underscore module、そこから import できる model / helper は実装上利用されていても公式 API ではありません。これらへ直接依存する code は Beta 中の内部 refactor で変更される可能性があります。

公式 surface を意図的に小さく保つことで、CLI と同じ高 level capability を Python へ提供しつつ、Configuration model や archive-planning internals を将来整理する余地を残します。

name: dirpluck

kind: Value

output: run, AlwaysMigrationWarning, ConfigurationDeprecationWarning, RunResult, DirpluckError, __version__

## 次に読む文書

Repository / source distribution では、次の公開文書を参照します。

- CLI argument と human-readable output: `docs/cli/INDEX.md`
- Configuration の書き方: `docs/configuration/INDEX.md`
- Configuration / Target / Case / traversal / Archive / Output の厳密な意味論: `docs/specification/INDEX.md`
- filesystem 操作と配布時の trust boundary: `docs/TRUST.md`
- 用語の意味: `GLOSSARY.md`

Wheel にも同じ公開文書一式を `dirpluck/_docs/` 以下へ同梱します。したがって installed wheel だけでも README、Glossary、CLI / Configuration / Python API guide、Trust model、Specification、CHANGELOG、STATUS を参照できます。
