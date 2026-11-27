"""Карта-навигатор ограничений (/karta/, /en/karta/).

Полноэкранная карта «Ночной радар» на MapLibre GL (своя копия в /assets/maplibre/) с векторной подложкой OpenFreeMap
(тёмная/светлая под тему сайта; если подложка недоступна, карта работает на пустом фоне):
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
           "desc": "Интерактивная карта: где отключают мобильный интернет, включают белые списки и сбоит GPS. Регионы, города, лента событий за 30 дней и проверка маршрута: где в пути пропадёт сеть.",
           "h": "Карта ограничений", "d1": "Сегодня", "d7": "7 дней", "d30": "30 дней", "route": "Проверить маршрут", "me": "Где я",
           "from": "Откуда (город или адрес)", "to": "Куда", "go": "Проверить маршрут", "close": "Закрыть",
           "none": "За выбранный период событий нет.", "load": "Загружаю карту…", "searching": "Ищу адреса…",
           "nf": "Не нашёл адрес: ", "rerr": "Не удалось построить маршрут, попробуйте ещё раз.",
           "clean": "За выбранный период на этом пути ограничений не отмечено. Но они вводятся внезапно: перед поездкой проверьте ещё раз.",
           "km": "км", "zone": "Зона постоянных проблем", "src": "Источник",
           "tips": "Перед поездкой: скачайте офлайн-карты, сохраните билеты и адреса скриншотами, настройте VPN заранее.",
           "note": "Карта показывает события из открытых источников и сообщения пользователей, а не точное покрытие вышек. Данные обновляются каждый день.",
           "status": "Сводка за сегодня", "check": "Проверить свой интернет",
           "k": {"slow": "Сбои мобильного", "outage": "Отключение", "whitelist": "Белые списки", "service": "Сервисы", "policy": "Законы"},
           "kall": "Все", "kslow": "Сбои", "kout": "Отключения", "kwl": "Белые списки", "ksvc": "Сервисы", "kz": "GPS и зоны",
           "nat": "По всей стране", "d7ago": "7 дней назад", "today": "Сегодня", "high": "Высокий", "mid": "Средний", "low": "Низкий",
           "p7": "за 7 дней", "p30": "за 30 дней", "feed": "Лента событий", "live": "обновляется каждый день",
           "kev": "событий", "kreg": "регионов", "ktoday": "сегодня", "upd": "Обновлено", "msk": "МСК",
           "risky": "участка с ограничениями", "norisk": "ограничений не отмечено", "riskhi": "Риск выше среднего", "riskmd": "Есть риск",
           "noev": "Ограничений не отмечено", "prep": "Настроить VPN перед поездкой",
           "leg": "Событий в регионе", "play": "Проиграть 30 дней", "cta1": "Режут сеть у вас?", "cta2": "Проверьте за 10 секунд, что работает",
           "search": "Поиск по карте"},
    "en": {"path": "/en/karta/", "title": "Russia internet restrictions map: where mobile internet and GPS fail",
           "desc": "Interactive map of mobile internet shutdowns, whitelist mode and GPS jamming in Russia: regions, cities, a 30-day event feed and a route checker.",
           "h": "Restrictions map", "d1": "Today", "d7": "7 days", "d30": "30 days", "route": "Check a route", "me": "Locate me",
           "from": "From (city or address)", "to": "To", "go": "Check route", "close": "Close",
           "none": "No events for the selected period.", "load": "Loading map…", "searching": "Searching…",
           "nf": "Address not found: ", "rerr": "Could not build the route, try again.",
           "clean": "No restrictions reported on this route for the period. They can start suddenly, so check again before you go.",
           "km": "km", "zone": "Persistent problem zone", "src": "Source",
           "tips": "Before the trip: download offline maps, screenshot tickets and addresses, set up your VPN in advance.",
           "note": "The map shows events from open sources and user reports, not exact cell tower coverage. Updated daily.",
           "status": "Today's summary", "check": "Check your internet",
           "k": {"slow": "Mobile outages", "outage": "Shutdown", "whitelist": "Whitelists", "service": "Services", "policy": "Laws"},
           "kall": "All", "kslow": "Outages", "kout": "Shutdowns", "kwl": "Whitelists", "ksvc": "Services", "kz": "GPS & zones",
           "nat": "Nationwide", "d7ago": "7 days ago", "today": "Today", "high": "High", "mid": "Medium", "low": "Low",
           "p7": "in 7 days", "p30": "in 30 days", "feed": "Event feed", "live": "updated daily",
           "kev": "events", "kreg": "regions", "ktoday": "today", "upd": "Updated", "msk": "Moscow time",
           "risky": "segments with restrictions", "norisk": "no restrictions reported", "riskhi": "Above-average risk", "riskmd": "Some risk",
           "noev": "No restrictions reported", "prep": "Set up a VPN before the trip",
           "leg": "Events in region", "play": "Play 30 days", "cta1": "Network cut where you are?", "cta2": "Check what works in 10 seconds",
           "search": "Map search"},
}

CSS = """<style>
body:has(#km) footer,body:has(#km) .qa-fab{display:none}
body:has(#km) main{padding:0}body:has(#km) main>.wrap{max-width:none;padding:0}
#km{position:relative;height:calc(100dvh - var(--hdr,64px));min-height:520px;display:flex;background:var(--bg)}
.km-side{flex:0 0 360px;display:flex;flex-direction:column;gap:14px;padding:18px;border-right:1px solid var(--line);overflow:auto;box-sizing:border-box}
.km-main{position:relative;flex:1;min-width:0}
#km-map{position:absolute;inset:0;background:var(--card2)}
.km-kpi{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.km-kpi div{padding:11px 12px;border-radius:14px;background:var(--card);border:1px solid var(--line)}
.km-kpi b{display:block;font:800 22px/1.1 Manrope,sans-serif}.km-kpi small{font-size:12px;color:var(--muted)}
.km-kpi .t{background:var(--violet-bg);border-color:var(--violet-line)}.km-kpi .t b{color:#ff6b8b}
.km-fh{display:flex;align-items:center;justify-content:space-between;gap:8px}.km-fh b{font:700 15px Manrope,sans-serif}
.km-fh small{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}.km-fh small:before{content:'';width:7px;height:7px;border-radius:50%;background:#ff5079}
#km-feed{display:flex;flex-direction:column;gap:8px}
.km-fi{all:unset;box-sizing:border-box;display:block;width:100%;cursor:pointer;padding:12px 14px;border-radius:14px;background:var(--card);border:1px solid var(--line);transition:border-color .2s}
.km-fi:hover,.km-fi:focus-visible{border-color:var(--line-hi)}.km-fi .km-ev{padding:0;border:0}
.km-cta{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:14px;background:var(--violet-bg);border:1px solid var(--violet-line);color:var(--text);text-decoration:none;margin-top:auto}
.km-cta span{flex:1;font-size:13px;line-height:1.35;color:var(--soft)}.km-cta b{display:block;font-size:14px;color:var(--text)}
.km-bar{position:absolute;z-index:5;left:12px;right:60px;top:12px;display:flex;gap:8px;flex-wrap:wrap;pointer-events:none}
.km-bar>*{pointer-events:auto}
.km-seg{display:flex;padding:4px;border-radius:14px;background:var(--card);border:1px solid var(--line2);box-shadow:0 6px 20px var(--sh)}
.km-seg button,.km-chip,.km-b{font:600 13px Inter,sans-serif;color:var(--soft);background:transparent;border:0;border-radius:10px;padding:0 12px;min-height:36px;cursor:pointer;display:inline-flex;align-items:center;gap:7px;white-space:nowrap}
.km-seg button[aria-pressed=true]{background:var(--accent);color:#fff}
.km-chips{display:flex;gap:6px;flex-wrap:wrap}
.km-chip{min-height:40px;padding:0 13px;border-radius:999px;background:var(--card);border:1px solid var(--line2);color:var(--text);box-shadow:0 6px 20px var(--sh)}
.km-chip i{width:8px;height:8px;border-radius:50%}.km-chip .n{opacity:.65}
.km-chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.km-b{min-height:40px;padding:0 14px;border-radius:12px;background:var(--card);border:1px solid var(--line2);color:var(--text);box-shadow:0 6px 20px var(--sh)}
.km-b.pri{background:var(--accent);border-color:var(--accent);color:#fff}
.km-sp{flex:1}
.km-leg{position:absolute;z-index:4;left:12px;bottom:104px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:9px 12px;font-size:12px;color:var(--soft);display:flex;flex-direction:column;gap:6px}
.km-leg div{display:flex;gap:2px}.km-leg div i{width:34px;height:8px;border-radius:2px}
.km-leg p{margin:0;display:flex;justify-content:space-between;width:142px}
.km-tlw{position:absolute;z-index:4;left:12px;right:12px;bottom:12px;display:flex;align-items:flex-end;gap:12px;padding:10px 14px;border-radius:16px;background:var(--card);border:1px solid var(--line);box-shadow:0 10px 30px var(--sh)}
#km-play{flex:none;width:44px;height:44px;border-radius:50%;border:0;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer}
#km-play[aria-pressed=true] .pl,#km-play .pa{display:none}#km-play[aria-pressed=true] .pa{display:block}
.km-tlb{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
#km-tl{display:flex;align-items:flex-end;gap:3px;height:46px}
.km-tb{all:unset;flex:1;height:100%;display:flex;align-items:flex-end;cursor:pointer}
.km-tb span{display:block;width:100%;border-radius:3px;background:var(--line2);transition:background .2s}
.km-tb.on span{background:#6a3fd8}.km-tb.cur span{background:#ff5079}.km-tb:hover span{background:var(--line-hi)}
#km-tl-l{display:flex;justify-content:space-between;font-size:11px;color:var(--muted)}#km-tl-l b{color:#ff6b8b;font-weight:600}
.km-sheet{position:absolute;z-index:8;left:0;right:0;bottom:0;max-height:62%;overflow:auto;background:var(--card);border-top:1px solid var(--line);border-radius:22px 22px 0 0;padding:16px 18px 22px;box-shadow:0 -10px 40px var(--sh);transform:translateY(105%);transition:transform .25s;box-sizing:border-box}
.km-sheet.on{transform:none}.km-sheet.min{max-height:64px;overflow:hidden}
.km-h{width:100%;height:22px;margin:-10px 0 4px;cursor:pointer;position:relative}.km-h:after{content:'';position:absolute;left:50%;top:8px;width:44px;height:5px;margin-left:-22px;border-radius:3px;background:var(--line2)}
.km-sheet h2{font:700 19px/1.25 Manrope,sans-serif;margin:0;padding-right:40px}.km-sheet h3{font:700 15px Manrope,sans-serif;margin:16px 0 4px}
.km-sheet p{margin:8px 0;color:var(--soft);font-size:14.5px}
.km-sub{color:var(--muted)!important;font-size:13px!important}
.km-x{position:absolute;right:12px;top:10px;width:36px;height:36px;border-radius:50%;border:0;background:var(--card2);color:var(--text);font-size:20px;cursor:pointer}
.km-rh{display:flex;align-items:center;gap:10px;padding-right:40px}.km-rh h2{padding:0}
.km-lvl{flex:none;padding:3px 9px;border-radius:999px;font-size:11.5px;font-weight:700}
.km-lvl.hi{background:rgba(255,80,121,.16);color:#ff6b8b}.km-lvl.md{background:rgba(240,138,93,.16);color:#f08a5d}.km-lvl.lo{background:rgba(52,211,153,.14);color:#10b981}
.km-b7{display:flex;gap:3px;align-items:flex-end;height:34px;margin:12px 0 4px}.km-b7 span{flex:1;border-radius:2px}
.km-b7l{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:6px}
.km-ev{padding:11px 0;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:4px}
.km-ev b{font-size:14.5px;line-height:1.35;color:var(--text)}.km-ev small{font-size:12.5px;color:var(--muted);line-height:1.4}.km-ev a{font-size:12.5px}
.km-ev-h{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:600}.km-ev-h i{width:8px;height:8px;border-radius:50%}.km-ev-h small{margin-left:auto}
.km-ev-r{color:var(--soft)!important}
.km-links{display:flex;gap:14px;flex-wrap:wrap;margin-top:14px}.km-links a{font-weight:700;font-size:14px}
.km-form{display:grid;gap:10px;margin:12px 0}.km-form label{display:grid;gap:4px;font-size:12.5px;color:var(--muted)}
.km-form input{font:16px Inter,sans-serif;padding:12px 14px;border-radius:12px;border:1px solid var(--line2);background:var(--card2);color:var(--text)}
.km-go{display:flex;align-items:center;justify-content:center;min-height:48px;border-radius:14px;border:0;background:var(--accent);color:#fff!important;font:700 15px Manrope,sans-serif;text-decoration:none;cursor:pointer;margin-top:12px}
.km-rsum{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px}.km-rsum b{font:800 17px Manrope,sans-serif}
.km-rbar{display:flex;gap:2px;height:8px;border-radius:4px;overflow:hidden;margin:12px 0 4px}
.km-step{display:flex;gap:12px;padding:10px 0;border-top:1px solid var(--line)}.km-step>i{flex:0 0 10px;height:10px;border-radius:50%;margin-top:5px}
.km-step>div{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}.km-step small{font-size:12.5px;color:var(--muted)}
.km-step-h{display:flex;gap:8px}.km-step-h small{margin-left:auto;white-space:nowrap}
.km-load{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:3;color:var(--soft)}
.km-city{all:unset;position:relative;cursor:pointer;width:var(--s);height:var(--s);display:block}
.km-city i{position:absolute;inset:0;border-radius:50%;background:#fff;border:3px solid #b24ad6;box-sizing:border-box;box-shadow:0 0 0 4px rgba(139,92,246,.25)}
.km-city.hot i{border-color:#ff5079;box-shadow:0 0 0 5px rgba(255,80,121,.25)}
.km-city.fresh:after{content:'';position:absolute;inset:-2px;border-radius:50%;border:2px solid #ff5079;animation:kmp 1.8s ease-out infinite}
@keyframes kmp{0%{transform:scale(.8);opacity:.9}100%{transform:scale(2.8);opacity:0}}
.km-city span{position:absolute;left:calc(100% + 6px);top:50%;transform:translateY(-50%);white-space:nowrap;font:600 12px Inter,sans-serif;color:var(--text);text-shadow:0 0 3px var(--bg),0 0 3px var(--bg),0 0 3px var(--bg);pointer-events:none}
.km-city span b{color:#ff6b8b}
.km-me{width:16px;height:16px;border-radius:50%;background:#2563eb;border:3px solid #fff;box-shadow:0 0 0 6px rgba(37,99,235,.25)}
.maplibregl-ctrl-group{background:var(--card)!important;border:1px solid var(--line2);box-shadow:0 6px 20px var(--sh)!important;border-radius:12px!important}
.maplibregl-ctrl-group button{width:40px!important;height:40px!important}.maplibregl-ctrl-group button+button{border-top:1px solid var(--line)!important}
:root:not([data-theme=light]) .maplibregl-ctrl-icon{filter:invert(1)}
.maplibregl-ctrl-attrib{background:var(--card)!important;color:var(--muted)}.maplibregl-ctrl-attrib a{color:var(--muted)}
#km .maplibregl-ctrl-bottom-right{bottom:96px}
.km-city.nl span{display:none}
#km-feed-b{display:none}
@media(min-width:1000px){.km-sheet{left:auto;right:12px;top:64px;bottom:auto;width:380px;max-height:calc(100% - 260px);border:1px solid var(--line);border-radius:18px;transform:translateX(calc(100% + 24px));opacity:0;transition:transform .25s,opacity .25s}.km-sheet.on{transform:none;opacity:1}.km-h{display:none}}
@media(max-width:999px){.km-side{display:none}#km-feed-b{display:inline-flex}.km-bar{right:12px}.km-bar .km-chips{flex-wrap:nowrap;overflow-x:auto;width:100%;padding-bottom:2px;scrollbar-width:none}.km-leg{display:none}.km-tlw{padding:8px 10px}#km-tl{height:34px}#km-play{width:40px;height:40px}.km-b{padding:0 11px}.km-b span{display:none}.km-seg{flex:1}.km-seg button{flex:1;justify-content:center;padding:0 6px;font-size:12.5px}#km .maplibregl-ctrl-bottom-right{bottom:78px}}
</style>"""

SVG = {
    "route": '<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/><path d="M8.5 19H15a3.5 3.5 0 0 0 0-7H9a3.5 3.5 0 0 1 0-7h6.5"/>',
    "me": '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "feed": '<path d="M4 6h16M4 12h16M4 18h10"/>',
    "signal": '<path d="M4 20v-3M9 20v-7M14 20v-11M19 20V5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}


def ic(n, s=16):
    return f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{SVG[n]}</svg>'


def page(lang, st, urls, UPD):
    t = T[lang]
    en = lang == "en"
    pre = "/en" if en else ""
    chips = "".join(f'<button type="button" class="km-chip" data-k="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
                    + (f'<i style="background:{c}"></i>' if c else "") + f'{t[lab]} <span class="n"></span></button>'
                    for k, lab, c in [("all", "kall", ""), ("slow", "kslow", "#f6c177"), ("outage", "kout", "#ff5079"),
                                      ("whitelist", "kwl", "#b9a4ff"), ("service", "ksvc", "#7dd3fc")])
    chips += f'<button type="button" class="km-chip" id="km-zones" aria-pressed="true"><i style="background:#8b5cf6;border-radius:2px"></i>{t["kz"]}</button>'
    side = (f'<aside class="km-side" aria-label="{t["feed"]}">'
            f'<div><b style="font:800 20px/1.2 Manrope,sans-serif">{t["h"]}</b><div style="font-size:12.5px;color:var(--muted);margin-top:3px">{t["upd"]} <span id="km-upd"></span>, 08:47 {t["msk"]}</div></div>'
            f'<div class="km-kpi"><div><b id="km-n-ev">0</b><small>{t["kev"]}</small></div><div><b id="km-n-reg">0</b><small>{t["kreg"]}</small></div>'
            f'<div class="t"><b id="km-n-today">0</b><small>{t["ktoday"]}</small></div></div>'
            f'<div class="km-fh"><b>{t["feed"]}</b><small>{t["live"]}</small></div><div id="km-feed"></div>'
            f'<a class="km-cta" href="{pre}/check/">{ic("signal", 20)}<span><b>{t["cta1"]}</b>{t["cta2"]}</span>{ic("arrow", 18)}</a></aside>')
    bar = (f'<div class="km-bar"><div class="km-seg" role="group"><button type="button" data-d="1" aria-pressed="false">{t["d1"]}</button>'
           f'<button type="button" data-d="7" aria-pressed="true">{t["d7"]}</button><button type="button" data-d="31" aria-pressed="false">{t["d30"]}</button></div>'
           f'<button type="button" class="km-b" id="km-feed-b" aria-label="{t["feed"]}">{ic("feed")}<span>{t["feed"]}</span></button>'
           f'<button type="button" class="km-b" id="km-me" aria-label="{t["me"]}">{ic("me")}<span class="t">{t["me"]}</span></button>'
           f'<button type="button" class="km-b pri" id="km-route" aria-label="{t["route"]}">{ic("route")}<span>{t["route"]}</span></button>'
           f'<div class="km-chips">{chips}</div></div>')
    leg = (f'<div class="km-leg"><span>{t["leg"]}</span><div><i style="background:#6a3fd8;opacity:.55"></i><i style="background:#8b5cf6"></i>'
           f'<i style="background:#b24ad6"></i><i style="background:#ff5079"></i></div><p><span>1</span><span>2-3</span><span>4-6</span><span>7+</span></p></div>')
    tl = (f'<div class="km-tlw"><button type="button" id="km-play" aria-pressed="false" aria-label="{t["play"]}">'
          '<svg class="pl" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5l11 7-11 7z"/></svg>'
          '<svg class="pa" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg></button>'
          '<div class="km-tlb"><div id="km-tl"></div><div id="km-tl-l"></div></div></div>')
    body = (CSS + f'<div id="km" data-lang="{lang}">{side}<div class="km-main"><div id="km-map"></div><div class="km-load">{t["load"]}</div>'
            f'{bar}{leg}{tl}'
            f'<div class="km-sheet" id="km-sheet" role="dialog" aria-live="polite"><div class="km-h" aria-hidden="true"></div><button class="km-x" type="button" aria-label="{t["close"]}">×</button><div id="km-c"></div></div></div></div>'
            f'<link rel="stylesheet" href="/assets/maplibre/maplibre-gl.css"><script src="/assets/maplibre/maplibre-gl.js"></script>'
            f'<script>window.KM_T={json.dumps(dict(t, bot=B.BOT), ensure_ascii=False)};window.KM_PRE="{pre}";</script><script src="/assets/karta.js?v={UPD.replace("-", "")}2"></script>')
    jsonld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": t["h"], "url": B.SITE + t["path"],
               "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any", "inLanguage": lang,
               "offers": {"@type": "Offer", "price": "0", "priceCurrency": "RUB"}}]
    B.write(t["path"].strip("/") + "/index.html", B.page(t["title"], t["desc"], t["path"], body, jsonld, lang=lang))
    urls.append((t["path"], UPD))


def write_data(st):
    p = B.ROOT / "karta" / "data.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data(st), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
