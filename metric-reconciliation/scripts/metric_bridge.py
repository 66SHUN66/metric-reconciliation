#!/usr/bin/env python3
"""Reconcile two versions of the same metric: definition diff, bridge, residual, memo.

Usage:
    python scripts/metric_bridge.py --input reconcile.json --out out/

Input JSON:
{
  "metric": "Monthly active subscribers",
  "period": "2026-10",
  "unit": "subscribers",
  "a": {"name": "Finance report", "total": 12450, "definitions": {...}},
  "b": {"name": "Product dashboard", "total": 13180, "definitions": {...}},
  "tolerance": {"type": "percent_of_a", "value": 0.5},
  "bridge": [{"cause": "refunds excluded on dashboard", "amount": -310, "evidence": "payments_refunds, Oct"}],
  "ruled_out": [{"cause": "bot traffic", "reason": "no bots in paid tier; checked user_agents"}]
}

Outputs (in --out):
  reconciliation_memo.md
  bridge.md
  audit.json
"""

import argparse
import json
import os


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            key = ("%s.%s" % (prefix, k)) if prefix else str(k)
            if isinstance(v, (dict, list)):
                out.update(flatten(v, key))
            else:
                out[key] = v
    elif isinstance(d, list):
        out[prefix or "(list)"] = json.dumps(d, ensure_ascii=False)
    else:
        out[prefix] = d
    return out


def fmt(n):
    if isinstance(n, float) and abs(n - round(n)) < 1e-9:
        return "%d" % round(n)
    if isinstance(n, float):
        return ("%.2f" % n).rstrip("0").rstrip(".")
    return str(n)


def pct(part, whole):
    if not whole:
        return "n/a"
    return "%.1f%%" % (100.0 * part / whole)


def md(s):
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    a = data.get("a") or {}
    b = data.get("b") or {}
    metric = data.get("metric", "the metric")
    period = data.get("period", "")
    tol_spec = data.get("tolerance", {"type": "absolute", "value": 0})
    if isinstance(tol_spec, (int, float)):
        tol_spec = {"type": "absolute", "value": float(tol_spec)}
    bridge = data.get("bridge") or []
    ruled_out = data.get("ruled_out") or []

    ta = float(a.get("total", 0) or 0)
    tb = float(b.get("total", 0) or 0)
    gap = tb - ta
    tol_type = (tol_spec.get("type") or "absolute").strip()
    tol_val = float(tol_spec.get("value", 0) or 0)
    if tol_type == "percent_of_a":
        tolerance = abs(ta) * tol_val / 100.0
    else:
        tolerance = abs(tol_val)

    da = flatten(a.get("definitions") or {})
    db = flatten(b.get("definitions") or {})
    keys = sorted(set(da) | set(db))
    diffs = []
    for k in keys:
        va = da.get(k, "UNKNOWN")
        vb = db.get(k, "UNKNOWN")
        same = str(va).strip().lower() == str(vb).strip().lower()
        diffs.append({"field": k, "a": va, "b": vb, "differs": not same})

    flags = []
    rows = []
    cum = 0.0
    for i, item in enumerate(bridge):
        cause = (item.get("cause") or "").strip()
        amount = item.get("amount")
        ev = (item.get("evidence") or "").strip()
        if isinstance(amount, str):
            try:
                amount = float(amount.replace(",", ""))
            except ValueError:
                flags.append({"level": "blocker", "code": "bad_amount",
                              "message": "item %d has a non-numeric amount: %r" % (i + 1, item.get("amount"))})
                amount = 0.0
        amount = float(amount or 0)
        if not cause:
            flags.append({"level": "warning", "code": "empty_cause",
                          "message": "item %d has no cause text" % (i + 1)})
        if not ev:
            flags.append({"level": "blocker", "code": "no_evidence",
                          "message": "cause '%s' has no evidence" % (cause or i + 1)})
        cum += amount
        rows.append({"cause": cause, "amount": amount, "evidence": ev,
                     "cumulative": cum, "share": pct(amount, gap)})

    explained = cum
    residual = gap - explained
    within = abs(residual) <= tolerance
    if not bridge and abs(gap) > tolerance:
        flags.append({"level": "blocker", "code": "no_bridge",
                      "message": "gap exceeds tolerance but no causes are listed"})
    if bridge and abs(gap) < 1e-9:
        flags.append({"level": "warning", "code": "zero_gap_with_causes",
                      "message": "the two totals are equal but causes are listed"})
    if abs(residual) > tolerance:
        flags.append({"level": "blocker", "code": "residual_over_tolerance",
                      "message": "residual %s exceeds tolerance %s" % (fmt(round(residual, 2)), fmt(round(tolerance, 2)))})
    if not any(d["differs"] for d in diffs):
        flags.append({"level": "warning", "code": "identical_definitions",
                      "message": "no definition field differs; look for a data-pipeline cause instead"})
    for k in keys:
        if k not in da or k not in db:
            flags.append({"level": "warning", "code": "undocumented_field",
                          "message": "field '%s' missing on one side (undocumented filter?)" % k})

    os.makedirs(args.out, exist_ok=True)

    lines = ["# Bridge - %s (%s)" % (metric, period), ""]
    lines.append("Direction: gap = B \u2212 A, where A = %s and B = %s." % (a.get("name", "A"), b.get("name", "B")))
    lines.append("")
    lines.append("| # | Cause | Amount | % of gap | Cumulative | Evidence |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        lines.append("| %d | %s | %s | %s | %s | %s |" % (
            i, md(r["cause"]), fmt(r["amount"]), r["share"], fmt(r["cumulative"]), md(r["evidence"])))
    lines.append("| | **Explained** | **%s** | %s | | |" % (fmt(explained), pct(explained, gap)))
    lines.append("| | **Gap** | **%s** | 100%% | | |" % fmt(gap))
    lines.append("| | **Residual** | **%s** | %s | | %s |" % (
        fmt(round(residual, 2)), pct(residual, gap), "within tolerance" if within else "OVER tolerance"))
    lines.append("")
    with open(os.path.join(args.out, "bridge.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    mem = ["# Reconciliation memo \u2014 %s, %s" % (metric, period), ""]
    sign = "above" if gap > 0 else "below"
    if within:
        verdict = ("%s reads %s, which is %s %s %s's %s \u2014 a %s difference. %d named causes account "
                   "for the whole gap; the residual of %s is inside the agreed tolerance of %s." % (
                       b.get("name", "B"), fmt(tb), fmt(abs(gap)), sign, a.get("name", "A"),
                       fmt(ta), pct(gap, ta), len(rows), fmt(round(residual, 2)), fmt(round(tolerance, 2))))
    else:
        verdict = ("%s reads %s, which is %s %s %s's %s. The gap is NOT closed: %d causes explain %s, "
                   "leaving an unexplained residual of %s against a tolerance of %s. Do not publish this "
                   "as reconciled." % (
                       b.get("name", "B"), fmt(tb), fmt(abs(gap)), sign, a.get("name", "A"), fmt(ta),
                       len(rows), fmt(explained), fmt(round(residual, 2)), fmt(round(tolerance, 2))))
    mem += ["## Verdict", "", "**%s**" % verdict, ""]

    mem += ["## Sources", "", "| Side | Source | Total | Unit |", "|---|---|---|---|"]
    mem.append("| A | %s | %s | %s |" % (md(a.get("name", "A")), fmt(ta), md(data.get("unit", ""))))
    mem.append("| B | %s | %s | %s |" % (md(b.get("name", "B")), fmt(tb), md(data.get("unit", ""))))
    mem.append("")

    mem += ["## Definition diff", ""]
    real_diffs = [d for d in diffs if d["differs"]]
    if real_diffs:
        mem += ["| Field | A | B |", "|---|---|---|"]
        for d in real_diffs:
            mem.append("| %s | %s | %s |" % (md(d["field"]), md(d["a"]), md(d["b"])))
    else:
        mem.append("No documented definition field differs. The cause is upstream of the definition: "
                   "pipeline, snapshot, or join. Fields marked UNKNOWN are undocumented rules \u2014 treat them as findings.")
    mem.append("")
    unknown = [d["field"] for d in diffs if str(d["a"]) == "UNKNOWN" or str(d["b"]) == "UNKNOWN"]
    if unknown:
        mem.append("**Undocumented on one side:** %s" % ", ".join(unknown))
        mem.append("")

    mem += ["## Bridge", "",
            "See `bridge.md`. Explained %s of %s (%s)." % (fmt(explained), fmt(gap), pct(explained, gap)), ""]

    if ruled_out:
        mem += ["## Ruled out", ""]
        for r in ruled_out:
            mem.append("- %s \u2014 %s" % (md(r.get("cause")), md(r.get("reason")))
        mem.append("")

    mem += ["## Residual and tolerance", "",
            "- Residual: %s (%s of the gap)" % (fmt(round(residual, 2)), pct(residual, gap)),
            "- Tolerance: %s (%s)" % (fmt(round(tolerance, 2)),
                                      ("%.1f%% of A" % tol_val) if tol_type == "percent_of_a" else "absolute units"),
            "- Status: %s" % ("reconciled within tolerance" if within else "NOT reconciled"),
            ""]

    mem += ["## Agreed definition going forward", "",
            "Fill from `assets/metric-contract-template.json`: population filter, event definition, window and "
            "timezone, timestamp used, dedup key, refund policy, currency and rate date, trial handling. "
            "Owner: _____  Effective from: _____", ""]

    mem += ["## Actions", "",
            "1. %s" % ("Confirm the contract above with both owners and store it where both pipelines can read it." if within
                       else "Return to the largest unexplained segment and size it before publishing any number."),
            "2. Add the row-count check between the two pipelines.",
            "3. Add a definition-diff alert if either definition lives in code.",
            ""]

    with open(os.path.join(args.out, "reconciliation_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(mem))

    audit = {
        "metric": metric, "period": period,
        "a_total": ta, "b_total": tb, "gap": gap,
        "explained": explained, "residual": round(residual, 2), "tolerance": round(tolerance, 2),
        "reconciled": within,
        "definition_diff_count": len(real_diffs),
        "flags": flags,
    }
    with open(os.path.join(args.out, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    print("metric: %s (%s)" % (metric, period))
    print("A=%s  B=%s  gap=%s" % (fmt(ta), fmt(tb), fmt(gap)))
    print("explained=%s  residual=%s  tolerance=%s  -> %s" % (
        fmt(explained), fmt(round(residual, 2)), fmt(round(tolerance, 2)),
        "RECONCILED" if within else "NOT RECONCILED"))
    print("definition fields differing: %d of %d" % (len(real_diffs), len(diffs)))
    for fl in flags:
        print("  [%s] %s: %s" % (fl["level"], fl["code"], fl["message"]))
    print("written: reconciliation_memo.md, bridge.md, audit.json in %s" % args.out)


if __name__ == "__main__":
    main()
