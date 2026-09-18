from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Specification")
class TITLE_0:
    r'''{{TERM_1}} の CLI と TOML {{TERM_2}}形式について、互換性対象となる厳密な動作意味論を定義する。用途は `../README.md`、用語の意味は `../GLOSSARY.md`、TOML の書き方は `CONFIGURATION.md`、CLI の操作方法は `CLI.md` を参照する。'''
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
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[import.<name>.companion.<name>]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

未知の key は error とする。各 Configuration は `[import.<name>]` を0個または1個、Target を0個または1個持てる。Companion と shared pattern は名前付きで複数定義できる。各 Configuration は `[output]` を1個持つ。

Root Configuration 自身に Target / Companion がなくても、import composition 後の{{TERM_15}}に Target または Companion が少なくとも1個残れば source 構成として有効である。'''
        vocabulary_refs @= (terms.TERM_15,)

    @title('4. Configuration import と composition')
    class TITLE_4:
        r'''{{TERM_13}}は `[import.<name>]` として宣言する。`<name>` は link を診断や{{TERM_10}}で識別するための空でない名前であり、Companion や shared pattern の namespace prefix ではない。

各 import が受理する field は次とする。

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

`case` field は受理しない。'''
        vocabulary_refs @= (terms.TERM_10, terms.TERM_13)

        @title('`root`')
        class TITLE_401:
            r'''`root` は、その import を記述した Configuration file の所在 directory から見た相対 directory path とする。空文字列、absolute path、glob を拒否する。`.` と `..` は使用でき、path separator は `/` を正規形とする。POSIX absolute path、Windows drive path、UNC path は実行 OS に関係なく拒否する。解決後は実在 directory でなければならない。

解決した root は直下 imported Configuration の execution root / filesystem boundary となる。chain の次の import も、その import を記述した Configuration file 自身を基準に同じ規則で解決する。'''

        @title('`configuration`')
        class TITLE_402:
            r'''`configuration` は import root から見た相対 TOML file path とする。空文字列、absolute path、import root 外へ出る `..`、glob、`.toml` 以外の extension を拒否する。解決先は import root 内の実在 regular file でなければならない。Root Configuration discovery は行わない。'''

        @title('Linear chain と cycle')
        class TITLE_403:
            r'''Imported Configuration も `[import.<name>]` を0個または1個持てる。Import depth に固定上限は設けない。

解決時は Configuration file の正規化済み実 path を現在の chain として保持する。同じ file が現在の chain に再登場した場合は cycle error とし、循環した chain を診断へ含める。Depth 自体による error / warning は行わない。'''

        @title('Definition resolution')
        class TITLE_404:
            r'''Chain の最深部を初期値とし、1 layer ずつ外側の definition を重ねて{{TERM_15}}を構成する。

- Target: outer layer に Target があれば inner Target 全体を shadow する。
- Companion: 同名 Companion は outer layer が全体を shadow し、異なる名前は保持する。
- shared include patterns: 同名 pattern は outer layer が配列全体を shadow する。
- shared exclude patterns: include とは独立した namespace で同じ規則を使う。

Target / Companion の shadow は部分 merge ではない。`path`、`description`、base selection、全 Case selection を含む source definition 全体を置き換える。

Selection の shared pattern reference は、source の origin layer ではなく chain 全体を重ね終えた effective namespace で解決する。Outer layer は inner source が参照する名前を提供または override できる。最終 composition 後も存在しない参照名は Configuration error とする。'''
            vocabulary_refs @= (terms.TERM_15,)

        @title('Import-root Companion overlay')
        class TITLE_405:
            r'''`[import.<name>.companion.<companion-name>]` は直下 import root を path 基準とする Companion definition である。通常 Companion と同じ selection schema を使い、`path = "."` を許可する。その他の absolute path、`..`、glob は拒否する。

Overlay は Companion 名 `<companion-name>` として outer layer から definition resolution へ参加し、直下 imported Configuration の同名 Companion を shadow できる。同じ Configuration layer で `[companion.x]` と `[import.<name>.companion.x]` を両方定義することはできない。

各 Configuration の `[output]` は schema validation の対象だが composition しない。実行で使用するのは最外側の{{TERM_14}}の output だけとする。'''
            vocabulary_refs @= (terms.TERM_14,)

    @title('5. Runtime source と Case')
    class TITLE_5:
        r'''{{TERM_15}}に Target が存在する場合、その Target definition の origin layer にかかわらず CLI `DIRECTORY` を1個以上必要とし、同じ Target selection を各 directory へ独立して適用する。各 `DIRECTORY` は{{TERM_14}}の execution root、すなわち process cwd 内で解決する。

Target selection の origin Configuration は definition composition にだけ影響し、runtime Target directory の自動推定には使用しない。Inner Configuration の Target が effective Target として残っていても、その Configuration file の配置から project directory を推定しない。

Target がない{{TERM_15}}では positional `DIRECTORY` を受理しない。

通常 Companion の `path` は definition を所有する Configuration layer の execution root 相対とする。Import-root overlay Companion は直下 import root 相対とする。Shadow されず inner layer から残った Companion は inner execution root を保持し、outer definition に置き換わった Companion は outer definition に対応する root を使用する。

{{TERM_4}}は{{TERM_15}}全体で0個または1個だけ有効にし、CLI `--case` から選択する。Layer ごとに別 Case を指定する field はない。

Case 未指定時は Target があれば `[target]`、各 Companion は base `[companion.<name>]` を使う。

Case 指定時に Target がある場合、同名 `[target.case.<name>]` を必須とする。各 Companion は同名 Case があれば使い、なければ base へ fallback する。Target がない場合は、少なくとも1個の Companion が同名 Case を定義しなければならない。

Case selection は base の差分ではなく完全な selection とし、include / exclude / shared pattern refs を継承しない。'''
        vocabulary_refs @= (terms.TERM_4, terms.TERM_14, terms.TERM_15)

    @title('6. Selection と shared pattern')
    class TITLE_6:
        r'''各 Target / Companion の base または Case selection は、空でない `description` と、直接記述または shared pattern reference による `include` / `include_if_exists` 相当候補の少なくとも一方を必要とする。

`include_pattern_refs` と `include_if_exists_pattern_refs` は effective include shared namespace、`exclude_pattern_refs` は effective exclude shared namespace の名前を参照する。Import 名を prefix した修飾参照は使用しない。

Shared refs は参照配列の順に展開し、その後に同種の direct pattern を追加する。展開後の必須 include 内、optional include 内、exclude 内の重複、および必須 / optional include 間の重複は Configuration error とする。

`if_empty` の既定値は `"error"` とする。`if_empty = "allow"` は展開後に必須 include pattern を持たない optional-only selection だけで指定できる。'''

        @title('Include pattern grammar')
        class TITLE_601:
            r'''Include pattern は source directory からの POSIX 形式の相対 path とする。Absolute path、pattern 全体としての `.`, `..` による逸脱を拒否し、validation 前に backslash は `/` へ正規化する。

各 path element には `*` を最大1個だけ含められる。`*` はひとつの実体名内部で0文字以上に一致し、path separator を越えない。そのため Configuration に書いた path hierarchy の深さは固定される。

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

最後に一致した実体が file ならその file を選択し、directory なら exclude と symbolic-link 規則に従って配下の file を再帰収集する。Hidden file、repository metadata、environment file、secret key などに対する暗黙 exclude は行わない。

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

    @title('7. Filesystem boundary と symbolic link')
    class TITLE_7:
        r'''{{TERM_14}}の execution root / filesystem boundary は process cwd とする。各 import layer の execution root は、その layer を読み込んだ `[import.<name>].root` の解決結果とする。

Import root を解決できる唯一の越境 path とする。Root 確定後は imported `configuration`、その layer の通常 Companion、Companion の selected file を対応する execution root 内へ限定する。Target directory は常に Root Configuration の execution root 内で CLI から解決する。

Symbolic link を利用した boundary 外への source path / selected file の逸脱は拒否する。Directory recursion では directory symlink をたどらず、外部へ解決する link は error、内部へ解決する link は循環と重複防止のため無視する。'''
        vocabulary_refs @= (terms.TERM_14,)

    @title('8. Archive planning')
    class TITLE_8:
        r'''Target の selected file は、Target definition の origin layer にかかわらず Root Configuration の execution root から見た filesystem relative path を ZIP 内で保持する。Companion の selected file は、その effective Companion definition に対応する execution root から見た relative path を保持する。

同じ archive path に同じ physical file が重なる場合は1回だけ書き込む。異なる physical file が同じ archive path へ衝突する場合、または同じ physical file が異なる execution root から異なる archive path へ解決される場合は ambiguity error とする。

Archive root には{{TERM_10}}を `README.md` として生成する。Configuration chain、各 execution root、effective definition、選択 Case、参加 source、description、selection count など、解決済み plan の事実を記録する。'''
        vocabulary_refs @= (terms.TERM_10,)

    @title('9. Output')
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

`path` と `if_exists` の両方を必須とする。Root Configuration の `path` は cwd より下にある具体的な cwd 相対 path とし、absolute path、`..`、glob を拒否する。必要な parent directory は作成する。Symbolic link によって cwd 外へ解決される output destination は拒否する。

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

Root Configuration の `directory` は cwd 内の具体的な cwd 相対 directory とし、`.` は cwd 自体として使用できる。Absolute path、`..`、glob を拒否する。必要な directory は作成し、symbolic link による cwd 外への逸脱を拒否する。

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

    @title('10. Dry run')
    class TITLE_10:
        r'''`--dry-run` は通常実行と同じ import chain resolution、cycle detection、definition composition、Target directory resolution、Case selection、file selection、archive planning を使うが、output を作成・変更しない。

不足する必須 `include` は `[missing]`、不足する optional pattern は `[optional missing]` と表示する。最終選択0件は policy に応じて `empty, allowed` または `empty, would error` と表示する。

Multiple import、import cycle、不正 root / configuration path、未解決 shared pattern ref、不正 source path、Case inconsistency などは dry-run でも error とする。Import depth 自体は error / warning にしない。'''

    @title('11. CLI contract')
    class TITLE_11:
        r'''CLI が受理する主な form は次とする。

```console
dirpluck DIRECTORY [DIRECTORY ...]
dirpluck --config NAME
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
dirpluck --config NAME --case NAME
dirpluck ... --dry-run
dirpluck ... --sequence N
dirpluck --configs
dirpluck --version
```

`--case` と `--sequence` はそれぞれ最大1回だけ指定できる。`--sequence` は1以上の integer を受理する。`--configs` は `DIRECTORY`、`--case`、`--sequence`、`--config`、`--dry-run` と組み合わせない。

Argument parse error と dirpluck の Configuration / build error は status 2 で終了する。Successful build と informational command は status 0 とする。通常 build の成功時は final output path を標準出力へ表示する。

Import chain 用の追加 CLI path や layer ごとの Case option は提供しない。Import は TOML の `[import.<name>]`、Case は composition 後の{{TERM_15}}へ適用する。'''
        vocabulary_refs @= (terms.TERM_15,)
