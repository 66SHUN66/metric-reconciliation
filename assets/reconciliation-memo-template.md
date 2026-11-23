# Reconciliation memo — template

Copy this file, rename it `<metric>_<period>_memo.md`, and fill it top to bottom. Delete a section only when it genuinely does not apply — never fill one with adjectives. Anything you cannot source goes in as `UNKNOWN` plus a question, not as a sentence.

Five rules to check before sending:

1. The verdict names the gap in units and as a percentage of one side.
2. Every bridge row carries an amount and an evidence pointer (query text or file path).
3. The residual is stated, not rounded away, and compared to a tolerance someone else agreed.
4. Ruled-out causes are written down with the reason, so the argument does not return next month.
5. The agreed definition has an owner and an effective date.

---

## 1. Verdict

> `<Side B>` reads `<gap>` (`<pct>%`) `<above|below>` `<Side A>` for `<period>`; `<n>` named causes account for `<sum>`, residual `<residual>` is `<within|outside>` the agreed tolerance of `<tolerance>`.

Status: `RECONCILED` / `PARTIAL — do not publish` / `NOT RECONCILABLE — split the metric`

## 2. Sources

| Side | Report | Source system / table | Extracted | Owner |
|---|---|---|---|---|
| A | `<report name>` | `<schema.table or file path>` | `<YYYY-MM-DD HH:MM>` | `<name, team>` |
| B | `<report name>` | `<schema.table or file path>` | `<YYYY-MM-DD HH:MM>` | `<name, team>` |

Sign-off needed from: `<name, role>`. Tolerance they accept: `<0.5% of A | N units>`.
Currency: `<USD, no conversion applied | rate X on YYYY-MM-DD>`.

## 3. Definition diff

| Field | A | B | Match |
|---|---|---|---|
| population_filter |  |  |  |
| event_definition |  |  |  |
| time_window / timezone |  |  |  |
| timestamp_used |  |  |  |
| dedup_key |  |  |  |
| refunds / cancellations |  |  |  |
| bot / internal traffic |  |  |  |
| trials / free tier |  |  |  |
| currency / FX date |  |  |  |

Mark `UNKNOWN` where the rule is not documented anywhere. Unknown is a finding, and it is the most common cause of a gap — do not infer it from the number.

## 4. Bridge

| # | Cause | Amount | % of gap | Cumulative | Evidence |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| | **Explained** |  |  |  |  |
| | **Gap** |  | 100% |  |  |
| | **Residual** |  |  |  |  |

Amounts are signed: a cause that pushes B up from A is positive, one that pulls it down is negative. A cause with no evidence pointer is not a cause — it is a hypothesis, and it belongs in section 5.

## 5. Ruled out

| Cause | Why it does not explain this gap | Checked |
|---|---|---|
|  |  | `<date, owner>` |

Keep this section. It is the cheapest defence against the same question next quarter.

## 6. Agreed definition, going forward

- Metric: `<name>` — `<one sentence: what it counts>`
- Population: `<paid subscribers only; excludes trials, comped, internal>`
- Event: `<one successful billing charge>`
- Window: `<calendar month, UTC>` · Timestamp: `<payment time>` · Dedup: `<subscription_id>`
- Refunds: `<net of refunds, refunded in the month>` · FX: `<no conversion; USD only>`
- Effective `<YYYY-MM-DD>` · Owner `<name, team>` · Build target `<both sides / one source of truth>`

## 7. Actions and monitoring

1. `<action>` — `<owner>`, by `<date>`
2. `<monitoring check: row-count parity | daily definition-diff alert>` — `<owner>`

## 8. Evidence index

| Ref | What it is | Where it lives |
|---|---|---|
| E1 |  | `<query text / file path / ticket id>` |

---

Notes on style that keep this usable:

- Numbers in tables, prose only for the verdict and the actions.
- No "approximately", "roughly", "some" in the bridge. Either you have the amount or the row is `UNKNOWN`.
- If a cause needs a paragraph to explain, it needs a second row instead.
- The memo is done when someone who disagrees with you can point at a row and say which amount they contest.
