"""Интерактивная карта ограничений по регионам (SVG, без внешних библиотек).

Регионы событий из _src/data/status.json сопоставляются с субъектами карты по корню названия.
Цвет региона = число событий за выбранный период (7 или 30 дней). Нажатие на регион
показывает список событий под картой."""
import json, os, re, html
from datetime import date, timedelta

D = os.path.dirname(os.path.abspath(__file__))
MAP = json.load(open(os.path.join(D, "data", "ru_map.json"), encoding="utf-8"))

ALIAS = {  # слово в тексте события -> субъект на карте
    "подмосков": "Московская область", "петербург": "Санкт-Петербург", "питер": "Санкт-Петербург",
    "екатеринбург": "Свердловская область", "казан": "Татарстан", "нижний новгород": "Нижегородская область",
    "уф": None, "хмао": "Ханты-Мансийский автономный округ - Югра", "югр": "Ханты-Мансийский автономный округ - Югра",
    "янао": "Ямало-Ненецкий автономный округ", "тул": "Тульская область", "иванов": "Ивановская область",
    "осети": "Северная Осетия - Алания", "якути": "Республика Саха (Якутия)", "кузбас": "Кемеровская область",
    "ростов": "Ростовская область", "удмурт": "Удмуртская республика", "чуваш": "Чувашия",
    "башкир": "Башкортостан", "кабардин": "Кабардино-Балкарская республика", "черкес": "Карачаево-Черкесская республика",
    "чечн": "Чеченская республика", "ставропол": "Ставропольский край", "владивосток": "Приморский край",
    "хабаровск": "Хабаровский край", "мурманск": "Мурманская область", "сочи": "Краснодарский край",
}
SKIP = {"республика", "область", "край", "автономный", "округ", "автономная"}
SUFFIX = ("енская", "инская", "ская", "ский", "ия", "ая", "ий", "а")


def stems():
    out = {}
    for r in MAP["regions"]:
        n = r["name"]
        if n == "Москва":
            out["москв"] = n
            continue
        w = next((x for x in re.split(r"[\s\-()]+", n) if x and x.lower() not in SKIP), n)
        w = w.lower()
        for suf in SUFFIX:
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)]
                break
        out.setdefault(w, n)
    for k, v in ALIAS.items():
        if v:
            out[k] = v
    return out


STEMS = stems()


def match(region_text):
    t = region_text.lower().replace("ё", "е")
    found = set()
    for st, name in STEMS.items():
        if re.search(r"(?<![а-я])" + re.escape(st), t):
            found.add(name)
    # «Московская область» не должна ловиться на «Москва», и наоборот
    return found


def build(events, upd, lang="ru"):
    today = date.fromisoformat(upd[:10])
    reg_ev, nation = {}, []
    for i, e in enumerate(events):
        age = (today - date.fromisoformat(e["date"])).days
        if age > 30 or age < 0:
            continue
        rt = e.get("region_en") if lang == "en" and False else e["region"]
        hits = match(rt)
        item = {"d": e["date"], "t": e.get("title_en") if lang == "en" else e["title"], "a": age, "k": e["type"]}
        if not hits:
            nation.append(item)
        for h in hits:
            reg_ev.setdefault(h, []).append(item)
    en = lang == "en"
    names = {r["name"]: (r["en"] if en else r["name"]) for r in MAP["regions"]}
    paths = []
    for r in MAP["regions"]:
        n = r["name"]
        paths.append(f'<path d="{r["d"]}" data-n="{html.escape(n)}"><title>{html.escape(names[n])}</title></path>')
    # Москва и Петербург крошечные: кружки поверх
    dots = ""
    for n in ("Москва", "Санкт-Петербург"):
        r = next(x for x in MAP["regions"] if x["name"] == n)
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", r["d"])]
        xs, ys = nums[0::2], nums[1::2]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        dots += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" data-n="{html.escape(n)}"><title>{html.escape(names[n])}</title></circle>'
    data = {"ev": reg_ev, "nat": nation, "names": names}
    T = {
        "ru": {"h": "Карта ограничений", "p": "Где за последнее время сообщали об отключениях, белых списках и сбоях. Нажмите на регион, чтобы увидеть события.",
               "d7": "7 дней", "d30": "30 дней", "none": "В этом регионе за период событий нет.", "nat": "По всей стране",
               "pick": "Выберите регион на карте", "zin": "Крупнее", "zout": "Вся Россия", "l0": "нет событий", "l1": "1", "l2": "2-3", "l3": "4+"},
        "en": {"h": "Restrictions map", "p": "Where shutdowns, whitelists and outages were reported recently. Tap a region to see events.",
               "d7": "7 days", "d30": "30 days", "none": "No events in this region for the period.", "nat": "Nationwide",
               "pick": "Pick a region on the map", "zin": "Zoom in", "zout": "All Russia", "l0": "no events", "l1": "1", "l2": "2-3", "l3": "4+"},
    }[lang]
    css = """<style>
.rmap{margin:22px 0;padding:20px;border-radius:var(--r-lg);background:var(--card);border:1px solid var(--line)}
.rmap h2{margin:0 0 6px}.rmap>p{margin:0 0 14px;color:var(--soft)}
.rmap-t{display:flex;gap:8px;margin-bottom:10px}.rmap-t button{font:700 14px Manrope,sans-serif;background:var(--card2);color:var(--soft);border:1px solid var(--line2);border-radius:999px;padding:8px 14px;cursor:pointer;min-height:40px}
.rmap-t button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.rmap svg{width:100%;height:auto;display:block;touch-action:manipulation}
.rmap path,.rmap circle{stroke:var(--bg,#0b0716);stroke-width:.6;cursor:pointer;transition:fill .2s}
.rmap circle{stroke-width:1.5}
.rmap path:hover,.rmap circle:hover,.rmap .on{stroke:var(--text);stroke-width:1.4}
.rmap-l{display:flex;flex-wrap:wrap;gap:12px;font-size:13px;color:var(--soft);margin:10px 0}
.rmap-l i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.rmap-i{margin-top:8px;padding:14px 16px;border-radius:14px;background:var(--card2);min-height:52px}
.rmap-i b{display:block;margin-bottom:6px}.rmap-i ul{margin:0;padding-left:18px}.rmap-i li{margin:4px 0;font-size:15px}
.rmap-i small{color:var(--soft)}
</style>"""
    js = ("<script>(function(){var D=" + json.dumps(data, ensure_ascii=False) + ",days=7,el=document.getElementById('rmap'),info=el.querySelector('.rmap-i'),cur=null;"
          "var C=['var(--card2)','#f6c177','#f08a5d','#e84855'];"
          "function lv(n){return n<1?0:n<2?1:n<4?2:3}"
          "function evs(n){return (D.ev[n]||[]).filter(function(e){return e.a<days})}"
          "function paint(){el.querySelectorAll('[data-n]').forEach(function(p){var c=C[lv(evs(p.getAttribute('data-n')).length)];p.style.fill=c})}"
          "function show(n){cur=n;el.querySelectorAll('.on').forEach(function(x){x.classList.remove('on')});"
          "el.querySelectorAll('[data-n=\"'+n+'\"]').forEach(function(x){x.classList.add('on')});"
          "var L=evs(n),h='<b>'+D.names[n]+'</b>';"
          "h+=L.length?'<ul>'+L.slice(0,6).map(function(e){return '<li><small>'+e.d.slice(8,10)+'.'+e.d.slice(5,7)+'</small> '+e.t+'</li>'}).join('')+'</ul>'+(L.length>6?'<small>+'+(L.length-6)+'</small>':''):'<small>" + T["none"] + "</small>';"
          "var N=D.nat.filter(function(e){return e.a<days});if(N.length)h+='<b style=\"margin-top:10px\">" + T["nat"] + "</b><ul>'+N.map(function(e){return '<li><small>'+e.d.slice(8,10)+'.'+e.d.slice(5,7)+'</small> '+e.t+'</li>'}).join('')+'</ul>';"
          "info.innerHTML=h}"
          "el.querySelectorAll('[data-n]').forEach(function(p){p.addEventListener('click',function(){show(p.getAttribute('data-n'));"
          "try{goatcounter.count({path:'map/region',title:'map region',event:true})}catch(e){}})});"
          "el.querySelectorAll('.rmap-t button').forEach(function(b){b.addEventListener('click',function(){days=+b.getAttribute('data-d');"
          "el.querySelectorAll('.rmap-t button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});paint();if(cur)show(cur)})});"
          "var svg=el.querySelector('svg'),full=svg.getAttribute('viewBox'),z=el.querySelector('.rmap-z'),zoomed=false;"
          "function fit(){var b=null;el.querySelectorAll('path[data-n]').forEach(function(p){if(!evs(p.getAttribute('data-n')).length)return;var r=p.getBBox();"
          "if(r.width>250)return;b=b?{x1:Math.min(b.x1,r.x),y1:Math.min(b.y1,r.y),x2:Math.max(b.x2,r.x+r.width),y2:Math.max(b.y2,r.y+r.height)}:{x1:r.x,y1:r.y,x2:r.x+r.width,y2:r.y+r.height}});"
          "if(!b)return full;var w=Math.max(b.x2-b.x1,200)+60,h=Math.max(b.y2-b.y1,140)+60;h=Math.max(h,w*0.6);w=Math.max(w,h/0.6);"
          "var cx=(b.x1+b.x2)/2,cy=(b.y1+b.y2)/2;return (cx-w/2)+' '+(cy-h/2)+' '+w+' '+h}"
          "function setZ(on){zoomed=on;svg.setAttribute('viewBox',on?fit():full);z.textContent=on?'" + T["zout"] + "':'" + T["zin"] + "'}"
          "z.addEventListener('click',function(){setZ(!zoomed)});"
          "paint();if(innerWidth<700)setZ(true);var best=Object.keys(D.ev).sort(function(a,b){return evs(b).length-evs(a).length})[0];if(best&&evs(best).length)show(best)})();</script>")
    legend = "".join(f'<span><i style="background:{c}"></i>{l}</span>' for c, l in
                     (("var(--card2)", T["l0"]), ("#f6c177", T["l1"]), ("#f08a5d", T["l2"]), ("#e84855", T["l3"])))
    return (css + f'<section class="rmap" id="rmap"><h2>{T["h"]}</h2><p>{T["p"]}</p>'
            f'<div class="rmap-t"><button type="button" data-d="7" aria-pressed="true">{T["d7"]}</button>'
            f'<button type="button" data-d="31" aria-pressed="false">{T["d30"]}</button>'
            f'<button type="button" class="rmap-z" style="margin-left:auto">{T["zin"]}</button></div>'
            f'<svg viewBox="0 0 {MAP["w"]} {MAP["h"]}" role="img" aria-label="{T["h"]}">{"".join(paths)}{dots}</svg>'
            f'<div class="rmap-l">{legend}</div><div class="rmap-i"><small>{T["pick"]}</small></div></section>' + js)
