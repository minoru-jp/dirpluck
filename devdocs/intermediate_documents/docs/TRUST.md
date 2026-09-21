<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `devdocs/canonical_documents/trust/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/intermediate_documents/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck Trust Model

この文書は、dirpluck の Configuration / Invocation Template と filesystem 操作をどの trust boundary で扱うかを説明します。正確な path resolution、selection、output semantics は `SPECIFICATION.md` を参照してください。

## Configuration は実行指示です

設定ファイルは、どの filesystem location から何を選び、どこへ Archive を書くかを宣言します。dirpluck は、その宣言が利用者の意図に対して適切か、参照先が機密か、description が実態と一致するかを推論しません。

Configuration を第三者から受け取った場合や、内容を自分で確認していない場合は、実行前に `about.base`、Scope、Always source、selection、Output を確認してください。Configuration は sandbox policy や capability manifest ではなく、dirpluck に渡す実行指示として扱います。

## Invocation Template も実行指示です

Invocation Templateは、使用する Configuration document、CLI Target reference、optional な default Case を default / named Invocation として保存した実行指示です。第三者から受け取った `.dirpluck-inv` document は、実行前に root `[invocation]` と使用予定の `[invocation.<name>]` にある `config`、`targets`、`case` を確認してください。`-e` / `--entry` は file 内の named Invocation を選び、CLI `--case` は選択した Invocation の `case` を上書きできます。

Named Invocation は root Invocation の差分ではなく独立しているため、選択した entry 自身の内容を確認してください。`config` の relative path は runtime cwd ではなく Invocation Template file 自身の directory を基準に解決し、`.dirpluck` suffix は省略できます。`config` を省略した場合は runtime cwd の `default.dirpluck` を使用します。CLI の `-i PATH` 自体は relative path なら runtime cwd 基準です。Configuration / Invocation Template document を選択・参照する path は host OS の通常の filesystem semantics に従うため、symbolic link / Windows directory junction を介した document も参照できます。Relative reference は選択した document path の directory を基準にするため、実行前に path と参照先の内容を確認してください。Invocation Template は Configuration の filesystem access capability を増やすものではありませんが、どの Configuration と Target を実行するかを選ぶため、信頼できない Template を無確認で実行しないでください。

## Filesystem permission が実際の権限境界です

dirpluck は OS の permission を越えて file を読む、または書く機能を持ちません。一方で、実行 user がアクセスでき、Configuration の path rules で参照できる場所は source や Output として指定できます。Relative `..` や absolute path も、そのための明示的な filesystem location です。

Relative filesystem path は runtime cwd ではなく、その field が記述された Configuration file の directory を基準に解決します。Base chain に含まれる Configuration もそれぞれ独自の anchor を持ちます。

Source boundary、archive path collision、Configuration schema、Output write-boundary overlap などの structural validation は行います。Configuration / Invocation Template document の参照と、Configuration が明示する named Scope / Always の source root location は host OS の通常の filesystem semantics に従い、alias を利用できます。一方、その明示 root からの Target discovery と Selection traversal では認識した symbolic link / Windows directory junction をたどらず Archive にも含めません。明示 location の resolution と source tree traversal は別の filesystem boundary です。FIFO、socket、device など regular file / regular directory ではない特殊 filesystem entry も Archive 対象にしません。これらは declared filesystem operation の目的や安全性を判定する guard ではありません。

## Selection の内容は利用者が決めます

Directory を `must` / `may` で選ぶと、その配下の regular file / directory が収集候補になります。`ignore` は name pattern に加えて Selection root からの `./...` concrete path reference も使え、dirpluck がその entry を selection 対象として扱わない明示指示として、link-like / special entry の種類による診断より優先します。Directory name ignore または directory path reference に一致した subtree は内部へ入る前に枝刈りし、ignored entry は skipped-link count や特殊 entry の diagnostic にも使いません。認識した non-ignored symbolic link / Windows directory junction は選択も traversal もせず Archive に含めません。FIFO、socket、device などその他の non-regular entry も Archive に含めません。`must` がそのような特殊 entry だけに一致した場合は理由付き error、`may` では optional missing とします。Hidden file、repository metadata、environment file、key material などを filename や内容から推論して自動 ignore することはありません。

Selection traversal 中に non-ignored link-like entry を認識して除外した場合、CLI の `--preview` と通常 build は除外件数を注記します。個々の path は列挙せず、ignored entry と `ignore` で走査前に枝刈りされた subtree 内の entry は count しません。

外部へ渡す Archive を作る場合は、Configuration の `must` / `may` / `ignore` と生成内容を、その用途に応じて確認してください。`--preview` は archive-relative な contents plan を確認するために利用できます。

## Link-like entry の検出限界

dirpluck が明示的に link-like entry として非 traversal 対象にするのは、platform API で symbolic link または Windows directory junction として認識できた entry です。それとは別に、regular file / regular directory として扱えない FIFO、socket、device などの特殊 filesystem entry も Archive 対象から除外します。Filesystem / OS には別種の reparse point、redirecting mechanism、特殊な filesystem object が存在し得るため、あらゆる環境で link-like mechanism や filesystem object の意味を完全に列挙・解釈し、Archive からの完全な不在を保証するものではありません。

この判定は source root からの自動 traversal 時に利用できる filesystem semantics に基づきます。Named Scope / Always の root location 自体を Configuration が明示している場合は、その location が alias であることだけを理由に拒否せず、host OS の通常の filesystem semantics で root を解決します。対応対象の Windows runtime で traversal 中の junction 判定に必要な reparse-tag API / metadata が取得できない場合、dirpluck はその entry を通常 directory として扱わず、安全に判定できないことを error として返します。将来別の mechanism を安全境界へ追加する場合も、dirpluck は認識対象を拡張できますが、未知の platform-specific behavior まで事前に保証しません。

また、生成した ZIP を展開するときに entry metadata や filesystem object をどのように解釈・作成するかは、利用する extractor と platform に依存します。dirpluck は第三者の unzip / archive software の展開時挙動を制御・保証しません。

## Output は宣言された policy に従います

Fixed Output の filename extension は ZIP format の判定には使いません。Configuration が指定した output location と `overwrite` policy に従って ZIP Archive を生成します。`overwrite = true` を指定した場合は、その fixed output path に存在する file を置き換える意図を明示したものとして扱います。省略時は `false` です。

Timestamp Output は Configuration が宣言した output directory の直下だけに dirpluck-generated filename を作ります。Base chain 上では Output の static write boundary が重ならないことを検証しますが、無関係な別 Configuration chain との filesystem ownership を発見・調停する仕組みではありません。

dirpluck は同じ output path を使う複数 process の lock や競合調停を行いません。`overwrite = false` や timestamp output の既存 destination check は、別 process に対する atomic な no-clobber guarantee ではありません。並行して実行される可能性がある場合は、呼び出し側で異なる output destination を割り当ててください。

Output file の permission は temporary-file implementation の固定 mode ではなく、host OS の通常の新規 file creation semantics に従います。POSIX では process `umask` が regular file creation mode に適用されます。`overwrite = true` で既存 file を置き換える場合も、既存 destination の mode を保存・継承せず、その run で新しく作成した Archive の mode を使用します。共有 group 向けなど特定の permission が必要な場合は、実行環境の `umask` や生成後の OS-level permission 設定で管理してください。

Output path と existing file の扱いは、実行前に Configuration で確認してください。

## Archive を外部へ渡すとき

生成されるアーカイブREADMEは、既定では source filesystem path を記録しません。`--paths` を指定した場合だけ、index に解決済み source directory を含めます。Absolute path など local environment の情報を含み得るため、外部へ渡す Archive で `--paths` を使う場合は内容を確認してください。

Archive 自体に含まれる file の selection は Configuration に従います。README から source path を隠すことは、Archive contents を検査または sanitize する機能ではありません。

## LLM-assisted work での位置付け

LLM-assisted work では、dirpluck は local filesystem 上の必要な材料を focused Archive として用意するために使えます。非 local の対話型 LLM へ upload したり、local agent 型の LLM が使う workspace へ配置したりする受け渡し物を作る用途です。

dirpluck 自体が LLM に local filesystem access を与える仕組みではなく、LLM が dirpluck を直接操作することも前提にしません。誰が Configuration を作成した場合でも、実行時の trust boundary は同じです。
