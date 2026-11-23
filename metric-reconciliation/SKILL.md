---
name: metric-reconciliation
description: Explains why two reports of the same metric disagree, and closes the gap with evidence. Builds a metric contract, diffs the two definitions field by field, decomposes the difference into causes (population, timing, dedup, refunds, FX, attribution, bot filtering), and issues a reconciliation memo with an unexplained residual called out. Use when the user says the numbers do not match, two dashboards show different values, finance and product disagree, a board deck number is challenged, a metric dropped or jumped without explanation, or they need a single agreed definition before building a report. Not for forecasting, causal analysis, or building the dashboard itself.
---

# Metric Reconciliation

Two numbers disagree. The answer is almost never "one team is wrong" — it is that the two numbers are computed on different populations, at different times, with different rules. The job is to name each difference, size it, and leave nothing unexplained.

## Contract

1. **Reconcile before you explain.** Write both definitions down and diff them field by field first. Jumping to "seasonality" or "a data bug" before the diff is how gaps stay open.
2. **Numbers, not adjectives.** Every cause carries an amount and a source. "Some refunds" is not a cause; "refunds: 310 units, from the payments table, Oct 1–31" is.
3. **Residual is the deliverable.** The gap minus all explained causes is the most important number in the memo. A memo without a residual is a story, not a reconciliation.
4. **Tolerance is agreed, not chosen by the analyst.** Ask who will sign off and what they will accept (often 0.5% or a fixed unit count). State it in the memo.
5. **One definition wins, and it is written down.** After reconciliation the metric gets a contract: population, event, window, timezone, dedup key, currency and rate date. Both sides build to it, or the difference is documented as intentional.

## Workflow

### Step 0 — Fix the frame

Record: the exact metric name on both sides, the period, the granularity (total / segment / daily), the currency or unit, the two sources with their owners, and who needs to sign off. Ambiguity here produces a memo that reconciles the wrong pair of numbers.

### Step 1 — Write both definitions (the contract diff)

Express each side as a definition object using `assets/metric-contract-template.json`. Fill only what is known; unknown fields become `UNKNOWN` and are themselves findings — an undocumented filter is the most common cause of a gap.

Fields that matter most: population filter, event definition, time window and timezone, timestamp used (event time vs ingestion time), deduplication key, currency and FX date, refunds/cancellations, bot/internal traffic, attribution window, whether trials or free tier count, segment joins and their filters.

### Step 2 — Diff and rank candidate causes

```bash
python scripts/metric_bridge.py --input reconcile.json --out out/
```

The script reports the definition diff and reserves space for the bridge. Read `references/definition-gaps.md` for the candidate-cause list ordered by how often each one actually explains a gap, with the query pattern that proves or kills it.

Rule: size candidates before investigating them. A definition difference that can move at most 2% of the total does not explain a 30% gap; stop chasing it.

### Step 3 — Size each cause with evidence

For each candidate, produce an amount and a source. Use `references/bridge-methods.md` for the standard decompositions:

- **Definition bridge**: recompute one side using the other side's rule, one rule at a time. The delta from each single-rule change is the cause's amount.
- **Timing bridge**: move the cutoff (event time vs ingestion time, timezone, late-arriving data). Amount = events that fall in one window but not the other.
- **Population bridge**: add/remove the excluded cohort (internal, bots, cancelled, trial) and measure.
- **Mix bridge**: if the totals are close but segments are not, decompose by segment and show where the mix diverges.

Every cause that survives gets a row in `bridge`. Causes that were investigated and ruled out go in the memo's "ruled out" list with the reason — that list is what stops the same argument next month.

### Step 4 — Close the residual

`residual = gap − sum(causes)`. If |residual| exceeds the agreed tolerance, do not publish a partial story. Either the causes are incomplete or one amount is wrong; return to Step 3 with the largest unexplained segment. A residual under tolerance is reported as "unexplained, within tolerance" — never rounded to zero silently.

### Step 5 — Ship the memo

Deliver `reconciliation_memo.md` from the script, then complete it by hand: one-line verdict at the top ("dashboard is 730 lower than finance, 100% explained by refunds and ingestion lag"), the definition diff, the bridge table, the ruled-out list, the residual and tolerance, and the agreed definition going forward with an owner and a date.

### Step 6 — Prevent the next gap

Hand back a metric contract (from `assets/metric-contract-template.json`, filled) plus one or two monitoring checks: a row-count check between the two pipelines, and a daily definition-diff alert if the two definitions are stored in code.

## Output format

- Memo: verdict line, then sections — Sources, Definition diff, Bridge, Ruled out, Residual, Agreed definition, Owner and date. Numbers in a table; prose only for the verdict and the actions.
- Every number in the memo is traceable to a query or a file; put the query text or file path in an "Evidence" column, not in a footnote.
- Currency: state the rate and the date used, or state that no conversion was applied.
- Do not present a reconciliation as complete while the residual exceeds tolerance.

## Boundaries

- Does not guess which side is "right". It shows which rules differ and what each costs.
- Does not run the warehouse queries itself unless the user provides access and asks; it writes the queries and interprets the results.
- Does not change production definitions or dashboards. It proposes the contract and the owner approves it.
- Not a forecasting or causal-attribution tool: a reconciled gap explains the past, it does not explain why users behave differently.
