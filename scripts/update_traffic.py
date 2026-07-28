#!/usr/bin/env python3
"""Merge GitHub's rolling traffic window into permanent clone history."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "traffic-history.json"
BADGE_PATH = ROOT / "traffic.json"
SVG_PATH = ROOT / "traffic.svg"


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sparkline(values, x=484, y=111, width=242, height=42):
    if not values:
        values = [0]
    peak = max(max(values), 1)
    step = width / max(len(values) - 1, 1)
    points = []
    for index, value in enumerate(values):
        px = x + index * step
        py = y + height - (value / peak) * height
        points.append(f"{px:.1f},{py:.1f}")
    if len(points) == 1:
        points.append(f"{x + width:.1f},{y + height:.1f}")
    return " ".join(points)


def render_svg(total, recent_total, recent_unique, values, updated):
    points = sparkline(values)
    return f"""<svg width="800" height="210" viewBox="0 0 800 210" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total} all-time tracked repository clones">
<defs>
  <linearGradient id="card" x1="0" y1="0" x2="800" y2="210" gradientUnits="userSpaceOnUse">
    <stop stop-color="#0B1020"/><stop offset=".52" stop-color="#111827"/><stop offset="1" stop-color="#17102E"/>
  </linearGradient>
  <linearGradient id="accent" x1="54" y1="0" x2="744" y2="0" gradientUnits="userSpaceOnUse">
    <stop stop-color="#22D3EE"/><stop offset=".52" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/>
  </linearGradient>
  <linearGradient id="chart" x1="484" y1="111" x2="726" y2="153" gradientUnits="userSpaceOnUse">
    <stop stop-color="#22D3EE"/><stop offset="1" stop-color="#A855F7"/>
  </linearGradient>
  <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="8" result="blur"/><feComposite in="blur" in2="SourceGraphic" operator="over"/>
  </filter>
</defs>
<rect x="1" y="1" width="798" height="208" rx="22" fill="url(#card)" stroke="#283451" stroke-width="2"/>
<rect x="28" y="25" width="5" height="160" rx="2.5" fill="url(#accent)" filter="url(#glow)"/>
<circle cx="738" cy="39" r="52" fill="#8B5CF6" fill-opacity=".08"/>
<circle cx="75" cy="184" r="64" fill="#22D3EE" fill-opacity=".05"/>

<g font-family="'Segoe UI', Ubuntu, Arial, sans-serif">
  <text x="55" y="52" fill="#94A3B8" font-size="13" font-weight="700" letter-spacing="2.4">REPOSITORY PULSE</text>
  <circle cx="258" cy="47" r="4" fill="#22C55E"/>
  <text x="270" y="52" fill="#86EFAC" font-size="11" font-weight="600">LIVE</text>

  <text x="53" y="126" fill="#F8FAFC" font-size="58" font-weight="800">{total}</text>
  <text x="55" y="151" fill="#C4B5FD" font-size="13" font-weight="700" letter-spacing="1.2">ALL-TIME TRACKED CLONES</text>
  <text x="55" y="177" fill="#64748B" font-size="11">tracking since Jul 29, 2026</text>

  <text x="420" y="53" fill="#E2E8F0" font-size="14" font-weight="700">LAST 14 DAYS</text>
  <text x="420" y="82" fill="#38BDF8" font-size="22" font-weight="800">{recent_total}</text>
  <text x="466" y="81" fill="#64748B" font-size="11">clones</text>
  <text x="560" y="82" fill="#C084FC" font-size="22" font-weight="800">{recent_unique}</text>
  <text x="606" y="81" fill="#64748B" font-size="11">unique cloners</text>

  <line x1="420" y1="96" x2="746" y2="96" stroke="#27324A"/>
  <polyline points="{points}" fill="none" stroke="url(#chart)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
  <line x1="484" y1="158" x2="726" y2="158" stroke="#334155" stroke-dasharray="3 5"/>
  <text x="420" y="178" fill="#64748B" font-size="10">DAILY CLONE MOMENTUM</text>
  <text x="746" y="178" fill="#475569" font-size="10" text-anchor="end">updated {updated}</text>
</g>
</svg>
"""


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: update_traffic.py <github-traffic-response.json>")

    traffic = load_json(Path(sys.argv[1]))
    history = load_json(HISTORY_PATH)
    cutoff = history["baselineThrough"]
    days = history.setdefault("days", {})

    for item in traffic.get("clones", []):
        date = item["timestamp"][:10]
        if date > cutoff:
            days[date] = {"clones": item["count"], "unique": item["uniques"]}

    total = history["baselineClones"] + sum(day["clones"] for day in days.values())
    recent = traffic.get("clones", [])
    values = [item["count"] for item in recent]
    updated = datetime.now(timezone.utc).strftime("%b %d, %Y")

    write_json(HISTORY_PATH, history)
    write_json(
        BADGE_PATH,
        {
            "schemaVersion": 1,
            "label": "all-time tracked clones",
            "message": str(total),
            "color": "8b5cf6",
        },
    )
    SVG_PATH.write_text(
        render_svg(total, traffic["count"], traffic["uniques"], values, updated),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
