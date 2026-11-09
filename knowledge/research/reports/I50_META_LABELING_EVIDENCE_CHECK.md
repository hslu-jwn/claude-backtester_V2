# I-50 meta-labeling evidence check

Date: 2026-10-28  
Decision: park; do not use meta-labeling to rescue the locally failed strategies and do not create
a model or strategy draft.

## Question and result

I-50 proposes training a secondary model to trade or skip signals from strategies 2, 5, or 6 using
several signal-time features. The method can reduce false positives when a genuine primary signal
already exists. It cannot manufacture independent evidence for a base rule whose unconditional
expectancy failed. Each feature, transform, label barrier, model, hyperparameter, probability
threshold, and retraining schedule creates another selection path.

The bounded source search found methodological demonstrations but no independently replicated,
cost-aware evidence that the proposed small-sample V2 use reliably improves failed intraday CFD
signals out of sample. The current base strategies are specifically the wrong starting point:
their adverse results would make meta-labeling a same-data search for favorable pockets.

## Evidence inspected

- López de Prado, *Advances in Financial Machine Learning* (2018) and *Machine Learning for Asset
  Managers* (2020), meta-labeling chapters. The local source notes and an accessible full-text
  excerpt were inspected. They explain labels, purging, precision/recall, and bet sizing, but do
  not provide independent net-performance evidence for I-50's proposed base signals and data.
- Thumm, Barucca, and Joubert, *Ensemble Meta-Labeling*, Journal of Financial Data Science 5
  (2023), <https://doi.org/10.3905/jfds.2022.1.114>. Only the repository abstract/metadata was
  accessible. It reports that ensembles can improve regime extraction and false-positive
  modeling in nonlinear, multi-regime experiments. The accessible material does not establish
  after-cost improvement on a frozen executable trading rule or transferability to the V2 sample.
- Singh and Joubert, *Does Meta Labeling Add to Signal Efficacy?* (Hudson & Thames research post),
  <https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/>.
  The full post was opened. Its E-mini examples report higher classification precision and some
  risk-adjusted improvement, but it is not peer reviewed, is tied to a commercial software
  implementation, and does not establish a pre-registered trial count or transferable CFD costs.
- Zhang, Chang, Zhang, and Wang, *Evaluating Interpretable Meta-Labeling for Intraday Futures Trend
  Following* (SSRN working paper, 2026), <https://ssrn.com/abstract=7356724>. The abstract was
  indexed but the full paper endpoint was inaccessible. It uses five Chinese futures, six
  features, XGBoost, purged folds, two seeds, and a fixed 4-bp cost; its own title describes
  contract-dependent outcomes. It is a useful lead, not peer-reviewed validation.
- Rosa, *Understanding intraday momentum strategies*, Journal of Futures Markets 42 (2022),
  <https://doi.org/10.1002/fut.22375>. The publisher abstract and article metadata were opened.
  The original intraday momentum predictability disappears out of sample; a regime/threshold
  model improves the implementation. This illustrates both possible conditional structure and the
  central danger: the filter is a new model and trial, not proof that the original signal survived.

## Minimum future admissibility rule

Reconsider meta-labeling only after an immutable base strategy has positive net development
expectancy, adequate independent event count, and a mechanism that is not dominated by a few
trades. Before fitting anything, freeze:

1. one label definition aligned exactly with the base strategy's real stop/target/time exit;
2. a small feature list available at signal time, with no feature chosen from base-trade outcomes;
3. one model class, preprocessing pipeline, hyperparameter-search budget, calibration rule, and
   trade/skip threshold;
4. purged/embargoed nested development folds that respect overlapping horizons and correlated
   symbols;
5. every attempted feature/model/threshold in the multiplicity ledger;
6. comparison of unchanged base versus filtered base on identical signals and resolved costs;
7. minimum retained trade count, both-half stability, and concentration rejection.

The final holdout remains user-authorized and one-time. It may not be used repeatedly to choose
features, models, or thresholds. Higher F1, precision, or AUC is insufficient unless net R and
drawdown improve after actual costs without discarding nearly all signals.

## Current implication

Strategies 2, 5, and 6 do not qualify as positive frozen bases. I-49 volatility rank and the other
suggested I-50 features also lack an independently validated direction map. Keep I-50 parked; do
not reinterpret a failed base rule as an unlabeled machine-learning opportunity.

