<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/python_api/run.py` です。
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

# dirpluck.run

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
case          --case CASE
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

name: dirpluck.run

kind: Operation

introduced: 0.9.0

input: targets: positional Target references, config: Configuration document path, case: Pluck / Always Case selector, sequence: explicit output sequence, invocation: Invocation Template path, entry: named Invocation entry, preview: preview mode, paths: include source paths in generated README, archive_mtime: Archive entry timestamp policy, output: runtime Output path, force: overwrite effective Output, cwd: runtime anchor for relative control-document paths

output: RunResult

## Configuration deprecation warning

0.14.0 から 1.0.0 未満で、読み込んだ Configuration が deprecated な1要素 nested-array reference を使用している場合、`dirpluck.run()` は Configuration file ごとに1回、Python の warnings framework に公開 `ConfigurationDeprecationWarning` を報告します。これは `FutureWarning` subclass のため Python の既定 filter でも表示されます。Base chain から読み込まれた Configuration も対象です。

Warning location は固定 `stacklevel` に依存せず、dirpluck package 外の最初の caller frame に帰属します。呼び出し側が明示的に制御したい場合は `dirpluck.ConfigurationDeprecationWarning` を category として warning filter に指定できます。この lifecycle diagnostic は planning diagnostic を返す `RunResult.warnings` には含まれません。CLI は同じ診断を収集して簡潔な stderr warning として表示するため、CLI 実行時に追加の Python warning は発行しません。

旧記法は 1.0.0 で invalid Configuration になります。Shared reference は `{ shared = "..." }`、`ignore` の concrete relative path は `{ path = "..." }` へ移行してください。0.16.0 から 1.0.0 未満では legacy `[pluck.case.<name>]` も同じ category で migration notice を報告し、canonical `[case.pluck.<name>]` への移行を案内します。

## Always migration warning

0.16.0 から 1.0.0 直前まで、`dirpluck.run()` は Always migration を公開 `AlwaysMigrationWarning` として Python の warnings framework へ報告します。0.14.x で有効だった Always source の旧 Archive identity と 0.16.x の effective Always name を比較し、実際に Archive root が変わる source にだけ layout migration warning を出します。Warning message には旧 root と新 root を含めます。旧・新 identity が同じ source には layout warning を出しません。0.17.0 以降で explicit Layout が有効な Always source では、Layout が現在の final Archive destination を意図的に決めているため、この旧 layout migration warning は抑制します。

`[always.<name>].namespace` を使用した場合は、layout 差分とは別に pre-1.0 compatibility warning を必ず報告します。0.16.x では Namespace name が Always name を一時的に置き換えますが、この field は 1.0.0 で削除されます。Archive directory name は `[always.<name>]` に直接記述してください。

`AlwaysMigrationWarning` は `FutureWarning` subclass で、warning location は dirpluck package 外の最初の caller frame に帰属します。呼び出し側は `dirpluck.AlwaysMigrationWarning` を filter / error 化でき、Archive layout の移行を CI から明示的に検知できます。これらは lifecycle diagnostic なので `RunResult.warnings` には含めません。CLI は同じ public warning を収集して stderr へ表示し、追加の Python warning は発行しません。

## README-only Archive

`dirpluck.run()` は resolved source が0件でも正常に完了できます。Target を渡さず、Always source も解決されない場合、build は generated `README.md` だけを含む Archive を生成し、`preview=True` は `README.md` だけの tree を返します。これは warning / exception ではありません。Generated README には source が0件だったことを informational text として記録し、`RunResult.archive_entries` は `("README.md",)` になります。

`case=` は CLI `--case CASE` と同じ2軸 selector です。`"audit"` は Pluck Case、`".release"` は Always Case、`"audit.release"` は両方を指定します。各軸の Case name 自体が Configuration 上で有効なら、その適用結果として source が0件でも正常です。指定した軸に存在しない Case name は error です。

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
