<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/configuration/sources.py` です。
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

# Configuration sources

この文書は、Target を選ぶ Pluck / Scope と、固定 source を追加する Always、および Archive 上の Namespace を説明します。

この guide は source authoring を説明し、互換性上の厳密な契約は Specification が定義します。Target / Scope / Always / Case の解決は `../specification/runtime-targets.md`、Namespace は `../specification/namespace.md`、source traversal boundary は `../specification/filesystem.md` を参照してください。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。

## Pluck

`[pluck]` は、今回の実行で選ばれた対象から何を取り出すかを定義します。Source path 自体は持たず、Target はスコープと CLI Target reference から解決します。

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents", "metadata.json"]
may = ["attachments"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

同じ実行で複数 Target を選んだ場合も、各 Target へ同じ pluck selection を独立して適用します。

Pluck がない Configuration では positional Target reference を使いません。

## Scope

スコープは Target を探す場所です。常設の default Scope と、必要に応じて追加する名前付き Scope を使えます。

Default Scope は常に存在し、ルート設定ファイルがある directory を探索 root とします。`[scope]` table は default Scope の optional `ignore` / `namespace` を設定するために使い、`path` は書きません。`[scope]` を省略した場合、または空の `[scope]` を書いた場合は `ignore = []`、Namespace なしと同じです。Base Configuration に書いた `[scope]` は、その Configuration 自身を Root として使う場合だけ有効で、outer Root の default Scope へ継承されません。

```toml
[scope]
ignore = ["archive", "tmp-*"]
```

名前付き Scope は `path` を持ちます。

```toml
[scope.work]
path = "../work"
ignore = ["archive", "tmp-*"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*"]
```

`ignore` は Scope 直下で Target candidate として扱わない directory name を指定します。File selection の `pluck.ignore` とは役割が違います。

CLI Target reference は Scope の有無と、1 Target / 全 Target の組み合わせとして次の4形です。

```text
NAME        -> 無名 Scope から1 Target
SCOPE/NAME  -> 名前付き Scope から1 Target
/           -> 無名 Scope の全 Target
SCOPE/      -> 名前付き Scope の全 Target
```

全展開は Scope 直下の eligible directory だけを対象とし、再帰しません。

Base chain では名前付き Scope だけを名前ごとに重ね、同名 Scope は外側の Configuration が置き換え、異名 Scope は共存します。Default Scope は base から継承せず、常に root Configuration に属します。したがって Base の `[scope].ignore` / `namespace` は outer Root では使用されませんが、その Base Configuration 自身を Root として使う場合には通常どおり有効です。名前付き Scope の root は定義元 Configuration を基準にした場所のままで rebase しません。

Scope には任意で `namespace = "<name>"` を指定できます。これは Target の探索場所を変えず、その Scope から得た Target の Archive root に、別途定義したネームスペースを prefix として追加します。Namespace は衝突時だけ自動適用されるものではなく、指定した Scope の Target に常に適用されます。

名前付き Scope の path が現在の filesystem で利用可能かどうかは、その Scope を Target reference で実際に使うときに確認します。未マウントなどで存在しない named Scope が定義されていても、別の Scope だけを使う実行は妨げません。Named Scope の root location 自体は symbolic link / Windows directory junction を含められますが、解決した Scope root 直下で自動発見した link-like entry は Target として選択・展開しません。厳密な duplicate root、Namespace reference、Target resolution の規則は `../specification/INDEX.md` を参照してください。

## Namespace

ネームスペースは、source root が Archive 上で同じ path に解決される場合などに、source を明示的に区別して配置するための Archive 専用 prefix です。Namespace 自体は名前付きの空 table として定義します。

```toml
[namespace.work]

[namespace.external]
```

Namespace 名そのものが Archive 上の1 directory 名になります。現時点で `[namespace.<name>]` は属性を持ちません。不要な設定値を持たせず、将来 Namespace 固有の policy が必要になった場合に同じ table を拡張できる構造とします。

Scope と Always source は Namespace 名を参照できます。

```toml
[namespace.work]
[namespace.external]

[scope.work]
path = "/srv/work"
namespace = "work"

[always.docs]
path = "../docs"
namespace = "external"
description = "External documentation."
must = ["*.md"]
```

たとえば `work/project` の source root が `project/` なら `work/project/`、Always source の通常の source root が `docs/` なら `external/docs/` として Archive に配置します。Namespace を指定しない source は従来どおり source root 自体を Archive root とします。

異なる resolved source の最終 Archive root が同じになる場合、dirpluck は source を黙って merge せず error にします。Namespace はこの衝突を明示的に避けるために使えますが、自動的に一意性を保証するものではありません。同じ Namespace を共有して最終 Archive root が再び同じになれば error です。

生成されるアーカイブREADMEは、Namespace を使う run では Namespace が Archive 専用の外側 directory であることを説明します。各 source は final Archive root 自体を見出しとして表示し、Namespace を使う source では Namespace と Source root も metadata として分けて示します。これにより受け手は Namespace directory を元 filesystem path の一部と誤認せず、その直下が source root であることを確認できます。

## Always

`[always.<name>]` は Configuration 側で source directory を固定し、実行のたびに参加させる常時ソースです。`path` は relative path と absolute path のどちらでも指定できます。

```toml
[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[always.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
must = ["*.md"]
```

Relative `path` は、その definition が記述されている Configuration file の directory を基準に解決します。`..` を使って外側の directory を参照することもできます。Absolute `path` は host filesystem 上の場所を直接参照します。明示した Always root location は symbolic link / Windows directory junction を含めることができ、alias の参照先 directory を source root として利用します。Archive 上の source root 名は実体側へ置き換えず、Configuration に書いた location 側の name / relative path を使います。

解決された source directory 自体が selection boundary です。Root 自体に alias を使えることと、Source 内の自動 traversal で link-like entry をたどることは別です。Source 内で symbolic link または Windows directory junction として認識した entry は選択せず、リンク先もたどりません。

Always source には任意で `namespace = "<name>"` を指定し、定義済みのネームスペースを Archive root の外側へ追加できます。Filesystem 上の source path や selection boundary は変わりません。

Always source の Selection は Target の Pluck とは独立して評価します。同じ physical file が Target 配下にも存在していても、Target 側の `ignore` や Selection result は Always source の Selection を変更しません。両方が同じ physical file を選択し、異なる Archive path に配置する場合は両方を収録します。生成されるアーカイブREADMEでは、Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合、その Always source section に Target 側の Archive root と重複 file 数を表示します。

複数の Always source は名前を変えて定義します。Pluck を持たず Always source だけで完結する Configuration も有効です。
