# 1.0 public contract tests

These tests exercise only supported external entry surfaces: the command-line interface
and the package-root Python API documented as public.

Internal module layout, intermediate models, parser objects, composition phases, and
private helper functions are not part of this suite's contract. A refactor that preserves
public behavior should not require these tests to know about the new internal IR.
