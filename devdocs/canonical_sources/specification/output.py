from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.composition import SPECIFICATION_PART as COMPOSITION_SPEC
from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from shikumi_devdoc.fields.specification import INFORMATIVE, MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary('fixed/timestamp/runtime Output、write boundary、collision 規則。')


@canonical_source('Output', filename='output.md', order=100, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_107:
        r"""Configuration は Output を省略できる。Output を持たない Configuration も Root として Archive planning / `--preview` に使用できる。Archive file を書き込む build では、{{TERM_14}}自身が宣言した fixed / timestamp Output、または runtime Output のどちらかを effective Output とする。Runtime Output がない場合だけ root 自身の Output declaration を必要とし、Base の Output は root の Output として継承しない。"""
        merge @= TERMS.TERM_14
        level @= MUST

    class SPEC_108:
        r"""Base chain では、実際に Output を宣言している definition だけが{{TERM_17}}の overlap validation に参加する。Output path の relative resolution は常にその Output を記述した Configuration file の directory を基準とする。"""
        merge @= TERMS.TERM_17
        level @= MUST
        related @= (COMPOSITION_SPEC.SECTION_403.SPEC_036, PATHS_SPEC.SPEC_018)

    class SECTION_901:
        title @= 'Fixed output'

        class SPEC_109:
            r"""
            ```toml
            [output]
            path = "artifacts/context.zip"
            overwrite = false
            ```
            """
            level @= INFORMATIVE

        class SPEC_110:
            r"""`path` を必須とし、`overwrite` は optional boolean、既定 `false` とする。`timestamp` subtable、`prefix`、`suffix` は fixed mode では指定できない。"""
            level @= MUST

        class SPEC_111:
            r"""`path` は concrete file path とする。末尾 `/` の directory notation、glob、directory として解決される destination を拒否する。Relative path では `.` と `..` を通常どおり解決できる。必要な parent directory は作成する。Output location に Configuration directory boundary は設けない。"""
            level @= MUST

        class SPEC_112:
            r"""`overwrite = false` では build 前と最終配置直前に destination が存在しないことを確認する。いずれかの確認時点で existing destination を認識した場合は、その existing output を変更せず失敗する。ただし、この存在確認と最終配置は concurrent writer に対する atomic な no-clobber operation ではない。最終確認後から配置までの間に別 process が同じ destination を作成または置換した場合、その file を dirpluck が置換し得る。"""
            level @= MUST
            condition @= "effective overwrite policy が false の場合"

        class SPEC_113:
            r"""`overwrite = true` では output directory の temporary file へ新しい ZIP を完成させた後で existing output を置換する。既存 destination の file mode は継承しない。"""
            level @= MUST
            condition @= "effective overwrite policy が true の場合"

        class SPEC_114:
            r"""生成する Archive file は host OS の通常の新規 file creation semantics に従う。POSIX では通常の regular file creation mode `0666` に process `umask` を適用した mode で temporary output を作成し、その mode のまま final destination へ置換する。したがって new output と overwrite のどちらも、その run の `umask` に基づく新規 file mode になる。"""
            level @= MUST

        class SPEC_115:
            r"""Filename extension は ZIP format の判定に使用しない。Fixed output では Configuration に書かれた filename を runtime に変更・展開しない。"""
            level @= MUST_NOT

    class SECTION_902:
        title @= 'Timestamp output'

        class SPEC_116:
            r"""
            ```toml
            [output.timestamp]
            path = "artifacts/snapshots/"
            prefix = "project"
            suffix = "review"
            ```
            """
            level @= INFORMATIVE

        class SPEC_117:
            r"""`path` を必須とし、`prefix` と `suffix` は任意とする。`overwrite` は指定できない。"""
            level @= MUST

        class SPEC_118:
            r"""`path` は concrete directory path とし、Configuration notation 上で末尾 `/` を必須とする。Glob は拒否する。Relative path では `.` と `..` を通常どおり解決できる。必要な directory は作成する。Output location に Configuration directory boundary は設けない。"""
            level @= MUST

        class SPEC_119:
            r"""`prefix` と `suffix` は空でない1個の portable filename fragment とし、`.`、`..`、path separator、control character、`< > : " | ? *` を拒否する。"""
            level @= MUST

        class SPEC_120:
            r"""
            Generated filename は次の固定形式とする。

            ```text
            [prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
            ```
            """
            level @= MUST

        class SPEC_121:
            r"""Timestamp は process local time を使い、build 開始時に一度だけ確定する。自由な timestamp format、variable expansion、naming template は提供しない。"""
            level @= MUST

        class SPEC_122:
            r"""`N` は CLI `--sequence N` または Python API `sequence=` から受け取る1以上の integer とする。省略時は number segment を出力しない。Existing output を探索して番号を推測せず、自動採番・自動 rename を行わない。`sequence` は automatic timestamp filename を生成する effective Output だけで使用できる。"""
            level @= MUST

        class SPEC_123:
            r"""Generated filename が確認時点で既に存在する場合は既定では error とする。Configuration schema に overwrite field は持たないが、runtime `--force` / `force=True` が指定された場合は effective overwrite policy を true として既存 destination を置換できる。Generated Archive file の permission / mode は fixed output と同じく host OS の通常の新規 file creation semantics に従う。"""
            level @= MUST
            condition @= "generated filename が既に存在する場合"

    class SECTION_9022:
        title @= 'Runtime output'

        class SPEC_124:
            r"""CLI `--here[=FILENAME]`、`-o PATH` / `--output PATH`、Python API `output=` は build 時の runtime Output を指定する。Runtime Output が存在する場合、Configuration の fixed output path / timestamp output directory は effective destination として使用しない。Root Configuration に Output declaration がなくても build できる。"""
            level @= MUST
            condition @= "runtime Output が存在する場合"

        class SPEC_125:
            r"""CLI `--here` は runtime cwd を output directory とする automatic output である。`--here=FILENAME` は runtime cwd 直下の exact output filename とし、`FILENAME` に `/` または `\` を含む path form、`.`、`..`、portable filename fragment として不正な character を受理しない。Optional filename は `--here=FILENAME` の `=` form でだけ指定し、`--here` と `--output` は同時に指定できない。`-h` は `--help` に予約し、`--here` の short option は持たない。"""
            level @= MUST

        class SPEC_126:
            r"""CLI `--output PATH` / `-o PATH` と Python API `output=PATH` は filesystem-location notation と同じく OS にかかわらず `/` separator を使用し、backslash / glob を受理しない。Relative `PATH` は runtime cwd、absolute `PATH` は host filesystem を基準とする。末尾 `/` がある `PATH` は output directory、末尾 `/` がない `PATH` は exact output file path とする。Filesystem の既存状態から file / directory form を推測しない。Exact form の final component が `.`, `..`、または file name を持たない形なら error とする。必要な parent / output directory は通常 build で作成する。"""
            level @= MUST
            related @= (PATHS_SPEC.SPEC_017, PATHS_SPEC.SPEC_022)

        class SPEC_127:
            r"""
            Automatic runtime output (`--here`、末尾 `/` の `--output` / `output=`) は process local time を1回取得し、timestamp filename を生成する。Root Configuration が `[output.timestamp]` を宣言している場合、その `prefix` / `suffix` を naming rule として再利用するが、その configured `path` は使用しない。Root に timestamp Output がない場合は `dirpluck` を固定 prefix とし、filename は次の形とする。

            ```text
            dirpluck-YYYYMMDD-HHMMSS[-N].zip
            ```
            """
            level @= MUST
            condition @= "automatic runtime output を使用する場合"

        class SPEC_128:
            r"""Root に timestamp Output がある場合は従来の `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` 形式を runtime directory 上で使用する。Exact runtime output は Configuration の `prefix` / `suffix` を使用せず、指定された filename を変更しない。"""
            level @= MUST
            condition @= "root に timestamp Output がある場合"

        class SPEC_129:
            r"""`--sequence N` / `sequence=` は automatic runtime output にも使用できる。Exact runtime output と組み合わせた場合は error とする。Generated destination が既に存在しても自動採番、自動 rename、timestamp 再取得を行わない。"""
            level @= MUST

        class SPEC_130:
            r"""Runtime Output の overwrite policy は既定で false とし、Configuration の fixed `overwrite` value は引き継がない。CLI `-f` / `--force` または Python API `force=True` は runtime Output と Configuration Output のどちらでも effective overwrite policy を true にする。`--force` / `force=True` がない Configuration fixed output だけは `[output].overwrite` を使用する。"""
            level @= MUST
            condition @= "runtime Output の overwrite policy を決定する場合"

    class SECTION_9025:
        title @= 'Archive entry timestamp'

        class SPEC_131:
            r"""`--archive-mtime VALUE` は Output path / filename ではなく、生成する ZIP entry metadata の timestamp policy とする。Configuration schema には対応 field を持たず、CLI / Python API の runtime option または Invocation Template の `archive_mtime` field から指定する。"""
            level @= MUST

        class SPEC_132:
            r"""`VALUE` は `now`、`zip-epoch`、または厳密な `YYYY-MM-DDTHH:MM:SS` string とする。明示 timestamp は timezone suffix / offset を持たない literal として解釈し、timezone conversion を行わない。ZIP/DOS timestamp が表現できる範囲として 1980-01-01T00:00:00 以上 2107-12-31T23:59:59 以下を受理する。`zip-epoch` は 1980-01-01T00:00:00 と等価とする。`now` は1回の high-level run で process local current time を1度だけ取得し、その1値を使用する。"""
            level @= MUST

        class SPEC_133:
            r"""ZIP timestamp は2秒粒度なので、resolved timestamp の秒が奇数なら直前の偶数秒へ切り下げる。Microsecond は保持しない。Resolved timestamp は generated root `README.md`、empty directory entry、selected source file を含む、その run で書き込むすべての ZIP entry へ同一に設定する。"""
            level @= MUST

        class SPEC_134:
            r"""`--archive-mtime` / Invocation `archive_mtime` を省略した場合は既存 semantics を維持し、selected source file は filesystem mtime を使用し、Dirpluck が `writestr` 相当で生成する entry は生成時刻を使用する。"""
            level @= MUST
            condition @= "`--archive-mtime` / Invocation `archive_mtime` を省略した場合"

        class SPEC_135:
            r"""この option は entry timestamp を固定し、timestamp に起因する byte 差を取り除くための機構である。Source file の permission bits は ZIP `external_attr` に保持されるため、file content と timestamp が同じでも permission が異なれば Archive byte 列は異なり得る。Dirpluck は permission bits を正規化しない。Compressor implementation、runtime version、platform 由来の ZIP metadata / serialization detail も含め、Archive 全体の byte-for-byte reproducibility は保証しない。また timestamp output の filename に使う process-local `YYYYMMDD-HHMMSS` とは独立し、その filename timestamp を変更しない。`--preview` では Archive を書かないため archive mtime は出力結果へ影響しない。"""
            level @= MUST

    class SECTION_903:
        title @= 'Static writable destination'

        class SPEC_136:
            r"""
            Configuration が宣言する Output naming は、Configuration だけから{{TERM_17}}を静的に確定できることを不変条件とする。Runtime Output は invocation ごとに与えるため、この static write-boundary model には参加しない。

            ```text
            fixed [output]
                -> resolved complete file path 1個

            timestamp [output.timestamp]
                -> resolved output directory を root とする directory tree
            ```
            """
            merge @= TERMS.TERM_17
            level @= MUST

        class SPEC_137:
            r"""Fixed output では user が filename 全体を決定し、dirpluck は runtime にその一部を補完しない。Timestamp output では user が output directory を決定し、dirpluck がその directory 直下の filename だけを決定する。`artifacts/{target}-{timestamp}.zip` のように Configuration から書き込み先 directory を静的に確定できない template mode は提供しない。"""
            level @= MUST_NOT

    class SECTION_904:
        title @= 'Base chain write-boundary overlap'

        class SPEC_138:
            r"""Base chain 上の各 Configuration が宣言する resolved{{TERM_17}}は、chain 内の別 Output と overlap してはならない。比較は Configuration に書かれた文字列ではなく、各 Configuration file を anchor として resolve / normalize した path で行う。"""
            merge @= TERMS.TERM_17
            level @= MUST
            related @= (COMPOSITION_SPEC.SECTION_403.SPEC_036,)

        class SPEC_139:
            r"""
            Fixed output 同士は、完全 file path が同一の場合だけ conflict とする。同じ directory に別 filename の fixed output を置くことはできる。

            ```text
            out/base.zip
            out/derived.zip
            ```
            """
            level @= MUST

        class SPEC_140:
            r"""
            Timestamp output 同士は、directory boundary が同一、祖先、子孫のいずれかなら conflict とする。

            ```text
            artifacts/
            artifacts/release/
            ```
            """
            level @= MUST

        class SPEC_141:
            r"""
            Fixed output と timestamp output では、fixed output の完全 file path が timestamp output の directory boundary 内に入る場合を conflict とする。

            ```text
            artifacts/            timestamp boundary
            artifacts/result.zip  fixed output -> conflict
            ```
            """
            level @= MUST

        class SPEC_142:
            r"""この validation は現在解決している1本の base chain 内だけで行う。無関係な別 Configuration chain が同じ filesystem location を宣言しているかどうかは探索・保証しない。"""
            level @= MUST_NOT

    class SECTION_905:
        title @= 'Concurrent write と input collision'

        class SPEC_143:
            r"""dirpluck は process 間 lock や競合調停を提供しない。同じ output path への concurrent write はサポート対象外とする。Effective overwrite policy が false の場合に行う existing destination check は、別 process に対する atomic な no-clobber guarantee ではない。並行する可能性がある呼び出し側は異なる output destination を選ぶ必要がある。"""
            level @= MUST_NOT

        class SPEC_144:
            r"""どの effective Output でも、実行で生成する最終 output file 自身を archive input として選択することはできない。"""
            level @= MUST_NOT
