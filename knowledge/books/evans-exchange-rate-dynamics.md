# Martin D. D. Evans, *Exchange-Rate Dynamics* (Princeton University Press, 2011)

Short: **ERD**. Cite by printed page. Read 2026-11-18 by Codex; PDF in the library folder Tier 2.

Evans examines exchange-rate determination through macroeconomic models and FX market microstructure. The relevant chapters explain how customer orders reach dealers, how interdealer trading distributes information, and how dealers adjust quotes and manage currency exposure (ERD pp. 302–303). Empirical chapters examine customer and interdealer flows at daily and intraday horizons, including reactions to macroeconomic releases (ERD pp. 310–313, 438–440, 456).

## Testable ideas

The book generally presents empirical relationships and mechanisms, rather than complete trading rules. Proposed entry and exit conditions below are explicitly **test hypotheses**, not rules claimed by the book.

- **Delayed FX response after an unexpected rate decision** (ERD pp. 438–440): In a single case, an unexpected Bundesbank rate increase on October 9, 1997 was followed by approximately **70 bp** of dollar depreciation against the deutschmark in two minutes and a further **40 bp** over the next two hours. Evans interprets the later move as dealers aggregating customer information through interdealer flow; subsequent intervention coincided with a reversal. A test hypothesis would enter in the initial move’s direction after the first two minutes and exit two hours after the announcement. It needs timestamped decisions, expectations and M1 FX prices; our venue is FX CFDs. This is a **single historical event**, not an estimated average return; the book gives no general entry rule or cost-adjusted size. **NEW**, as a specific post-decision continuation hypothesis.

- **Customer-segment flow and FX returns** (ERD pp. 311–313): Citibank EUR/USD customer flow was split into corporate, leveraged and unleveraged financial customers, with US and non-US segments, from April 1993 to June 1999. Segmented flows explained **19.5%** of weekly excess-return variation versus **5.4%** for aggregate flow. The proposed mechanism is that customer orders contain dispersed information passed through dealer trading. The book’s returns and flows cover the **same period**: it gives no forward entry, exit or bp return size. A prospective test would require timestamped, segmented customer-flow data and subsequent FX prices; our venue is FX CFDs. **NEW**, but proprietary flow availability and forward predictability are unresolved.

- **Dealer rebalancing after macro releases** (ERD pp. 453–456): Dealers may adjust quotes to induce customer orders that help share unwanted currency exposure after a release. In six years of EUR/USD data covering 43 US and German release variables, news affected some customer-flow segments for several days; in eight of ten cases with a significant initial spot-rate effect, it also significantly affected returns on at least one later day. The reported results are variance contributions, **not directional bp returns**. The book provides no executable entry or exit rule. Testing would need timestamped release surprises, segmented customer flows and subsequent daily FX prices; our venue is FX CFDs. **NEW**, but no size given for a tradable return.

- **Interdealer flow price impact** (ERD pp. 304–305): In DM/USD data from May through August 1996, the estimated contemporaneous relationship implies **0.54% per $1 billion** of net dollar purchases, using the sample’s average trade size. Dealers’ trades transmit information initially dispersed among customer orders (ERD pp. 302–304). The book found no evidence of a relationship with the previous day’s order flow, and supplies no forward trading rule (ERD p. 305). A test would need timestamped interdealer flow and subsequent FX prices; our venue is FX CFDs. **NEW**, as a flow mechanism, but the quoted size is contemporaneous rather than an available post-signal return.

## Method notes

- Align signal availability and returns carefully: the customer-flow regressions aggregate flow over the **same interval** as the return being explained (ERD p. 312).
- Split customer flows by type where data permit; aggregate single-bank flow can obscure relationships visible in disaggregated data (ERD pp. 311–313).
- Do not treat a segment’s regression coefficient as its causal price impact: flows are correlated across segments and through time, and the single-bank regression is not structural (ERD p. 313).
- Interdealer trade counts are only a proxy for value-weighted order flow when individual transaction sizes are unavailable (ERD p. 304).
- Overlapping weekly and monthly observations induce serial dependence; the cited study adjusts standard errors for the resulting moving-average process and heteroskedasticity (ERD p. 312).
- A release’s effect on return **variance** is not the same as a directional expected return; the persistence study reports the former (ERD pp. 456–457).

## Verdict

The post-decision continuation case has a plausible dealer-information mechanism and a stated **40 bp** subsequent move, making it the strongest candidate for an exploratory card—but the evidence is one event, and it does not establish a repeatable or cost-adjusted effect (ERD pp. 438–440). Customer-segment flow and dealer rebalancing merit mechanism notes, but the book supplies no forward bp return for them; the larger interdealer-flow estimate is contemporaneous and therefore cannot be treated as a trading payoff (ERD pp. 304–305, 311–313, 456).

