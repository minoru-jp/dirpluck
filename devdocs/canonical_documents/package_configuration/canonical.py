from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Configuration Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 Configuration reference です。Configuration document は `.dirpluck` extension を使い、内容は TOML syntax です。`.toml` extension は Configuration として受理しません。`.dirpluck-inv` は別の Invocation Template document type であり、Configuration schema / base chain には参加しません。

```toml
[about]
description = "Materials prepared for reviewing the current project."

[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive", "tmp-*"]

[scope.work]
path = "/srv/work"
ignore = ["archive"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[about].description` は Archive 全体の任意説明です。Base chain に複数ある場合は outermost から最初に定義された値を使い、生成される Archive README の index より前に表示します。別の Configuration を基礎にする場合は同じ `[about]` に `base = "../common/common.dirpluck"` を記述できます。`description` と `base` はそれぞれ任意です。

外部へ渡す Archive を作る場合は selection を確認してください。dirpluck はどの file が機密かを推論しないため、含めるべきでないものは `ignore` で明示します。

```toml
[pluck]
ignore = [".git/", ".env*", "*.pem", "*.key"]
```

これは一例です。Trust boundary と filesystem 操作の責任範囲は、同梱の `TRUST.md` を参照してください。

Pluck の実 Target は CLI positional `TARGET` から選びます。Default Scope は常に root Configuration file の directory を root とします。`[scope]` は default Scope の optional `ignore` / `namespace` を設定します。Base の `[scope]` は outer Root の default Scope へ継承されず、その Base 自身を Root として使う場合だけ有効です。`[scope]` を省略しても default Scope は利用できます。`project` は default Scope の `project`、`work/project` は named Scope `work` 直下の `project`、`/` は default Scope、`work/` は named Scope `work` の eligible direct child directory をすべて Target として展開します。多階層 Target reference と未定義 Scope は error です。`scope.ignore` は Target candidate directory name に適用し、selection の `ignore` とは別です。Named Scope の path は、その Scope を実際に使うときに存在確認します。 Scope 直下で symbolic link または Windows directory junction として認識した entry は Target candidate にしません。

Archive 上で異なる source root が同じ path に解決される場合、dirpluck はそれらを黙って merge せず error にします。必要な場合は空の `[namespace.<name>]` table を定義し、Scope または Always source の `namespace = "<name>"` から参照します。Namespace 名は Archive root の外側へ常に追加されます。

```toml
[namespace.work]

[scope.work]
path = "/srv/work"
namespace = "work"
```

Namespace を使う Archive の `README.md` は、Namespace が元 source path の一部ではない Archive 専用 directory であることを説明します。各 source は final Archive root を見出しとして表示し、Namespace を使う source では Namespace / Source root も metadata として分けて表示します。

Always source は `path` を Configuration に固定します。Configuration の filesystem location は `/` を separator として書き、Windows でも backslash は separator として使いません。Relative path はその field を記述した Configuration file の directoryを基準に解決します。Absolute path も指定できます。Named Scope / Always の明示 root location は symbolic link / Windows directory junction を含めることができますが、解決した root からの自動 Target discovery / Selection traversal では link-like entry をたどりません。Configuration document 自体を参照する `about.base` も host OS の通常の filesystem semantics に従い、relative reference は選択した Configuration path の directory を基準にします。

Selection では次を使えます。

- `description`: Archive README の source section で役割を説明する任意の non-empty string。複数行も使用できます。
- `must`: 存在を必要とする candidate。
- `may`: 不在を許容する candidate。
- `ignore`: 選択候補から拾わない file / directory name。`["./path/to/file"]` / `["./path/to/directory/"]` の1要素 nested arrayでは Selection root からの concrete path も指定できます。
- `allow_empty = true`: `must` を持たない selection の0件を許容。
- `["name"]`: 同じ field category の Shared pattern reference。`ignore` だけは `./` で始めると Shared reference ではなく Selection-relative path reference。

Reusable pattern は `[shared.must]` / `[shared.may]` / `[shared.ignore]` に定義します。Named variation は `[pluck.case.<name>]` / `[always.<name>.case.<name>]` に完全な selection として定義します。Selection-relative path reference の `./` は Pluck では Target root、Always では Always source root を表し、末尾 `/` で directory を明示します。Name / Shared / path の ignore 条件が重なっても error にはせず、除外条件の和として扱います。`ignore` は entry の種類による診断より優先し、ignored entry は skipped-link count や special-entry-only error の根拠にしません。Selection traversal で non-ignored symbolic link または Windows directory junction として認識した entry はたどらず、Archive に含めません。FIFO、socket、device など regular file / regular directory ではない特殊 entry も Archive に含めず、`must` がそのような entry だけに一致した場合は理由付き error にします。

別の Configuration は次の形で base にできます。

```toml
[about]
base = "../base/base.dirpluck"
```

Output は Configuration 単体では optional です。共通 definition を提供する Base Configurationだけでなく、`--preview` に使う root Configuration でも省略できます。実際に Archive file を書き込む通常 build では root 自身に fixed mode または timestamp mode のどちらか一方を直接宣言する必要があります。Base の Output は継承されません。Fixed mode では filename まで指定し、`overwrite` の既定は `false` です。生成する Archive file は通常の新規 file creation と同じ permission semantics に従い、POSIX では process `umask` が適用されます。Overwrite でも既存 file mode は継承しません。

```toml
[output]
path = "artifacts/review.zip"
overwrite = true
```

Timestamp mode では directory を末尾 `/` 付きで指定します。

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

Pattern grammar、base composition、Scope shadowing、Case semantics、filesystem boundary、Output write-boundary collision などの詳細は、同じ release の source distribution にある `docs/CONFIGURATION.md` と `docs/SPECIFICATION.md` を参照してください。Trust model は同梱の `TRUST.md`、CLI reference は同梱の `CLI.md` にあります。
'''
    vocabulary_refs @= (terms.TERM_1,)
