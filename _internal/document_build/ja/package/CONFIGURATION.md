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
正本は `dirpluck_docs/package_configuration/canonical.py` です。
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

# dirpluck Configuration Quick Reference

wheel に同梱する最小 TOML reference です。

```toml
[about]
description = "Materials prepared for reviewing the current project."

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

`[about].description` は Archive 全体の任意説明です。Import chain に複数ある場合は outermost から最初に定義された値を使い、生成される Archive README の索引表より前に表示します。

Target の実 directory は CLI `DIRECTORY` から与えます。Companion は `path` を Configuration に固定します。Configuration の filesystem location は `/` を separator として書き、Companion `path` は relative / absolute のどちらでも指定できます。Relative Companion path は対応する Configuration execution root を基準に解決します。

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

Pattern grammar、import shadowing、Case semantics、filesystem boundary、output collision などの詳細は、同じ release の source distribution にある `docs/CONFIGURATION.md`、`docs/SPECIFICATION.md`、`docs/TRUST.md` を参照してください。CLI reference は同梱の `CLI.md` にあります。
