"""Render every graphic from fabricated data, so you can iterate on the design
without burning API calls or waiting for a real contribution history.

    python3 scripts/preview_mock.py

Writes the same filenames the real generator writes. Delete them (or run the
real generator) before committing, or you will publish invented numbers.
"""

import datetime as dt
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_stats as G  # noqa: E402
import svgkit as K  # noqa: E402


def fake_days(seed=7):
    rng = random.Random(seed)
    today = dt.date(2026, 8, 10)
    start = today - dt.timedelta(days=364)
    # Align to a Sunday so the week buckets look like GitHub's.
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)

    days = []
    date = start
    while date <= today:
        weekend = date.weekday() >= 5
        if rng.random() < (0.55 if weekend else 0.18):
            count = 0
        else:
            count = rng.choice([1, 1, 2, 3, 3, 5, 8, 11, 14, 21])
        days.append((date.isoformat(), count))
        date += dt.timedelta(days=1)
    return days


def fake_data():
    days = fake_days()
    current, longest = G.streaks(days)
    langs = [
        ("Python", 1840221), ("TypeScript", 1290110), ("Rust", 610455),
        ("Go", 388120), ("Shell", 141900), ("C", 96540),
        ("HTML", 74310), ("Lua", 31200), ("Nix", 12040), ("Makefile", 5100),
    ]
    return {
        "contrib": {
            "name": "Example Person",
            "login": "example",
            "followers": {"totalCount": 142},
            "contributionsCollection": {
                "totalCommitContributions": 1204,
                "totalPullRequestContributions": 168,
                "totalIssueContributions": 74,
                "totalPullRequestReviewContributions": 233,
                "contributionCalendar": {
                    "totalContributions": sum(c for _, c in days),
                    "weeks": [],
                },
            },
        },
        "days": days,
        "current": current,
        "longest": longest,
        "langs": langs,
        "langs_by_repo": {name: 3 + i for i, (name, _) in enumerate(langs)},
        "repo_count": 37,
        "stars": 1284,
    }


def main():
    data = fake_data()
    for name, draw in (("stats", G.draw_stats), ("streak", G.draw_streak),
                       ("langs", G.draw_langs), ("year", G.draw_year)):
        for theme in ("light", "dark"):
            filename = "%s.svg" % name if theme == "light" else "%s-dark.svg" % name
            path = os.path.join(K.ROOT, filename)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(draw(data, theme))
            print("  wrote %-18s %6.1f KB" % (filename, os.path.getsize(path) / 1024.0))
    print("\n  MOCK DATA. Do not commit these.")


if __name__ == "__main__":
    main()
