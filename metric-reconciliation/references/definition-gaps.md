# Definition gaps: candidate causes, ranked by how often they explain a real gap

Read this at Step 2. The order matters: the first five explain most mismatches between a finance report and a product dashboard.

## 1. Population filter

**Looks like**: the gap is large, stable across periods, and roughly proportional to the total.
**Ask**: does one side count only paying users, only verified accounts, only users above a plan, or exclude a region?
**Prove it**: recompute with the filter removed; if the gap collapses, this is the cause.

## 2. Time window and timezone

**Looks like**: the gap moves with the calendar; it grows in periods with a boundary (month end, DST change, Sunday).
**Ask**: which timestamp is used (event time, order time, payment time, ingestion time), and is the window expressed in UTC, in local time, or in the finance close calendar?
**Prove it**: shift the cutoff by the offset and recompute; the amount explained equals the events that cross the boundary.

## 3. Late-arriving data

**Looks like**: the dashboard is lower than the warehouse for the most recent period, and the gap shrinks when the period is re-run later.
**Ask**: what is the ingestion lag, and was the report snapshot taken before backfill?
**Prove it**: compare the same period snapshot taken today with the one used in the report.

## 4. Refunds, cancellations and chargebacks

**Looks like**: finance is higher gross, lower net; product reports bookings while finance reports recognised revenue.
**Ask**: gross or net, and is the cancellation reflected in the period of the original sale or the period of the refund?
**Prove it**: sum refunds in the period and add or subtract as a single line.

## 5. Deduplication key

**Looks like**: the count is inflated on one side by a suspicious factor (1.1–1.5×), often with duplicates concentrated in one channel or device type.
**Ask**: deduped on user id, email, device, order, or nothing?
**Prove it**: count distinct keys on both sides; the difference is the duplicate mass.

## 6. Definition of the event itself

**Looks like**: the gap exists even with identical windows and populations.
**Ask**: is "active" a login, a session, a page view, a feature use, a payment, or any event? Is a session counted per 30 minutes idle or per day?
**Prove it**: compute the event count under both event definitions on the same raw table. Only one rule usually differs; size it.

## 7. Internal, bot and test traffic

**Looks like**: small consistent gap (1–5%), higher in low-traffic periods.
**Ask**: is there an internal-account list, a bot filter, an IP or user-agent filter, and does the other side apply it?
**Prove it**: mark internal and bot events and subtract; compare with the gap.

## 8. Trials, free tier, and comped accounts

**Looks like**: one side counts them, the other does not; gap matches the trial cohort size.
**Ask**: does the metric include trial users, and does it include comped or staff accounts?
**Prove it**: cohort the population by plan type and compare.

## 9. Currency and FX

**Looks like**: gap proportional to revenue in non-reporting currencies, and it changes when the rate date changes.
**Ask**: which rate (daily, monthly average, close), applied on which date, and are refunds converted at the original or the refund rate?
**Prove it**: recompute with a single rate for all periods; residual becomes stable.

## 10. Attribution and segment joins

**Looks like**: totals agree but segments do not, or the gap appears only in a channel or region breakdown.
**Ask**: which attribution model and window, and does the join keep or drop rows with no segment?
**Prove it**: compare row counts pre- and post-join; unmatched rows are the gap.

## 11. Restatements and period reassignment

**Looks like**: an older period's number changed between reports.
**Ask**: was anything restated, and is the report pulling the original or the restated figure?
**Prove it**: diff the two snapshots of the same period.

## Writing a gap that is not a gap

If the two numbers answer different questions — bookings vs recognised revenue, sessions vs users — they are not reconcilable and should not be forced into one line. Say so explicitly: "these are two metrics with similar names; the contract below separates them." That is a valid, and often the correct, verdict.
