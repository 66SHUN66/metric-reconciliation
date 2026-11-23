# Bridge methods: turning causes into numbers

## The arithmetic

Let A be the reporting side (usually finance or the official number) and B the challenger (dashboard, product, marketing). Define:

```
gap = B − A
residual = gap − Σ causes
```

Causes are signed: a cause that makes B larger than A is positive. Always define direction once and state it in the memo, because half of all reconciliation arguments are about sign conventions.

**Tolerance.** Take it from the sign-off owner: either an absolute unit count or a percentage of A. Put it in the memo verbatim. If |residual| ≤ tolerance the gap is "explained within tolerance"; otherwise the memo is not finished.

## Definition bridge (one rule at a time)

Recompute B with A's rule, changing exactly one rule per run:

```
effect_i = B(with rule i replaced by A's rule) − B(current)
```

Sum of effects over all differing rules should approach the gap. If two rules interact (a filter changes both population and dedup), run the combination and report the interaction separately rather than double-counting.

Report each effect with the query that produced it. A rule whose effect is smaller than the noise floor (say <1% of the gap) is not worth a row; mention it in "ruled out".

## Timing bridge

```
effect = count of events in one window and not the other
```

Three cases: (a) cutoff offset (timezone or close calendar), (b) event time vs ingestion time, (c) late arrivals after the snapshot. For (c) the amount is the backfill delta between the two snapshots of the same period.

## Population bridge

Cohort the metric by the contested attribute (plan, region, internal flag, bot flag) and compare cohort by cohort. The gap is usually one cohort plus a rounding difference in the rest; name the cohort rather than reporting a lump.

## Mix bridge (segments agree on total, disagree inside)

Decompose by segment s:

```
gap_s = B_s − A_s
```

If Σ gap_s over segments ≈ 0 while individual gaps are large, the two sides assign the same units to different segments — a join or attribution problem, not a volume problem. Report it as "allocation differs by segment", with the two largest swaps, and fix the join.

## Ratio and rate metrics

For rates (conversion, churn, ARPU) reconcile the numerator and the denominator separately, then show the rate effect:

```
rate_gap ≈ (Δnum / den_A) − (num_A / den_A²) * Δden
```

Do not reconcile a rate by bridging percentages; that double-counts the denominator change.

## Currency

Convert at one rate per period unless the policy says otherwise, state the rate and date, and keep refunds at the rate of the original transaction if accounting requires it. Changing the rate convention is itself a cause and gets a row.

## Sign-off package

1. Bridge table: cause, amount, % of gap, cumulative, evidence (query or file).
2. Residual and tolerance, with the verdict.
3. Definition contract going forward, with an owner and an effective date.
4. Two monitoring checks so the gap is caught before a board deck finds it.

## Common traps

- Bridging with percentages that were rounded to one decimal — rounding alone can exceed tolerance on small metrics.
- Using the same source twice as "independent evidence".
- Accepting a cause whose amount was estimated by subtraction (that is the residual wearing a cause's name).
- Letting the analyst pick the tolerance after seeing the residual.
