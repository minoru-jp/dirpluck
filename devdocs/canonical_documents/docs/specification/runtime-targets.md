<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/runtime_targets.py` です。
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

# Runtime Target, Scope, and Case

## SPEC_037

実効設定に Pluck が存在する場合は、既存契約どおり CLI positional `TARGET` reference を1個以上必要とする。Pluck がない Effective Configuration でも `target_kind = "file"` の Scope から file Target を選ぶ positional Target reference は受理する。Pluck がなく Always source もなく file-kind Scope だけを持つ場合は、実行時に positional Target reference を1個以上必要とする。

level: MUST

condition: Effective Configuration に Pluck が存在する場合, Effective Configuration に Pluck が存在しない場合

## SPEC_038

各 positional reference は effective Scope から1個以上の対象を解決する。Directory Target には同じ effective Pluck selection を独立して適用し、file Target には Pluck を適用せず regular file 自体を atomic source とする。Pluck がない場合に directory Target を解決しようとした run は error とする。Target を Configuration file の配置や Pluck definition の origin から自動推定しない。

level: MUST

## SECTION_501

title: Scope

### SPEC_039

Default Scope は常に1個存在し、ルート設定ファイルがある directory を Scope root とする。Directory name による special case は設けない。`[scope]` はこの default Scope の optional `description` / `target_kind` / `ignore` / `namespace` を設定し、`path` を持たない。`target_kind` の既定は `"directory"` とする。`[scope]` を省略した場合と空の `[scope]` は同じ意味で、description なし、directory Target、`ignore` は空、Namespace reference はなしとする。

level: MUST

related: [SPEC_030](composition.md#spec_030), [SPEC_032](composition.md#spec_032)

### SPEC_040

名前付き `[scope.<name>]` は required `path` と optional `description` / `target_kind` / `ignore` / `namespace` を持つ。`target_kind` は `"directory"` または `"file"` とし、既定は `"directory"` とする。`path` は concrete directory path とし、empty string と glob を拒否する。Relative `path` は Filesystem path notation の共通規則に従って definition の Configuration file directory から解決し、absolute `path` は host filesystem 上の directory を直接参照する。明示された Scope root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で解決した先が実在 directory でなければならない。Scope root 自体が alias であることと、その root 直下で自動発見した link-like Target candidate を除外することは別の rule とする。`description` は空でない string とし Target discovery / Archive placement を変更しない。

level: MUST

related: [SPEC_018](paths.md#spec_018), [SPEC_024](paths.md#spec_024)

### SPEC_041

Named Scope の root が実在し directory であることは、その Scope を `SCOPE/NAME`、`SCOPE/`、`SCOPE:[...]`、`SCOPE:<...>` のいずれかで実際に使用するときに検証する。未使用の named Scope の filesystem availability は、その run を失敗させない。Duplicate effective Scope root の検査は Configuration-level validation として行い、未使用 Scope の存在確認を必要としない。

level: MUST

condition: named Scope を実際に使用する場合

### SPEC_042

Scope name は CLI Target reference の1 path segment として使用できる空でない名前とし、`.`、`..`、`/`、backslash を含めない。

level: MUST

### SPEC_043

Default / named Scope の `namespace` は optional string とし、effective `[namespace.<name>]` の名前を参照する。ネームスペース reference は Target の探索 root、Target candidate、CLI Target reference の意味には影響せず、Archive placement だけに使用する。Unknown Namespace reference は Configuration error とする。

level: MUST

### SPEC_044

`scope.ignore` は Scope の `target_kind` に対応する direct-child Target candidate の **name** を case-sensitive に照合し、一致した entry は単一 Target 選択と全展開のどちらでも Target にできない。Directory mode では directory name、file mode では regular-file name に適用する。File selection の `pluck.ignore` / `always.<name>.ignore` とは独立する。

level: MUST

### SPEC_045

Scope ignore pattern は `name` (exact)、`name*` (prefix)、`*name` (suffix)、`*name*` (substring) の4形式とする。`*` 単体、path separator、backslash、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!` を拒否する。Empty array は有効とする。

level: MUST

## SECTION_502

title: CLI Target reference resolution

### SPEC_046

各 positional `TARGET` argument は、次の形式を受理する。

```text
NAME
SCOPE/NAME
/
SCOPE/
:[NAME/NAME/...]
SCOPE:[NAME/NAME/...]
:<REGEX>
SCOPE:<REGEX>
```

`:[...]` / `SCOPE:[...]` と `:<...>` / `SCOPE:<...>` は `target_kind = "file"` の Scope だけで使用できる file Target selector とする。

level: MUST

### SPEC_047

`NAME` は default Scope の `target_kind` に対応する direct child entry を1個選ぶ。`SCOPE/NAME` は named Scope `SCOPE` の `target_kind` に対応する direct child entry `NAME` を1個選ぶ。`/` は default Scope の全展開、`SCOPE/` は named Scope の全展開とする。`:[...]` / `SCOPE:[...]` は file name の literal list、`:<...>` / `SCOPE:<...>` は eligible file name に対する regular-expression selector とする。

level: MUST

### SPEC_048

`/` は filesystem root を意味しない。CLI Target reference grammar における default Scope の expansion marker である。`./`、`./NAME`、`/NAME`、`SCOPE/team/NAME` のような別表記、多階層 literal reference、absolute filesystem path は受理しない。Literal Target reference と list selector の file name では backslash を path separator として受理しない。Regular-expression selector 内の backslash は regex escape として使用できる。

level: MUST

### SPEC_049

`NAME`、`/`、`:[...]`、`:<...>` は常設の default Scope を使う。`SCOPE/NAME`、`SCOPE/`、`SCOPE:[...]`、`SCOPE:<...>` の `SCOPE` は effective named Scope に存在しなければならず、selector reference を別の relative path interpretation へ fallback しない。

level: MUST

### SPEC_050

Single Target resolution では指定した entry が Scope root の **direct child** にあり、Scope の `target_kind = "directory"` なら実在 directory、`target_kind = "file"` なら実在 regular file でなければならない。Symbolic link または Windows junction として認識した entry は Target として選択せず、明示的な `NAME` / `SCOPE/NAME` がそのような link-like entry を指す場合は error とする。File mode で directory、directory mode で file、または特殊 filesystem entry を指定した場合も error とする。

level: MUST

condition: single Target を解決する場合

### SPEC_051

Scope name は Target lookup の識別子であり、それ自体を archive path に暗黙利用しない。Archive placement に outer directory が必要な場合だけ、Scope が明示参照するネームスペースを使用する。

level: MUST NOT

### SPEC_153

File Target selector は `target_kind = "file"` の Scope だけで有効とする。Directory-kind Scope に `:[...]` / `SCOPE:[...]` または `:<...>` / `SCOPE:<...>` を使用した場合は error とする。

level: MUST

### SPEC_154

List selector は最外郭の `[` と `]` だけを selector syntax とし、その内部を `/` で分割した各 non-empty component を literal direct-child file name とする。内部の `[` / `]` / `<` / `>` / `,` / `:` などは file name の通常文字として扱う。Empty list、empty component、missing closing `]`、存在しない file、Scope `ignore` に一致する file、regular file ではない entry は error とする。

level: MUST

### SPEC_155

Regular-expression selector は最外郭の `<` と `>` を selector syntax とし、その内部を Python-compatible regular expression として compile する。Pattern は Scope `ignore` と link-like exclusion を適用済みの eligible direct-child regular file の basename **全体**へ full-match semantics で適用する。Pattern は non-empty、512 character 以下、`/` を含まないものとし、invalid regular expression と0件 match は error とする。

level: MUST

### SPEC_156

File selector は Scope の candidate discovery を置き換えない。まず `target_kind = "file"`、Scope `ignore`、regular-file requirement、link-like exclusion によって eligible direct-child file Target を確定し、その後 selector で選ぶ。再帰探索は行わない。

level: MUST

### SPEC_157

`:` は Target reference の Scope/selector 境界で `:[` または `:<` の selector marker として現れる場合だけ file selector syntax を開始する。`SCOPE/NAME` の `NAME` 内部を含む、それ以外の `:` は literal Target name の通常文字として扱い、既存の `foo:bar` や `SCOPE/foo:[bar]` のような literal name の意味を変更しない。Selector syntax と同じ形を持つ literal default-Scope file name を明示する必要がある場合は list selector の1 item として指定できる。

level: MUST

## SECTION_503

title: Scope expansion

### SPEC_052

`/` または `SCOPE/` は対応する Scope root の direct child entry を列挙し、Scope の `target_kind` と `ignore` に従う eligible entry をそれぞれ独立した Target として展開する。`target_kind = "directory"` では regular directory だけ、`target_kind = "file"` では regular file だけを対象とし、再帰列挙は行わない。

level: MUST

### SPEC_053

Ignore 対象 entry と、symbolic link / Windows junction として認識した entry は Target candidate として扱わない。認識した link-like entry の参照先は解決せず、`/` / `SCOPE/` の展開結果にも含めない。現在の `target_kind` に対応する eligible direct child が0件の場合は error とする。

level: MUST

### SPEC_054

複数 positional Target reference、Scope expansion、file selector は同じ run で併用できる。

level: MAY

### SPEC_158

File selector と literal Target reference、または複数 file selector が同じ filesystem entry を解決した overlap は1個の runtime Target にまとめる。Selector を含まない既存 literal Target reference 同士が同じ filesystem entry を重複指定した場合は、従来どおり distinct-entry validation error とする。

level: MUST

## SECTION_504

title: Always source と Case

### SPEC_055

`[always.<name>].path` は concrete directory path とし、empty string と glob を拒否する。Relative path は Filesystem path notation の共通規則に従って definition の Configuration file directory を基準に解決する。`.` と `..` を使用でき、absolute path は host filesystem 上の directory を直接参照する。明示された Always source root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で実在 directory に解決する。解決した source directory 自体を selection boundary とし、filesystem root 自体は Always source として拒否する。Root location が alias であることは許可するが、その root 内の Selection traversal で遭遇した link-like entry は Filesystem boundary and entry types の link-like entry rule に従って選択・走査しない。

level: MUST

related: [SPEC_018](paths.md#spec_018), [SPEC_024](paths.md#spec_024), [SPEC_032](composition.md#spec_032)

### SPEC_056

Always source は optional `namespace` string を持てる。値は effective `[namespace.<name>]` を参照し、source filesystem path と selection boundary は変更しない。Unknown ネームスペース reference は Configuration error とする。

level: MUST

### SPEC_057

ケースは実効設定全体で0個または1個だけ有効にし、CLI `--case` から選択する。Layer ごとに別 Case を指定する field はない。

level: MUST

### SPEC_058

Case 未指定時は Pluck があれば `[pluck]`、各 Always source は base `[always.<name>]` selection を使う。

level: MUST

condition: Case を指定しない場合

### SPEC_059

Case 指定時に Pluck がある場合、同名 `[pluck.case.<name>]` を必須とする。各 Always source は同名 `[always.<name>.case.<name>]` があれば使い、なければ base selection へ fallback する。Pluck がない場合は、少なくとも1個の Always source が同名 Case を定義しなければならない。

level: MUST

condition: Case を指定する場合

### SPEC_060

Case selection は base selection の差分ではなく完全な selection とし、`must` / `may` / `ignore` / Shared reference / `allow_empty` を継承しない。

level: MUST
