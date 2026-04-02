#!/usr/bin/env python3
"""
Compare two k6 --summary-export JSON files side by side (terminal + HTML).

Interpreting x_cache_* rows:
  Your API only sends the ``X-Cache: HIT`` header on a cache hit; on a miss the
  header is absent, so k6 counts those as ``x_cache_not_hits``. A 0% hit rate
  means no response included ``X-Cache: HIT`` (all misses or failed requests).
  k6 may omit ``x_cache_hits`` from the JSON when the counter never incremented;
  this script displays that as 0.

Usage:
  python3 scripts/k6/compare_summaries.py \\
    scripts/k6/out/summary-staging.json scripts/k6/out/summary-production.json

  python3 scripts/k6/compare_summaries.py   # defaults to the two paths above

Writes: scripts/k6/out/compare-report.html (same directory as first file)
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any


def load_summary(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def metric(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    m = data.get("metrics", {}).get(name)
    return m if isinstance(m, dict) else None


def fmt_ms(ms: Any) -> str:
    if ms is None:
        return "—"
    try:
        v = float(ms)
    except (TypeError, ValueError):
        return "—"
    if v >= 1000:
        return f"{v:,.0f} ms ({v / 1000:.2f} s)"
    return f"{v:,.2f} ms"


def pct_from_rate(m: dict[str, Any] | None) -> str:
    if not m or "value" not in m:
        return "—"
    try:
        return f"{100.0 * float(m['value']):.2f}%"
    except (TypeError, ValueError, KeyError):
        return "—"


def counter_count(m: dict[str, Any] | None) -> str:
    if not m:
        return "—"
    if "count" in m:
        return str(int(m["count"]))
    return "—"


def counter_count_zero_if_absent(m: dict[str, Any] | None) -> str:
    """
    k6 often omits Counter metrics from --summary-export when the value stayed at 0.
    Treat missing as 0 so 'no hits' shows as 0, not an em dash.
    """
    if not m:
        return "0"
    if "count" in m:
        return str(int(m["count"]))
    return "0"


def build_rows(a: dict[str, Any], b: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Rows: (label, left, right)."""

    def dur_pair(name: str) -> list[tuple[str, str, str]]:
        ma, mb = metric(a, name), metric(b, name)
        rows_out: list[tuple[str, str, str]] = []
        for label, key in [
            ("avg", "avg"),
            ("p(95)", "p(95)"),
            ("median", "med"),
            ("max", "max"),
        ]:
            va = ma.get(key) if ma else None
            vb = mb.get(key) if mb else None
            rows_out.append(
                (f"{name} ({label})", fmt_ms(va), fmt_ms(vb))
            )
        return rows_out

    rows: list[tuple[str, str, str]] = [
        ("http_reqs (count)", counter_count(metric(a, "http_reqs")), counter_count(metric(b, "http_reqs"))),
        ("http_req_failed", pct_from_rate(metric(a, "http_req_failed")), pct_from_rate(metric(b, "http_req_failed"))),
    ]
    rows.extend(dur_pair("http_req_duration"))
    rows.append(
        (
            "x_cache_hit_rate (custom)",
            pct_from_rate(metric(a, "x_cache_hit_rate")),
            pct_from_rate(metric(b, "x_cache_hit_rate")),
        )
    )
    rows.append(
        (
            "x_cache_hits (custom)",
            counter_count_zero_if_absent(metric(a, "x_cache_hits")),
            counter_count_zero_if_absent(metric(b, "x_cache_hits")),
        )
    )
    rows.append(
        (
            "x_cache_not_hits (custom)",
            counter_count(metric(a, "x_cache_not_hits")),
            counter_count(metric(b, "x_cache_not_hits")),
        )
    )
    rows.append(
        (
            "iterations",
            counter_count(metric(a, "iterations")),
            counter_count(metric(b, "iterations")),
        )
    )
    return rows


def print_table(left_name: str, right_name: str, rows: list[tuple[str, str, str]]) -> None:
    w_label = max(len(r[0]) for r in rows)
    w_l = max(len(r[1]) for r in rows)
    w_r = max(len(r[2]) for r in rows)
    header = f"{'Metric':<{w_label}}  {left_name:<{w_l}}  {right_name:<{w_r}}"
    print(header)
    print("-" * len(header))
    for label, lv, rv in rows:
        print(f"{label:<{w_label}}  {lv:<{w_l}}  {rv:<{w_r}}")


def write_html(
    out_path: Path,
    left_name: str,
    right_name: str,
    left_file: str,
    right_file: str,
    rows: list[tuple[str, str, str]],
) -> None:
    esc = html.escape
    body_rows = []
    for label, lv, rv in rows:
        body_rows.append(
            f"<tr><td>{esc(label)}</td><td class='num'>{esc(lv)}</td><td class='num'>{esc(rv)}</td></tr>"
        )
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>k6 summary comparison</title>
  <style>
    :root {{
      --bg: #0f1419;
      --fg: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --border: #30363d;
      --row: #161b22;
    }}
    body {{
      font-family: ui-sans-serif, system-ui, sans-serif;
      background: var(--bg);
      color: var(--fg);
      margin: 0;
      padding: 1.5rem;
      line-height: 1.5;
    }}
    h1 {{ font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem 0; }}
    .meta {{ color: var(--muted); font-size: 0.875rem; margin-bottom: 1.25rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 56rem; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border: 1px solid var(--border); }}
    th {{ background: var(--row); color: var(--accent); font-weight: 600; }}
    tr:nth-child(even) td {{ background: #121820; }}
    td.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>k6 load test comparison</h1>
  <p class="meta">
    <strong>{esc(left_name)}</strong>: {esc(left_file)}<br/>
    <strong>{esc(right_name)}</strong>: {esc(right_file)}
  </p>
  <table>
    <thead>
      <tr><th>Metric</th><th>{esc(left_name)}</th><th>{esc(right_name)}</th></tr>
    </thead>
    <tbody>
      {''.join(body_rows)}
    </tbody>
  </table>
</body>
</html>
"""
    out_path.write_text(html_doc, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parent
    default_out = root / "out"
    ap = argparse.ArgumentParser(description="Compare two k6 summary JSON files.")
    ap.add_argument(
        "left",
        nargs="?",
        default=str(default_out / "summary-staging.json"),
        help="First summary JSON (e.g. staging)",
    )
    ap.add_argument(
        "right",
        nargs="?",
        default=str(default_out / "summary-production.json"),
        help="Second summary JSON (e.g. production)",
    )
    ap.add_argument(
        "--html",
        default="",
        help="Write HTML report to this path (default: <first file dir>/compare-report.html)",
    )
    ap.add_argument(
        "--left-label",
        default="Staging",
        help="Column label for first file",
    )
    ap.add_argument(
        "--right-label",
        default="Production",
        help="Column label for second file",
    )
    args = ap.parse_args()

    left_path = Path(args.left)
    right_path = Path(args.right)
    if not left_path.is_file():
        print(f"Missing file: {left_path}", file=sys.stderr)
        return 1
    if not right_path.is_file():
        print(f"Missing file: {right_path}", file=sys.stderr)
        return 1

    data_a = load_summary(left_path)
    data_b = load_summary(right_path)
    rows = build_rows(data_a, data_b)

    print()
    print_table(args.left_label, args.right_label, rows)
    print()

    html_out = Path(args.html) if args.html else left_path.parent / "compare-report.html"
    write_html(
        html_out,
        args.left_label,
        args.right_label,
        str(left_path),
        str(right_path),
        rows,
    )
    print(f"HTML report: {html_out}")
    print(f"  Open in a browser: file://{html_out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
