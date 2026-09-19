from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Configuration Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 TOML reference です。

```toml
[about]
description = "Materials prepared for reviewing the current project."

[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
skip = ["archive", "tmp-*"]
if_empty = "allow"

[target.location.work]
path = "/srv/work"
skip = ["archive"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`[about].description` は Archive 全体の任意説明です。Import chain に複数ある場合は outermost から最初に定義された値を使い、生成される Archive README の索引表より前に表示します。

外部へ渡す Archive を作る場合は selection を確認してください。dirpluck はどの file が機密かを推論しないため、含めるべきでないものは `exclude` で明示します。

```toml
exclude = [".git/", ".env*", "*.pem", "*.key"]
```

これは一例です。信頼境界と filesystem 操作の責任範囲は、同梱の `TRUST.md` を参照してください。

Target の実 directory は CLI positional `TARGET` から選びます。Target candidate は cwd または `[target.location.<name>]` の `path` の直下だけです。`project` は `cwd/project`、`work/project` は `work` location 直下の `project`、`work/` は `work` location 直下の eligible directory をすべて Target として展開します。多階層 Target reference と未定義 location は error です。`[target].skip` は cwd Target、`[target.location.<name>].skip` はその location の Target candidate directory 名を exact / prefix / suffix / substring pattern で除外し、明示指定にも適用します。Selection の `exclude` とは別です。Companion は `path` を Configuration に固定します。Configuration の filesystem location は `/` を separator として書き、Target location / Companion `path` は relative / absolute のどちらでも指定できます。Relative path は対応する Configuration execution root を基準に解決します。

Selection では次を使えます。

- `description`: archive index で内容を説明する source / selection の役割。
- `include`: 存在を必要とする候補。
- `include_if_exists`: 不在を許容する候補。
- `exclude`: 選択済み範囲から除外する名前。
- `if_empty = "allow"`: optional-only selection の0件を許容。
- `include_pattern_refs`, `include_if_exists_pattern_refs`, `exclude_pattern_refs`: shared pattern の参照。

Reusable pattern は `[shared.include_patterns]` / `[shared.exclude_patterns]` に定義します。Named variation は `[target.case.<name>]` / `[companion.<name>.case.<name>]` に完全な selection として定義します。

別の Configuration は次の形で import できます。`root` は relative / absolute のどちらでも指定でき、`configuration` は import root 内の relative TOML path です。

```toml
[import.base]
root = ".."
configuration = "base/dirpluck.toml"
```

Output の `path` / `directory` も relative / absolute のどちらでも指定できます。Fixed form のほか、`directory`, `timestamp = true`, optional `prefix` / `suffix` を使う generated form があります。

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

Pattern grammar、import shadowing、Case semantics、filesystem boundary、output collision などの詳細は、同じ release の source distribution にある `docs/CONFIGURATION.md` と `docs/SPECIFICATION.md` を参照してください。Trust model は同梱の `TRUST.md`、CLI reference は同梱の `CLI.md` にあります。
'''
    vocabulary_refs @= (terms.TERM_1,)
