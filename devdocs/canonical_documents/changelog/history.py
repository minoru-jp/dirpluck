from shikumi_devdoc.norms.changelog import ADDED, CHANGED, FIXED, change, changelog_part, release, vocabulary_refs

from canonical_documents import terms


@changelog_part(order=30)
class CHANGELOG_PART:
    @release("0.8.0")
    class RELEASE_13:
        r'''Target discovery を direct-child model に単純化し、cwd / Target location ごとに Target candidate directory を `skip` できるようにする。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''CLI Target reference を `NAME`、`LOCATION/NAME`、`LOCATION/` の3形式へ限定する。cwd Target と location Target はそれぞれ resolution base の直下 directory だけを対象とし、`work/team/project` のような多階層 Target、`.`、`./project` を受理しない。`LOCATION/NAME` の location が未定義の場合は cwd-relative path へ fallback せず error とする。これにより Target の内部 directory が別の Target として再帰的に解決される状態をなくす。'''

        @change(ADDED)
        class CHANGE_2:
            r'''`[target].skip` と `[target.location.<name>].skip` を追加する。前者は cwd 直下、後者は各 location 直下の Target candidate directory name に適用し、explicit Target reference と `LOCATION/` expansion の両方から一致 directory を除外する。Pattern は case-sensitive な exact (`name`)、prefix (`name*`)、suffix (`*name`)、substring (`*name*`) を受理し、file selection の `exclude` とは独立させる。'''

        @change(CHANGED)
        class CHANGE_3:
            r'''Target の archive root は cwd / location のどちらから選んだ場合も direct child directory name 1 segment とし、logical location 名を archive path へ含めない。Named-location expansion は `skip` 適用後の eligible direct child directory だけを展開し、0件なら error とする。'''

    @release("0.7.0")
    class RELEASE_12:
        r'''Target を Configuration workspace から独立して配置できるようにし、named Target location と logical CLI reference による Target resolution を導入する。'''

        @change(ADDED)
        class CHANGE_1:
            r'''`[target.location.<name>]` を追加する。Location は Target definition に属する named filesystem base で、relative `path` はその Target definition を所有する Configuration layer の execution root、absolute `path` は host filesystem 上の directory を参照する。Outer Target が inner Target を shadow すると、Case と同様に location 集合も Target definition 全体とともに置き換わる。'''

        @change(CHANGED)
        class CHANGE_2:
            r'''CLI positional argument を raw directory path ではなく Target reference として解決する。`work/project` の先頭 segment が effective Target location 名と一致すれば残りをその location から解決し、一致しなければ従来どおり cwd 相対で解決する。`./work/project` は location lookup を明示的に回避する。Absolute positional Target reference は受理せず、cwd 外の Target には Target location を使用する。'''

        @change(ADDED)
        class CHANGE_3:
            r'''`<location>/` の形を named-location expansion として追加する。対応する location 直下の directory だけを独立した runtime Target として展開し、再帰列挙や regular file の Target 化は行わない。未定義 location、0 directory の展開、location boundary 外へ解決する directory symbolic link は error とする。複数の通常 Target reference と expansion は同じ run で併用できる。'''

        @change(CHANGED)
        class CHANGE_4:
            r'''Target location から解決した Target の archive path は logical location 名を含めず、location directory から見た filesystem-relative path を保持する。cwd-relative Target は引き続き cwd からの relative path を保持する。どちらの Target も最終的に解決された Target directory 自体を file selection boundary とする。'''

    @release("0.6.2")
    class RELEASE_11:
        r'''0.6.1 公開後の文書配布を微調整し、共有前の注意を入口文書へ戻すとともに、wheel だけでも trust model を参照できるようにする。実装上の挙動変更はない。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''README と wheel 同梱の Configuration quick reference に、外部へ渡す Archive の selection を確認する短い注意と `exclude = [".git/", ".env*", "*.pem", "*.key"]` の例を追加する。`docs/TRUST.md` 自体も wheel に同梱し、簡易文書から trust model へ直接到達できるようにする。'''

    @release("0.6.1")
    class RELEASE_10:
        r'''LLM-assisted work の位置付けと Configuration の trust boundary を文書上で明確化し、過剰な再現可能性の表現を取り除く。実装上の挙動変更はない。'''

        @change(ADDED)
        class CHANGE_1:
            r'''`docs/TRUST.md` を追加し、Configuration を filesystem 操作の実行指示として扱うこと、dirpluck は参照先の機密性や操作の適切さを推論して補正しないこと、OS permission と明示された path が実際の権限境界であることをまとめて説明する。Source boundary や schema validation などの structural checks と、内容や意図を判断する guard を区別する。'''

        @change(CHANGED)
        class CHANGE_2:
            r'''README の LLM-assisted work の説明を、非ローカルの対話型 LLM へ upload する Archive、またはローカル agent workspace へ配置する Archive を準備する用途として明確化する。LLM が dirpluck を直接操作することを前提とするように読める表現を削除し、trust model の詳細は `docs/TRUST.md` へ集約する。'''

        @change(CHANGED)
        class CHANGE_3:
            r'''README から `reproducibly` / 「再現可能」の売り文句を削除する。dirpluck の価値は TOML に明示した selection intent から必要な file をまとめることとして説明し、ZIP byte stream の再現性を示唆する専門的な意味を持たせない。'''

    @release("0.6.0")
    class RELEASE_9:
        r'''Filesystem location の表現力を拡張し、Archive README を配布向けの単純な索引へ整理するとともに、Configuration 全体の説明を記述できるようにする。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''Configuration の filesystem location は OS にかかわらず `/` separator で記述する。Companion `path`、import `root`、Root output の `path` / `directory` は host OS が認識する absolute path を受理し、relative path では field ごとの基準に従って `.` / `..` を扱う。別 OS の absolute-root notation への変換、`~` expansion、environment-variable interpolation は行わない。Include pattern と imported `configuration` は引き続き relative path に限定し、backslash を拒否する。'''

        @change(CHANGED)
        class CHANGE_2:
            r'''Companion が Configuration execution root の外側を含む任意の実在 source directory を relative `..` または absolute `path` で直接参照できるようにする。解決済み Companion source directory 自体を selection boundary とし、include や symbolic link からその外へ逸脱することは引き続き拒否する。Resolution base 外の Companion は解決済み source directory の最終 directory name を archive root とし、host の absolute path、drive、UNC share 名を archive path へ埋め込まない。'''

        @change(CHANGED)
        class CHANGE_3:
            r'''Archive root の `README.md` を dirpluck の resolution report から単純な contents index へ変更する。各 resolved source は final Archive root を見出しとして、selected file 数と任意の `description` を section body に記録する。description は table cell に圧縮せず複数行も保持する。Target / Companion、Case、Configuration chain、execution root などの dirpluck 固有情報や source filesystem path は既定では含めず、CLI `--paths` を指定した場合だけ各 source section に解決済み source directory を追加する。'''

        @change(ADDED)
        class CHANGE_4:
            r'''任意の `[about].description` を追加する。Configuration chain では outermost layer から inward に探索して最初に定義された値を effective description とし、存在する場合は Archive README の見出し直下、contents index の前へ表示する。Chain 全体に定義がない場合は全体説明を省略する。'''

    @release("0.5.2")
    class RELEASE_8:
        r'''公開文書体系を用途ごとに再構成し、語彙を概念上の基盤として分離するとともに、wheel には実行時に必要な最小限の参照文書だけを収録する。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''公開文書を `README.md`、`GLOSSARY.md`、`CHANGELOG.md` と `docs/CLI.md`、`docs/CONFIGURATION.md`、`docs/SPECIFICATION.md` に整理する。従来の `USAGE.md` は廃止し、CLI 操作と TOML Configuration の記述方法をそれぞれ専用文書へ分離する。README は用途と導入判断、Glossary は概念、各 `docs/` 文書は必要時に読む詳細という役割を明確にする。'''

        @change(CHANGED)
        class CHANGE_2:
            r'''`GLOSSARY.md` から個数制約、shadowing、path 規則、validation などの仕様詳細を外し、文書体系で共有する概念定義に限定する。厳密な挙動は `docs/SPECIFICATION.md` に集約し、CLI と Configuration のガイドでは作業に必要な範囲だけを説明して、より詳細な意味論へは参照を設ける。'''

        @change(CHANGED)
        class CHANGE_3:
            r'''wheel の同梱文書を、簡潔な `dirpluck/docs/CLI.md` と `dirpluck/docs/CONFIGURATION.md` の2つへ変更する。完全な Glossary、詳細ガイド、Specification、文書正本、日本語中間文書は sdist から参照できる構成を維持し、実行時の軽量な参照と詳細調査の導線を分離する。'''

    @release("0.5.1")
    class RELEASE_7:
        r'''0.5.0 の実効 Target binding を修正し、Target 定義の origin layer に依存せず runtime directory を CLI から受け取る一貫したモデルへ戻す。'''

        @change(FIXED)
        class CHANGE_1:
            r'''{{TERM_15}}に Target が存在する場合、Target 定義が{{TERM_14}}自身または import chain 内側のどちらに由来していても CLI `DIRECTORY` を1個以上必須とする。0.5.0 で導入した imported Target の Configuration placement から project directory を推定する規則と、imported Target への CLI `DIRECTORY` 禁止を廃止する。Target Selection は chain で名前解決し、runtime Target directory は常に{{TERM_14}}の execution root 内で解決する。'''
            vocabulary_refs @= (terms.TERM_14, terms.TERM_15)

    @release("0.5.0")
    class RELEASE_6:
        r'''Configuration import を1本の linear layering として一般化し、Target、Companion、共有パターンを import 先から import 元へ同じ名前解決規則で構成できるようにする。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''各 Configuration が持てる `[import.<name>]` を最大1個に限定する一方、import 先からさらに1個の Configuration を import する linear chain を許可する。chain の深さには上限を設けず、同じ解決済み Configuration file が現在の chain に再登場した場合だけ循環参照として拒否する。'''

        @change(CHANGED)
        class CHANGE_2:
            r'''Configuration chain を最深部から最外側へ解決して{{TERM_15}}を作る。Target は singleton 名 `target`、Companion と{{TERM_12}}は各自の名前で解決し、外側の同名定義が内側の定義全体を shadow する。共有パターン参照は最終的な実効名前空間で解決し、0.4.x の `<import>.<pattern>` 修飾名前空間を名前解決の必須モデルとして扱わない。'''
            vocabulary_refs @= (terms.TERM_12, terms.TERM_15)

        @change(CHANGED)
        class CHANGE_3:
            r'''import chain で最終的に残った Target を実行対象として使用できるようにする。{{TERM_14}}自身の Target が残る場合は従来どおり CLI `DIRECTORY` を束縛し、import 由来 Target が残る場合はその Target を定義した Configuration の project directory を `dirpluck.toml` または `dirpluck/<name>.toml` の配置から解決する。外側 Target が存在する場合は内側 Target とその Case をまとめて shadow する。'''
            vocabulary_refs @= (terms.TERM_14,)

        @change(CHANGED)
        class CHANGE_4:
            r'''Case 選択を import ごとの独立指定から{{TERM_15}}全体への1個の選択へ整理し、`[import.<name>].case` を使用しない。最終的な Target / Companion 定義に対して CLI `--case` を適用し、source が shadow された場合はその source の Case 定義も一緒に置き換える。'''
            vocabulary_refs @= (terms.TERM_15,)

        @change(CHANGED)
        class CHANGE_5:
            r'''最終出力は引き続き{{TERM_14}}自身の `[output]` だけを使用し、import chain 内側の output は実行しない。0.4.x の再帰 import 禁止に伴うバージョン固定エラー文言を廃止し、循環参照は解決 chain を示す version-independent な Configuration error として扱う。'''
            vocabulary_refs @= (terms.TERM_14,)

    @release("0.4.1")
    class RELEASE_5:
        r'''現在のパッケージバージョンを `dirpluck.__version__` に一本化し、文書生成ではそこから生成した外部 JSON context を利用する。'''

        @change(CHANGED)
        class CHANGE_1:
            r'''現在のリリース番号を用語集の語彙として保持する方式を廃止する。文書生成用の外部 context JSON は `dirpluck.__version__` から生成し、README など現在バージョンを必要とする文書は `version` context 値を参照する。CHANGELOG の各リリース番号は履歴情報として canonical source に直接記述する。'''

    @release("0.4.0")
    class RELEASE_4:
        r'''import 先 Configuration の共有 include / exclude パターンを、import 名前空間付きで Root 側から明示的に再利用できるようにする。'''

        @change(ADDED)
        class CHANGE_1:
            r'''設定インポートで読み込んだ Configuration の `[shared.include_patterns]` / `[shared.exclude_patterns]` を、{{TERM_14}}側から `<import-name>.<pattern-name>` の修飾名で参照できるようにする。Root local の{{TERM_12}}は従来どおりローカル名で参照し、include / exclude の種別は分離したまま維持する。'''
            vocabulary_refs @= (terms.TERM_12, terms.TERM_14)

        @change(ADDED)
        class CHANGE_2:
            r'''import 由来の修飾{{TERM_12}}を、{{TERM_14}}が所有する Target、Root Companion、`[import.<name>.companion.<name>]` の base / Case Selection から利用できるようにする。import 先 Configuration 自身が宣言する Companion は、引き続きその Configuration 自身の共有パターンをローカル名で解決し、Root 側の名前空間へ再束縛しない。'''
            vocabulary_refs @= (terms.TERM_12, terms.TERM_14)

        @change(ADDED)
        class CHANGE_3:
            r'''Root local の共有パターン名と import 由来の修飾共有パターン名が同じ参照文字列になる場合は、暗黙の優先順位を設けず設定エラーにする。共有パターンは import によって merge・自動適用されず、各 Selection が参照名を明示する既存モデルを維持する。'''

    @release("0.3.0")
    class RELEASE_3:
        r'''別ディレクトリの dirpluck Configuration が宣言する Companion を明示的に取り込み、各 Configuration の境界を保ったままひとつのアーカイブへ統合できるようにする。'''

        @change(ADDED)
        class CHANGE_1:
            r'''設定インポートを導入する。{{TERM_14}}の `[import.<name>]` に `root`、`configuration`、必要に応じて `case` を記述し、別の dirpluck 設定ファイルが宣言する Companion の抽出結果を同じ archive plan へ統合できるようにする。Root Configuration はローカル source を持たず設定インポートだけで構成することもできる。'''
            vocabulary_refs @= (terms.TERM_14,)

        @change(ADDED)
        class CHANGE_2:
            r'''設定インポートの `root` を、{{TERM_14}}の cwd 境界を明示的に越えられる唯一の path として定義する。`root` は{{TERM_14}}自身の所在ディレクトリからの相対 path に限定し、POSIX / Windows / UNC の絶対指定を OS にかかわらず拒否する。import root を解決した後は、`configuration`、import 先 Companion、選択ファイルをその root 内へ再び限定し、各 Configuration が独立した filesystem boundary を持つようにする。'''
            vocabulary_refs @= (terms.TERM_14,)

        @change(ADDED)
        class CHANGE_3:
            r'''{{TERM_14}}の CLI `DIRECTORY` と `--case` を import 先へ暗黙に伝播させず、import 先の Target は使用しない。`case` は import 先 Companion 群だけへ独立して適用する。import 先設定の `[output]` は schema validation だけを行って実行時には使用せず、最終出力は{{TERM_14}}の `[output]` だけとする。0.3.0 では import 先からさらに設定を import する再帰構成を拒否する。'''
            vocabulary_refs @= (terms.TERM_14,)

        @change(ADDED)
        class CHANGE_4:
            r'''Archive path を、各ファイルを選択した Configuration の execution root から見た相対 path として統合する。同じ archive path に同じ物理ファイルが重なる場合は1回だけ格納し、異なる物理ファイルが同じ archive path へ衝突する場合、または同じ物理ファイルが異なる archive path へ解決される場合は曖昧としてエラーにする。アーカイブ README には使用した設定インポートと各 execution root を記録する。'''
            vocabulary_refs @= ()

        @change(ADDED)
        class CHANGE_5:
            r'''設定インポートでは{{TERM_14}}から `[import.<name>.companion.<companion-name>]` を定義し、import root 内の追加 source を Target ではなく Companion として取り込めるようにする。import 配下の Companion は import 先設定由来か Root 側追加かにかかわらず `<import>.<companion>` の論理名を持ち、同じ import 内での重複を拒否する。Root 側追加 Companion は Root の shared pattern を、import 先設定由来 Companion は import 先の shared pattern を使用し、`path = "."` によって import root 自体を Companion として選べる。'''
            vocabulary_refs @= (terms.TERM_14,)

    @release("0.2.0")
    class RELEASE_2:
        r'''共有パターンを導入し、抽出条件をケース間や source 間で明示的に再利用できるようにする。'''

        @change(ADDED)
        class CHANGE_1:
            r'''{{TERM_12}}を導入する。`[shared.include_patterns]` と `[shared.exclude_patterns]` に `name = [...]` の形で名前付きパターン集合を定義し、対象またはコンパニオンの base / case 選択から `include_pattern_refs` / `include_if_exists_pattern_refs` / `exclude_pattern_refs` で明示的に参照できるようにする。共有パターンは参照した選択にだけ追加され、base から case への継承や暗黙の merge、source 間の自動適用は行わない。'''
            vocabulary_refs @= (terms.TERM_12,)

        @change(ADDED)
        class CHANGE_2:
            r'''include 用の{{TERM_12}}は include のパターン文法で、exclude 用の共有パターンは exclude のパターン文法で検証する。include 用の共有パターンは `include_pattern_refs` から必須候補、`include_if_exists_pattern_refs` から任意候補として参照でき、exclude 用は `exclude_pattern_refs` から参照できる。いずれも直接記述した `include` / `include_if_exists` / `exclude` と併用できる。'''
            vocabulary_refs @= (terms.TERM_12,)

        @change(ADDED)
        class CHANGE_3:
            r'''sdist をリリースの再構築・検証に使えるソース配布物として拡充し、従来の tests と公開文書に加えて `_internal/` の文書正本・日本語中間文書と `tools/` の同期・配布検証ツールを収録する。`_internal/`、`tools/`、tests、`.github/` は wheel へ含めない。'''

        @change(ADDED)
        class CHANGE_4:
            r'''実行時に必要な操作規則を短く確認できる公開 `USAGE.md` を追加する。文書は正本から日本語中間文書を生成して英訳する既存フローで管理し、リポジトリルート、sdist、および wheel の `dirpluck/docs/USAGE.md` に収録する。wheel に同梱する文書は `USAGE.md` のみに整理し、`README.md`、`CONFIGURATION.md`、`GLOSSARY.md`、`SPECIFICATION.md` は sdist またはリポジトリで提供する。'''

    @release("0.1.0")
    class RELEASE_1:
        r'''最初の公開リリース。'''

        @change(ADDED)
        class CHANGE_1:
            r'''ひとつの{{TERM_2}}をひとつの抽出意図として扱い、省略可能な runtime-bound {{TERM_3}}定義と0個以上の固定コンパニオンの少なくとも一方、必須の{{TERM_9}}から ZIP {{TERM_8}}を生成できるようにする。対象を定義する場合は同じ対象規則へ CLI から1個以上のディレクトリを与えられ、TOML の対象定義自体は1個のままにする。対象を持たない設定は位置引数なしで実行し、その設定へ `DIRECTORY` を渡すことはエラーにする。抽出条件は各 source へ直接記述し、名前付きの共有抽出規則やバンドル参照を持たない。'''
            vocabulary_refs @= (terms.TERM_2, terms.TERM_3, terms.TERM_8, terms.TERM_9)

        @change(ADDED)
        class CHANGE_2:
            r'''{{TERM_4}}を設定ファイル全体で1個だけ有効になる平坦な名前付き selection variation として一般化する。対象がある場合は `[target.case.<name>]` が選択ケースを必ず定義し、各コンパニオンは同名の `[companion.<name>.case.<name>]` があれば使い、なければ base へフォールバックする。対象がない場合は少なくとも1個のコンパニオンがケースを定義する。ケース定義は完全な選択で継承・merge せず、source 構成、コンパニオン path、出力方針は変更しない。ケースの組み合わせと多階層化も拒否する。'''
            vocabulary_refs @= (terms.TERM_4,)

        @change(ADDED)
        class CHANGE_3:
            r'''`include` と `include_if_exists` で階層数を明示した相対パスを指定し、各パス要素に最大1個の `*` を使って同一階層の実体名だけを可変にできるようにする。`include` は一致を必須とし、`include_if_exists` は0件一致を許容する。`**` による任意深度検索は提供しない。'''

        @change(ADDED)
        class CHANGE_4:
            r'''`exclude` で、選択済み範囲のファイル名またはディレクトリ名に対する exact / prefix / suffix / contains の限定された除外フィルタを提供する。'''

        @change(ADDED)
        class CHANGE_5:
            r'''`if_empty` の既定値を `error` とし、`include_if_exists` だけを持つ対象またはコンパニオンでは `allow` を明示して0件の最終選択を正常として扱えるようにする。空を許したディレクトリは{{TERM_8}}へ空ディレクトリとして保持できる。'''
            vocabulary_refs @= (terms.TERM_8,)

        @change(ADDED)
        class CHANGE_6:
            r'''`--dry-run` で ZIP を作成せず生成予定の構成を tree 形式で表示する。不足する `include` は `[missing]`、不足する `include_if_exists` は `[optional missing]` として表示し、空結果の方針も可視化する。'''

        @change(ADDED)
        class CHANGE_7:
            r'''処理対象を実行時のカレントディレクトリ内に限定し、シンボリックリンクによる対象外への逸脱を拒否する。{{TERM_3}}には cwd 自体も指定でき、その場合も{{TERM_8}}内では cwd の実ディレクトリ名を保持する。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_8)

        @change(ADDED)
        class CHANGE_8:
            r'''各{{TERM_3}}ケースとコンパニオンに `description` を必須化し、{{TERM_8}}ルートへ{{TERM_10}}を自動生成する。同じ実ディレクトリが複数の目的から要求された場合はファイルを実パスで合成し、README にそれぞれの目的を併記する。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_8, terms.TERM_10)

        @change(ADDED)
        class CHANGE_9:
            r'''Python 3.11 以降を対象とし、MIT License で配布する。実行時のサードパーティ依存は持たない。'''

        @change(ADDED)
        class CHANGE_10:
            r'''PyPI 配布物の内容を明示する。wheel には実行コードと公開 `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md` を収録し、sdist にはさらに tests と公開文書を含める。`_internal/` と `.github/` はリポジトリ専用とし、配布物には含めない。'''

        @change(ADDED)
        class CHANGE_11:
            r'''CLI の通常形を `dirpluck DIRECTORY [DIRECTORY ...]` とし、`build` サブコマンドを廃止する。{{TERM_2}}は cwd と `./dirpluck/` の直下だけから探索し、既定では `dirpluck.toml`、`--config NAME` 指定時は同名の TOML を両方の場所から探す。候補が複数なら暗黙に優先せず曖昧としてエラーにし、`--configs` で検出候補と競合を列挙できるようにする。'''
            vocabulary_refs @= (terms.TERM_2,)
        @change(ADDED)
        class CHANGE_12:
            r'''`README.md` を具体的な利用例と反復可能なファイル集合の価値を中心に再構成し、TOML の書き方を `CONFIGURATION.md`、厳密な動作意味論を `SPECIFICATION.md` へ分離する。'''

        @change(ADDED)
        class CHANGE_13:
            r'''{{TERM_8}}ルートの{{TERM_10}}を用途中立の索引に限定する。固定文言から生成ツール名と下流用途の説明を除き、具体的な用途は各{{TERM_3}}・コンパニオンの `description` に委ねる。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_8, terms.TERM_10)

        @change(ADDED)
        class CHANGE_14:
            r'''{{TERM_9}}に固定出力と動的命名出力の2形式を設ける。動的命名では `directory`、`timestamp = true`、任意の `prefix` / `suffix` から `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` を生成し、通常実行では既存の同名出力を拒否する。`--sequence N` で呼び出し側が正の整数を明示できるが、自動採番、自動リネーム、上書きは行わない。非同期・並列実行の競合調停は行わず、同じ出力 path への並行書き込みは呼び出し側が避ける。'''
            vocabulary_refs @= (terms.TERM_9,)


        @change(ADDED)
        class CHANGE_15:
            r'''README と `CONFIGURATION.md` で、ディレクトリを選択すると配下を再帰的に収集し、`.env`、秘密鍵、`.git` などを秘密情報として推論・自動除外しない責任境界を明示する。広い選択では用途に応じた `exclude` を設定する。'''
