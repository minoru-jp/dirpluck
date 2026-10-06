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

この文書は、Target を選ぶ Pluck / Scope、Archive 内の最上位配置を決める Layout、固定 source を追加する Always、および互換 Namespace を説明します。

この guide は source authoring を説明し、互換性上の厳密な契約は Specification が定義します。Target / Scope / Always / Case の解決は `../specification/runtime-targets.md`、Archive placement は `../specification/archive.md`、Namespace は `../specification/namespace.md`、source traversal boundary は `../specification/filesystem.md` を参照してください。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。

## Pluck

`[pluck]` は、今回の実行で選ばれた **directory** 対象から何を取り出すかを定義します。Source path 自体は持たず、Target はスコープと CLI Target reference から解決します。`target_kind = "file"` または `"both"` の Scope から得た file Target は atomic source であり、Pluck は適用しません。

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents/", "metadata.json"]
may = ["attachments/"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

同じ実行で複数 directory Target を選んだ場合も、各 directory Target へ同じ pluck selection を独立して適用します。File Target と directory Target は同じ実行で併用できます。Pluck がない Configuration でも `target_kind = "file"` または `"both"` の Scope から file Target は positional Target reference で選択できますが、directory Target は選択できません。

## Scope

スコープは Target を探す場所です。常設の default Scope と、必要に応じて追加する名前付き Scope を使えます。

Default Scope は常に存在し、ルート設定ファイルがある directory を探索 root とします。`[scope]` table は default Scope の optional `description` / `target_kind` / `ignore` / `layout` / `namespace` を設定するために使い、`path` は書きません。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` です。`[scope]` を省略した場合、または空の `[scope]` を書いた場合は directory Target、description なし、`ignore = []`、Namespace なしという従来動作になります。Base Configuration に書いた `[scope]` は、その Configuration 自身を Root として使う場合だけ有効で、outer Root の default Scope へ継承されません。

```toml
[scope]
ignore = ["archive/", "tmp-*/"]
```

名前付き Scope は `path` を持ちます。

```toml
[scope.work]
path = "../work"
ignore = ["archive/", "tmp-*/"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*/"]
```

`target_kind = "directory"` の Scope は直下の eligible directory だけ、`target_kind = "file"` は直下の eligible regular file だけ、`target_kind = "both"` はその両方を Target candidate とします。`target_kind` は Scope 直下の entry に対する type filter として働きます。Scope `ignore` は除外側の規則として広く扱い、末尾 `/` なしは matching file / directory Target candidate の両方、末尾 `/` ありは directory candidate だけを除外します。File selection の `pluck.ignore` とは役割が違います。`description` はその Scope から得た Target group の Archive README context として1回表示されます。Generated README の Scope 名は選択範囲を識別するための名前であり、Target 間の優先度・重要度・階層関係を表しません。追加の意味を持たせる場合は `description` に明記します。

CLI Target reference は、single Target と全展開に加え、すべての `target_kind` で使える Target selector を持ちます。

```text
NAME                    -> default Scope の file Target
./NAME                  -> default Scope の file Target (explicit form)
./NAME/                 -> default Scope の directory Target
SCOPE/NAME              -> named Scope の file Target
SCOPE/NAME/             -> named Scope の directory Target
/                       -> default Scope の全 Target
SCOPE/                  -> named Scope の全 Target
:[...]                  -> default Scope の typed literal Target list
SCOPE:[...]             -> named Scope の typed literal Target list
:<regex>                -> default Scope の regular-expression Target selector
SCOPE:<regex>           -> named Scope の regular-expression Target selector
```

Literal Target reference は末尾 `/` なしを file、末尾 `/` ありを directory とし、filesystem から型を推測しません。`SCOPE/` は Scope expansion に予約されるため、default Scope の directory Target は `./NAME/` と書きます。全展開は Scope の `target_kind` に対応する direct child だけを対象とし、再帰しません。Directory mode では eligible directory、file mode では eligible regular file、both mode ではその両方を展開します。

`[...]` の list item も同じ型規則を使います。`/` は item separator でもあるため、途中の directory item は `project//archive.zip` のように directory marker と separator が `//` になります。3連以上の `/` は error です。`<...>` は file candidate を `NAME`、directory candidate を `NAME/` と正規化した文字列全体へ Python-compatible regular expression を full-match します。`/?` などで両型を明示的に選べます。Pattern は空にできず、512 character 超、invalid regex、0件 match を error とします。

Base chain では名前付き Scope だけを名前ごとに重ね、同名 Scope は `description` / `target_kind` / `path` / `ignore` / `layout` / `namespace` を含む definition 全体として外側の Configuration が置き換え、異名 Scope は共存します。Default Scope は base から継承せず、常に root Configuration に属します。したがって Base の `[scope]` metadata / policy は outer Root では使用されませんが、その Base Configuration 自身を Root として使う場合には通常どおり有効です。名前付き Scope の root は定義元 Configuration を基準にした場所のままで rebase しません。

Scope には任意で `layout = "<name>"` を指定でき、`[about].targets_layout` より優先して、その Scope から得た Target を宣言済み Layout directory の下へ配置します。どちらも無ければ Archive root 直下です。Scope の `namespace = "<name>"` は既存の prefix semantics を持ちますが、effective Layout と Namespace は同一 Scope で併用できません。

名前付き Scope の path が現在の filesystem で利用可能かどうかは、その Scope を Target reference で実際に使うときに確認します。未マウントなどで存在しない named Scope が定義されていても、別の Scope だけを使う実行は妨げません。Named Scope の root location 自体は symbolic link / Windows directory junction を含められますが、解決した Scope root 直下で自動発見した link-like entry は Target として選択・展開しません。厳密な duplicate root、Namespace reference、Target resolution の規則は `../specification/INDEX.md` を参照してください。

## Namespace

ネームスペースは source の logical Archive identity を補助する名前付き concept です。Namespace 自体は名前付きの空 table として定義します。

```toml
[namespace.work]

[namespace.external]
```

Namespace 名は1個の Archive directory component です。現時点で `[namespace.<name>]` は属性を持ちません。`/` と `\`、ASCII control character は Archive component の構造を壊すため拒否しますが、dirpluck は OS 固有の予約名や filename 規則を独自判定しません。別の OS / filesystem へ展開する Archive を作る場合は、利用者が展開先に適した名前を選んでください。Namespace 名の一意性は大文字小文字を区別せず判定します。

Scope の `namespace = "<name>"` は Target の final Archive root の prefix として使用します。0.17.0 で追加した Layout とは path を合成せず、同じ Scope に effective Layout と Namespace が同時に存在する Configuration は error です。

```toml
[namespace.work]

[scope.work]
path = "/srv/work"
namespace = "work"
```

0.16.x 以降の 0.x series では `[always.<name>].namespace` も pre-1.0 compatibility として受理しますが、1.0.0 で削除します。Always source の Archive directory name は `[always.<name>]` の `<name>` に直接記述してください。互換期間の挙動と warning は `../specification/compatibility.md` と `../migration/0.16.md` を参照してください。

生成されるアーカイブREADMEでは、各 source の final Archive root 自体を見出しとして表示し、Namespace と source root を分離した補助 metadata は追加しません。

## Layout

Layout は Archive 内の最上位 directory を名前付きで宣言する仕組みです。配置先として使う名前は必ず `[layout.<name>]` で先に宣言します。

```toml
[about]
always_layout = "dependencies"
targets_layout = "development-targets"

[layout.dependencies]
description = "Development dependencies."

[layout.development-targets]
description = "Repositories being changed."

[always.wheels]
path = "dist"
must = ["*.whl"]

[scope.external]
path = "../external"
layout = "development-targets"
```

Layout name は1個の Archive directory component です。`description` は任意で、空の `[layout.<name>]` も有効です。Layout を宣言しただけでは ZIP に空 directory は作りません。実際にその Layout を使う source があるときだけ `<name>/...` が Archive path に現れます。使用された Layout に `description` があれば generated README にその directory の説明として表示します。

`[about].always_layout` と `[about].targets_layout` はそれぞれ Always source / Target の既定 Layout です。個別の `[always.<name>].layout` または `[scope]` / `[scope.<name>].layout` がある場合は個別指定を優先します。個別指定も既定値も無い source は Archive root 直下へ配置します。

参照先は Base composition 後の effective Layout 集合から解決し、未定義 Layout は error です。Layout name は大文字小文字を区別しない比較で一意でなければなりません。Layout は source 側 filesystem directory を指定するものではなく、Archive destination だけを決めます。

## Always

`[always.<name>]` は Configuration 側で source directory を固定し、実行のたびに参加させる常時ソースです。0.16.0 以降、`<name>` は Always source の Archive directory identity そのものです。`path` は filesystem 上の取得元 directory / Selection root だけを指定し、path の basename や Configuration directory からの relative path は Archive root に使いません。

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

たとえば `[always.guidelines] path = "review-guidelines"` は selected file を `guidelines/` の下へ配置します。`review-guidelines` という source directory name は Archive path に現れません。`[always.company_reference] path = "/srv/company/reference"` も `company_reference/` の下へ配置します。

Relative `path` は、その definition が記述されている Configuration file の directory を基準に解決します。`..` を使って外側の directory を参照でき、absolute `path` は host filesystem 上の directory を直接参照します。`path` は必ず実在 directory に解決し、その directory 自体を Selection boundary とします。Filesystem root も明示的な Always source directory として使用できます。明示 location は symbolic link / Windows directory junction を含められますが、その root 内の自動 traversal で link-like entry は選択・走査しません。

Layout を使わない Always source の Archive directory identity は `[always.<name>]` の `<name>` です。`layout = "<name>"` があれば個別 Layout、なければ `[about].always_layout` を使い、effective Layout がある場合は `LAYOUT/ALWAYS_NAME/...` へ配置します。どちらも無ければ従来どおり `ALWAYS_NAME/...` です。Compatibility `namespace` と effective Layout は同時に使用できません。

Always source の Selection は Target の Pluck とは独立して評価します。同じ physical file が Target 配下にも存在していても、Target 側の `ignore` や Selection result は Always source の Selection を変更しません。両方が同じ physical file を選択し、異なる Archive path に配置する場合は両方を収録します。

Layout 適用後の final archive root は source role に関係なく、大文字小文字を区別しない比較で一意でなければなりません。Target と Always が同じ root に解決する場合も composition は行わず error にします。Pluck を持たず Always source だけで完結する Configuration も有効です。
