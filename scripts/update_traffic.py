#!/usr/bin/env python3
"""Track permanent clone history across every accessible GitHub repository."""

import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OWNER = "Preethesh16"
ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "traffic-history.json"
BADGE_PATH = ROOT / "traffic.json"
SVG_PATH = ROOT / "traffic.svg"
API_VERSION = "2022-11-28"


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def api_get(path, token):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "Preethesh16-traffic-tracker",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def owned_repositories(token):
    repositories = []
    page = 1
    while True:
        batch = api_get(
            f"/user/repos?affiliation=owner&visibility=all&per_page=100&page={page}",
            token,
        )
        repositories.extend(
            repo for repo in batch if repo["owner"]["login"].lower() == OWNER.lower()
        )
        if len(batch) < 100:
            return repositories
        page += 1


def sparkline(values, x=397, y=238, width=358, height=34):
    values = values or [0]
    peak = max(max(values), 1)
    step = width / max(len(values) - 1, 1)
    points = [
        f"{x + index * step:.1f},{y + height - (value / peak) * height:.1f}"
        for index, value in enumerate(values)
    ]
    if len(points) == 1:
        points.append(f"{x + width:.1f},{y + height:.1f}")
    return " ".join(points)


def compact_name(name, limit=22):
    """Keep long repository names inside the fixed-width SVG column."""
    return name if len(name) <= limit else name[: limit - 1] + "…"


def render_svg(total, recent, repo_count, daily, top_repos, updated):
    points = sparkline(daily)
    top_lines = []
    peak_repo = max((count for _, count in top_repos[:3]), default=1) or 1
    for index, (name, count) in enumerate(top_repos[:3]):
        y = 112 + index * 43
        bar_width = max(18, round(260 * count / peak_repo))
        safe_name = html.escape(compact_name(name))
        top_lines.append(
            f'<text x="397" y="{y}" fill="#526174" font-size="10" '
            f'font-weight="700">0{index + 1}</text>'
            f'<text x="429" y="{y}" fill="#D7E1EC" font-size="12" '
            f'font-weight="600">{safe_name}</text>'
            f'<text x="755" y="{y}" fill="#32D7FF" font-size="12" '
            f'font-weight="800" text-anchor="end">{count:,}</text>'
            f'<rect x="429" y="{y + 12}" width="260" height="3" rx="1.5" fill="#172333"/>'
            f'<rect x="429" y="{y + 12}" width="{bar_width}" height="3" rx="1.5" fill="#32D7FF"/>'
        )
    top_markup = "".join(top_lines) or (
        '<text x="397" y="112" fill="#64748B" font-size="12">Waiting for clone data</text>'
    )

    return f"""<svg width="800" height="320" viewBox="0 0 800 320" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total} tracked clones across {repo_count} repositories">
<defs>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
    <path d="M24 0H0V24" fill="none" stroke="#263244" stroke-opacity=".22"/>
  </pattern>
  <clipPath id="plot"><rect x="394" y="234" width="364" height="42" rx="4"/></clipPath>
</defs>
<rect x="1" y="1" width="798" height="318" rx="18" fill="#080D14" stroke="#263244" stroke-width="2"/>
<rect x="2" y="2" width="796" height="316" rx="17" fill="url(#grid)"/>
<path d="M1 18C1 8.6 8.6 1 18 1H782C791.4 1 799 8.6 799 18V66H1V18Z" fill="#0D141E"/>
<line x1="1" y1="66" x2="799" y2="66" stroke="#263244"/>
<rect x="1" y="66" width="4" height="188" fill="#32D7FF"/>
<g font-family="'Segoe UI', Ubuntu, Arial, sans-serif">
  <rect x="30" y="27" width="12" height="12" rx="2" fill="#32D7FF"/>
  <rect x="47" y="27" width="12" height="12" rx="2" fill="#32D7FF" fill-opacity=".3"/>
  <text x="75" y="38" fill="#E7EEF7" font-size="12" font-weight="800">PREETHESH / REPOSITORY INTELLIGENCE</text>
  <text x="75" y="51" fill="#526174" font-size="9">ACCOUNT-WIDE CLONE TELEMETRY</text>
  <rect x="683" y="22" width="82" height="28" rx="14" fill="#0A2428" stroke="#176273"/>
  <circle cx="701" cy="36" r="3" fill="#32D7FF"/>
  <text x="712" y="40" fill="#7DE9FF" font-size="9" font-weight="800">LIVE FEED</text>

  <text x="40" y="92" fill="#526174" font-size="9" font-weight="700">SYSTEM METRIC / 01</text>
  <text x="40" y="117" fill="#94A3B8" font-size="11" font-weight="700">TOTAL TRACKED CLONES</text>
  <text x="35" y="180" fill="#F8FAFC" font-size="68" font-weight="800">{total:,}</text>
  <line x1="40" y1="193" x2="348" y2="193" stroke="#263244"/>

  <rect x="40" y="211" width="145" height="61" rx="8" fill="#0D151F" stroke="#263244"/>
  <text x="56" y="239" fill="#32D7FF" font-size="21" font-weight="800">{recent:,}</text>
  <text x="56" y="257" fill="#64748B" font-size="9" font-weight="700">LAST 14 DAYS</text>
  <rect x="197" y="211" width="151" height="61" rx="8" fill="#0D151F" stroke="#263244"/>
  <text x="213" y="239" fill="#F8FAFC" font-size="21" font-weight="800">{repo_count:,}</text>
  <text x="213" y="257" fill="#64748B" font-size="9" font-weight="700">REPOSITORIES</text>
  <text x="40" y="297" fill="#526174" font-size="9">ARCHIVE ACTIVE / SINCE 29 JUL 2026</text>

  <line x1="373" y1="86" x2="373" y2="296" stroke="#263244"/>
  <text x="397" y="91" fill="#E7EEF7" font-size="12" font-weight="800">LEADERBOARD</text>
  <text x="755" y="91" fill="#526174" font-size="9" font-weight="700" text-anchor="end">CLONES</text>
  {top_markup}
  <line x1="397" y1="220" x2="755" y2="220" stroke="#263244"/>
  <text x="397" y="232" fill="#526174" font-size="8" font-weight="700">14-DAY SIGNAL</text>
  <g clip-path="url(#plot)">
    <line x1="397" y1="272" x2="755" y2="272" stroke="#263244" stroke-dasharray="3 6"/>
    <polyline points="{points}" fill="none" stroke="#32D7FF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <text x="755" y="297" fill="#526174" font-size="9" text-anchor="end">SYNC / {updated.upper()}</text>
</g>
</svg>
"""


def main():
    token = os.environ.get("TRAFFIC_TOKEN")
    if not token:
        raise SystemExit("TRAFFIC_TOKEN is required")

    history = load_json(HISTORY_PATH)
    repositories_history = history.setdefault("repositories", {})
    snapshots = {}
    failures = []

    repositories = owned_repositories(token)
    for repo in repositories:
        name = repo["name"]
        try:
            snapshots[name] = api_get(f"/repos/{OWNER}/{name}/traffic/clones", token)
        except urllib.error.HTTPError as error:
            failures.append(f"{name} ({error.code})")

    if not snapshots:
        raise SystemExit("No repository traffic was accessible. Check token permissions.")

    for name, traffic in snapshots.items():
        record = repositories_history.setdefault(
            name,
            {"baselineThrough": "", "baselineClones": 0, "days": {}},
        )
        cutoff = record.get("baselineThrough", "")
        days = record.setdefault("days", {})
        for item in traffic.get("clones", []):
            date = item["timestamp"][:10]
            if date > cutoff:
                days[date] = {
                    "clones": item["count"],
                    "unique": item["uniques"],
                }

    totals = {}
    for name, record in repositories_history.items():
        totals[name] = record.get("baselineClones", 0) + sum(
            day["clones"] for day in record.get("days", {}).values()
        )

    overall = sum(totals.values())
    recent = sum(snapshot["count"] for snapshot in snapshots.values())
    all_dates = sorted(
        {
            item["timestamp"][:10]
            for snapshot in snapshots.values()
            for item in snapshot.get("clones", [])
        }
    )
    daily = [
        sum(
            next(
                (
                    item["count"]
                    for item in snapshot.get("clones", [])
                    if item["timestamp"][:10] == date
                ),
                0,
            )
            for snapshot in snapshots.values()
        )
        for date in all_dates
    ]
    top_repos = sorted(totals.items(), key=lambda item: (-item[1], item[0].lower()))
    updated = datetime.now(timezone.utc).strftime("%b %d, %Y")

    history["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    history["accessibleRepositories"] = sorted(snapshots)
    if failures:
        history["inaccessibleRepositories"] = failures
        print("Skipped repositories: " + ", ".join(failures), file=sys.stderr)
    else:
        history.pop("inaccessibleRepositories", None)

    write_json(HISTORY_PATH, history)
    write_json(
        BADGE_PATH,
        {
            "schemaVersion": 1,
            "label": "overall tracked clones",
            "message": str(overall),
            "color": "8b5cf6",
        },
    )
    SVG_PATH.write_text(
        render_svg(overall, recent, len(snapshots), daily, top_repos, updated),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
