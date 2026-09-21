from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Specification")
class TITLE_0:
    r'''{{TERM_1}} の CLI、`.dirpluck` {{TERM_2}}形式、`.dirpluck-inv` {{TERM_19}}形式について、互換性対象となる厳密な動作意味論を定義する。両 document の内容は TOML syntax を使用する。 Python package root の公式 API surface と `run()` の呼び出し契約は `PYTHON_API.md` に定義し、`run()` が実行する Configuration / Target / Case / Invocation / Archive semantics はこの仕様と共通とする。用途は `../README.md`、用語の意味は `../GLOSSARY.md`、Configuration の書き方は `CONFIGURATION.md`、CLI の操作方法は `CLI.md`、Configuration / Invocation Template と filesystem 操作の trust boundary は `TRUST.md` を参照する。'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_2, terms.TERM_19)

    @title('1. 公開面')
    class TITLE_1:
        r'''互換性を保証する公開面は `dirpluck` CLI、この文書で定義する `.dirpluck` Configuration document / `.dirpluck-inv` Invocation Template document 形式、および `PYTHON_API.md` で明示する package-root Python API とする。両 document の内容は TOML syntax を使用する。Package root から明示的に export しない Python module / name は内部実装として扱う。'''

    @title('2. CLI document selection')
    class TITLE_2:
        r'''Configuration document の filename extension は `.dirpluck` で、内容は TOML syntax とする。`--config` を省略した場合、dirpluck が暗黙に選択する Configuration は process cwd 直下の `default.dirpluck` 1個だけとする。別 directory の `default.dirpluck`、別名の `*.dirpluck`、file 内容から推論した候補は探索・列挙・自動選択しない。cwd の `default.dirpluck` が存在しなければ not-found error とし、`.toml` file への compatibility fallback は提供しない。

`--config PATH` を指定した場合、`PATH` は4節の filesystem-location notation と同じ lexical rule を使う1個の Configuration document path とする。Relative path は runtime cwd から、absolute path は host filesystem 上の location として解決する。末尾が `.dirpluck` でなければその suffix を付加するため、`release-1.2` は cwd の `release-1.2.dirpluck`、`configs/release-1.2` は cwd の `configs/release-1.2.dirpluck` を表す。Dot を含む stem を別 extension として拒否しない。Trailing `/`、`.`、`..` のように file name を持たない directory form は受理しない。解決後はその1 path だけを使用し、別 directory の同名 file を探索せず、directory を指定して内部の `default.dirpluck` を補完しない。Document path は host OS の通常の filesystem semantics に従って解決し、symbolic link / Windows directory junction を含む path を特別に拒否しない。dirpluck は suffix completion と lexical absolute 化の後の選択 path を Configuration location として保持し、document 内の relative filesystem path の基準にする。解決先が既存 regular file でなければ not-found / invalid-file error とする。

{{TERM_19}} document の filename extension は `.dirpluck-inv` とする。Invocation Template file は `-i PATH` / `--invocation-template PATH` で明示した場合だけ使用し、file 自体の implicit default は持たない。`PATH` の lexical rule と relative / absolute resolution は `--config PATH` と同じで、relative path は runtime cwd 基準とする。末尾が `.dirpluck-inv` でなければ suffix を付加し、`set-2.1` は cwd の `set-2.1.dirpluck-inv`、`invocations/release` は cwd の `invocations/release.dirpluck-inv` を表す。解決後はその1 path だけを使用し、別 directory を探索しない。Document path は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path を特別に拒否しない。Suffix completion と lexical absolute 化の後の選択 path を Invocation Template location として保持する。

`.dirpluck-inv` document は top-level `invocation` table を必要とする。完全に空の document や top-level `invocation` を持たない document は error とする。TOML の `[invocation.<name>]` declaration により親 `invocation` table が暗黙に成立する場合も、この requirement を満たす。

Root `[invocation]` は `-e` / `--entry` を省略したときに選択する default Invocation とする。`[invocation.<name>]` は `-e NAME` / `--entry NAME` で選択する named Invocation entry とする。Named entry は root Invocation の差分・派生ではなく独立した Invocation であり、未指定 field を root から継承・merge しない。`config`、`targets`、`case`、`archive_mtime` は root Invocation の field 名として予約し、同名を named Invocation entry name として受理しない。指定した named entry が存在しなければ error とする。`-e` / `--entry` は Invocation Template file を選択した実行でだけ受理し、最大1回だけ指定できる。

Default Invocation と各 named entry は `config`、`targets`、`case`、`archive_mtime` だけを field として受理し、4 field はすべて optional とする。Field を1つも持たない Invocation も schema 上および実行上有効とする。`targets` は CLI positional Target reference の array とし、各 element は空でない string で6節の grammar に従って execution 時に解決する。`case` は空でない1個の default Case name とする。`archive_mtime` は13節の `--archive-mtime VALUE` と同じ string grammar を使用し、Archive entry timestamp の runtime default とする。`config` は concrete Configuration document path とし、`--config PATH` と同じく末尾が `.dirpluck` でなければ suffix を付加する。4節の filesystem-location notation と同じく `/` separator を使用して glob / backslash を受理しない。Relative `config` path は選択した Invocation Template location の directory、absolute path は host filesystem 上の location を参照し、`~` expansion や environment-variable interpolation は行わない。Control document path の symbolic link / Windows directory junction は host OS の通常の filesystem semantics に従う。

選択した Invocation が `config` を省略した場合は runtime cwd の `default.dirpluck` を使用し、`targets` を省略した場合は positional Target を与えない実行として扱い、`case` を省略した場合は通常の default Case semantics、`archive_mtime` を省略した場合は通常の Archive entry timestamp semantics を使用する。4 field がすべて未指定でも、CLI から与えた runtime value とこれらの normal defaults を通常どおり適用する。成功した `--preview` または通常 build で field を1つも持たない Invocation が選択されていた場合は、その状態を warning ではない runtime note として CLI output に表示する。

Invocation Template を使用する実行では positional `TARGET` と `--config` による差分・override を受理しない。`--case` は選択した Invocation の保存 field override として受理し、指定時はその Invocation の `case` より優先する。`--archive-mtime` も保存 field override として受理し、指定時は Invocation の `archive_mtime` より優先する。`--preview`、`--sequence`、`--archive-mtime`、`--paths` は Template の保存内容を変更しない runtime modifier として通常の制約の範囲で併用できる。

{{TERM_13}}の参照では CLI document selection を行わない。各 Configuration は `about.base` に `.dirpluck` extension を持つ concrete Configuration file path を直接記述する。Base path も host OS の通常の filesystem semantics に従い、relative path は参照元 Configuration location の directory を基準にする。`.dirpluck-inv` document は Configuration ではなく base chain に参加しない。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_19)

    @title('3. Configuration schema')
    class TITLE_3:
        r'''受理する top-level 構造は次とする。

```text
[about]
[shared.must]
[shared.may]
[shared.ignore]
[pluck]
[pluck.case.<name>]
[scope]
[scope.<name>]
[namespace.<name>]
[always.<name>]
[always.<name>.case.<name>]
[output]
[output.timestamp]
```

未知の key は error とする。

`[about]` は任意で、`description` と `base` だけを持つ。両 field はそれぞれ任意だが、`[about]` を定義する場合は少なくとも一方を必要とする。`description` は空でない string、`base` は1個の Configuration file path とする。

各 Configuration layer は Pluck を0個または1個、名前付き Scope、Always source、Shared pattern、{{TERM_18}}を0個以上持てる。`[scope]` は root Configuration で常設される default Scope の optional `ignore` / `namespace` 設定であり、Scope の存在宣言ではない。Pluck / Always は Case を0個以上持てる。

各 Configuration は Output を0個または1個宣言できる。Output を宣言する場合、fixed output と timestamp output は排他的である。Configuration file 単体の schema validity と Archive planning / `--preview` には Output を要求しない。実際に Archive file を書き込む build では、{{TERM_14}}自身が Output を直接宣言しなければならない。Base layer の Output は root へ継承しない。

ひとつの Configuration layer が local source definition を持たなくてもよい。Base composition 後の{{TERM_15}}には Pluck または Always source の少なくとも一方が必要である。Default Scope は root Configuration に常に存在するため、Effective Pluck のために別途 Scope declaration を要求しない。'''
        vocabulary_refs @= (terms.TERM_14, terms.TERM_15, terms.TERM_18)

    @title('4. Filesystem path notation')
    class TITLE_350:
        r'''Configuration / Invocation Template の TOML で filesystem location を表す field と、CLI の `--config PATH` / `-i PATH` は、host OS に関係なく `/` を path separator として使用する。Backslash は separator として受理せず、Windows でも `/` を記述する。

Configuration 内の relative filesystem path は、field の種類や runtime state によって resolution base を切り替えず、**その field が記述されている Configuration file の directory**から解決する。少なくとも次の field にこの規則を適用する。

```text
about.base
scope.<name>.path
always.<name>.path
output.path
output.timestamp.path
```

Base chain の inner Configuration に記述された relative path は inner Configuration 自身の directory から解決し、outer Configuration の directory へ rebase しない。

Absolute path は host OS が完全な absolute path として認識する root form を `/` separator で記述し、その場所を直接参照する。例として POSIX host の `/opt/data`、Windows host の `C:/data` と `//server/share/data` を受理できる。別 OS の root form へ自動変換しない。Windows drive-relative form (`C:foo`) は absolute path として扱わない。

Filesystem-location notation では `~` expansion と environment-variable interpolation を行わず、glob を受理しない。`.` と `..` は field / option 固有の file / directory 条件を満たす範囲で通常の path component として解決する。Absolute path を使用した Configuration や CLI document selection は参照先 filesystem に依存し、OS 間 portability を保証しない。

CLI の `--config PATH` / `-i PATH` だけは relative path の resolution base を runtime cwd とする。Invocation Template 内の default / named Invocation の `config` は Template document 自身の directory を基準にする。Configuration 読み込み後の relative filesystem path resolution に runtime cwd を使用しない。

Configuration / Invocation Template **document 自体を選択または参照する path** は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path を特別に拒否しない。cwd の `default.dirpluck`、`--config PATH`、`-i PATH`、`about.base`、Invocation の `config` のいずれでも、dirpluck は選択・参照した path を symlink target の実体 path へ置き換えず、lexical な absolute document location として保持する。Relative document reference と、その document に記述された relative filesystem location はこの document location の directory を基準にする。Base-chain cycle detection のように file identity が必要な内部判定だけ、実体 path を用いて alias を同一 Configuration と認識する。

この control-document rule は source root resolution / source tree traversal の link handling とは別である。`[scope.<name>].path` と `[always.<name>].path` のように Configuration が明示する source root location は host OS の通常の filesystem semantics に従い、path の途中または最終 component が symbolic link / Windows directory junction であることだけを理由に拒否しない。明示 location を実在 directory に解決した後、その directory を source root / selection boundary とする。一方、その root から Dirpluck が Target discovery / Selection traversal を自動的に行う段階では9節の規則に従って認識した link-like entry を選択・走査しない。Include pattern、ignore pattern、archive path、CLI Target reference など filesystem location ではない値は、それぞれの規則に従う。'''

    @title('5. Base chain と composition')
    class TITLE_4:
        r'''{{TERM_13}}は `[about].base` として宣言する。`base` は concrete Configuration file path とし、空文字列と glob を拒否する。Relative path は4節の共通規則で現在の Configuration file directory から解決し、absolute path は host filesystem 上の file を直接参照する。Path は `.dirpluck` extension を必要とし、host OS の通常の filesystem semantics に従って参照する。解決先は実在 regular file で、内容が有効な TOML Configuration schema でなければならない。

各 Configuration が参照できる base は0個または1個とする。Base Configuration がさらに `base` を持つ場合は linear chain を形成する。Depth に固定上限は設けない。'''
        vocabulary_refs @= (terms.TERM_13,)

        @title('Cycle detection')
        class TITLE_401:
            r'''Base resolution では、診断と relative path resolution のために各 Configuration の選択された document location を保持しつつ、cycle identity は symbolic link / junction alias を解決した実体 file path で比較する。alias 解決後に同じ physical Configuration path となる Configuration が別の document path alias から現在の chain に再登場した場合も cycle error とし、診断には選択された document location の chain を含める。Depth 自体による error / warning は行わない。'''

        @title('Definition composition')
        class TITLE_402:
            r'''Chain の最深部を初期値とし、1 layer ずつ外側の definition を重ねて{{TERM_15}}を構成する。

`[about].description` は outermost layer から inner layer へ探索し、最初に定義された値を effective description とする。Chain 全体に定義がなければ effective description は存在しない。`about.base` は chain link であり effective value として shadow / merge しない。Base layer に書かれた `[scope]` はその Configuration 自身を Root として使う場合の default Scope 設定であり、outer Root の default Scope へ継承しない。

- Pluck: outer layer に Pluck があれば inner Pluck definition 全体を shadow する。
- Always source: 同名 source は outer layer が definition 全体を shadow し、異なる名前は保持する。
- Named Scope: 同名 Scope は outer layer が definition 全体を shadow し、異なる名前は保持する。Default Scope は compose せず、6節で定める Root Configuration location から root を決め、root Configuration の `[scope].ignore` / `namespace` だけを使う。
- {{TERM_18}}: 同名 Namespace は outer layer が definition 全体を shadow し、異なる名前は保持する。Scope / Always の Namespace reference は composition 後の effective Namespace 集合に対して解決する。
- Shared pattern: `must` / `may` / `ignore` を独立した namespace とし、各 namespace の同名 pattern set は outer layer が配列全体を shadow する。

Pluck / Always / named Scope / {{TERM_18}} の shadow は field 単位の partial merge ではない。Source definition の Case も source definition と一緒に置き換える。

Named Scope root と Always source path は、その definition を記述した Configuration file の directory を基準として解決する。Base から残った definition は origin の resolution result を保持し、outer layer へ rebase しない。Default Scope は path field を持たず、6節の専用 rule で root を決める。

Composition 後の effective Scope 群について、filesystem 上の存在を要求せずに path を解決・正規化した Scope root が同一 location になる定義を複数持つことはできない。Default Scope と named Scope の組み合わせにもこの rule を適用する。親子関係にある異なる directory は、この duplicate rule だけでは同一とはみなさない。

Selection の Shared reference は、source の origin layer ではなく chain 全体を重ね終えた effective shared namespace で解決する。Outer layer は inner source が参照する同名 pattern set を提供または shadow できる。'''
            vocabulary_refs @= (terms.TERM_15, terms.TERM_18)

        @title('Output と base chain')
        class TITLE_403:
            r'''Output definition は source definition のようには compose しない。Configuration は Output を省略でき、共通 definition だけを提供する Base Configuration として利用できる。Archive planning と `--preview` は root Output を必要としない。実際に Archive file を書き込む build で使用するのは{{TERM_14}}自身が直接宣言した Output だけとし、root が Output を持たない場合は build error とする。Inner layer の Output を root へ継承しない。

Base chain 上では、Output を宣言している Configuration の definition だけを各 Configuration の書き込み所有境界として保持し、11節の規則で chain 内の{{TERM_17}}が overlap しないことを検証する。Output を宣言しない layer は write boundary を持たない。'''
            vocabulary_refs @= (terms.TERM_14, terms.TERM_17)

    @title('6. Runtime Target、Scope、Case')
    class TITLE_5:
        r'''{{TERM_15}}に Pluck が存在する場合は CLI positional `TARGET` reference を1個以上必要とする。Pluck がない Effective Configuration では positional Target reference を受理しない。

各 positional reference は effective Scope から1個以上の{{TERM_3}}を解決し、各 Target へ同じ effective Pluck selection を独立して適用する。Target を Configuration file の配置や Pluck definition の origin から自動推定しない。'''
        vocabulary_refs @= (terms.TERM_3, terms.TERM_15)

        @title('Scope')
        class TITLE_501:
            r'''Default Scope は常に1個存在し、{{TERM_14}}がある directory を Scope root とする。Directory name による special case は設けない。`[scope]` はこの default Scope の optional `ignore` / `namespace` だけを設定し、`path` を持たない。`[scope]` を省略した場合と空の `[scope]` は同じ意味で、default Scope の `ignore` は空、Namespace reference はなしとする。

名前付き `[scope.<name>]` は required `path` と optional `ignore` / `namespace` を持つ。`path` は concrete directory path とし、empty string と glob を拒否する。Relative `path` は4節の共通規則で definition の Configuration file directory から解決し、absolute `path` は host filesystem 上の directory を直接参照する。明示された Scope root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で解決した先が実在 directory でなければならない。Scope root 自体が alias であることと、その root 直下で自動発見した link-like Target candidate を除外することは別の rule とする。

Named Scope の root が実在し directory であることは、その Scope を `SCOPE/NAME` または `SCOPE/` で実際に使用するときに検証する。未使用の named Scope の filesystem availability は、その run を失敗させない。Duplicate effective Scope root の検査は Configuration-level validation として行い、未使用 Scope の存在確認を必要としない。

Scope name は CLI Target reference の1 path segment として使用できる空でない名前とし、`.`、`..`、`/`、backslash を含めない。

Default / named Scope の `namespace` は optional string とし、effective `[namespace.<name>]` の名前を参照する。{{TERM_18}} reference は Target の探索 root、Target candidate、CLI Target reference の意味には影響せず、Archive placement だけに使用する。Unknown Namespace reference は Configuration error とする。

`scope.ignore` は Target candidate の direct child directory **name** を case-sensitive に照合し、一致した directory は単一 Target 選択と全展開のどちらでも Target にできない。File selection の `pluck.ignore` / `always.<name>.ignore` とは独立する。

Scope ignore pattern は `name` (exact)、`name*` (prefix)、`*name` (suffix)、`*name*` (substring) の4形式とする。`*` 単体、path separator、backslash、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!` を拒否する。Empty array は有効とする。'''
            vocabulary_refs @= (terms.TERM_14, terms.TERM_18)

        @title('CLI Target reference resolution')
        class TITLE_502:
            r'''各 positional `TARGET` argument は、次の4形式のいずれかだけを受理する。

```text
NAME
SCOPE/NAME
/
SCOPE/
```

`NAME` は default Scope 直下の directory を1個選ぶ。`SCOPE/NAME` は named Scope `SCOPE` 直下の directory `NAME` を1個選ぶ。`/` は default Scope の全展開、`SCOPE/` は named Scope の全展開とする。

`/` は filesystem root を意味しない。CLI Target reference grammar における default Scope の expansion marker である。`./`、`./NAME`、`/NAME`、`SCOPE/team/NAME` のような別表記、多階層 reference、absolute filesystem path、backslash separator は受理しない。

`NAME` と `/` は常設の default Scope を使う。`SCOPE/NAME` と `SCOPE/` の `SCOPE` は effective named Scope に存在しなければならず、unknown name を別の relative path interpretation へ fallback しない。

Single Target resolution では指定した entry が Scope root の **direct child** にある実在 directory でなければならない。Symbolic link または Windows directory junction として認識した entry は Target として選択せず、明示的な `NAME` / `SCOPE/NAME` がそのような link-like entry を指す場合は error とする。

Scope name は Target lookup の識別子であり、それ自体を archive path に暗黙利用しない。Archive placement に outer directory が必要な場合だけ、Scope が明示参照する{{TERM_18}}を使用する。'''
            vocabulary_refs @= (terms.TERM_18,)

        @title('Scope expansion')
        class TITLE_503:
            r'''`/` または `SCOPE/` は対応する Scope root の direct child directory entry を列挙し、Scope の `ignore` に一致しないものをそれぞれ独立した Target として展開する。再帰的な directory 列挙は行わず、regular file は Target にしない。

Ignore 対象 entry と、symbolic link / Windows directory junction として認識した entry は Target candidate として扱わない。認識した link-like entry の参照先は解決せず、`/` / `SCOPE/` の展開結果にも含めない。展開結果が0 eligible directory の場合は error とする。

複数 positional Target reference と expansion は同じ run で併用できる。'''

        @title('Always source と Case')
        class TITLE_504:
            r'''`[always.<name>].path` は concrete directory path とし、empty string と glob を拒否する。Relative path は4節の共通規則で definition の Configuration file directory を基準に解決する。`.` と `..` を使用でき、absolute path は host filesystem 上の directory を直接参照する。明示された Always source root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で実在 directory に解決する。解決した source directory 自体を selection boundary とし、filesystem root 自体は Always source として拒否する。Root location が alias であることは許可するが、その root 内の Selection traversal で遭遇した link-like entry は9節の規則どおり選択・走査しない。

Always source は optional `namespace` string を持てる。値は effective `[namespace.<name>]` を参照し、source filesystem path と selection boundary は変更しない。Unknown {{TERM_18}} reference は Configuration error とする。

{{TERM_4}}は{{TERM_15}}全体で0個または1個だけ有効にし、CLI `--case` から選択する。Layer ごとに別 Case を指定する field はない。

Case 未指定時は Pluck があれば `[pluck]`、各 Always source は base `[always.<name>]` selection を使う。

Case 指定時に Pluck がある場合、同名 `[pluck.case.<name>]` を必須とする。各 Always source は同名 `[always.<name>.case.<name>]` があれば使い、なければ base selection へ fallback する。Pluck がない場合は、少なくとも1個の Always source が同名 Case を定義しなければならない。

Case selection は base selection の差分ではなく完全な selection とし、`must` / `may` / `ignore` / Shared reference / `allow_empty` を継承しない。'''
            vocabulary_refs @= (terms.TERM_4, terms.TERM_15, terms.TERM_18)

    @title('7. Namespace')
    class TITLE_550:
        r'''{{TERM_18}}は `[namespace.<name>]` という名前付き table で定義する。現行 schema では table 本体は空でなければならず、属性を受理しない。親 `[namespace]` だけを空で定義することは Namespace definition にならないため error とする。

Namespace name はそのまま ZIP 内の directory component になる。空名、`.`、`..`、`/`、backslash、control character、portable filename component として不適切な `< > : " | ? *` を拒否する。Namespace は filesystem path ではなく Archive path の1 component である。

Scope / Always source の `namespace` field は effective Namespace name を参照する。Namespace を参照した source の final archive root は `NAMESPACE/SOURCE_ROOT` とする。この prefix は他 source との衝突有無にかかわらず常に適用する。Namespace を参照しない source の final archive root は `SOURCE_ROOT` のままとする。

複数 source が同じ Namespace を参照すること自体は有効である。ただし Namespace は自動 collision resolver ではなく、final archive root の一意性は10節の Archive planning rule で検証する。'''
        vocabulary_refs @= (terms.TERM_18,)

    @title('8. Selection と Shared pattern')
    class TITLE_6:
        r'''Pluck / Always source の base または Case selection は、`must` / `may` の candidate を少なくとも1個必要とする。Candidate は direct pattern または Shared reference で記述できる。`description` は任意で、記述する場合だけ空でない string を必要とする。

`must` / `may` の array item は direct pattern string または1要素 Shared reference array とする。

```text
"foo"       direct pattern
["foo"]     Shared reference
```

`ignore` の direct string は name pattern とする。1要素 nested array は reference marker とし、中の string が `./` で始まれば Selection-relative path reference、それ以外なら `shared.ignore` の Shared reference とする。

```text
"*.pyc"                         direct name pattern
["python-noise"]               Shared ignore reference
["./tests/fixtures/big.bin"]   file path reference
["./tests/fixtures/"]          directory path reference
```

Nested array の要素数はちょうど1、要素は non-empty string でなければならない。`[]`、`["foo", "bar"]`、`[123]` は error とする。`must` / `may` では nested array は Shared reference 専用とする。

Shared reference namespace は field から一意に決まる。

```text
must   -> shared.must
may    -> shared.may
ignore -> shared.ignore
```

Shared pattern definition の value は direct pattern の non-empty array とし、Shared reference や path reference を nested させない。

Base composition 後の effective shared namespace に対して Shared reference を解決する。Unknown reference は Configuration error とする。Selection array の順序を保って Shared reference をその pattern set へ展開する。Path reference は Shared namespace を参照せず、その Selection の source root を基準に解釈する。

展開後の `must` 内、`may` 内、`ignore` 内の同一記述の duplicate pattern/reference、および `must` / `may` 間の duplicate include pattern は Configuration error とする。一方、異なる ignore 条件が同じ filesystem entry に一致する semantic overlap は有効で、除外結果は条件の和とする。

`allow_empty` は boolean で既定 `false` とする。`allow_empty = true` は、Shared reference 展開後に `must` pattern を持たない selection だけで指定できる。'''

        @title('Include pattern grammar (`must` / `may`)')
        class TITLE_601:
            r'''`must` と `may` の direct / expanded pattern は source directory からの `/` separator の relative path とする。Absolute path、`.` / `..` による逸脱、backslash を拒否する。

各 path element には `*` を最大1個だけ含められる。`*` はひとつの実体名内部で0文字以上に一致し、path separator を越えない。そのため Configuration に書いた path hierarchy の深さは固定される。

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

`must` pattern は1件以上の **non-ignored selectable entry** に一致しなければ error、`may` pattern は0件一致を許容する。複数一致した場合は `ignore` 適用後に残ったものを selection candidate とする。

最後に一致した実体が regular file ならその file を選択し、regular directory なら `ignore` に従って配下の regular file を再帰収集する。`ignore` は entry の種類による診断より優先し、ignored entry は selectable match、link-only / special-entry-only match、skipped-link count のいずれにも含めない。Symbolic link または Windows directory junction として認識した **non-ignored** entry は selectable entry とみなさない。Pattern がそのような non-ignored link-like entry だけに一致した場合、`must` は通常の不存在と区別できる理由付き error とし、`may` は optional missing として扱う。

FIFO、socket、device など regular file / regular directory ではない **non-ignored** filesystem entry も selectable entry とせず、Archive に含めない。`may` がそのような特殊 entry に一致しても選択せず optional missing とし、`must` が特殊 entry だけに一致した場合は unsupported special filesystem entry にしか一致しなかったことを示す理由付き error とする。Regular directory の配下を再帰収集するときに現れる特殊 entry は traversal せず、静かに除外する。内容や filename の意味に基づく暗黙 ignore は行わない。

Matching は OS に依存せず case-sensitive とする。`**`、`?`、character class (`[]`)、`!` はサポートしない。複数一致を version、mtime、その他 metadata で順位付けしない。'''

        @title('Ignore grammar')
        class TITLE_602:
            r'''Selection の `ignore` は name pattern と Selection-relative concrete path reference の2種類を持つ。

Direct string はひとつの実体名を case-sensitive に照合する。末尾 `/` の pattern は directory name、`/` のない pattern は file name に適用する。対応形式は次とする。

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

Directory name pattern ではこの body の末尾に `/` を付ける。

```text
.git/
__pycache__/
tmp-*/
```

Selection-relative path reference は1要素 nested arrayの stringを `./` で始める。Pluck では Target directory、Always source では解決済み Always source directory を Selection root とする。末尾 `/` は concrete directory path、末尾 `/` なしは concrete file path とし、filesystem 上の現状から file / directory を推測しない。

```text
["./tests/fixtures/big.bin"]   exact file path
["./tests/fixtures/"]          exact directory path and its subtree
```

Path reference は Selection root の内側だけを指し、`./` 自体、`..` component、absolute path、glob、backslash を拒否する。Path separator は `/` とする。Directory path reference に一致した directory は subtree を traversal する前に prune する。File path reference は完全一致した fileだけを除外する。

Name pattern、Shared ignore expansion、path reference は集合的な除外条件として適用する。同じ entry に複数条件が一致しても error ではなく、評価順序は observable semantics に含めない。実装は directory 条件に一致した subtree を早期に prune してよい。

`ignore` は link-like / special entry の種類による診断より優先する。Ignored entry は Selection candidate、link-only / special-entry-only error の根拠、skipped-link count の対象にせず、ignored subtree の entry も列挙や traversal-time validation の対象にしない。末尾 `/` のない name pattern は regular file だけでなく、同じ name を持つ特殊 entry にも適用する。Path reference が link-like entry 自身に一致する場合も ignored entry として扱う。

Name pattern では `*` 単体、`*/`、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!`、backslash、body 内の path separator を拒否する。Path reference は wildcard syntax を持たない。'''

    @title('9. Filesystem boundary と non-regular entry')
    class TITLE_7:
        r'''Configuration file directory は relative Configuration path の resolution anchor であり、すべての source をその配下へ閉じ込める共通 boundary ではない。

Runtime Target directory は対応する Scope root の direct child として解決する。Scope root は Target candidate を探す base であり、selected file の boundary は最終的に解決した Target directory 自体である。

Named Scope / Always source の明示 root location は relative / absolute `path` から host OS の通常の filesystem semantics で実在 directory を解決でき、symbolic link / Windows directory junction を含む location も root として利用できる。Always は解決した source directory 自体を selection boundary とする。Output location は source boundary に参加しない。

各 source の include resolution と selected file は、その source directory 内へ限定する。Archive に含める filesystem object は regular file に限定し、regular directory は traversal のためだけに扱う。Target discovery または Selection traversal で symbolic link として認識した entry は selectable entry とせず、リンク先を解決・走査せず、Archive にも含めない。Windows では directory junction も同じ link-like entry として扱う。File symlink、directory symlink、broken symlink、認識した Windows directory junction はいずれも traversal しない。FIFO、socket、device などその他の non-regular entry も Archive に含めず、directory として traversal しない。

Python 3.11 でも Windows directory junction を判定できるよう、Windows では `lstat` が返す reparse tag を利用する。判定はひとつの内部 helper に集約し、Target discovery、Selection traversal、link-like entry を拒否する runtime filesystem check で同じ判定を使用する。Control document path の resolution にはこの link-like 判定を適用しない。対応対象の Windows runtime で junction 判定に必要な reparse-tag 定数または stat metadata を取得できない場合は、通常 directory とみなして traversal を続けず、safety boundary を確立できない error とする。これは既知の symbolic link / directory junction を扱うための safety boundary であり、platform に存在し得るすべての reparse point や未知の redirecting mechanism の完全な検出を保証しない。

Selection traversal で認識して除外した **non-ignored** link-like entry は、同じ path を複数 pattern から観測しても1件として数える。`--preview` は contents tree の後に、通常 build は output path の後に、除外した総件数を CLI note として表示する。個々の link path は表示せず、Archive `README.md` にもこの runtime note を記録しない。`ignore` に一致した link-like entry と、directory `ignore` によって内部へ入る前に枝刈りされた subtree の entry は skipped-link count に含めない。

この規則は source root から自動的に tree を探索するときに現れる entry に対するものであり、Configuration の `about.base`、named Scope `path`、Always `path`、Output `path` といった明示 filesystem path の resolution rule は4節および各該当節に従う。特に named Scope / Always の root location は alias を利用できても、そこから先の Target discovery / Selection traversal が別の link-like entry をたどることを意味しない。生成した ZIP を展開するときの entry / filesystem object の解釈は extractor と platform に依存し、dirpluck は第三者の展開 software の動作を保証しない。'''

    @title('10. Archive planning')
    class TITLE_8:
        r'''Scope から解決した Target の source root は Target directory name 1 segment とする。Logical Scope name は archive path へ暗黙には含めない。

Always source の source root は、実体 directory ではなく Configuration に明示された source location から決める。Source location が、その definition を記述した Configuration file directory の配下にある場合は、その Configuration directory から見た lexical relative path とする。Absolute path または `..` により source location がその base 外にある場合は、明示 location の最終 directory name を source root とする。最終 component が symbolic link / Windows directory junction で実体 directory name と異なる場合も、Archive では明示 location 側の name を保持する。Filesystem root 自体を Always source として受理しないのは、この portable source root を持たないためである。Host の absolute path、drive、UNC share 名そのものは archive path へ埋め込まない。

{{TERM_18}}を参照しない source の final archive root は source root と同じである。Namespace を参照する source は `NAMESPACE/SOURCE_ROOT` を final archive root とし、その下へ source directory からの relative selected file path を配置する。Namespace は collision が実際に起きた場合だけ追加するのではなく、その source へ常に適用する。

1回の実行で異なる resolved source が同じ final archive root に解決された場合は、file selection の内容が重ならなくても ambiguity error とする。dirpluck は source を同じ directory へ黙って merge せず、自動 suffix や Scope / Always 名による自動 qualification も行わない。必要な場合は Configuration で Namespace を明示して final archive root を区別する。

Final archive root が一意であることを確認した後も、同じ archive path に異なる physical file が衝突する場合、または同じ physical file が異なる source mapping から異なる archive path へ解決される場合は ambiguity error とする。同じ archive path に同じ physical file が再度現れる場合は1回だけ書き込む。

Archive root の root-level `README.md` は dirpluck が生成する index 用の予約 path とする。Resolved source の final archive root の先頭 component が case-insensitive に `README.md` と一致する場合は error とし、その下へ source tree を配置しない。この規則は Namespace 名だけでなく、Namespace を使わない source root にも同じように適用する。

Archive root には{{TERM_10}}を `README.md` として生成する。これは archive contents の index であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は `# Archive contents` の直後にその本文を表示する。存在しない場合はこの全体説明を省略する。

各 resolved source は、その final archive root を inline code とした level-2 heading で1 sectionずつ表現する。Section には selected file 数を `Files: N` として記録し、selection `description` が存在する場合は、その metadata の後へ本文としてそのまま表示する。`description` を table cell へ圧縮せず、複数行を含む説明も section body として保持する。description がない source には説明本文を追加しない。

少なくとも1個の source に Namespace が適用される場合、README は source section の前に Namespace が Archive 専用の outer directory であり元 source path の一部ではないこと、source root がその直下にあることを説明する。Namespace を使う各 source section には `Namespace` と `Source root` も表示する。Namespace を使わない source にはこの metadata を追加しない。

既定では source filesystem path、Configuration path / table、base chain、Scope / Pluck / Always 名、選択 Case などの dirpluck 固有情報を記録しない。CLI `--paths` が指定された場合だけ各 source section に `Source` として解決済み source directory を `/` separator の filesystem path で記録する。`--paths` は archive path や file selection を変更しない。'''
        vocabulary_refs @= (terms.TERM_10, terms.TERM_18)

    @title('11. Output')
    class TITLE_9:
        r'''Configuration は Output を省略できる。Output を持たない Configuration も Root として Archive planning / `--preview` に使用できる。実際に Archive file を書き込む build では、{{TERM_14}}が fixed output または timestamp output のどちらか一方を自身で直接宣言しなければならない。Base の Output は root の Output として継承しない。Output filesystem path の既存状態確認、directory 作成、Archive 書き込みを行うのは build 時の root 自身の Output だけとする。

Base chain では、実際に Output を宣言している definition だけが{{TERM_17}}の overlap validation に参加する。Output path の relative resolution は常にその Output を記述した Configuration file の directory を基準とする。'''
        vocabulary_refs @= (terms.TERM_14, terms.TERM_17)

        @title('Fixed output')
        class TITLE_901:
            r'''```toml
[output]
path = "artifacts/context.zip"
overwrite = false
```

`path` を必須とし、`overwrite` は optional boolean、既定 `false` とする。`timestamp` subtable、`prefix`、`suffix` は fixed mode では指定できない。

`path` は concrete file path とする。末尾 `/` の directory notation、glob、directory として解決される destination を拒否する。Relative path では `.` と `..` を通常どおり解決できる。必要な parent directory は作成する。Output location に Configuration directory boundary は設けない。

`overwrite = false` では build 前と最終配置直前に destination が存在しないことを確認する。いずれかの確認時点で existing destination を認識した場合は、その existing output を変更せず失敗する。ただし、この存在確認と最終配置は concurrent writer に対する atomic な no-clobber operation ではない。最終確認後から配置までの間に別 process が同じ destination を作成または置換した場合、その file を dirpluck が置換し得る。

`overwrite = true` では output directory の temporary file へ新しい ZIP を完成させた後で existing output を置換する。既存 destination の file mode は継承しない。

生成する Archive file は host OS の通常の新規 file creation semantics に従う。POSIX では通常の regular file creation mode `0666` に process `umask` を適用した mode で temporary output を作成し、その mode のまま final destination へ置換する。したがって new output と overwrite のどちらも、その run の `umask` に基づく新規 file mode になる。

Filename extension は ZIP format の判定に使用しない。Fixed output では Configuration に書かれた filename を runtime に変更・展開しない。'''

        @title('Timestamp output')
        class TITLE_902:
            r'''```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` を必須とし、`prefix` と `suffix` は任意とする。`overwrite` は指定できない。

`path` は concrete directory path とし、Configuration notation 上で末尾 `/` を必須とする。Glob は拒否する。Relative path では `.` と `..` を通常どおり解決できる。必要な directory は作成する。Output location に Configuration directory boundary は設けない。

`prefix` と `suffix` は空でない1個の portable filename fragment とし、`.`、`..`、path separator、control character、`< > : " | ? *` を拒否する。

Generated filename は次の固定形式とする。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

Timestamp は process local time を使い、build 開始時に一度だけ確定する。自由な timestamp format、variable expansion、naming template は提供しない。

`N` は CLI `--sequence N` から受け取る1以上の integer とする。省略時は number segment を出力しない。Existing output を探索して番号を推測せず、自動採番・自動 rename を行わない。`--sequence` は timestamp output だけで使用できる。

Generated filename が確認時点で既に存在する場合は error とし、overwrite option は提供しない。Generated Archive file の permission / mode は fixed output と同じく host OS の通常の新規 file creation semantics に従う。'''

        @title('Archive entry timestamp')
        class TITLE_9025:
            r'''`--archive-mtime VALUE` は Output path / filename ではなく、生成する ZIP entry metadata の timestamp policy とする。Configuration schema には対応 field を持たず、CLI / Python API の runtime option または Invocation Template の `archive_mtime` field から指定する。

`VALUE` は `now`、`zip-epoch`、または厳密な `YYYY-MM-DDTHH:MM:SS` string とする。明示 timestamp は timezone suffix / offset を持たない literal として解釈し、timezone conversion を行わない。ZIP/DOS timestamp が表現できる範囲として 1980-01-01T00:00:00 以上 2107-12-31T23:59:59 以下を受理する。`zip-epoch` は 1980-01-01T00:00:00 と等価とする。`now` は1回の high-level run で process local current time を1度だけ取得し、その1値を使用する。

ZIP timestamp は2秒粒度なので、resolved timestamp の秒が奇数なら直前の偶数秒へ切り下げる。Microsecond は保持しない。Resolved timestamp は generated root `README.md`、empty directory entry、selected source file を含む、その run で書き込むすべての ZIP entry へ同一に設定する。

`--archive-mtime` / Invocation `archive_mtime` を省略した場合は既存 semantics を維持し、selected source file は filesystem mtime を使用し、Dirpluck が `writestr` 相当で生成する entry は生成時刻を使用する。

この option は entry timestamp を固定し、timestamp に起因する byte 差を取り除くための機構である。Source file の permission bits は ZIP `external_attr` に保持されるため、file content と timestamp が同じでも permission が異なれば Archive byte 列は異なり得る。Dirpluck は permission bits を正規化しない。Compressor implementation、runtime version、platform 由来の ZIP metadata / serialization detail も含め、Archive 全体の byte-for-byte reproducibility は保証しない。また timestamp output の filename に使う process-local `YYYYMMDD-HHMMSS` とは独立し、その filename timestamp を変更しない。`--preview` では Archive を書かないため archive mtime は出力結果へ影響しない。'''

        @title('Static writable destination')
        class TITLE_903:
            r'''Output naming は、Configuration だけから{{TERM_17}}を静的に確定できることを不変条件とする。

```text
fixed [output]
    -> resolved complete file path 1個

timestamp [output.timestamp]
    -> resolved output directory を root とする directory tree
```

Fixed output では user が filename 全体を決定し、dirpluck は runtime にその一部を補完しない。Timestamp output では user が output directory を決定し、dirpluck がその directory 直下の filename だけを決定する。`artifacts/{target}-{timestamp}.zip` のように Configuration から書き込み先 directory を静的に確定できない template mode は提供しない。'''
            vocabulary_refs @= (terms.TERM_17,)

        @title('Base chain write-boundary overlap')
        class TITLE_904:
            r'''Base chain 上の各 Configuration が宣言する resolved{{TERM_17}}は、chain 内の別 Output と overlap してはならない。比較は Configuration に書かれた文字列ではなく、各 Configuration file を anchor として resolve / normalize した path で行う。

Fixed output 同士は、完全 file path が同一の場合だけ conflict とする。同じ directory に別 filename の fixed output を置くことはできる。

```text
out/base.zip
out/derived.zip
```

Timestamp output 同士は、directory boundary が同一、祖先、子孫のいずれかなら conflict とする。

```text
artifacts/
artifacts/release/
```

Fixed output と timestamp output では、fixed output の完全 file path が timestamp output の directory boundary 内に入る場合を conflict とする。

```text
artifacts/            timestamp boundary
artifacts/result.zip  fixed output -> conflict
```

この validation は現在解決している1本の base chain 内だけで行う。無関係な別 Configuration chain が同じ filesystem location を宣言しているかどうかは探索・保証しない。'''
            vocabulary_refs @= (terms.TERM_17,)

        @title('Concurrent write と input collision')
        class TITLE_905:
            r'''dirpluck は process 間 lock や競合調停を提供しない。同じ output path への concurrent write はサポート対象外とする。Fixed output の `overwrite = false` と timestamp output の既存 destination check は、別 process に対する atomic な no-clobber guarantee ではない。並行する可能性がある呼び出し側は異なる output destination を選ぶ必要がある。

どちらの output mode でも、実行で生成する最終 output file 自身を archive input として選択することはできない。'''

    @title('12. Preview')
    class TITLE_10:
        r'''`--preview` は通常実行と同じ base chain resolution、cycle detection、definition composition、Scope lookup / expansion、Target direct-child resolution と Scope ignore filtering、Case selection、file selection、archive planning を使うが、output file / directory を作成・変更しない。Root Configuration に Output declaration がなくても使用できる。`--preview` は output filename generation を行わないため `--sequence` と組み合わせない。`--archive-mtime` は preview でも validation するが、Archive を書き込まないため preview result には影響しない。

不足する `must` pattern は `[missing]`、不足する `may` pattern は `[optional missing]` と表示する。最終 selection 0件は policy に応じて `empty, allowed` または `empty, would error` と表示する。

不正 base path、base cycle、duplicate effective Scope root、使用した Scope root の不在、unknown Scope、不正 Target reference、direct-child boundary を外れる Target、未解決 Shared / Namespace reference、不正 source path、Case inconsistency、duplicate final archive root、Output schema / base-chain write-boundary conflict など Configuration と planning の error は preview でも error とする。未使用の named Scope root が現在存在しないことだけでは error にしない。Base depth 自体は error / warning にしない。'''

    @title('13. CLI contract')
    class TITLE_11:
        r'''CLI が受理する主な form は次とする。

```console
dirpluck TARGET [TARGET ...]
dirpluck --config PATH
dirpluck TARGET [TARGET ...] --case NAME
dirpluck --config PATH --case NAME
dirpluck -i PATH [-e NAME] [--case NAME]
dirpluck --invocation-template PATH [--entry NAME] [--case NAME]
dirpluck ... --preview
dirpluck ... --paths
dirpluck ... --sequence N
dirpluck ... --archive-mtime VALUE
dirpluck --version
```

Effective Configuration に Pluck がある場合、positional argument は `TARGET` reference として6節の規則で解決する。Pluck がない場合は positional `TARGET` を受理しない。

`--case`、`--sequence`、`--archive-mtime`、`-i` / `--invocation-template`、`-e` / `--entry` はそれぞれ最大1回だけ指定できる。`-e` / `--entry` は Invocation Template と一緒にだけ使用できる。Invocation Template を指定した場合は positional `TARGET` と `--config` を受理しない。`--case` は Invocation Template と併用でき、指定時は選択した Invocation の `case` を上書きする。`--archive-mtime VALUE` も Invocation Template と併用でき、指定時は選択した Invocation の `archive_mtime` を上書きする。`VALUE` は11節の Archive entry timestamp grammar に従う。`--sequence` は1以上の integer を受理し、`--preview` とは組み合わせない。`--preview`、`--sequence`、`--archive-mtime`、`--paths` も Invocation Template と併用できる。`--paths` は通常 build で生成する{{TERM_10}}の各 source section へ `Source` metadata を追加する。`--preview` と組み合わせても Archive は生成されないため、表示 tree に source filesystem path を追加しない。

Argument parse error と dirpluck の Configuration / build error は status 2 で終了する。Successful build と informational command は status 0 とする。通常 build の成功時は final output path を標準出力へ表示する。Field を1つも持たない Invocation を選択した成功実行では、通常 build は output path の後、`--preview` は tree の後に、保存済み実行入力がなく CLI runtime value と normal defaults を使うことを note として表示する。

Base chain 用の追加 CLI path や layer ごとの Case option は提供しない。Base chain は TOML の `about.base`、Case は composition 後の{{TERM_15}}へ適用する。'''
        vocabulary_refs @= (terms.TERM_10, terms.TERM_15)
