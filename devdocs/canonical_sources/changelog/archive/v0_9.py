from shikumi_devdoc.fields.changelog import added, changed, fixed, version
from shikumi_devdoc.norms.common import canonical_source, summary
from shikumi_devdoc.norms.document import title


@summary("現在の model へ移行した 0.9.x 系列のリリース履歴。")
@canonical_source(
    "dirpluck CHANGELOG 0.9.x",
    filename="0.9.x.md",
    merge_policy="forbidden",
    heading="title",
    order=10,
)
class CHANGELOG_0_9:
    r"""
    dirpluck 0.9.x のリリース履歴。0.10.0 以降の履歴は [main CHANGELOG](../../CHANGELOG.md) を参照してください。
    """

    class RELEASE_15:
        r"""
        Target と Always source が同じ physical material を独立した役割で含められるようにし、Archive planning と生成 README の重複表現を修正する。

        この version は PyPI へ公開しなかった development milestone です。
        """

        title @= "0.9.1"

        version @= "0.9.1"

        fixed @= "Target と Always source が同じ physical file を選択して異なる Archive path へ配置する場合に ambiguity error として拒否していた制約を解除する。Target の Pluck と Always source の Selection は physical overlap の有無にかかわらず独立して評価し、Target 側の `ignore` や未選択結果によって Always source を抑止しない。同じ archive path に異なる physical file が衝突する場合は引き続き error とし、同じ archive path に同じ physical file が重なる場合は1回だけ書き込む。Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合は、生成 Archive README の Always source section に Target 側の final Archive root と重複 file 数を表示する。"

    class RELEASE_14:
        r"""
        1.0 に向けて Configuration language の語彙と filesystem model を整理し、公開設定面を新しい Pluck / Scope / Always / Base / Output model へ移行する。Development Status を Beta へ進める。
        """

        title @= "0.9.0"

        version @= "0.9.0"

        changed @= "Configuration vocabulary を全面的に整理する。`[target]` を `[pluck]`、`[companion.<name>]` を `[always.<name>]`、Target location を Configuration-level の `[scope]` / `[scope.<name>]` へ変更する。Selection は `include` / `include_if_exists` / `exclude` を `must` / `may` / `ignore`、`if_empty` を boolean `allow_empty` へ置き換える。旧 schema の compatibility layer は設けない。"

        changed @= "Configuration layering を `[about].base` による linear base chain へ単純化する。旧 `[import.<name>]`、`root`、`configuration` と import overlay Companion を廃止し、relative filesystem path は `about.base`、Scope、Always source、Output のいずれも、その field を記述した Configuration file の directory を基準に解決する。Base から継承した definition は outer Configuration の位置へ rebase しない。"

        changed @= "Target discovery を独立した Scope 群として整理する。Default Scope は常に root Configuration directory を探索 root とし、`[scope]` はその optional `ignore` を設定する。名前付き Scope は `path` で追加の探索 root を定め、base chain では同名 named Scope を outer layer が definition 全体で shadow する。CLI Target reference は `NAME`、`SCOPE/NAME`、`/`、`SCOPE/` の4形式とし、`/` は default Scope の direct-child expansion を表す。Scope `ignore` は単一選択と全展開の両方へ適用する。"

        changed @= 'Shared pattern を `[shared.must]` / `[shared.may]` / `[shared.ignore]` の3 namespace に分け、専用 `*_pattern_refs` field を廃止する。Selection array の通常 string を direct pattern、1要素 nested array (`["name"]`) を同じ field の Shared reference として解釈し、effective Shared namespace で展開する。'

        changed @= "Output を fixed `[output]` と timestamp `[output.timestamp]` の排他的な2 mode に整理する。Fixed output は concrete file `path` と optional `overwrite` を持ち、`overwrite` の既定値は `false` とする。Timestamp output は末尾 `/` を持つ directory `path` と optional `prefix` / `suffix` を使い、旧 `directory` と boolean `timestamp = true` を廃止する。"

        changed @= "Base chain 上の Output について static writable destination を検証する。Fixed output は完全 file path、timestamp output は output directory tree を書き込み境界とし、同一 fixed file、重なる timestamp directory、timestamp boundary 内の fixed file を conflict とする。同じ directory に異なる filename の fixed output を置くことは許可する。実際に書き込むのは引き続きルート設定ファイル自身の Output だけとする。"

        changed @= "Project metadata の Development Status classifier を `3 - Alpha` から `4 - Beta` へ変更する。"

        fixed @= "ZIP 作成時に selected file の mtime が ZIP format の timestamp 範囲外でも traceback せず、範囲内へ clamp して Archive を作成できるようにする。また selected file を Archive へ追加する際に `OSError` が発生した場合は `SelectionError` として扱い、CLI が raw traceback を表示せず一時 Archive を残さないようにする。"

        fixed @= "Scope handling を単純化し、default Scope を root Configuration directory に常設する。これにより `[scope.<name>]` の TOML 親 table と明示 `[scope]` を区別する補助的な text detection を不要にする。また named Scope root の存在・directory validation はその Scope を Target resolution / expansion に実際に使用するときまで遅延し、未マウントなどで利用不能な未使用 Scope が別 Scope の実行を失敗させないようにする。"

        changed @= "Filesystem traversal で symbolic link をたどる挙動を廃止する。Scope 直下の symbolic link は Target candidate にせず、Selection 内の file / directory symbolic link も selectable entry とせず Archive に含めない。明示 Target reference が symbolic link を指す場合は error とし、`must` / `may` pattern が symbolic link だけに一致する場合はそれぞれ required missing / optional missing として扱う。"

        fixed @= "Selection の directory `ignore` を再帰走査後の後処理 filter ではなく traversal-time pruning として適用する。Ignore 対象 directory の内部を列挙しないため、大きな ignored subtree の不要な走査を避け、内部の entry による traversal-time error も発生させない。"

        fixed @= "README と wheel 同梱 Configuration quick reference の機密 file 除外例に `[pluck]` table header を追加し、`ignore = [...]` をそのまま top-level key として貼り付けて Configuration error になる曖昧さをなくす。"

        changed @= "Output declaration を Configuration 単体の schema では optional にする。Output を持たない Configuration は共通 Base として利用でき、root Configuration でも Archive planning / `--preview` には Output を要求しない。実際に Archive file を書き込む build では root 自身の fixed または timestamp Output を直接宣言しなければならず、Base の Output は継承しない。Base chain の write-boundary validation には Output を実際に宣言した layer だけが参加する。"

        fixed @= "内部の `resolve_sources` / `plan_archive` / `build_archive` が受け取っていた `cwd` 引数を削除する。これらの引数は存在確認だけを行い resolution には使用されておらず、Configuration-relative path を制御できるように見える誤解を招いていた。Runtime cwd は implicit `default.dirpluck` selection と CLI で指定する relative document path の基準にだけ残し、source / Output resolution は引き続き各 Configuration file の位置だけを基準にする。"

        changed @= "Selection の内部表現を、Shared reference を保持する parse 済み `SelectionDefinition` と、effective Shared namespace で展開済みの `Selection` に分離する。parse 前後の状態を1つの object に二重保持していた `must_items` / `may_items` / `ignore_items` と、それに伴う型抑制・自己代入を廃止する。"

        changed @= "現在の Configuration model に合わせて semantic test module と package-interface test の名称・対象を整理する。過去の release 段階を表す test 名ではなく、現在検証している Configuration semantics / effective-Configuration boundary を名前に使用する。"

        added @= 'Archive placement 専用の名前付き `[namespace.<name>]` definition を追加する。Namespace は現時点では属性を持たない空 table とし、名前そのものを Archive directory component とする。Default / named Scope と Always source は optional `namespace = "<name>"` で effective Namespace を参照でき、指定した source の通常 source root の外側へ Namespace を常に追加する。'

        changed @= "異なる resolved source が同じ final archive root に解決された場合、selected file が直接衝突しなくても黙って同一 directory へ merge せず error とする。衝突回避は明示的な Namespace で行い、自動 suffix や Scope / Always 名による暗黙 qualification は行わない。Namespace を使用する Archive README では final Archive root を見出しとし、Namespace / Source root を metadata として分け、Namespace が元 source path ではなく Archive 専用の outer directory であることを明示する。"

        changed @= "Archive を書き込まず生成予定内容を確認する CLI option を `--dry-run` から `--preview` へ変更する。互換 alias は設けない。また `--help` の positional `TARGET` 説明に `NAME`、`SCOPE/NAME`、`/`、`SCOPE/` の4形式と、それぞれ default / named Scope の単一選択・全展開であることを明示する。"

        fixed @= "Generated archive index が使用する root-level `README.md` を予約 path とし、resolved source の final archive root が case-insensitive にその path 自身またはその配下へ解決される場合は Archive 作成前に error とする。Namespace 名だけを特別扱いせず、Namespace なしの source root にも同じ規則を適用する。"

        changed @= "`--preview` と内部 `plan_archive()` は root Configuration に Output declaration がなくても Archive contents を解決できるようにする。実際に file を書き込む `build_archive()` だけが root 自身の Output を要求する。`--preview` は output filename generation を行わないため `--sequence` と同時指定できない。"

        fixed @= "Default Scope の `ignore` / `namespace` は root-local であり base composition されないことを Configuration 文書で明示する。Base に `[scope]` を書くこと自体は有効で、その Configuration 自身を Root として使用した場合だけ default Scope 設定として適用される。"

        changed @= "Configuration 候補を推論・一覧表示する `--configs` を廃止する。CLI が暗黙に選ぶ Configuration は runtime cwd の `default.dirpluck` だけに限定し、単独の別名 Configuration を implicit default として選ばず、file 内容から Configuration らしさを判定する heuristic discovery も行わない。別名または別 directory の Configuration は `--config PATH` で明示する。互換 alias は設けない。"

        fixed @= "Symbolic link の非 traversal policy を Windows directory junction にも拡張し、Python 3.11 でも `lstat` の reparse tag から junction を認識できる共通 helper を使用する。Selection traversal で認識して Archive から除外した link-like entry は path を列挙せず件数だけを `--preview` と通常 build の CLI output に note として表示する。`must` pattern が link-like entry だけに一致した場合は単なる `no matches` ではなく、link-like entry が selectable でないことを示す error にする。TRUST 文書では platform 固有の未知の link-like mechanism を完全には検出保証しないこと、および第三者 extractor の展開時解釈を dirpluck が保証しないことを明記する。"

        fixed @= "型検査で見つかった内部の型不整合を修正する。Effective Configuration validation では Scope binding と Always binding の loop 変数を別名にして異なる binding 型を混同しないようにし、Configuration table の key validation helper は実際の TOML table に合わせて `Mapping[str, object]` を受け取る。Windows 固有の `stat_result.st_reparse_tag` は `getattr` で取得し、type checker が非 Windows の `stat_result` に存在しない属性への直接参照として扱わないようにする。Runtime behavior と公開 API は変更しない。"

        fixed @= "Archive build の Output preflight を archive planning より前へ戻す。Root Output の有無、`--sequence` の妥当性、解決済み output path、既存 output に対する overwrite policy を先に検証し、失敗が確定している build で大きな source tree を走査しないようにする。Planning 後にしか判定できない「output 自身が selected input に含まれる」検査と、directory 作成・ZIP 書き込みなどの副作用は引き続き planning 後に行う。"

        fixed @= "Selection `ignore` の優先順位を明確化し、ignored entry は link-like entry としての skipped count や link-only `must` error の根拠にしない。`must` が ignored entry にしか一致しない場合は通常の unsatisfied pattern として扱い、directory `ignore` で枝刈りした subtree と同様に「無視する」という Configuration の明示指示を runtime diagnostics より優先する。"

        fixed @= "Windows directory junction の safety boundary を fail-closed にする。対応 Windows runtime で `IO_REPARSE_TAG_MOUNT_POINT` または `st_reparse_tag` を取得できない場合に junction 判定を黙って無効化せず error とし、Windows CI の junction integration test は junction 作成失敗を skip せず test failure として扱う。"

        fixed @= "CLI が skipped-link count を受け取るための build-and-plan helper を内部名へ戻し、Python module の公開面に新しい API を増やさない。あわせて Ruff の preview E3 blank-line rule (`E301`〜`E306`) を explicit rule として repository の lint 設定へ追加し、`src` / `tests` / `tools` の空行を整える。Runtime behavior と package-root public interface は変更しない。"

        fixed @= "Selection が扱う filesystem object の境界を regular file / regular directory に明確化する。FIFO、socket、device などその他の non-regular entry は Archive に含めず、directory traversal 中や optional `may` match では静かに除外する。`must` pattern が non-ignored special entry だけに一致した場合は単なる `no matches` ではなく、unsupported special filesystem entry が selectable でないことを示す理由付き error にする。`ignore` に一致した special entry は種類別 diagnostic より先に除外する。"

        changed @= "Configuration document の identity を `.toml` から `.dirpluck` extension へ移行する。内容の syntax は引き続き TOML とする。`--config` 省略時に暗黙使用する document は runtime cwd の `default.dirpluck` だけとし、`about.base` も concrete `.dirpluck` path を要求する。`.toml` Configuration、旧 `dirpluck.toml`、旧 `./dirpluck/` discovery location への compatibility alias / fallback は設けない。"

        added @= "繰り返し使う CLI invocation を保存する `.dirpluck-inv` Invocation Template document と、`-i PATH` / `--invocation-template PATH`、`-e NAME` / `--entry NAME` を追加する。1 file は root `[invocation]` を default Invocation、`[invocation.<name>]` を named Invocation entry として複数の呼び出しを保持できる。各 Invocation は optional `config` / `targets` / `case` / `archive_mtime` を独立して持ち、named entry は root から field を継承しない。CLI では cwd 基準の relative path または absolute path で Template file を明示選択し、`-e` 省略時は root、指定時は named entry を選ぶ。Relative `config` path は Template file 自身の directory 基準とする。Field を持たない Invocation も有効で CLI runtime value と normal defaults を使い、成功した preview / build では note を表示する。Template 使用時は positional Target / `--config` の override や一般的な差分合成を提供しない一方、`--case` と `--archive-mtime` は選択した Invocation の保存値を実行時に上書きできる。`--preview` / `--sequence` / `--archive-mtime` / `--paths` も runtime modifier として併用できる。"

        changed @= "Invocation の `case` を固定値ではなく default Case として扱い、`-i` / `--invocation-template` と CLI `--case` を併用できるようにする。CLI `--case` が指定された場合は選択した default / named Invocation の `case` より優先し、CLI 側を省略した場合だけ Invocation の値を使用する。"

        changed @= "CLI の Configuration / Invocation Template path で `Path.suffix` による extension 判定をやめ、required suffix が末尾になければ `.dirpluck` / `.dirpluck-inv` をそのまま付加する。これにより `--config release-1.2` は cwd の `release-1.2.dirpluck`、`--config configs/release-1.2` は cwd の `configs/release-1.2.dirpluck`、`-i set-2.1` は cwd の `set-2.1.dirpluck-inv` を選び、stem 内の dot を不正 extension として拒否しない。"

        changed @= "CLI の document selection を単純化し、`--config` を省略した場合に自動選択する Configuration を runtime cwd の `default.dirpluck` だけへ限定する。`./.dirpluck/` は reserved discovery / control directory として扱わず、`.dirpluck` という directory name に Scope semantics 上の special case も持たせない。`--config PATH` と `-i PATH` は Configuration の filesystem-location notation と同じ `/` separator、glob / backslash なしの path 表記を受理し、relative path は runtime cwd、absolute path は host filesystem から1個の document を直接選ぶ。Directory 指定から default document を補完せず、別 location の同名 file を探索・ambiguity 解決しない。Default Scope root は常に Root Configuration file の directory とする。"

        fixed @= "空の `.dirpluck-inv` document に対する diagnostic を `[invocation]: expected a table` から `[invocation] table is required` へ変更し、required table 自体の欠落と、`invocation = ...` のような table 型違いを区別する。Field を持たない空の `[invocation]` table は引き続き有効とする。"

        changed @= "Configuration / Invocation Template の control document path は host OS の通常の filesystem semantics に従う形へ整理する。cwd の `default.dirpluck`、`--config PATH`、`-i PATH`、`[about].base`、Invocation の `config` では symbolic link / Windows directory junction を含む path も通常の filesystem semantics で扱い、選択・参照した lexical absolute path を document location として保持する。Relative reference はその location の directory を基準にし、Base chain の cycle detection のように file identity が必要な内部判定だけ実体 path を使う。Source tree の symbolic link / junction 非 traversal policy は独立した extraction boundary として維持する。"

        fixed @= "`[invocation.config]`、`[invocation.targets]`、`[invocation.case]` を field value の型 error として報告していた ambiguity を解消する。`config` / `targets` / `case` は root Invocation の field 名として予約し、named Invocation entry name には使用できないことを schema と diagnostic で明示する。"

        changed @= 'Invocation の `config` path も CLI `--config PATH` と同じ suffix completion を行うようにし、`.dirpluck` を省略可能にする。`config = "configs/release-1.2"` は Template document の directory を基準に `configs/release-1.2.dirpluck` を参照する。`[about].base` は Configuration schema 内の explicit document reference として `.dirpluck` extension 必須のままとする。'

        fixed @= "Filesystem-location notation で backslash を拒否する diagnostic に、host OS が Windows の場合も `/` を path separator として使用することを明示する。受理する path grammar 自体は変更せず、CLI の `--config PATH` / `-i PATH` と Configuration / Invocation Template 内の filesystem-location field で共通の説明を返す。"

        changed @= "Source root と traversal entry の link handling を整理する。Configuration が `[scope.<name>].path` / `[always.<name>].path` で明示した root location は host OS の通常の filesystem semantics で解決し、symbolic link / Windows directory junction を含む location も root として使用できる。一方、解決した root から Dirpluck が自動的に行う Target discovery / Selection traversal では link-like entry を引き続き選択・走査しない。Always source の Archive source root は alias の実体 directory name へ置き換えず、Configuration に明示した lexical source location の name / relative path を保持する。"

        changed @= "Pluck / Always source / Case selection の `description` を必須 metadata から任意 metadata へ変更する。Selection の成立条件は `must` / `may` candidate と `allow_empty` policy だけで決まり、`description` を省略しても抽出意味論は変わらない。Archive README の source index は table ではなく final Archive root ごとの section とし、selected file 数を metadata、任意の `description` を section body として表示する。これにより複数行の description も table cell へ圧縮せず保持する。"

        fixed @= "Atomic Output write に使用する temporary file の `0600` mode が、そのまま final ZIP の permission になる実装依存を解消する。Temporary output を通常の new regular file と同じ creation mode で作成し、POSIX では process `umask` を適用した mode を final Archive へ保持する。`overwrite = true` でも既存 destination の mode は継承せず、その run の新規 file creation semantics を使用する。"

        added @= 'Selection `ignore` に Selection-root-relative の concrete path reference を追加する。`ignore = [["./tests/fixtures/big.bin"], ["./src/generated/"]]` のように、1要素 nested array の string を `./` で始めた場合は Shared ignore reference ではなく path reference として解釈する。Pluck では Target root、Always source ではその source root を基準とし、末尾 `/` で directory を明示する。Path reference は Selection root 内へ限定し、`..`、absolute path、glob、backslash を拒否する。Name pattern / Shared ignore / path reference の semantic overlap は error とせず除外条件の和として扱い、directory reference は subtree traversal 前に prune できる。'

        added @= "Beta 公開面として最小の公式 Python API を package root に追加する。`dirpluck.run()` は CLI と同じ Configuration / Target / Case / Invocation Template / Entry / preview / output semantics を programmatic に実行し、`RunResult` で output path、preview tree、Archive entry、生成 README、link-like skip count、空 Invocation の状態を返す。公式 package-root export は `run`、`RunResult`、`DirpluckError`、`__version__` に限定し、builder / config / invocation などの低 level module は引き続き互換性保証対象外とする。CLI は argparse 後に同じ application layer を呼ぶ adapter とする。"

        changed @= "文書開発 workspace を `_internal/document_source` / `_internal/document_build/ja` から公開 repository structure の `devdocs/` へ再編する。Canonical Python source は `devdocs/canonical_documents/`、shikumi-devdoc へ渡す repository configuration は `devdocs/config/`、日本語 intermediate Markdown は `devdocs/intermediate_documents/` に配置する。`canonical_documents` 自体を import package とし、Vocabulary 由来の生成 `terms.py` はその package root に置く。Intermediate documents は repository publication path を mirror し、wheel-facing artifacts は `package/` namespace に分離する。`devdocs/README.md` も canonical source から生成する。`devdocs/` は sdist に含め、wheel からは除外する。"

        changed @= "Output の concurrent-writer boundary を明確化する。Fixed output の `overwrite = false` と timestamp output は既存 destination を build 前および最終配置前に検査するが、この check と final placement は別 process に対する atomic な no-clobber operation ではない。同じ output path への concurrent write は dirpluck の調停対象外とし、並行実行する呼び出し側が異なる destination を割り当てる。実装の output policy 自体は変更しない。"

        added @= "Archive entry timestamp を runtime で統一する `--archive-mtime VALUE` と Invocation Template の `archive_mtime` field を追加する。`VALUE` は `YYYY-MM-DDTHH:MM:SS`、`now`、`zip-epoch` を受理し、CLI value は選択した Invocation の保存値を上書きする。`now` は1 run で local current time を1回だけ取得し、`zip-epoch` は ZIP 最小 timestamp `1980-01-01T00:00:00` を使う。ZIP の2秒粒度に合わせて奇数秒を切り下げ、generated README / empty directory / source file の全 entry へ同じ timestamp を設定する。Option を省略した場合は従来の entry timestamp behavior を維持する。固定 mtime は timestamp 差を取り除き reproducible な Archive を作る一助になるが、source file の permission bits など他の metadata は正規化せず、Archive 全体の byte-for-byte reproducibility は保証しない。"
