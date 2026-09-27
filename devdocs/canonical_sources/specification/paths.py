from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.specification import MUST, level
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary('Configuration と runtime input で使用する filesystem path notation。')


@canonical_source('Filesystem path notation', filename='paths.md', order=30, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_017:
        r"""Configuration / Invocation Template の TOML で filesystem location を表す field と、CLI の `--config PATH` / `-i PATH` / `--output PATH`、Python API の runtime `output` は、host OS に関係なく `/` を path separator として使用する。Backslash は separator として受理せず、Windows でも `/` を記述する。"""
        level @= MUST

    class SPEC_018:
        r"""
        Configuration 内の relative filesystem path は、field の種類や runtime state によって resolution base を切り替えず、**その field が記述されている Configuration file の directory**から解決する。少なくとも次の field にこの規則を適用する。

        ```text
        about.base
        scope.<name>.path
        always.<name>.path
        output.path
        output.timestamp.path
        ```
        """
        level @= MUST

    class SPEC_019:
        r"""Base chain の inner Configuration に記述された relative path は inner Configuration 自身の directory から解決し、outer Configuration の directory へ rebase しない。"""
        level @= MUST

    class SPEC_020:
        r"""Absolute path は host OS が完全な absolute path として認識する root form を `/` separator で記述し、その場所を直接参照する。例として POSIX host の `/opt/data`、Windows host の `C:/data` と `//server/share/data` を受理できる。別 OS の root form へ自動変換しない。Windows drive-relative form (`C:foo`) は absolute path として扱わない。"""
        level @= MUST

    class SPEC_021:
        r"""Filesystem-location notation では `~` expansion と environment-variable interpolation を行わず、glob を受理しない。`.` と `..` は field / option 固有の file / directory 条件を満たす範囲で通常の path component として解決する。Absolute path を使用した Configuration や CLI document selection は参照先 filesystem に依存し、OS 間 portability を保証しない。"""
        level @= MUST

    class SPEC_022:
        r"""CLI の `--config PATH` / `-i PATH` / `--output PATH` と Python API の runtime `output` は relative path の resolution base を runtime cwd とする。Invocation Template 内の default / named Invocation の `config` は Template document 自身の directory を基準にする。Configuration に記述された relative filesystem path resolution に runtime cwd を使用しない。"""
        level @= MUST

    class SPEC_023:
        r"""Configuration / Invocation Template **document 自体を選択または参照する path** は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path を特別に拒否しない。cwd の `default.dirpluck`、`--config PATH`、`-i PATH`、`about.base`、Invocation の `config` のいずれでも、dirpluck は選択・参照した path を symlink target の実体 path へ置き換えず、lexical な absolute document location として保持する。Relative document reference と、その document に記述された relative filesystem location はこの document location の directory を基準にする。Base-chain cycle detection のように file identity が必要な内部判定だけ、実体 path を用いて alias を同一 Configuration と認識する。"""
        level @= MUST

    class SPEC_024:
        r"""この control-document rule は source root resolution / source tree traversal の link handling とは別である。`[scope.<name>].path` と `[always.<name>].path` のように Configuration が明示する source root location は host OS の通常の filesystem semantics に従い、path の途中または最終 component が symbolic link / Windows directory junction であることだけを理由に拒否しない。明示 location を実在 directory に解決した後、その directory を source root / selection boundary とする。一方、その root から Dirpluck が Target discovery / Selection traversal を自動的に行う段階では Filesystem boundary and entry types の link-like entry rule に従い、認識した link-like entry を選択・走査しない。Include pattern、ignore pattern、archive path、CLI Target reference など filesystem location ではない値は、それぞれの規則に従う。"""
        level @= MUST
