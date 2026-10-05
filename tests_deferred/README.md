# Deferred tests during the 1.0 refactor

These tests are intentionally excluded from normal `tests/` discovery.

- `pending_1_0/` is reserved for already-decided 1.0 contract behavior not yet implemented.
  It is currently empty; promote tests into `tests/contract/` as soon as the implementation satisfies them.
- `legacy_behavior/` preserves executable examples of behavior deliberately removed from
  the 1.0 contract. Once the implementation stops providing that behavior, these tests are
  expected to fail and must not be treated as an active regression suite.
