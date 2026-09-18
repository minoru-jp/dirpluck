from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Configuration Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 TOML reference です。

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

Target の実 directory は CLI `DIRECTORY` から与えます。Companion は `path` を Configuration に固定します。

Selection では次を使えます。

- `description`: source / selection の役割。
- `include`: 存在を必要とする候補。
- `include_if_exists`: 不在を許容する候補。
- `exclude`: 選択済み範囲から除外する名前。
- `if_empty = "allow"`: optional-only selection の0件を許容。
- `include_pattern_refs`, `include_if_exists_pattern_refs`, `exclude_pattern_refs`: shared pattern の参照。

Reusable pattern は `[shared.include_patterns]` / `[shared.exclude_patterns]` に定義します。Named variation は `[target.case.<name>]` / `[companion.<name>.case.<name>]` に完全な selection として定義します。

別の Configuration は次の形で import できます。

```toml
[import.base]
root = ".."
configuration = "base/dirpluck.toml"
```

Output は fixed form のほか、`directory`, `timestamp = true`, optional `prefix` / `suffix` を使う generated form があります。

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

Pattern grammar、import shadowing、Case semantics、filesystem boundary、output collision などの詳細は、同じ release の source distribution にある `docs/CONFIGURATION.md` と `docs/SPECIFICATION.md` を参照してください。CLI reference は同梱の `CLI.md` にあります。
'''
    vocabulary_refs @= (terms.TERM_1,)
