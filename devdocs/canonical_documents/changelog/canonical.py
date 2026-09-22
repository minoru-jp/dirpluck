from shikumi_devdoc.norms.changelog import ADDED, CHANGED, canonical, change, changelog, release, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@changelog("dirpluck CHANGELOG")
class CHANGELOG:
    r'''{{TERM_1}} のリリースごとの変更履歴。'''
    vocabulary_refs @= (terms.TERM_1,)

    @release("0.10.0")
    class RELEASE_16:
        r'''Runtime から Output destination と overwrite policy を指定できるようにし、Configuration の抽出定義を保ったまま書き出し場所を invocation ごとに変更できるようにする。'''

        @change(ADDED)
        class CHANGE_1:
            r'''CLI に `--here[=FILENAME]`、`-o PATH` / `--output PATH`、`-f` / `--force` を追加する。`--here` は runtime cwd、`--output` は runtime cwd 基準の明示 path を Output として使用し、末尾 `/` の `--output` は directory 指定として timestamp filename を自動生成する。`--here=FILENAME` は cwd 直下の filename だけを受理し、path を指定する場合は `--output` を使用する。'''

        @change(ADDED)
        class CHANGE_2:
            r'''公式 Python API の `run()` に `output` と `force` を追加する。`output` は CLI `--output` と同じ path semantics を持ち、末尾 `/` なら automatic timestamp filename、末尾 `/` がなければ exact output file path とする。Relative `output` は API の `cwd` を基準に解決する。'''

        @change(CHANGED)
        class CHANGE_3:
            r'''Runtime Output が指定された build では root Configuration に Output declaration を要求しない。Exact runtime output はその filename をそのまま使い、automatic runtime output は root Configuration が `[output.timestamp]` を宣言している場合だけその `prefix` / `suffix` naming rule を再利用する。Root に timestamp Output がない場合は `dirpluck-YYYYMMDD-HHMMSS.zip` を既定名とする。Configuration 側の output directory / fixed path は runtime destination へ引き継がない。'''

        @change(CHANGED)
        class CHANGE_4:
            r'''`--sequence N` は Configuration timestamp output に加えて、`--here` と末尾 `/` の runtime Output が生成する automatic timestamp filename にも適用する。Exact runtime file path と組み合わせた場合は error とする。Generated name の collision に対する自動採番・自動 rename・timestamp 再取得は行わない。'''

        @change(CHANGED)
        class CHANGE_5:
            r'''Runtime Output の default overwrite policy は `false` とし、`--force` / `force=True` で effective Output を overwrite 可能にする。`--force` は runtime Output だけでなく Configuration の fixed / timestamp Output にも適用できる。Runtime path notation は Configuration と同じく OS にかかわらず `/` separator を使用し、backslash を受理しない。'''

        @change(CHANGED)
        class CHANGE_6:
            r'''`--preview` / `preview=True` は Output を解決・書き込みしないため、runtime Output を指定する `--here` / `--output` / `output=`、overwrite を要求する `--force` / `force=True`、および output filename を変更する `--sequence` との組み合わせを error とする。指定した runtime Output option を preview が暗黙に無視する挙動は行わない。'''
