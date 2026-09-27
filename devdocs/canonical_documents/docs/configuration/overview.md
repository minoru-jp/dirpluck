<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/configuration/overview.py` です。
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

# Configuration overview

この文書は、設定ファイル の基本的な文書形式、metadata、path notation を説明します。Source、Selection、Base、Output はそれぞれ collection 内の専用文書に分けています。

この guide は authoring を説明し、互換性上の厳密な契約は Specification が定義します。Document schema は `../specification/configuration-schema.md`、path notation は `../specification/paths.md`、CLI からの document 選択は `../specification/document-selection.md` を参照してください。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。

## Configuration document

Configuration は `.dirpluck` extension を持つ document として保存し、内容には TOML syntax を使用します。`.toml` extension は dirpluck Configuration として受理しません。

```text
default.dirpluck
review.dirpluck
configs/common.dirpluck
```

`default.dirpluck` は CLI で `--config` を省略したときだけ、runtime cwd から自動的に使用される特別な filename です。別名 Configuration や別 directory の Configuration は `--config PATH` で明示的に選びます。Relative CLI path は cwd 基準、Configuration 内の relative filesystem path はその Configuration file の directory 基準です。Configuration document を選択・参照する path は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path も利用できます。Relative path の基準には link target の実体 location ではなく、選択・参照した document path の directory を使います。詳しい選択規則は `../cli/INDEX.md` / `../specification/INDEX.md` を参照してください。Base Configuration は filename に特別な default name を必要とせず、`[about].base` から concrete `.dirpluck` path を参照します。

`.dirpluck-inv` は Configuration ではなく、CLI invocation を保存する別 document type です。Configuration の schema や base chain には参加しません。Invocation Template の書き方と選択方法は `../cli/INDEX.md` を参照してください。

## 基本形

Configuration はひとつの最終 Archive intent を表します。実行時に選ぶ Target がある場合は `pluck` と `scope`、Configuration に固定する source は `always` で表します。

```toml
[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive", "tmp-*"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[pluck]` は対象へ適用するpluck、`[scope]` / `[scope.<name>]` は Target を探すスコープ、`[always.<name>]` は常時ソースです。Archive 上で同名の source root を区別する必要がある場合はネームスペースを使えます。必要に応じて共有パターン、ケース、基底設定ファイルを使って構成を広げます。

## About

`[about]` は Configuration 自身についての宣言です。`description` と `base` を持てます。

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
base = "../common/common.dirpluck"
```

`description` は任意で、生成される Archive README の見出し直下に表示する Configuration 全体の説明です。Base chain に複数の description がある場合は、外側から見て最初に定義されたものを使います。

`base` も任意で、この Configuration が基礎とする基底設定ファイルを1個指定します。`description` を書かず `base` だけを書くこともできます。`[about]` を定義する場合は、少なくともどちらか一方を記述します。

Base chain の composition と cycle detection は `../specification/INDEX.md` を参照してください。

## Path notation

Configuration で filesystem location を表す path は、host OS に関係なく `/` を separator として書きます。Backslash は path separator として使いません。Windows でも `C:/...` や `//server/share/...` のように `/` を使います。

相対 filesystem path は、**その field が記述されている Configuration file の directory**を基準に解決します。Runtime cwd を path resolution base として切り替えることはありません。

```text
project/default.dirpluck
    [always.notes]
    path = "../notes"
        -> project/ から解決
```

Absolute path は host OS が absolute root として認識する形を `/` separator で記述します。

```text
# POSIX host
/opt/company/references

# Windows host
C:/Users/name/references
//server/share/references
```

Absolute path はその場所を直接参照するため、Configuration の portability は低くなります。別 OS の absolute-root notation への変換、`~` expansion、environment-variable interpolation は行いません。

この基準は少なくとも `about.base`、`scope.<name>.path`、`always.<name>.path`、`output.path`、`output.timestamp.path` に共通です。Configuration document 自体を参照する `about.base` だけでなく、named Scope / Always のように明示した source root location も host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む location を利用できます。明示 root の alias を解決して source root とすることと、その root からの自動 traversal で link-like entry を選択しないことは別です。Pattern や CLI Target reference のように filesystem location ではない値は、それぞれの規則に従います。厳密な validation は `../specification/INDEX.md` を参照してください。
