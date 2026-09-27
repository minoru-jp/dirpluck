<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/archive.py` です。
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

# Archive planning

## SPEC_095

Scope から解決した Target の source root は Target directory name 1 segment とする。Logical Scope name は archive path へ暗黙には含めない。

level: MUST

related: [SPEC_050](runtime-targets.md#spec_050)

## SPEC_096

Always source の source root は、実体 directory ではなく Configuration に明示された source location から決める。Source location が、その definition を記述した Configuration file directory の配下にある場合は、その Configuration directory から見た lexical relative path とする。Absolute path または `..` により source location がその base 外にある場合は、明示 location の最終 directory name を source root とする。最終 component が symbolic link / Windows directory junction で実体 directory name と異なる場合も、Archive では明示 location 側の name を保持する。Filesystem root 自体を Always source として受理しないのは、この portable source root を持たないためである。Host の absolute path、drive、UNC share 名そのものは archive path へ埋め込まない。

level: MUST

## SPEC_097

ネームスペースを参照しない source の final archive root は source root と同じである。Namespace を参照する source は `NAMESPACE/SOURCE_ROOT` を final archive root とし、その下へ source directory からの relative selected file path を配置する。Namespace は collision が実際に起きた場合だけ追加するのではなく、その source へ常に適用する。

level: MUST

related: [SPEC_063](namespace.md#spec_063)

## SPEC_098

1回の実行で異なる resolved source が同じ final archive root に解決された場合は、file selection の内容が重ならなくても ambiguity error とする。dirpluck は source を同じ directory へ黙って merge せず、自動 suffix や Scope / Always 名による自動 qualification も行わない。必要な場合は Configuration で Namespace を明示して final archive root を区別する。

level: MUST

related: [SPEC_064](namespace.md#spec_064)

## SPEC_099

Final archive root が一意であることを確認した後、同じ archive path に異なる physical file が衝突する場合は ambiguity error とする。同じ archive path に同じ physical file が再度現れる場合は1回だけ書き込む。同じ physical file が異なる resolved source から異なる archive path へ解決されることは許可し、それぞれの archive path に書き込む。

level: MUST

## SPEC_100

Target と Always source の Selection は source ごとに独立して評価する。ある physical file が Target の source tree に含まれていても、Target 側の `ignore`、未選択、missing result は Always source の Selection を変更しない。Physical overlap は各 source の Selection が完了した後に判定し、Selection result 自体を merge、suppress、error にしない。

level: MUST

related: [SPEC_065](selection.md#spec_065)

## SPEC_101

Archive root の root-level `README.md` は dirpluck が生成する index 用の予約 path とする。Resolved source の final archive root の先頭 component が case-insensitive に `README.md` と一致する場合は error とし、その下へ source tree を配置しない。この規則は Namespace 名だけでなく、Namespace を使わない source root にも同じように適用する。

level: MUST

## SPEC_102

Archive root にはアーカイブREADMEを `README.md` として生成する。これは archive contents の index であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は `# Archive contents` の直後にその本文を表示する。存在しない場合はこの全体説明を省略する。

level: MUST

## SPEC_103

各 resolved source は、その final archive root を inline code とした level-2 heading で1 sectionずつ表現する。Section には selected file 数を `Files: N` として記録し、selection `description` が存在する場合は、その metadata の後へ本文としてそのまま表示する。`description` を table cell へ圧縮せず、複数行を含む説明も section body として保持する。description がない source には説明本文を追加しない。

level: MUST

## SPEC_104

Always source が実際に選択した physical file と Target が実際に選択した physical file に重複がある場合、その Always source section に Target ごとの `Target overlap` metadata を表示する。Metadata は重複 file 数と Target の final archive root を記録する。同じ physical file が Target 側で `ignore` されるなどして実際には選択されていない場合は overlap に数えない。この metadata は physical overlap の説明であり、Selection や Archive placement を変更しない。

level: MUST

condition: Always source と Target が同じ physical file を選択した場合

## SPEC_105

少なくとも1個の source に Namespace が適用される場合、README は source section の前に Namespace が Archive 専用の outer directory であり元 source path の一部ではないこと、source root がその直下にあることを説明する。Namespace を使う各 source section には `Namespace` と `Source root` も表示する。Namespace を使わない source にはこの metadata を追加しない。

level: MUST

condition: 少なくとも1個の source に Namespace が適用される場合

## SPEC_106

既定では source filesystem path、Configuration path / table、base chain、Scope / Pluck / Always 名、選択 Case などの dirpluck 固有情報を記録しない。Target overlap metadata は Target 名ではなく final archive root を使用する。CLI `--paths` が指定された場合だけ各 source section に `Source` として解決済み source directory を `/` separator の filesystem path で記録する。`--paths` は archive path や file selection を変更しない。

level: MUST

condition: CLI `--paths` が指定された場合

related: [SPEC_093](filesystem.md#spec_093)
