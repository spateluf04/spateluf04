"""Draw stats.svg, streak.svg, langs.svg and year.svg from the GitHub GraphQL
API. Runs nightly in Actions.

Standard library only, on purpose. A dependency install is one more thing that
can break in CI at 05:17 UTC while you are asleep.

Two determinism traps are handled here. Both cost real time to find, and both
produce a nightly stream of meaningless commits if you miss them:

  1. The contribution window is pinned to whole UTC days. Left alone,
     contributionsCollection measures "the past year" from the moment of the
     request, so two runs minutes apart bucket days into different weeks and
     shift the sparkline by a fraction of a pixel. Enough to look changed
     every night, forever.

  2. Repositories are filtered to public only. Your personal token sees
     private repos and the workflow's token does not, so without the filter
     the language percentages disagree depending on who ran the script.

Nothing here writes a timestamp into the output. If the numbers did not
change, the bytes do not change, and the workflow skips the commit.
"""

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgkit as K  # noqa: E402

API = "https://api.github.com/graphql"
W = 860  # every graphic is this wide, so the README column stays straight

TOP_LANGS = 8
SPARK_WEEKS = 52


# --------------------------------------------------------------------------
# api
# --------------------------------------------------------------------------

def graphql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "profile-stats",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        sys.exit("GraphQL HTTP %s: %s" % (exc.code, exc.read().decode()[:400]))

    if "errors" in payload:
        sys.exit("GraphQL error: %s" % json.dumps(payload["errors"])[:400])
    return payload["data"]


CONTRIB_QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

REPO_QUERY = """
query($login:String!, $after:String) {
  user(login: $login) {
    repositories(first: 100, after: $after, privacy: PUBLIC, isFork: false,
                 ownerAffiliations: OWNER,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def utc_window(today):
    """Whole UTC days, 365 of them inclusive. This is trap number one."""
    start = today - dt.timedelta(days=364)
    return (start.strftime("%Y-%m-%dT00:00:00Z"),
            today.strftime("%Y-%m-%dT23:59:59Z"))


def fetch(login, token, today):
    frm, to = utc_window(today)
    contrib = graphql(CONTRIB_QUERY, {"login": login, "from": frm, "to": to}, token)["user"]

    repos, cursor = [], None
    total_repos = 0
    while True:
        page = graphql(REPO_QUERY, {"login": login, "after": cursor}, token)["user"]["repositories"]
        total_repos = page["totalCount"]
        repos.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return contrib, repos, total_repos


# --------------------------------------------------------------------------
# derived numbers
# --------------------------------------------------------------------------

def flatten_days(calendar):
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    days.sort()
    return days


def streaks(days):
    """Current streak counts back from today, or from yesterday if today is
    still empty. A day you have not finished yet should not break the run."""
    longest = {"length": 0, "start": None, "end": None}
    run_len, run_start = 0, None

    for date, count in days:
        if count > 0:
            run_len += 1
            run_start = run_start or date
            if run_len > longest["length"]:
                longest = {"length": run_len, "start": run_start, "end": date}
        else:
            run_len, run_start = 0, None

    current = {"length": 0, "start": None, "end": None}
    idx = len(days) - 1
    if idx >= 0 and days[idx][1] == 0:
        idx -= 1  # today not started yet
    end = days[idx][0] if idx >= 0 and days[idx][1] > 0 else None
    while idx >= 0 and days[idx][1] > 0:
        current["length"] += 1
        current["start"] = days[idx][0]
        idx -= 1
    current["end"] = end
    return current, longest


def language_totals(repos):
    by_bytes, by_repo = {}, {}
    for repo in repos:
        seen = set()
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            by_bytes[name] = by_bytes.get(name, 0) + edge["size"]
            if name not in seen:
                by_repo[name] = by_repo.get(name, 0) + 1
                seen.add(name)
    # Deterministic order: bytes descending, then name ascending.
    ranked = sorted(by_bytes.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked, by_repo


def weekly(days):
    """Aggregate to weeks. A line through daily counts would claim values that
    never existed: 0, 0, 11, 0, 0, 10 is not a slope. Weekly totals are
    continuous enough that an area is defensible."""
    out = []
    for i in range(0, len(days) - 6, 7):
        out.append(sum(count for _, count in days[i:i + 7]))
    return out[-SPARK_WEEKS:]


def human(value):
    if value >= 1000000:
        return "%.1fM" % (value / 1000000.0)
    if value >= 1000:
        return "%.1fk" % (value / 1000.0)
    return str(value)


def pretty_date(iso):
    if not iso:
        return "-"
    d = dt.date(*[int(p) for p in iso.split("-")])
    return d.strftime("%-d %b %Y") if os.name != "nt" else d.strftime("%d %b %Y")


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------

def spark_path(values, x, y, w, h):
    if not values:
        return "", ""
    peak = max(values) or 1
    step = w / float(max(1, len(values) - 1))
    pts = []
    for i, value in enumerate(values):
        pts.append((x + i * step, y + h - (value / float(peak)) * h))

    line = "M " + " L ".join("%s %s" % (K.n(px), K.n(py)) for px, py in pts)
    area = line + " L %s %s L %s %s Z" % (K.n(x + w), K.n(y + h), K.n(x), K.n(y + h))
    return line, area


def draw_stats(data, theme):
    t = K.THEMES[theme]
    c = data["contrib"]["contributionsCollection"]
    total = c["contributionCalendar"]["totalContributions"]
    height = 200

    parts = [K.rect(0, 0, W, height, "none")]

    # hero
    parts.append(K.text(0, 62, human(total), fill=t["ink"], size=54, weight=700))
    parts.append(K.text(0, 86, "contributions in the last 365 days", fill=t["dim"], size=12))

    # breakdown, four plain numbers rather than four coloured chips
    breakdown = [
        ("commits", c["totalCommitContributions"]),
        ("pull requests", c["totalPullRequestContributions"]),
        ("reviews", c["totalPullRequestReviewContributions"]),
        ("issues", c["totalIssueContributions"]),
    ]
    x = 0
    for label, value in breakdown:
        parts.append(K.text(x, 132, human(value), fill=t["ink"], size=19, weight=700))
        parts.append(K.text(x, 150, label, fill=t["dim"], size=11))
        x += 118

    parts.append(K.rule(0, 168, W, t["rule"]))
    # Separate with a middle dot, not with runs of spaces. Whitespace collapses
    # in SVG text unless you ask it not to, and the label is not monospace-safe.
    parts.append(K.text(0, 188, "%s public repos · %s stars · %s followers"
                        % (data["repo_count"], data["stars"],
                           data["contrib"]["followers"]["totalCount"]),
                        fill=t["dim"], size=11))

    # weekly sparkline, right-aligned
    values = weekly(data["days"])
    sx, sy, sw, sh = W - 380, 26, 380, 92
    line, area = spark_path(values, sx, sy, sw, sh)
    if line:
        parts.append('<path d="%s" fill="%s" opacity="0.35"/>' % (area, t["ink"]))
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.5" '
                     'stroke-linejoin="round"/>' % (line, t["ink"]))
        parts.append(K.rule(sx, sy + sh, sw, t["rule"]))
        parts.append(K.text(W, sy + sh + 16,
                            "weekly totals · %d weeks · peak %s" % (len(values), max(values)),
                            fill=t["dim"], size=11, anchor="end"))

    style = K.ui_faces() + "text{font-family:'UI',ui-monospace,monospace;}"
    return K.document(W, height, style,
                      "".join(parts),
                      "%s contributions in the last 365 days" % total)


def draw_streak(data, theme):
    t = K.THEMES[theme]
    current, longest = data["current"], data["longest"]
    active = sum(1 for _, count in data["days"] if count > 0)
    height = 128

    cells = [
        ("current streak", "%d days" % current["length"],
         "%s to %s" % (pretty_date(current["start"]), pretty_date(current["end"]))
         if current["length"] else "no active streak"),
        ("longest streak", "%d days" % longest["length"],
         "%s to %s" % (pretty_date(longest["start"]), pretty_date(longest["end"]))
         if longest["length"] else "-"),
        ("active days", "%d of 365" % active,
         "%.0f%% of the year" % (active / 365.0 * 100)),
    ]

    parts = []
    col = W / 3.0
    for i, (label, value, meta) in enumerate(cells):
        x = i * col
        parts.append(K.text(x, 22, label, fill=t["dim"], size=11))
        parts.append(K.text(x, 62, value, fill=t["ink"], size=30, weight=700))
        parts.append(K.text(x, 84, meta, fill=t["dim"], size=11))
        if i:
            parts.append('<line x1="%s" y1="8" x2="%s" y2="96" stroke="%s" '
                         'stroke-width="1"/>' % (K.n(x - 24.5), K.n(x - 24.5), t["rule"]))
    parts.append(K.rule(0, 110, W, t["rule"]))

    style = K.ui_faces() + "text{font-family:'UI',ui-monospace,monospace;}"
    return K.document(W, height, style, "".join(parts),
                      "Current streak %d days, longest %d days"
                      % (current["length"], longest["length"]))


def draw_langs(data, theme):
    t = K.THEMES[theme]
    ranked, by_repo = data["langs"], data["langs_by_repo"]
    top = ranked[:TOP_LANGS]
    total = sum(size for _, size in ranked) or 1

    row_h = 26
    height = 34 + len(top) * row_h + 26

    parts = [K.text(0, 14, "by bytes written, public repositories only",
                    fill=t["dim"], size=11)]

    label_w, bar_x, bar_w = 132, 132, W - 132 - 150
    for i, (name, size) in enumerate(top):
        y = 34 + i * row_h
        share = size / float(total)
        parts.append(K.text(0, y + 13, name[:16], fill=t["ink"], size=12))
        parts.append(K.rect(bar_x, y + 4, bar_w, 12, t["faint"], 'rx="1"'))
        parts.append(K.rect(bar_x, y + 4, max(1.0, bar_w * share), 12, t["ink"], 'rx="1"'))
        parts.append(K.text(W, y + 13,
                            "%.1f%% · %d repos" % (share * 100, by_repo.get(name, 0)),
                            fill=t["dim"], size=11, anchor="end"))

    tail = ranked[TOP_LANGS:]
    if tail:
        rest = sum(size for _, size in tail) / float(total)
        parts.append(K.text(0, height - 8,
                            "%d more languages, %.1f%% combined" % (len(tail), rest * 100),
                            fill=t["dim"], size=11))

    style = K.ui_faces(bold=False) + "text{font-family:'UI',ui-monospace,monospace;}"
    return K.document(W, height, style, "".join(parts),
                      "Top languages: " + ", ".join(name for name, _ in top))


def draw_year(data, theme):
    """One character per day, using the portrait's own ramp. A zero day is a
    full stop, not a coloured square: empty space reads as empty."""
    t = K.THEMES[theme]
    days = data["days"]

    counts = sorted(count for _, count in days if count > 0)
    # Decile thresholds rather than count/max, so one enormous day does not
    # flatten every ordinary one into the same glyph.
    cuts = [counts[max(0, int(len(counts) * step / 10.0) - 1)]
            for step in range(1, 10)] if counts else []

    def glyph(count):
        if count <= 0:
            return "."
        rank = sum(1 for cut in cuts if count > cut)
        return K.RAMP[3 + rank]

    cell_w, cell_h = 15.0, 15.0
    left, top = 34, 46
    columns = (len(days) + 6) // 7

    parts = [K.text(0, 14, "the year, one character per day", fill=t["dim"], size=11)]

    # month labels along the top
    seen_month = None
    for index, (date, _) in enumerate(days):
        col, row = index // 7, index % 7
        if row != 0:
            continue
        month = date[5:7]
        if month != seen_month:
            seen_month = month
            name = dt.date(int(date[:4]), int(month), 1).strftime("%b").lower()
            parts.append(K.text(left + col * cell_w, top - 8, name, fill=t["dim"], size=10))

    # GitHub's calendar weeks always begin on Sunday, so row 0 is Sunday.
    for label, row in (("mon", 1), ("wed", 3), ("fri", 5)):
        parts.append(K.text(0, top + row * cell_h + 11, label, fill=t["dim"], size=10))

    # One <text> per weekday row rather than one per day. The font advance is
    # exactly 0.600 em by construction, so letter-spacing alone lands every
    # character on the grid, and the file drops from 365 elements to 7.
    glyph_size = 13.0
    tracking = cell_w - glyph_size * 0.600

    grid = []
    for row in range(7):
        line = "".join(glyph(count) for _, count in days[row::7])
        grid.append('<text x="%s" y="%s">%s</text>'
                    % (K.n(left), K.n(top + row * cell_h + 11), K.esc(line)))
    parts.append('<g fill="%s" font-size="%s" letter-spacing="%s" '
                 'xml:space="preserve">%s</g>'
                 % (t["ink"], K.n(glyph_size), K.n(tracking), "".join(grid)))

    height = top + 7 * cell_h + 34
    legend = "less  " + "".join(K.RAMP[3:13:2]) + "  more"
    parts.append(K.text(W, height - 10, legend, fill=t["dim"], size=11, anchor="end"))
    parts.append(K.rule(0, height - 26, W, t["rule"]))

    style = K.ui_faces(bold=False) + "text{font-family:'UI',ui-monospace,monospace;white-space:pre;}"
    return K.document(max(W, left + columns * cell_w + 10), height, style,
                      "".join(parts), "Contribution grid for the last 365 days")


# --------------------------------------------------------------------------

def main():
    login = os.environ.get("GH_LOGIN")
    token = os.environ.get("GITHUB_TOKEN")
    if not login or not token:
        sys.exit("set GH_LOGIN and GITHUB_TOKEN")

    today = dt.datetime.now(dt.timezone.utc).date()
    contrib, repos, repo_count = fetch(login, token, today)

    days = flatten_days(contrib["contributionsCollection"]["contributionCalendar"])
    current, longest = streaks(days)
    ranked, by_repo = language_totals(repos)

    data = {
        "contrib": contrib,
        "days": days,
        "current": current,
        "longest": longest,
        "langs": ranked,
        "langs_by_repo": by_repo,
        "repo_count": repo_count,
        "stars": sum(repo["stargazerCount"] for repo in repos),
    }

    graphics = {
        "stats": draw_stats,
        "streak": draw_streak,
        "langs": draw_langs,
        "year": draw_year,
    }

    for name, draw in graphics.items():
        for theme in ("light", "dark"):
            filename = "%s.svg" % name if theme == "light" else "%s-dark.svg" % name
            path = os.path.join(K.ROOT, filename)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(draw(data, theme))
            print("  wrote %s" % filename)

    print("  total %s, current streak %s, longest %s"
          % (contrib["contributionsCollection"]["contributionCalendar"]["totalContributions"],
             current["length"], longest["length"]))


if __name__ == "__main__":
    main()
