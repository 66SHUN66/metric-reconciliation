# metric-reconciliation

> Agensi listing (free): https://agensi.io/skills/metric-reconciliation-why-two-numbers-disagree

An agent skill for the meeting where two reports show different numbers. It writes both definitions down, diffs them field by field, sizes every cause into a bridge, and publishes a memo with an unexplained-residual verdict.

The rule it enforces: a cause without an amount and a source is not a cause, and a gap whose residual exceeds the agreed tolerance is not reconciled.

## Files

```
SKILL.md                                workflow, contract, output format
references/definition-gaps.md           11 candidate causes, ranked, each with the query that proves it
references/bridge-methods.md            definition / timing / population / mix bridges, rate metrics, currency, traps
assets/metric-contract-template.json    a filled contract to drop into a repo
scripts/metric_bridge.py                reconcile.json -> memo + bridge + audit
```

## Quick start

```bash
python scripts/metric_bridge.py --input reconcile.json --out out/
```

`reconcile.json`:

```json
{
  "metric": "Monthly active subscribers",
  "period": "2026-10",
  "a": {"name": "Finance report", "total": 12450, "definitions": {...}},
  "b": {"name": "Product dashboard", "total": 13180, "definitions": {...}},
  "tolerance": {"type": "percent_of_a", "value": 0.5},
  "bridge": [{"cause": "refunds not subtracted", "amount": 310, "evidence": "payments_refunds, Oct"}],
  "ruled_out": [{"cause": "bot traffic", "reason": "paid tier only, 0 automated sessions"}]
}
```

Outputs `reconciliation_memo.md` (verdict, definition diff, bridge, ruled-out list, residual, agreed definition), `bridge.md` (running table), `audit.json`.

## Boundaries

Does not decide which team is right or guess a cause. Does not accept an amount estimated by subtraction. Does not change production definitions: it proposes a contract and the owner approves.

## License

MIT
