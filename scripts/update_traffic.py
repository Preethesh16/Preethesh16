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


def sparkline(values, x=425, y=153, width=320, height=44):
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


def render_svg(total, recent, repo_count, daily, top_repos, updated):
    points = sparkline(daily)
    top_lines = []
    for index, (name, count) in enumerate(top_repos[:3]):
        y = 105 + index * 27
        safe_name = html.escape(name)
        top_lines.append(
            f'<text x="425" y="{y}" fill="#CBD5E1" font-size="12">{safe_name}</text>'
            f'<text x="745" y="{y}" fill="#A78BFA" font-size="12" '
            f'font-weight="700" text-anchor="end">{count}</text>'
        )
    top_markup = "".join(top_lines) or (
        '<text x="425" y="105" fill="#64748B" font-size="12">Waiting for clone data</text>'
    )

    return f"""<svg width="800" height="250" viewBox="0 0 800 250" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total} tracked clones across {repo_count} repositories">
<defs>
  <linearGradient id="card" x1="0" y1="0" x2="800" y2="250"><stop stop-color="#080D19"/><stop offset=".55" stop-color="#111827"/><stop offset="1" stop-color="#1A1033"/></linearGradient>
  <linearGradient id="accent" x1="28" y1="20" x2="770" y2="230"><stop stop-color="#22D3EE"/><stop offset=".52" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/></linearGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="5" result="b"/><feComposite in="b" in2="SourceGraphic" operator="over"/></filter>
</defs>
<rect x="1" y="1" width="798" height="248" rx="22" fill="url(#card)" stroke="#2B3651" stroke-width="2"/>
<rect x="24" y="24" width="5" height="202" rx="2.5" fill="url(#accent)" filter="url(#glow)"/>
<circle cx="750" cy="25" r="75" fill="#8B5CF6" fill-opacity=".07"/>
<g font-family="'Segoe UI', Ubuntu, Arial, sans-serif">
  <text x="52" y="48" fill="#94A3B8" font-size="12" font-weight="700" letter-spacing="2.2">ACCOUNT CLONE PULSE</text>
  <circle cx="243" cy="44" r="4" fill="#22C55E"/><text x="255" y="48" fill="#86EFAC" font-size="10" font-weight="700">LIVE</text>
  <text x="52" y="122" fill="#F8FAFC" font-size="58" font-weight="800">{total}</text>
  <text x="54" y="146" fill="#C4B5FD" font-size="12" font-weight="700" letter-spacing="1.1">OVERALL TRACKED CLONES</text>
  <text x="54" y="181" fill="#38BDF8" font-size="24" font-weight="800">{recent}</text>
  <text x="93" y="180" fill="#64748B" font-size="11">clones · last 14 days</text>
  <text x="54" y="211" fill="#A78BFA" font-size="20" font-weight="800">{repo_count}</text>
  <text x="87" y="210" fill="#64748B" font-size="11">repositories tracked</text>
  <line x1="384" y1="35" x2="384" y2="218" stroke="#27324A"/>
  <text x="425" y="52" fill="#E2E8F0" font-size="13" font-weight="700">TOP CLONED PROJECTS · TRACKED</text>
  {top_markup}
  <polyline points="{points}" fill="none" stroke="url(#accent)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
  <line x1="425" y1="202" x2="745" y2="202" stroke="#334155" stroke-dasharray="3 5"/>
  <text x="425" y="224" fill="#64748B" font-size="9">DAILY MOMENTUM ACROSS ALL REPOS</text>
  <text x="745" y="224" fill="#475569" font-size="9" text-anchor="end">updated {updated}</text>
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
