<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/filesystem.py` です。
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

# Filesystem boundary and entry types

## SPEC_088

Configuration file directory は relative Configuration path の resolution anchor であり、すべての source をその配下へ閉じ込める共通 boundary ではない。

level: MUST

## SPEC_089

Runtime Target は対応する Scope root の direct child として解決する。`target_kind = "directory"` の Target はその directory 自体を Selection boundary とし、`target_kind = "file"` の Target は regular file 自体を atomic source として扱い、その内部への Selection traversal は行わない。Scope root は Target candidate を探す base である。

level: MUST

## SPEC_090

Named Scope / Always source の明示 root location は relative / absolute `path` から host OS の通常の filesystem semantics で実在 directory を解決でき、symbolic link / Windows directory junction を含む location も root として利用できる。Always は解決した source directory 自体を selection boundary とする。Output location は source boundary に参加しない。

level: MUST

## SPEC_091

Directory source の include resolution と selected file は、その source directory 内へ限定する。File Target は Selection を行わず、その direct-child regular file 自体だけを Archive candidate とする。Archive に含める filesystem object は regular file に限定し、regular directory は Target root または traversal のためだけに扱う。Target discovery または Selection traversal で symbolic link として認識した entry は selectable entry とせず、リンク先を解決・走査せず、Archive にも含めない。Windows では directory junction も同じ link-like entry として扱う。File symlink、directory symlink、broken symlink、認識した Windows directory junction はいずれも traversal しない。FIFO、socket、device などその他の non-regular entry も Archive に含めず、directory として traversal しない。

level: MUST

related: [SPEC_050](runtime-targets.md#spec_050), [SPEC_052](runtime-targets.md#spec_052), [SPEC_077](selection.md#spec_077)

## SPEC_092

Python 3.11 でも Windows directory junction を判定できるよう、Windows では `lstat` が返す reparse tag を利用する。判定はひとつの内部 helper に集約し、Target discovery、Selection traversal、link-like entry を拒否する runtime filesystem check で同じ判定を使用する。Control document path の resolution にはこの link-like 判定を適用しない。対応対象の Windows runtime で junction 判定に必要な reparse-tag 定数または stat metadata を取得できない場合は、通常 directory とみなして traversal を続けず、safety boundary を確立できない error とする。これは既知の symbolic link / directory junction を扱うための safety boundary であり、platform に存在し得るすべての reparse point や未知の redirecting mechanism の完全な検出を保証しない。

level: MUST

condition: Windows runtime で directory junction を判定する場合

## SPEC_093

Selection traversal で認識して除外した **non-ignored** link-like entry は、同じ path を複数 pattern から観測しても1件として数える。`--preview` は contents tree の後に、通常 build は output path の後に、除外した総件数を CLI note として表示する。個々の link path は表示せず、Archive `README.md` にもこの runtime note を記録しない。`ignore` に一致した link-like entry と、directory `ignore` によって内部へ入る前に枝刈りされた subtree の entry は skipped-link count に含めない。

level: MUST

condition: non-ignored link-like entry を Selection traversal で除外した場合

## SPEC_094

この規則は source root から自動的に tree を探索するときに現れる entry に対するものであり、Configuration の `about.base`、named Scope `path`、Always `path`、Output `path` といった明示 filesystem path の resolution rule は Filesystem path notation と各 field 固有の規則に従う。特に named Scope / Always の root location は alias を利用できても、そこから先の Target discovery / Selection traversal が別の link-like entry をたどることを意味しない。生成した ZIP を展開するときの entry / filesystem object の解釈は extractor と platform に依存し、dirpluck は第三者の展開 software の動作を保証しない。

level: MUST

related: [SPEC_023](paths.md#spec_023), [SPEC_024](paths.md#spec_024)
