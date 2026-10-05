# Pre-1.0 compatibility tests

Everything in this directory exists only to protect compatibility behavior that is
explicitly scheduled for removal in 1.0.0.

Current coverage includes deprecated nested-array Selection references, legacy Pluck
Case syntax, Always Namespace compatibility semantics, and migration/deprecation warning
surfaces. Canonical tests should not use these forms merely as fixtures; use the current
canonical syntax instead.
