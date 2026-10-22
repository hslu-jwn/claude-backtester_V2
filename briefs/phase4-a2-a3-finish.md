# Brief: finish A2 + A3 (an unfinished attempt is in the working tree)

Another model started `briefs/phase4-a2-a3.md` and ran out of quota after 13 minutes. Its
uncommitted changes are in the working tree now (`git diff`, `git status`): files
`src/backtester/paths.py`, `data/cache.py`, `engine/costs.py`, `risk/monte_carlo.py`,
`risk/prop_rules.py`, tests `tests/test_paths.py`, `tests/risk/test_monte_carlo.py`,
`test_prop_rules.py`, `test_sizer.py`.

1. Review that partial work against `briefs/phase4-a2-a3.md`: keep what is correct and
   tested, fix or drop the rest (it was not reviewed). Make sure no existing test expectation
   was changed (compare with `git diff` of the test files) and no trading rule / default.
2. Then finish every remaining item of `briefs/phase4-a2-a3.md` the same way (test first).

Done = as in `briefs/phase4-a2-a3.md`. Run the full suite with output redirected to a file
(this PC's terminal stalls unread output). Report per finding: done by whom (kept / fixed /
new), test name, files.
