"""Почасовой сбор трафика сайта из GoatCounter -> _src/data/traffic.json.

Без токена берёт публичный счётчик (/counter/<путь>.json): визиты по страницам и клики по кнопкам.
С секретом GOATCOUNTER_TOKEN дополнительно берёт источники переходов (откуда пришли люди).
Находит всплески: страница за сегодня набрала втрое больше своего среднего и не меньше 30 визитов.
Даты по Москве.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_src" / "data" / "traffic.json"
SITE = "https://thuggervpn.goatcounter.com"
TOKEN = os.environ.get("GOATCOUNTER_TOKEN", "").strip()
MSK = timezone(timedelta(hours=3))
DAYS = 14


def http(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "thuggervpn-traffic", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def num(s):
    return int(re.sub(r"\D", "", str(s)) or 0)


def counter(path, start=None, end=None):
    q = ""
    if start:
        q = "?" + urllib.parse.urlencode({"start": start, "end": end})
    try:
        d = json.loads(http(f"{SITE}/counter/{urllib.parse.quote(path, safe='')}.json{q}"))
        return num(d.get("count", 0))
    except Exception:
        return 0


def site_paths():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return sorted(set(re.findall(r"<loc>https://[^/]+(/[^<]*)</loc>", xml)))


def event_paths():
    names = set()
    for f in ROOT.rglob("*.html"):
        if "/_src/" in str(f) or "/.git/" in str(f):
            continue
        names |= set(re.findall(r'data-goatcounter-click="([^"]+)"', f.read_text(encoding="utf-8", errors="ignore")))
    names |= {"chat/open", "chat/sent", "video/play", "app/install-click", "app/installed"}
    return sorted(names)


def referrers(start, end):
    if not TOKEN:
        return None
    h = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    try:
        d = json.loads(http(f"{SITE}/api/v0/stats/toprefs?" + urllib.parse.urlencode(
            {"start": start + "T00:00:00Z", "end": end + "T23:59:59Z", "limit": 20}), h))
        return [{"ref": (s.get("name") or "(прямой заход)"), "count": s.get("count", 0)} for s in d.get("stats", [])]
    except Exception as e:
        return {"error": str(e)[:120]}


def main():
    now = datetime.now(MSK)
    today = now.date()
    days = [(today - timedelta(days=i)) for i in range(DAYS - 1, -1, -1)]
    paths = site_paths()
    events = event_paths()

    def daily(p):
        return [counter(p, d.isoformat(), (d + timedelta(days=1)).isoformat()) for d in days]

    with ThreadPoolExecutor(8) as ex:
        totals = dict(zip(paths + events, ex.map(counter, paths + events)))
    # по дням считаем только страницы, где были визиты, и итог
    active = [p for p in paths if totals.get(p)] + ["TOTAL"]
    with ThreadPoolExecutor(6) as ex:
        series = dict(zip(active, ex.map(daily, active)))

    spikes = []
    for p, s in series.items():
        if p == "TOTAL":
            continue
        t, prev = s[-1], s[-8:-1]
        avg = sum(prev) / len(prev) if prev else 0
        if t >= 30 and t >= 3 * max(avg, 1):
            spikes.append({"path": p, "today": t, "avg7": round(avg, 1)})

    bot = {k: v for k, v in totals.items() if k.startswith("bot") and v}
    pages = {k: v for k, v in totals.items() if k.startswith("/") and v}
    # клики «в бота» по странице: bot/<путь>, bot-top/<путь>, bot-mid/<путь>, bot-sticky/<путь>
    conv = []
    for p, visits in sorted(pages.items(), key=lambda x: -x[1]):
        clicks = {k.split("/", 1)[0]: v for k, v in bot.items() if "/" + k.split("/", 1)[1] == p}
        c = sum(clicks.values())
        conv.append({"path": p, "visits": visits, "bot_clicks": c, "by_place": clicks,
                     "rate": round(100 * c / visits, 1) if visits else 0})

    data = {
        "_comment": "Сбор раз в час (GitHub Actions). Даты по Москве. by_day: последние 14 дней, последний элемент = сегодня.",
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "days": [d.isoformat() for d in days],
        "total_all_time": totals.get("TOTAL") or counter("TOTAL"),
        "by_day": series,
        "spikes_today": spikes,
        "pages_all_time": pages,
        "conversion": conv[:40],
        "events_all_time": {k: v for k, v in totals.items() if not k.startswith("/") and v},
        "referrers_7d": referrers((today - timedelta(days=6)).isoformat(), today.isoformat()),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"traffic: {len(pages)} страниц с визитами, всплесков сегодня: {len(spikes)}")


if __name__ == "__main__":
    main()
