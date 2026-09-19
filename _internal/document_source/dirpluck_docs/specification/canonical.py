from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Specification")
class TITLE_0:
    r'''{{TERM_1}} の CLI と TOML {{TERM_2}}形式について、互換性対象となる厳密な動作意味論を定義する。用途は `../README.md`、用語の意味は `../GLOSSARY.md`、TOML の書き方は `CONFIGURATION.md`、CLI の操作方法は `CLI.md`、Configuration と filesystem 操作の信頼境界は `TRUST.md` を参照する。'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_2)

    @title('1. 公開面')
    class TITLE_1:
        r'''互換性を保証する公開面は `dirpluck` CLI と、この文書で定義する TOML Configuration 形式である。パッケージ内の Python module は、将来 Python API として明示されない限り内部実装として扱う。'''

    @title('2. Root Configuration discovery')
    class TITLE_2:
        r'''CLI から{{TERM_14}}を選ぶ discovery は再帰せず、process cwd を基準とした次の2箇所だけで行う。

- cwd 直下
- `./dirpluck/` 直下

`--config` を省略した場合の候補名は `dirpluck.toml` とする。`--config NAME` の `NAME` は任意 path ではなく filename として扱い、`.toml` は省略できる。

一致する候補が0件なら error とする。同じ候補名が両方の discovery location に存在する場合は ambiguous として拒否し、優先順位では解決しない。

`--configs` は検出可能な root 候補を列挙する。cwd 直下では dirpluck Configuration らしい top-level 構造を持つ TOML だけを列挙し、`./dirpluck/` 直下では TOML を候補として列挙する。両方に同名がある場合は `ambiguous` と表示する。

{{TERM_13}}では discovery を行わない。各 import は `configuration` に import root 内の相対 TOML path を明示し、その file を直接読み込む。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_14)

    @title('3. Configuration schema')
    class TITLE_3:
        r'''受理する top-level 構造は次とする。

```text
[about]
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[import.<name>.companion.<name>]
[target]
[target.location.<name>]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

未知の key は error とする。`[about]` は任意で、定義する場合は空でない `description` だけを持つ。各 Configuration は `[import.<name>]` を0個または1個、Target を0個または1個持てる。Target は名前付き{{TERM_16}}を0個以上持てる。Companion と shared pattern も名前付きで複数定義できる。各 Configuration は `[output]` を1個持つ。

`[target.location.<name>]` の `<name>` は CLI の path segment として使用できる空でない名前とし、`.`、`..`、`/`、backslash を含めない。Location は Target の一部であり、Case ごとの location は定義しない。

Root Configuration 自身に Target / Companion がなくても、import composition 後の{{TERM_15}}に Target または Companion が少なくとも1個残れば source 構成として有効である。'''
        vocabulary_refs @= (terms.TERM_15, terms.TERM_16)

    @title('4. Configuration filesystem path notation')
    class TITLE_350:
        r'''TOML で filesystem location を表す field は、host OS に関係なく `/` を path separator として使用する。Backslash は separator として受理しない。

Relative path は各 field が定める基準 directory から解決する。Absolute path は host OS が完全な absolute path として認識する root form を `/` separator で記述し、その場所を直接参照する。例として POSIX host の `/opt/data`、Windows host の `C:/data` と `//server/share/data` を受理できる。別 OS の root form へ自動変換しない。Windows drive-relative form (`C:foo`) は absolute path として扱わない。

Filesystem-location field では `~` expansion と environment-variable interpolation を行わず、glob を受理しない。`.` と `..` は field 固有の規則で許可または拒否する。Absolute path を使用した Configuration は参照先 filesystem に依存し、OS 間 portability を保証しない。

この notation は Target location の `path`、import `root`、通常 / import-root overlay Companion の `path`、Root output の `path` / `directory` に適用する。Imported `configuration`、include pattern、archive path、CLI の Target reference など relative notation として別途定義する値は、それぞれの規則に従う。'''

    @title('5. Configuration import と composition')
    class TITLE_4:
        r'''{{TERM_13}}は `[import.<name>]` として宣言する。`<name>` は link を診断で識別するための空でない名前であり、Companion や shared pattern の namespace prefix ではない。

各 import が受理する field は次とする。

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

`case` field は受理しない。'''
        vocabulary_refs @= (terms.TERM_13,)

        @title('`root`')
        class TITLE_401:
            r'''`root` は concrete directory path とし、空文字列と glob を拒否する。Relative `root` は、その import を記述した Configuration file の所在 directory を基準に解決し、`.` と `..` を使用できる。Absolute `root` は host filesystem 上の directory を直接参照する。解決後は実在 directory でなければならない。

解決した root は直下 imported Configuration の execution root となる。chain の次の import も、その import を記述した Configuration file 自身を relative `root` の基準として同じ規則で解決する。'''

        @title('`configuration`')
        class TITLE_402:
            r'''`configuration` は import root から見た `/` separator の相対 TOML file path とする。空文字列、backslash、absolute path、`.` / `..` component、import root 外への逸脱、glob、`.toml` 以外の extension を拒否する。解決先は import root 内の実在 regular file でなければならない。Root Configuration discovery は行わない。'''

        @title('Linear chain と cycle')
        class TITLE_403:
            r'''Imported Configuration も `[import.<name>]` を0個または1個持てる。Import depth に固定上限は設けない。

解決時は Configuration file の正規化済み実 path を現在の chain として保持する。同じ file が現在の chain に再登場した場合は cycle error とし、循環した chain を診断へ含める。Depth 自体による error / warning は行わない。'''

        @title('Definition resolution')
        class TITLE_404:
            r'''Chain の最深部を初期値とし、1 layer ずつ外側の definition を重ねて{{TERM_15}}を構成する。

`[about].description` は outermost layer から inner layer へ探索し、最初に定義された値を effective description とする。Chain 全体に定義がなければ effective description は存在しない。`about` table を whole-definition shadowing の対象とはせず、現時点ではこの optional value だけを独立に解決する。

- Target: outer layer に Target があれば inner Target 全体を shadow する。
- Companion: 同名 Companion は outer layer が全体を shadow し、異なる名前は保持する。
- shared include patterns: 同名 pattern は outer layer が配列全体を shadow する。
- shared exclude patterns: include とは独立した namespace で同じ規則を使う。

Target / Companion の shadow は部分 merge ではない。Target は `description`、base selection、全 Case selection、全 Target location を含む definition 全体を置き換える。Companion も `path`、`description`、base selection、全 Case selection を含む definition 全体を置き換える。

Selection の shared pattern reference は、source の origin layer ではなく chain 全体を重ね終えた effective namespace で解決する。Outer layer は inner source が参照する名前を提供または override できる。最終 composition 後も存在しない参照名は Configuration error とする。'''
            vocabulary_refs @= (terms.TERM_15,)

        @title('Import-root Companion overlay')
        class TITLE_405:
            r'''`[import.<name>.companion.<companion-name>]` は直下 import root を relative `path` の基準とする Companion definition である。通常 Companion と同じ selection schema と filesystem-location path notation を使い、relative `path` では `.` と `..`、absolute `path` では host filesystem 上の任意の concrete directory を指定できる。Glob は拒否する。

Overlay は Companion 名 `<companion-name>` として outer layer から definition resolution へ参加し、直下 imported Configuration の同名 Companion を shadow できる。同じ Configuration layer で `[companion.x]` と `[import.<name>.companion.x]` を両方定義することはできない。

各 Configuration の `[output]` は schema validation の対象だが composition しない。実行で使用するのは最外側の{{TERM_14}}の output だけとする。'''
            vocabulary_refs @= (terms.TERM_14,)

    @title('6. Runtime source と Case')
    class TITLE_5:
        r'''{{TERM_15}}に Target が存在する場合は、Target definition の origin layer にかかわらず CLI positional `TARGET` を1個以上必要とする。Positional `TARGET` は source directory の raw path そのものとは限らず、次の規則で1個以上の runtime Target directory へ解決する。

Target がない{{TERM_15}}では positional `TARGET` を受理しない。

Target selection の origin Configuration は definition composition と Target location の relative `path` 基準に影響するが、runtime Target directory を Configuration file の配置から自動推定しない。Inner Configuration の Target が effective Target として残っていても、CLI positional argument から Target を選ぶ。'''
        vocabulary_refs @= (terms.TERM_15,)

        @title('Target location')
        class TITLE_501:
            r'''`[target.location.<name>]` は `path` だけを持つ。`path` は concrete directory path とし、empty string と glob を拒否する。Relative `path` は effective Target definition を所有する Configuration layer の execution root を基準に解決し、`.` と `..` を使用できる。Absolute `path` は host filesystem 上の directory を直接参照する。解決先は実在 directory でなければならない。

Target location は Target definition の一部であり、outer Target が inner Target を shadow した場合は location 集合も全体として置き換わる。Case selection は location 集合を変更しない。'''

        @title('CLI Target reference resolution')
        class TITLE_502:
            r'''各 positional `TARGET` argument は独立して次の順序で解決する。

1. Argument が `./` で始まる場合、location lookup を行わず process cwd を基準とした明示的な cwd-relative Target reference とする。
2. Argument が `<name>/` という「1個の non-dot segment と末尾 `/` だけ」の形なら、named-location expansion とする。`<name>` と一致する effective Target location がなければ error とし、cwd へ fallback しない。
3. それ以外で先頭 segment が effective Target location 名と一致し、後続 relative path がある場合、その location directory を基準に後続 path を解決する。
4. それ以外は argument 全体を process cwd を基準とする relative Target reference として解決する。

Absolute positional Target reference は受理しない。cwd 外の Target を選ぶ場合は Target location を定義する。

cwd-relative Target は解決後も process cwd 内、location-relative Target は解決後もその location directory 内に存在しなければならない。`..` や symbolic link によって各 resolution base の外へ出る Target reference は拒否する。解決先は実在 directory でなければならない。

Location prefix は locating namespace であり Target 名ではない。`work/project` の `work` が location 名でも、runtime Target は解決された `project` directory である。'''

        @title('Named-location expansion')
        class TITLE_503:
            r'''`<name>/` は、対応する Target location directory の直下にある directory entry を列挙し、それぞれを独立した runtime Target directory として展開する。再帰的な directory 列挙は行わず、regular file は Target にしない。

Directory symbolic link は解決先が同じ Target location directory 内にある場合だけ Target 候補として扱い、外部へ解決する link は error とする。展開結果が0 directory の場合は error とする。

複数 positional `TARGET` と location expansion は同じ run で併用でき、最終的に得られた各 runtime Target directoryへ同じ effective Target selection を独立して適用する。'''

        @title('Companion と Case')
        class TITLE_504:
            r'''通常 Companion の relative `path` は definition を所有する Configuration layer の execution root を基準とする。Import-root overlay Companion の relative `path` は直下 import root を基準とする。どちらも `.` と `..` を使用でき、absolute `path` は基準 root に依存せず host filesystem 上の directory を直接参照する。解決先は実在 directory でなければならず、filesystem root 自体は Companion source として拒否する。Shadow されず inner layer から残った Companion は inner layer の path 基準を保持し、outer definition に置き換わった Companion は outer definition に対応する基準を使用する。

{{TERM_4}}は{{TERM_15}}全体で0個または1個だけ有効にし、CLI `--case` から選択する。Layer ごとに別 Case を指定する field はない。

Case 未指定時は Target があれば `[target]`、各 Companion は base `[companion.<name>]` を使う。

Case 指定時に Target がある場合、同名 `[target.case.<name>]` を必須とする。各 Companion は同名 Case があれば使い、なければ base へ fallback する。Target がない場合は、少なくとも1個の Companion が同名 Case を定義しなければならない。

Case selection は base の差分ではなく完全な selection とし、include / exclude / shared pattern refs を継承しない。'''
            vocabulary_refs @= (terms.TERM_4, terms.TERM_15)

    @title('7. Selection と shared pattern')
    class TITLE_6:
        r'''各 Target / Companion の base または Case selection は、空でない `description` と、直接記述または shared pattern reference による `include` / `include_if_exists` 相当候補の少なくとも一方を必要とする。

`include_pattern_refs` と `include_if_exists_pattern_refs` は effective include shared namespace、`exclude_pattern_refs` は effective exclude shared namespace の名前を参照する。Import 名を prefix した修飾参照は使用しない。

Shared refs は参照配列の順に展開し、その後に同種の direct pattern を追加する。展開後の必須 include 内、optional include 内、exclude 内の重複、および必須 / optional include 間の重複は Configuration error とする。

`if_empty` の既定値は `"error"` とする。`if_empty = "allow"` は展開後に必須 include pattern を持たない optional-only selection だけで指定できる。'''

        @title('Include pattern grammar')
        class TITLE_601:
            r'''Include pattern は source directory からの `/` separator の相対 path とする。Absolute path、`.` / `..` による逸脱、backslash を拒否する。

各 path element には `*` を最大1個だけ含められる。`*` はひとつの実体名内部で0文字以上に一致し、path separator を越えない。そのため Configuration に書いた path hierarchy の深さは固定される。

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

最後に一致した実体が file ならその file を選択し、directory なら exclude と symbolic-link 規則に従って配下の file を再帰収集する。内容や filename の意味に基づく暗黙 exclude は行わない。Trust boundary の説明は `TRUST.md` に置く。

複数一致した場合はすべて選択する。Matching は OS に依存せず case-sensitive とする。`**`、`?`、character class (`[]`)、`!` はサポートしない。複数一致を version、mtime、その他 metadata で順位付けしない。'''

        @title('Exclude pattern grammar')
        class TITLE_602:
            r'''Exclude は relative path ではなく、ひとつの実体名を照合する。末尾 `/` の pattern は directory name、`/` のない pattern は file name に適用する。

対応形式は次とする。

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

`*` 単体、`*/`、`foo*bar` のような内部 wildcard、`**`、`?`、character class、`!`、backslash、path separator を拒否する。'''

    @title('8. Filesystem boundary と symbolic link')
    class TITLE_7:
        r'''{{TERM_14}}の execution root は process cwd とする。各 import layer の execution root は、その layer を読み込んだ `[import.<name>].root` の解決結果とする。Execution root は relative Configuration path の resolution base であり、すべての source をその配下へ閉じ込める共通 boundary ではない。

Target location を使わない runtime Target directory は process cwd 内で解決し、その Target directory 自体を selection boundary とする。Target location を使う runtime Target directory はその location directory 内で解決し、解決後の Target directory 自体を selection boundary とする。Location は Target を探す boundary であり、selected file の boundary は常に最終 Target directory である。

Imported `configuration` は import root 内へ限定する。Companion は relative / absolute `path` から任意の実在 directory を解決でき、解決した Companion source directory 自体を selection boundary とする。Output location は source boundary に参加しない。

各 source の include resolution と selected file は、その source directory 内へ限定する。Symbolic link による source boundary 外への file / directory の逸脱は拒否する。Directory recursion では directory symlink をたどらず、外部へ解決する link は error、内部へ解決する link は循環と重複防止のため無視する。'''
        vocabulary_refs @= (terms.TERM_14,)

    @title('9. Archive planning')
    class TITLE_8:
        r'''cwd-relative Target の selected file は、Target definition の origin layer にかかわらず process cwd から見た filesystem relative path を ZIP 内で保持する。Target location から解決した Target の selected file は、location directory から見た filesystem relative path を ZIP 内で保持する。Logical location 名そのものは archive path へ含めない。たとえば `work/team/project` が location `work` から解決された場合、archive path は `team/project/...` であり `work/team/project/...` ではない。`work/` expansion で得た direct child も同じ規則を使う。

Companion source directory がその Companion の relative-path resolution base 内にある場合、selected file は従来どおりその base から見た relative path を ZIP 内で保持する。Absolute path または `..` により source directory がその base 外にある場合は、解決済み source directory の最終 directory name を archive root とし、その下へ source directory からの relative path を配置する。Filesystem root 自体を Companion source として受理しないのは、この portable archive root を持たないためである。Host の absolute path、drive、UNC share 名そのものは archive path へ埋め込まない。

同じ archive path に同じ physical file が重なる場合は1回だけ書き込む。異なる physical file が同じ archive path へ衝突する場合、または同じ physical file が異なる source mapping から異なる archive path へ解決される場合は ambiguity error とする。

Archive root には{{TERM_10}}を `README.md` として生成する。これは archive contents の索引であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は `# Archive contents` の直後、索引 table の前にその本文を表示する。存在しない場合はこの全体説明を省略する。

既定の表は `Path`、`Description`、`Files` の3列とし、各 resolved source について archive root、選択された selection の `description`、その source が選択した file 数を1行記録する。同じ archive root を複数 source が共有する場合も、各 description を別行として保持する。

既定では source filesystem path、Configuration path / table、Configuration chain、execution root、Target / Companion 名、選択 Case などの dirpluck 固有情報を記録しない。CLI `--paths` が指定された場合だけ `Source` 列を追加し、各 source の解決済み source directory を `/` separator の filesystem path として記録する。`--paths` は archive path や file selection を変更しない。'''
        vocabulary_refs @= (terms.TERM_10,)

    @title('10. Output')
    class TITLE_9:
        r'''各 Configuration の `[output]` は fixed output または generated output のどちらか一方だけを定義する。実行時に filesystem path の解決、collision check、directory 作成、書き込みを行うのは{{TERM_14}}の output だけとする。'''
        vocabulary_refs @= (terms.TERM_14,)

        @title('Fixed output')
        class TITLE_901:
            r'''```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

`path` と `if_exists` の両方を必須とする。Root Configuration の `path` は concrete file path とし、relative path は cwd を基準に解決し、absolute path は host filesystem 上の destination を直接指定する。Relative path では `..` を使用できる。`.`、glob、directory として解決される destination は拒否する。必要な parent directory は作成する。Output location に cwd boundary は設けない。

`if_exists` は次だけを受理する。

- `error`: existing output を変更せず失敗する。
- `overwrite`: output directory の temporary file へ新しい ZIP を完成させた後で existing output を置換する。

`error` では build 前と最終配置直前に output destination が存在しないことを確認する。ZIP は同一 output directory の temporary file へ完成させてから最終 path へ配置する。'''

        @title('Generated output')
        class TITLE_902:
            r'''```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

`directory` と `timestamp = true` を必須とし、`prefix` と `suffix` は任意とする。`path` と `if_exists` は指定できない。

Root Configuration の `directory` は concrete directory path とし、relative path は cwd を基準に解決し、absolute path は host filesystem 上の directory を直接指定する。Relative path では `.` と `..` を使用できる。Glob は拒否する。必要な directory は作成する。Output location に cwd boundary は設けない。

`prefix` と `suffix` は空でない1個の portable filename fragment とし、`.`、`..`、path separator、control character、`< > : " | ? *` を拒否する。

Generated filename は次の固定形式とする。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

Timestamp は process local time を使い、build 開始時に一度だけ確定する。自由な timestamp format、variable expansion、naming template は提供しない。

`N` は CLI `--sequence N` から受け取る1以上の integer とする。省略時は number segment を出力しない。既存 output を探索して番号を推測せず、自動採番・自動 rename を行わない。`--sequence` は generated output だけで使用でき、複数回指定できない。

Generated filename が確認時点で既に存在する場合は error とし、overwrite option は提供しない。'''

        @title('Concurrent write と input collision')
        class TITLE_903:
            r'''dirpluck は process 間 lock や競合調停を提供しない。同じ output path への concurrent write はサポート対象外とする。並行する可能性がある呼び出し側は異なる output path を選ぶ必要がある。

どちらの output 形式でも、最終 output file 自身を archive input として選択することはできない。'''

    @title('11. Dry run')
    class TITLE_10:
        r'''`--dry-run` は通常実行と同じ import chain resolution、cycle detection、definition composition、Target location lookup / expansion、Target directory resolution、Case selection、file selection、archive planning を使うが、output を作成・変更しない。

不足する必須 `include` は `[missing]`、不足する optional pattern は `[optional missing]` と表示する。最終選択0件は policy に応じて `empty, allowed` または `empty, would error` と表示する。

Multiple import、import cycle、不正 root / configuration path、不正な host absolute path、unknown location expansion、location boundary を外れる Target reference、未解決 shared pattern ref、不正 source path、Case inconsistency などは dry-run でも error とする。Import depth 自体は error / warning にしない。'''

    @title('12. CLI contract')
    class TITLE_11:
        r'''CLI が受理する主な form は次とする。

```console
dirpluck TARGET [TARGET ...]
dirpluck --config NAME
dirpluck TARGET [TARGET ...] --case NAME
dirpluck --config NAME --case NAME
dirpluck ... --dry-run
dirpluck ... --paths
dirpluck ... --sequence N
dirpluck --configs
dirpluck --version
```

Effective Configuration に Target がある場合、positional argument は `TARGET` reference として6節の規則で解決する。Target がない場合は positional `TARGET` を受理しない。

`--case` と `--sequence` はそれぞれ最大1回だけ指定できる。`--sequence` は1以上の integer を受理する。`--paths` は通常 build で生成する{{TERM_10}}へ Source column を追加する。`--dry-run` と組み合わせても archive は生成されないため、表示 tree には影響しない。`--configs` は `TARGET`、`--case`、`--sequence`、`--config`、`--dry-run`、`--paths` と組み合わせない。

Argument parse error と dirpluck の Configuration / build error は status 2 で終了する。Successful build と informational command は status 0 とする。通常 build の成功時は final output path を標準出力へ表示する。

Import chain 用の追加 CLI path や layer ごとの Case option は提供しない。Import は TOML の `[import.<name>]`、Case は composition 後の{{TERM_15}}へ適用する。'''
        vocabulary_refs @= (terms.TERM_10, terms.TERM_15,)
