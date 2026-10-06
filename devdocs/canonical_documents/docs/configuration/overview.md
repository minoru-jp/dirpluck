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

Configuration はひとつの最終 Archive intent を表します。実行時に選ぶ Target の探索場所と kind は `scope` で表し、directory Target の内部 Selection は `pluck`、Configuration に固定する source は `always`、Case で必要時だけ追加する fixed source は `extra` で表します。File Target は `scope` だけで選択でき、Pluck は適用しません。

```toml
[pluck]
description = "The project currently under review."
may = ["README.md", "src/", "tests/"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive/", "tmp-*/"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[pluck]` は directory 対象へ適用するpluck、`[scope]` / `[scope.<name>]` は Target を探し `target_kind` を決めるスコープ、`[always.<name>]` は常時参加する常時ソース、`[extra.<name>]` は `case.always` の `include` / `add` で有効化されたときだけ参加する追加 source です。Archive 内の最上位配置を分けたい場合は `[layout.<name>]` を宣言し、Always / Extra / Target の既定値または個別 source から参照します。必要に応じて共有パターン、ケース、基底設定ファイルを使って構成を広げます。

## About

`[about]` は Configuration 自身についての宣言です。全体 `description`、source 構成に応じた追加 description、Always / Target の既定 Layout、および `base` を持てます。

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
description_no_targets = "This Archive contains only fixed reference material."
description_no_always = "This Archive contains only requested Targets."
description_empty = "No sources were selected for this run."
always_layout = "dependencies"
targets_layout = "development-targets"
base = "../common/common.dirpluck"
```

`description` は任意で、生成される Archive README の見出し直下に常に表示する Configuration 全体の説明です。`description_no_targets`、`description_no_always`、`description_empty` も任意で、resolved source が Always のみ、Target のみ、0件のときに対応する1個だけを追加表示します。`description_empty` の場合も generated `README.md` 自体は作られます。

`always_layout` / `targets_layout` は、宣言済み `[layout.<name>]` を参照して Always / Extra / Target の既定配置先を指定します。個別 `[always.<name>].layout` / `[extra.<name>].layout` / `[scope].layout` / `[scope.<name>].layout` がある場合はそちらを優先し、どちらもなければ Archive root 直下へ配置します。

これらの `[about]` field は Base chain で field ごとに、外側から見て最初に定義された値を使います。`base` は任意で、この Configuration が基礎とする基底設定ファイルを1個指定します。`[about]` を定義する場合は少なくとも1 field を記述します。

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

この基準は少なくとも `about.base`、`scope.<name>.path`、`always.<name>.path`、`extra.<name>.path`、`output.path`、`output.timestamp.path` に共通です。Configuration document 自体を参照する `about.base` だけでなく、named Scope / Always / Extra のように明示した source root location も host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む location を利用できます。明示 root の alias を解決して source root とすることと、その root からの自動 traversal で link-like entry を選択しないことは別です。Pattern や CLI Target reference のように filesystem location ではない値は、それぞれの規則に従います。厳密な validation は `../specification/INDEX.md` を参照してください。
