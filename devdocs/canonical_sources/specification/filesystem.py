from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from devdocs.canonical_sources.specification.runtime_targets import (
    SPECIFICATION_PART as RUNTIME_TARGETS_SPEC,
)
from devdocs.canonical_sources.specification.selection import SPECIFICATION_PART as SELECTION_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, summary


@summary("filesystem boundary、link-like entry、non-regular entry の扱い。")
@canonical_source(
    "Filesystem boundary and entry types",
    filename="filesystem.md",
    order=80,
    merge_policy="local",
    heading="identity",
)
class SPECIFICATION_PART:
    class SPEC_088:
        r"""Configuration file directory は relative Configuration path の resolution anchor であり、すべての source をその配下へ閉じ込める共通 boundary ではない。"""

        level @= MUST

    class SPEC_089:
        r"""Runtime Target は対応する Scope root の direct child として解決する。Scope の `target_kind` は direct-child Target candidate の type filter であり、`"directory"` は directory、`"file"` は regular file、`"both"` はその両方を許可する。解決後の directory Target はその directory 自体を Selection boundary とし、file Target は regular file 自体を atomic source として扱い、その内部への Selection traversal は行わない。Scope root は Target candidate を探す base である。"""

        level @= MUST

    class SPEC_090:
        r"""Named Scope / Always source の明示 root location は relative / absolute `path` から host OS の通常の filesystem semantics で実在 directory を解決でき、symbolic link / Windows directory junction を含む location も root として利用できる。Always は解決した source directory 自体を selection boundary とする。Output location は source boundary に参加しない。"""

        level @= MUST

    class SPEC_091:
        r"""Directory source の include resolution と selected file は、その source directory 内へ限定する。File Target は Selection を行わず、その direct-child regular file 自体だけを Archive candidate とする。Archive に含める filesystem object は regular file に限定し、regular directory は Target root または traversal のためだけに扱う。Target discovery または Selection traversal で symbolic link として認識した entry は selectable entry とせず、リンク先を解決・走査せず、Archive にも含めない。Windows では directory junction も同じ link-like entry として扱う。File symlink、directory symlink、broken symlink、認識した Windows directory junction はいずれも traversal しない。FIFO、socket、device などその他の non-regular entry も Archive に含めず、directory として traversal しない。"""

        level @= MUST
        related @= (
            RUNTIME_TARGETS_SPEC.SECTION_502.SPEC_050,
            RUNTIME_TARGETS_SPEC.SECTION_503.SPEC_052,
            SELECTION_SPEC.SECTION_601.SPEC_077,
        )

    class SPEC_092:
        r"""Windows runtime では、directory junction として認識した entry を symbolic link と同じ link-like entry として扱い、自動走査しない。対応環境で安全な junction 判定を成立させられない場合は、通常 directory とみなして traversal を続けず error とする。この boundary は認識可能な symbolic link / directory junction を対象とし、platform に存在し得る未知の redirecting mechanism の完全な検出を保証しない。"""

        level @= MUST
        condition @= "Windows runtime で directory entry を自動走査する場合"

    class SPEC_093:
        r"""Selection traversal で認識して除外した **non-ignored** link-like entry は、同じ path を複数 pattern から観測しても1件として数える。`--preview` と通常 build は、除外した総件数を informational CLI note として表示する。Note の表示位置や exact wording は互換性契約に含めない。個々の link path は表示せず、Archive `README.md` にもこの runtime note を記録しない。`ignore` に一致した link-like entry と、directory `ignore` によって除外された subtree 内の entry は skipped-link count に含めない。"""

        level @= MUST
        condition @= "non-ignored link-like entry を Selection traversal で除外した場合"

    class SPEC_094:
        r"""この規則は source root から自動的に tree を探索するときに現れる entry に対するものであり、Configuration の `about.base`、named Scope `path`、Always `path`、Output `path` といった明示 filesystem path の resolution rule は Filesystem path notation と各 field 固有の規則に従う。特に named Scope / Always の root location は alias を利用できても、そこから先の Target discovery / Selection traversal が別の link-like entry をたどることを意味しない。生成した ZIP を展開するときの entry / filesystem object の解釈は extractor と platform に依存し、dirpluck は第三者の展開 software の動作を保証しない。"""

        level @= MUST
        related @= (PATHS_SPEC.SPEC_023, PATHS_SPEC.SPEC_024)
