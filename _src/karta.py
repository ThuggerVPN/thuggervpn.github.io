"""Карта-навигатор ограничений (/karta/, /en/karta/).

Полноэкранная карта на Leaflet (своя копия в /assets/leaflet/) с подложкой OpenStreetMap:
- регионы, окрашенные по числу событий за 7/30 дней (данные _src/data/status.json);
- города, упомянутые в событиях (_src/data/ru_cities.json, города от 90 тыс. жителей);
- зоны постоянных проблем со связью и геолокацией (_src/data/zones.json, только с источниками);
- маршрут: поиск адресов через Nominatim, путь через OSRM, список мест на пути, где могли быть ограничения.
Данные для карты пишутся в /karta/data.json при каждой сборке."""
import json, os, re, html
from datetime import date

import build as B
import ru_map

D = os.path.dirname(os.path.abspath(__file__))
GEO = json.load(open(os.path.join(D, "data", "ru_regions_web.geojson"), encoding="utf-8"))
CITIES = json.load(open(os.path.join(D, "data", "ru_cities.json"), encoding="utf-8"))
ZONES_F = os.path.join(D, "data", "zones.json")


def _fix_lon(coords):
    if isinstance(coords[0], (int, float)):
        return [coords[0] + 360 if coords[0] < 0 else coords[0], coords[1]]
    return [_fix_lon(c) for c in coords]


def city_hits(text):
    t = " " + text.lower().replace("ё", "е") + " "
    out = []
    for c in CITIES:
        n = c["n"].lower().replace("ё", "е")
        if len(n) < 4:
            continue
        stem = n if len(n) <= 5 else n[:-1]  # Пенза -> Пенз(е), Самара -> Самар(е)
        if re.search(r"(?<![а-я])" + re.escape(stem) + r"[а-я]{0,3}(?![а-я])", t):
            out.append(c)
    return out


def data(st):
    upd = st["updated"]
    today = date.fromisoformat(upd[:10])
    evs, cities = [], {}
    for e in st["events"]:
        age = (today - date.fromisoformat(e["date"])).days
        if age < 0 or age > 30:
            continue
        regs = sorted(ru_map.match(e["region"]))
        txt = " ".join([e["region"], e["title"], e.get("meaning", "")])
        cs = city_hits(txt)
        i = len(evs)
        evs.append({"d": e["date"], "a": age, "k": e["type"], "r": regs,
                    "t": e["title"], "te": e.get("title_en") or e["title"],
                    "m": e.get("meaning", ""), "me": e.get("meaning_en") or e.get("meaning", ""),
                    "s": e.get("source", ""), "u": e.get("url", "")})
        for c in cs:
            cities.setdefault(c["n"], {"n": c["n"], "lat": c["lat"], "lon": c["lon"], "e": []})["e"].append(i)
    feats = []
    for f in GEO["features"]:
        g = f["geometry"]
        feats.append({"type": "Feature", "properties": {"n": f["properties"]["name"], "en": f["properties"].get("name_latin", "")},
                      "geometry": {"type": g["type"], "coordinates": _fix_lon(g["coordinates"])}})
    zones = json.load(open(ZONES_F, encoding="utf-8")) if os.path.exists(ZONES_F) else []
    return {"updated": upd, "events": evs, "cities": list(cities.values()), "zones": zones,
            "regions": {"type": "FeatureCollection", "features": feats}}


T = {
    "ru": {"path": "/karta/", "title": "Карта ограничений интернета: где не работает мобильный интернет и GPS",
           "desc": "Интерактивная карта: где отключают мобильный интернет, включают белые списки и сбоит GPS. Регионы, города, зоны постоянных проблем и проверка маршрута: где в пути пропадёт сеть.",
           "h": "Карта ограничений", "d7": "7 дней", "d30": "30 дней", "route": "Маршрут", "me": "Где я",
           "from": "Откуда (город или адрес)", "to": "Куда", "go": "Проверить маршрут", "close": "Закрыть",
           "lr": "Регионы", "lc": "Города", "lz": "Зоны", "none": "За выбранный период событий нет.",
           "load": "Загружаю карту…", "searching": "Ищу адреса…", "nf": "Не нашёл адрес: ", "rerr": "Не удалось построить маршрут, попробуйте ещё раз.",
           "onroute": "На маршруте", "clean": "За выбранный период на этом пути ограничений не отмечено. Но они вводятся внезапно: перед поездкой проверьте ещё раз.",
           "km": "км", "ev": "событий", "zone": "Зона постоянных проблем", "src": "Источник",
           "tips": "Перед поездкой: скачайте офлайн-карты, сохраните билеты и адреса скриншотами, настройте VPN заранее.",
           "legend": "Цвет региона: сколько событий за период", "note": "Карта показывает события из открытых источников и сообщения пользователей, а не точное покрытие вышек. Данные обновляются каждый день.",
           "status": "Сводка за сегодня", "check": "Проверить свой интернет"},
    "en": {"path": "/en/karta/", "title": "Russia internet restrictions map: where mobile internet and GPS fail",
           "desc": "Interactive map of mobile internet shutdowns, whitelist mode and GPS jamming in Russia: regions, cities, persistent problem zones and a route checker.",
           "h": "Restrictions map", "d7": "7 days", "d30": "30 days", "route": "Route", "me": "Locate me",
           "from": "From (city or address)", "to": "To", "go": "Check route", "close": "Close",
           "lr": "Regions", "lc": "Cities", "lz": "Zones", "none": "No events for the selected period.",
           "load": "Loading map…", "searching": "Searching…", "nf": "Address not found: ", "rerr": "Could not build the route, try again.",
           "onroute": "On your route", "clean": "No restrictions reported on this route for the period. They can start suddenly, so check again before you go.",
           "km": "km", "ev": "events", "zone": "Persistent problem zone", "src": "Source",
           "tips": "Before the trip: download offline maps, screenshot tickets and addresses, set up your VPN in advance.",
           "legend": "Region colour: events in the period", "note": "The map shows events from open sources and user reports, not exact cell tower coverage. Updated daily.",
           "status": "Today's summary", "check": "Check your internet"},
}

CSS = """<style>
body:has(#km) footer,body:has(#km) .qa-fab{display:none}
body:has(#km) main{padding:0}body:has(#km) main>.wrap{max-width:none;padding:0}
#km{position:relative;height:calc(100dvh - var(--hdr,64px));min-height:420px}
#km-map{position:absolute;inset:0;background:var(--card2)}
.km-bar{position:absolute;z-index:500;left:10px;right:10px;top:10px;display:flex;gap:8px;flex-wrap:wrap;pointer-events:none}
.km-bar>*{pointer-events:auto}
.km-b{font:700 14px Manrope,sans-serif;background:var(--card);color:var(--text);border:1px solid var(--line2);border-radius:999px;padding:9px 14px;min-height:42px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18)}
.km-b[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.km-b.pri{background:var(--accent);border-color:var(--accent);color:#fff}
.km-sp{flex:1}
.km-sheet{position:absolute;z-index:600;left:0;right:0;bottom:0;max-height:55%;overflow:auto;background:var(--card);border-top:1px solid var(--line);border-radius:22px 22px 0 0;padding:16px 18px 22px;box-shadow:0 -10px 40px rgba(0,0,0,.25);transform:translateY(105%);transition:transform .25s}
.km-sheet.on{transform:none}.km-sheet.half{max-height:42%}.km-sheet.min{max-height:64px;overflow:hidden}.km-h{width:100%;height:22px;margin:-10px 0 4px;cursor:pointer;position:relative}.km-h:after{content:'';position:absolute;left:50%;top:8px;width:44px;height:5px;margin-left:-22px;border-radius:3px;background:var(--line2)}
.km-sheet h2{font-size:19px;margin:0 0 8px;padding-right:40px}.km-sheet p{margin:6px 0;color:var(--soft);font-size:15px}
.km-x{position:absolute;right:12px;top:10px;width:36px;height:36px;border-radius:50%;border:0;background:var(--card2);color:var(--text);font-size:20px;cursor:pointer}
.km-ev{padding:10px 0;border-top:1px solid var(--line)}.km-ev:first-of-type{border-top:0}
.km-ev small{color:var(--soft)}.km-ev b{display:block;font-size:15.5px;margin:2px 0}
.km-ev a{font-size:13px}
.km-form{display:grid;gap:8px;margin:10px 0}.km-form input{font:16px Inter,sans-serif;padding:12px 14px;border-radius:12px;border:1px solid var(--line2);background:var(--card2);color:var(--text)}
.km-leg{position:absolute;z-index:500;left:10px;bottom:24px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:8px 12px;font-size:12.5px;color:var(--soft);display:flex;gap:10px;align-items:center;flex-wrap:wrap;max-width:calc(100% - 20px)}
.km-leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.km-load{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:400;color:var(--soft)}
.km-step{display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)}.km-step:first-of-type{border-top:0}
.km-step i{flex:0 0 10px;height:10px;border-radius:50%;margin-top:6px}
.km-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.km-links a{font-weight:700;font-size:14px}
.leaflet-container{font-family:Inter,sans-serif}
</style>"""


def page(lang, st, urls, UPD):
    t = T[lang]
    en = lang == "en"
    pre = "/en" if en else ""
    body = (CSS + f'<div id="km" data-lang="{lang}"><div id="km-map"></div><div class="km-load">{t["load"]}</div>'
            f'<div class="km-bar"><button class="km-b" data-d="7" aria-pressed="true">{t["d7"]}</button>'
            f'<button class="km-b" data-d="31" aria-pressed="false">{t["d30"]}</button><span class="km-sp"></span>'
            f'<button class="km-b" id="km-me">📍 {t["me"]}</button><button class="km-b pri" id="km-route">🧭 {t["route"]}</button></div>'
            f'<div class="km-leg"><span>{t["legend"]}:</span><span><i style="background:#f6c177"></i>1</span>'
            f'<span><i style="background:#f08a5d"></i>2-3</span><span><i style="background:#e84855"></i>4+</span>'
            f'<span><i style="background:#7c3aed;border-radius:50%"></i>{t["lz"]}</span></div>'
            f'<div class="km-sheet" id="km-sheet"><div class="km-h" aria-label="{t["close"]}"></div><button class="km-x" aria-label="{t["close"]}">×</button><div id="km-c"></div></div></div>'
            f'<link rel="stylesheet" href="/assets/leaflet/leaflet.css"><script src="/assets/leaflet/leaflet.js"></script>'
            f'<script>window.KM_T={json.dumps(t, ensure_ascii=False)};window.KM_PRE="{pre}";</script><script src="/assets/karta.js?v={UPD.replace("-", "")}"></script>')
    jsonld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": t["h"], "url": B.SITE + t["path"],
               "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any", "inLanguage": lang,
               "offers": {"@type": "Offer", "price": "0", "priceCurrency": "RUB"}}]
    B.write(t["path"].strip("/") + "/index.html", B.page(t["title"], t["desc"], t["path"], body, jsonld, lang=lang))
    urls.append((t["path"], UPD))


def write_data(st):
    p = B.ROOT / "karta" / "data.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data(st), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
