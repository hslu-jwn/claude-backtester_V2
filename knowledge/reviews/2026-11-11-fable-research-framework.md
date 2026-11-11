# Online idea-harvest framework (design, 2026-11-11, Claude Fable 5.2)

A design only: no research was done, no idea is rated here. Paths are relative to
`backtester-claude_V2/`. Numbers marked *(estimate)* are my guesses, to be replaced by measured
yields after the first batch. **UNVERIFIED** = not checked.

## The design in five lines

1. The internet is cut into small **tasks** (one source type x market x horizon x mechanism), kept in
   one CSV, so workers never overlap and coverage is visible.
2. A **web-capable cheap worker** (Codex terra; that route did the 2026-11-10 harvests) runs one task
   and returns ideas in a fixed JSON schema with a URL and a verbatim quote.
3. **Local scripts, zero tokens,** fetch every URL, check the quote is really on the page, drop
   duplicates and untestable ideas, and compute a score.
4. **Text-only cheap models** (Ollama, groq, openrouter, gemini-api) only work on text the script
   fetched (translate, fill the schema, tag red flags). They are never asked for sources: the
   2026-11-09 scans showed they invent citations.
5. **Opus** sees only the top of each batch, opens the sources itself, and turns the best into idea
   cards, screens and specs under the existing `continue-research` rules.

Files (new): under `research/harvest/`: `tasks.csv` (coverage), `raw/<task_id>.jsonl` (worker
output), `known_families.csv` (what is already tested); and `research/ledger.csv` (one row per
unique idea with its stage: the single count of everything tried, see the decisions at the end). One script, `tools/harvest.py`, with the subcommands
`plan`, `check`, `dedup`, `score`, `report` (about 300 lines, stdlib plus `requests`).

---

## 1. Source map

Signal-to-noise = usable, testable ideas per worker task *(estimate)*.

| Code | Sources | Example queries | Expected signal-to-noise |
|---|---|---|---|
| ACAD | SSRN, arXiv q-fin, NBER, journal pages, Google Scholar | `"intraday" "futures" "after transaction costs" 2019..2025`; `site:arxiv.org q-fin "month-end" rebalancing equity index`; `"out-of-sample" "post-publication" anomaly futures` | High on mechanism and rules, low on size: most effects are below our costs. About 1 idea per task. |
| CB | Central banks (BIS, Fed, ECB, BoE, BoJ, SNB), exchanges (CME, Eurex, JPX), index providers, clearing houses | `site:bis.org working paper FX "intraday" flows fixing`; `site:cmegroup.com settlement procedure "final settlement" equity index`; `MSCI index review effective date price pressure` | Few results, best mechanisms (who must trade, when). About 0.5-1 per task. |
| AGG | Curated lists: Quantpedia (free part), Alpha Architect, Quantocracy link archive, CXO Advisory summaries | `quantpedia futures calendar strategy`; `quantocracy "FX" "seasonality"`; `alpha architect "trend following" replication` | Highest per task, because someone already filtered. 2-3 per task. |
| BOOK | Books with tested rules that are not yet in `knowledge/books/` | `table of contents systematic trading futures rules backtest 2018..2025`; `"trading system" book chapter rules "sample code"` | Medium. Rules are precise, evidence is the author's own. About 1 per task. |
| BLOG | Practitioner quant blogs (found through Quantocracy), Substack, Medium | `"backtest" "after costs" index futures overnight blog`; `"I tested" "gold" strategy "out of sample"` | Medium-low. About 0.5 per task. Good for rule detail and honest failures. |
| GIT | GitHub repos and their READMEs, awesome-lists, papers-with-code style lists | `github awesome systematic trading strategies`; `github backtest forex strategy "walk forward" README` | Low for edges, high for exact rules and for links to papers. About 0.3 per task. |
| FORUM | ForexFactory, Elite Trader, futures.io, Trade2Win, MQL5 forum | `site:forexfactory.com "trading systems" "rules" "backtest" EURUSD`; `site:elitetrader.com "month end" index futures` | Very low: about 1 idea per 50-100 threads. Run a few tasks to measure, then decide. |
| REDDIT | r/algotrading, r/quant, r/Forex, r/Daytrading | `site:reddit.com/r/algotrading "stopped working" strategy costs`; `site:reddit.com/r/algotrading "edge" futures "calendar"` | Very low for ideas, useful for failure reports (why something dies live). |
| AV | YouTube and podcast transcripts (systematic-trader interviews) | `"Better System Trader" transcript strategy rules`; `"Top Traders Unplugged" transcript "short-term" futures` | Very low and costly to verify (a transcript must be fetched). Mechanisms, rarely rules. |
| BROKER | Prop-firm and broker pages: rules, banned strategies, swap, dividend and roll schedules, spread and session times | `FTMO "dividend" index CFD adjustment`; `CFD "rollover" futures "expiry" schedule oil`; `prop firm "prohibited strategies" list` | Not ideas but mechanics and cost facts (compare review B4, B5). High value per task for realism. |
| xx- prefix | Non-English versions of the above: `JA-`, `DE-`, `ZH-`, `FR-`, `ES-`, `RU-` | JA: `五十日 仲値 ドル円 検証`; `月末 リバランス 日経平均 アノマリー`. DE: `DAX Handelsstrategie Backtest Statistik "nach Kosten"`; `Hexensabbat DAX Statistik`. ZH: `恒生指数 午盘 统计 策略 回测` | Unknown. Possibly under-harvested: Gotobi, the only idea that passed all development gates, came from Japanese market practice. |

Rules for all sources: public pages only, no login, no paywall bypass, respect robots.txt, at most
one request per second per site, store only the URL and a quote of at most 300 characters, never
send repository content or account data anywhere.

---

## 2. Coverage plan

**Task key** = `SOURCE.MARKET.HORIZON.MECHANISM`, for example `ACAD.IDX-US.SWING.FLOW`.

| Dimension | Values |
|---|---|
| SOURCE (10 + language prefix) | ACAD, CB, AGG, BOOK, BLOG, GIT, FORUM, REDDIT, AV, BROKER; `JA-`, `DE-`, ... in front for another language |
| MARKET (7) | FX-MAJ, FX-CROSS (incl. JPY crosses), IDX-US, IDX-INTL (GER40, UK100, EU50, JP225, HK50, AUS200), METAL, ENERGY, CRYPTO |
| HORIZON (3) | INTRA (minutes to one session), SWING (1-10 days), POS (weeks and longer) |
| MECHANISM (8) | FLOW (forced or scheduled flows: rebalancing, fixing, settlement, expiry, auctions), EVENT (scheduled releases), CARRY (carry, term structure, financing), TREND, REVERSAL (liquidity provision), VOL (volatility state), CROSS (lead-lag, relative value), MICRO (session structure, broker and CFD mechanics) |

The full grid is about 1,700 cells per language; it is **not** enumerated. `harvest.py plan --n 20` writes the
next rows of `tasks.csv`:

- A cell's priority = source yield (measured, starts from the table above) x mechanism prior x
  market cost factor (cheap symbols first, from the cost table of 2026-11-09). 80 % of a batch goes
  to the best cells, 20 % to cells never tried, so yields are learned.
- Invalid cells are skipped by a small rule list (for example `BROKER.*.*.TREND`, `CRYPTO` with
  `POS` before 2019).
- Each task carries **3 fixed queries** built from templates for its cell, a cap of **5 ideas** and
  a time cap of 20 minutes. Small tasks keep weak models on track and make re-runs cheap.

**No overlap:** a task row is set to `running` with the worker's name before dispatch; queries are
derived from the cell, so two workers never get the same ones. Ideas found twice across cells are
merged later by the dedup step, and the second find raises `seen_count`.

**Tracking:** `tasks.csv` columns: `task_id, key, queries, status (open / running / done / empty /
failed), worker, run_date, n_raw, n_verified, n_kept`. `harvest.py report` prints a mechanism x
market table of done / empty / kept and the yield per source. A cell with two empty runs is closed
for six months.

---

## 3. Worker prompt template

One task per call. The three `{...}` blocks are filled by `harvest.py`; `{known_families}` is the
short list from section 4, step 5.

```text
You collect trading ideas from the web. You do not judge them.

TASK {task_id}: sources = {source_description}; market = {market}; holding time = {horizon};
mechanism = {mechanism_description}.
Run these searches: {query_1} | {query_2} | {query_3}

RULES
1. Open the page before you use it. Never cite a page you did not open.
2. Report an idea only if the page states a trading rule or a measurable price effect.
3. Copy one sentence from the page, word for word, that states the rule or effect ("quote").
4. Do not fill gaps. If the page does not give a value, write "not stated".
5. Skip ideas in this list: {known_families}
6. At most 5 ideas. If you find none, answer exactly: {"task_id": "{task_id}", "ideas": []}
7. No opinion on whether it makes money. No advice. Output JSON only, nothing else.

OUTPUT (one JSON object)
{"task_id": "{task_id}", "ideas": [{
  "name": "max 8 words",
  "claim": "one sentence: what the source says happens",
  "source_url": "the exact page you opened",
  "source_type": "paper | central_bank | book | blog | repo | forum | video | broker",
  "quote": "one sentence copied from the page, max 300 characters",
  "language": "en | de | ja | ...",
  "mechanism": "who trades and why, as the source says, or 'not stated'",
  "rules": {"market": "", "timeframe": "", "entry": "", "exit": "", "stop": "", "filters": ""},
  "not_stated": ["rule fields the source leaves open"],
  "claimed_result": "numbers and test period as stated, or 'not stated'",
  "required_data": ["price bars", "calendar of ...", "..."],
  "we_have": "yes | partly | no   (we have: 1-minute prices 2015-2026 for FX, gold, silver, oil, gas,
              major stock indices, BTC, ETH; Binance funding rates; a news schedule without values)",
  "red_flags": ["choose from: sells_course, no_test_period, single_example, tiny_sample,
                 needs_discretion, in_sample_only, costs_ignored, none"]
}]}
```

If the worker has no web access it must answer `{"task_id": "...", "error": "no web access"}`.

---

## 4. Filter pipeline (scripts first, in this order)

| Step | Check | Fails go to |
|---|---|---|
| 1 Schema | Valid JSON, all fields present, enums valid, quote ≤ 300 characters. | `failed` task, one re-run |
| 2 Source | The script fetches `source_url` itself: HTTP 200, not a login or paywall page; the quote is found in the page text (whitespace and case ignored, `difflib` ratio ≥ 0.9). Papers: DOI or arXiv ID resolves through the Crossref / arXiv API and the title matches. Video: only with a fetched transcript. | rejected `unverified_source` (counted per model, section 6) |
| 3 Seller | Domain block list plus words near the claim: course, enroll, signals group, discount code, affiliate, "funded account" coupon. | rejected `sells_course` |
| 4 Testable | Market maps to one of our symbols (SPX → US500, DAX → GER40, ...). Entry **and** exit are stated. No "discretion / feel / context / experience". | rejected `untestable` |
| 5 Dedup | (a) URL or DOI already in `knowledge/research/source_registry.csv` or `research/ledger.csv`. (b) Family match against `known_families.csv` (family, keywords, verdict), built once from `cost-wall.md` §1 and §4, `research/candidates/README.md`, the `knowledge/ideas.md` overview and `research_registry.csv`. (c) Among new ideas: same market and horizon and token overlap of entry + exit text ≥ 0.6. | merged, `seen_count + 1`; a match with a falsified family is rejected `known_family` |
| 6 Data | `required_data` against a fixed list of what the cache holds. | **parked** `needs_data` (kept: the list shows which data purchase would unlock most ideas) |
| 7 Mechanism | `mechanism` is "not stated". A practitioner's own explanation counts; a paper is not required (the user's rule of 2026-11-10 stays). | **parked** `no_mechanism` |
| 8 Hindsight | Red-flag words in claim or quote ("would have", "turned $", "never loses", win rate above 90 %), one chart as evidence, stated test under 2 years or under 30 trades. | rejected `hindsight`; `in_sample_only` and `costs_ignored` only lower the score |
| 9 Cost | Stop / hold class of the idea → cost in R from `knowledge/research/reports/2026-11-09_cost_in_R_table.md`. A stated move per trade below that cost, or an intraday rule with a stop under 0.5 daily ATR on a non-cheap symbol without a stated move. | rejected `cost_wall` |

Steps 3, 7 and 8 may use a text-only model on the fetched page text when the word lists are not
enough; steps 1, 2, 4, 5, 6 and 9 are plain code.

**Score (0-10, ranks attention only; it says nothing about profit):**

| Part | Points |
|---|---|
| Mechanism | forced or scheduled flow, or broker mechanics: 3; risk premium (carry, liquidity provision): 2; behavioural: 1 |
| Source | peer-reviewed, central bank, exchange: 2; working paper, book or blog with data and period: 1; forum, video: 0 |
| Rules | entry, exit and stop stated: 2; one missing: 1 |
| Cost headroom | stated move ≥ 3 x cost, or hold of hours and longer on a cheap symbol: 2; unknown: 1 |
| Found independently | on two or more different domains: 1 |
| Red flags | -1 each, at most -3 |

The top 10 of a batch (score ≥ 6) go to Opus. Everything else stays in `research/ledger.csv` with its reason.

---

## 5. Escalation

| Step | Who | Notes |
|---|---|---|
| Plan the batch, fetch pages, quote check, dedup, cost check, score, coverage report | Local scripts | zero tokens |
| Run search tasks | Codex `gpt-6.1-terra` low / medium, up to 2 in parallel (the routing rule); `ai_dispatch gemini` only if its web access works headless (**UNVERIFIED**) | read-only dispatch; one task = one call |
| Translate non-English page text, fill the schema from a fetched page, red-flag tags | `ai_dispatch local` (Ollama), then groq / openrouter `:free` / gemini-api | text in, text out; never asked to find sources |
| Second search of a cell with a high failure rate | a different search route than the first | no silent switch to a paid model |
| Read the top 10, open each source, final ranking, idea card in `knowledge/ideas.md`, skeptic pass, kill criteria, screen design, spec | Opus | as in the `continue-research` skill; Codex sol builds only after a passed screen |
| Approve | The user | the batch size and Codex share before a batch; any new data download or purchase; a new source type with terms-of-use risk; reviving parked ideas; the one-time MT5 test (existing rule). Specs need no approval (existing rule). |

Sonnet is not part of this pipeline (rule of 2026-11-10: small finishes only).

---

## 6. Quality guards

**Invented sources**
- The model never proves its own source. The script fetches the URL and finds the quote; no match,
  no idea.
- Two **canary tasks** in every batch: one with a known answer (the cell where Breedon & Ranaldo's
  FX local-hours paper must appear) and one nonsense cell that must come back empty. They give a
  recall rate and an invention rate per model.
- `unverified_source` is counted per model and source type. Above 20 %, that model is taken off that
  source type and its tasks of the batch are re-run on another route.
- Opus opens every source it relies on (existing rule); a spec cites only sources with
  `OPENED-FULL`, as the research reports already do.

**Multiple testing**
- `research/ledger.csv` is the single count: harvested / verified / kept / carded / screened / specced /
  development-passed / tested / confirmed. The numbers stand at the top of every batch report. Commit
  the file (review B7: today's trial log is not versioned).
- An idea gets its **kill criterion written into its row before any data is looked at**: what is
  measured, on which symbols and period, and the value that ends it.
- Screens and development runs use data before 2021-09-14 only (`--dev-only`; review B2 proposes
  making the test opt-in). Where pre-sample data exists, discover there and confirm on 2015-2021, as
  the calendar x clock screens did.
- A fixed **budget per batch**: at most 5 ideas go to a screen, picked by score before any result is
  seen. No rescue variants; a changed rule is a new row and a new count.
- The pass threshold rises with the count of screened ideas N in the family: |t| ≥ 3.0 up to 10,
  3.5 up to 50, 4.0 above (4.0 is what the 792-cell screen used). Every report states the expected
  number of false passes, N x alpha, next to the passes.
- A passed screen is a reason to write a spec, not a finding. Nothing is called profitable before
  the one-time test (umbrella `AGENTS.md`).

---

## 7. First batch: 20 tasks

Chosen for three reasons: (a) start where the cost wall leaves room (forced flows, moves stated in
bp per event, holds of hours to days); (b) touch every source type once so its yield is measured,
not guessed; (c) two canaries to measure the workers.

| # | Task key | Why first |
|---|---|---|
| 1 | AGG.IDX-US.SWING.FLOW | Curated lists give the most ideas per call; index flows are the best-documented forced flows. |
| 2 | AGG.FX-MAJ.SWING.CARRY | Same source, the cheapest symbols, holds long enough to dilute costs. |
| 3 | AGG.ENERGY.POS.CARRY | Term-structure effects are large per trade; shows what curve data would be needed. |
| 4 | ACAD.IDX-US.SWING.FLOW | Rebalancing, month- and quarter-end, index reviews: the direction is known before the trade. |
| 5 | ACAD.IDX-INTL.SWING.REVERSAL | Liquidity-provision reversals grow with volatility: few trades, large moves. |
| 6 | ACAD.FX-MAJ.INTRA.FLOW (2019+ only) | Only post-2015 evidence and replications: tells which known FX hour effects still exist. |
| 7 | ACAD.*.*.* "replication / post-publication / out-of-sample" | A meta task: papers that list which anomalies survived. Feeds `known_families.csv` and saves later tasks. |
| 8 | ACAD.METAL.SWING.EVENT | Gold and silver are under-covered in the records beyond clock and fix rules. |
| 9 | CB.FX-MAJ.INTRA.FLOW | BIS and central-bank work on fixings, settlement and month-end flows: best mechanisms. |
| 10 | CB.IDX-INTL.SWING.FLOW | Exchange and index-provider calendars (settlements, reviews, rolls): public dates, forced trades. |
| 11 | CB.FX-CROSS.SWING.FLOW | Japanese official and institutional flows (in English); the Gotobi area gave the one development pass. |
| 12 | JA-BLOG.FX-CROSS.INTRA.FLOW | Japanese practitioner sources on fixing days and month-end; likely under-harvested in English. |
| 13 | DE-BLOG.IDX-INTL.SWING.MICRO | German sources on DAX specifics (auctions, expiry days); GER40 is one of the cheapest symbols. |
| 14 | BROKER.IDX-INTL.SWING.MICRO | Dividend, financing and roll rules of index and oil CFDs: cost facts the engine lacks (review B4, B5). |
| 15 | BROKER.*.*.MICRO "prohibited strategies" | What prop firms ban shows which mechanics exist and which ideas are not allowed anyway. |
| 16 | BOOK.*.SWING.TREND | Books not yet in `knowledge/books/` with tested multi-day rules. |
| 17 | BLOG.IDX-US.SWING.VOL | Practitioner tests with stated periods and costs; measures the blog yield. |
| 18 | GIT.*.*.* awesome-lists | Mostly an index of papers and rule sets; measures the GitHub yield. |
| 19 | REDDIT.*.*.* "stopped working / failed live" + FORUM.FX-MAJ.SWING.FLOW (one call each, counted as one task) | Measures the noisiest sources cheaply and collects failure reports. |
| 20 | Canaries: ACAD.FX-MAJ.INTRA.FLOW "local hours" (known answer) and a nonsense cell | Recall and invention rate per model before trusting the other 18. |

Not in the first batch: AV (verification cost is high; decide after the yields are known), CRYPTO
(short development history and the highest costs), ZH sources (HK50 is the most expensive index here).

After the batch: `harvest.py report`, replace the yield estimates in section 1 by measured ones, and
let the planner pick batch 2.

---

## To turn this into a skill

- `.claude/skills/idea-harvest/SKILL.md`: sections 3, 5 and 6 of this file as the procedure, plus
  the commands `harvest.py plan | check | dedup | score | report`.
- `tools/harvest.py` with tests for the quote check, the dedup rules and the score (plain code, no
  network in tests: fetched pages as fixtures).
- `research/harvest/known_families.csv`: build once by hand from the four files named in step 5;
  this is the one piece that needs Opus, about an hour.
- Decided by the user, 2026-11-11: ideas without a stated mechanism are **parked**, not dropped
  (step 7 of the filter stays as written; they are counted and can be revived on the user's word).
- Decided by the user, 2026-11-11: **one file.** The harvest's idea list and the hypothesis ledger
  proposed in the review (A1) are the same file, `research/ledger.csv`. It holds every idea from
  "harvested" to "confirmed", so it also needs the review's columns (family, cells, development
  period, trades, gross / cost / net R per trade, gates, test spent, verdict, spec path). The
  hypotheses already run (strategies 1-14, hypotheses 1-15, C1-C3) are entered once by hand.
