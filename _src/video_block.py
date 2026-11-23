"""Блок с видеоинструкцией по сайту (RU/EN): плеер 9:16, главы с переходом по времени, VideoObject."""
import json

SITE = "https://thuggervpn.github.io"
V = {
    "ru": {"src": "/assets/video/guide-ru.mp4", "poster": "/assets/video/guide-ru.jpg", "dur": "PT1M18S", "len": 78,
           "h": "Видео: весь сайт за минуту", "chl": "Главы видео",
           "p": "Как проверить свой VPN, где смотреть статус блокировок и как поставить сайт на экран телефона. 78 секунд, со звуком.",
           "name": "Как пользоваться сайтом ThuggerVPN: проверка VPN, статус блокировок, инструкция",
           "ch": [(0, "Проверка VPN за 5 секунд"), (24, "Белые списки"), (29, "Статус блокировок"), (36, "Индекс блокировок"),
                  (43, "Страницы операторов"), (51, "Инструкция по подключению"), (58, "Приложение на экране"), (67, "Чат «Помощь»")]},
    "en": {"src": "/assets/video/guide-en.mp4", "poster": "/assets/video/guide-en.jpg", "dur": "PT1M6S", "len": 66,
           "h": "Video: the whole site in a minute", "chl": "Video chapters",
           "p": "How to check your VPN, where to see blocking status and how to add the site to your home screen. 66 seconds, with sound.",
           "name": "How to use the ThuggerVPN website: VPN check, blocking status, setup",
           "ch": [(0, "VPN check in 5 seconds"), (21, "Whitelist"), (26, "Blocking status"), (32, "Blocking index"),
                  (39, "Operator pages"), (44, "Setup guide"), (49, "Home screen app"), (56, "Help chat")]},
}
CSS = """<style>.vg{display:grid;grid-template-columns:minmax(0,300px) 1fr;gap:28px;align-items:center}
.vg video{cursor:pointer;width:100%;aspect-ratio:9/16;border-radius:var(--r-lg);border:1px solid var(--line);background:#0b0716;display:block}
.vg-ch{margin-top:14px}.vg ol{list-style:none;padding:0;margin:4px 0 14px;display:grid;gap:8px}
.vg ol button{all:unset;cursor:pointer;display:flex;gap:12px;align-items:center;padding:9px 14px;border-radius:12px;border:1px solid var(--line);background:var(--card);width:100%;box-sizing:border-box;font-size:15.5px}
.vg ol button:hover{border-color:var(--line-hi)}.vg ol b{color:var(--accent2);font-variant-numeric:tabular-nums;min-width:34px}
.vg video::-webkit-media-controls-overlay-play-button{display:none}
@media(max-width:700px){.vg{grid-template-columns:1fr}.vg video{max-width:300px;margin:0 auto}}</style>"""
JS = ("<script>(function(){var qt=+(new URLSearchParams(location.search).get('t')||0);document.querySelectorAll('.vg').forEach(function(g,gi){var v=g.querySelector('video');if(qt&&gi===0){var b0=[].slice.call(g.querySelectorAll('[data-t]')).filter(function(x){return +x.getAttribute('data-t')===qt})[0];setTimeout(function(){g.scrollIntoView({block:'center'});if(b0){var d=b0.closest('details');if(d)d.open=true;b0.click()}},300)}"
      "v.addEventListener('click',function(){if(!v.controls){v.controls=true;var p=v.play();if(p&&p.catch)p.catch(function(){})}});v.addEventListener('play',function(){v.controls=true});v.addEventListener('ended',function(){try{if(document.fullscreenElement)document.exitFullscreen();if(v.webkitDisplayingFullscreen)v.webkitExitFullscreen()}catch(e){}v.controls=false;v.removeAttribute('src');v.load();v._c=0});v.addEventListener('keydown',function(e){if(!v.controls&&(e.key==='Enter'||e.key===' ')){e.preventDefault();v.click()}});g.querySelectorAll('[data-t]').forEach(function(b){b.addEventListener('click',function(){var t=+b.getAttribute('data-t');function go(){v.currentTime=t;var p=v.play();if(p&&p.catch)p.catch(function(){})}if(v.readyState>=1)go();else{v.addEventListener('loadedmetadata',go,{once:true});v.preload='auto';v.load()}"
      "try{goatcounter.count({path:'video/chapter/'+b.getAttribute('data-t'),title:'video chapter',event:true})}catch(e){}})});"
      "v.addEventListener('play',function(){if(v._c)return;v._c=1;try{goatcounter.count({path:'video/play',title:'video play',event:true})}catch(e){}})})})();</script>")


def block(lang, sec_id="video", wrap=True, upload="2026-11-22T03:00:00+03:00", ld=False, page_url=None):
    t = V[lang]
    ch = "".join(f'<li><button type="button" data-t="{s}"><b>{s // 60}:{s % 60:02d}</b>{n}</button></li>' for s, n in t["ch"])
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": t["name"], "description": t["p"],
          "thumbnailUrl": SITE + t["poster"], "contentUrl": SITE + t["src"], "uploadDate": upload, "duration": t["dur"],
          "inLanguage": lang,
          "hasPart": [{"@type": "Clip", "name": n, "startOffset": s, "endOffset": (t["ch"][i + 1][0] if i + 1 < len(t["ch"]) else t["len"]), "url": f"{page_url}?t={s}"} for i, (s, n) in enumerate(t["ch"])]}
    inner = (f'<div class="vg"><video playsinline preload="none" tabindex="0" aria-label="{t['h']}" poster="{t["poster"]}"><source src="{t["src"]}" type="video/mp4"></video>'
             f'<div><h2>{t["h"]}</h2><details class="acc-q vg-ch"><summary>{t["chl"]}</summary><ol>{ch}</ol></details></div></div>'
             + (f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld and page_url else ''))
    return CSS + (f'<section class="sec" id="{sec_id}">{inner}</section>' if wrap else inner) + JS


W = {
    "ru": {"path": "/video/", "home": ("Главная", "/"), "crumb": "Видеоинструкция",
           "title": "Видеоинструкция: как пользоваться сайтом ThuggerVPN",
           "desc": "Видео за минуту: проверка VPN и белых списков, статус и индекс блокировок, страницы операторов, инструкция и приложение на экране.",
           "tr": "Текст видео"},
    "en": {"path": "/en/video/", "home": ("Home", "/en/"), "crumb": "Video guide",
           "title": "Video guide: how to use the ThuggerVPN website",
           "desc": "A one-minute video: VPN and whitelist check, blocking status and index, operator pages, setup guide and the home screen app.",
           "tr": "Transcript"},
}


def watch_page(lang, urls, UPD):
    import os, re, html
    import build as B
    w = W[lang]
    url = SITE + w["path"]
    raw = open(os.path.join(os.path.dirname(__file__), "video", "script.txt" if lang == "ru" else "script_en.txt"), encoding="utf-8").read()
    raw = raw.replace("Тагер ВиПиЭн", "ThuggerVPN").replace("Tugger V.P.N.", "ThuggerVPN")
    def fix(word):
        if "VPN" in word or "МегаФон" in word or "MegaFon" in word or not any(c.islower() for c in word): return word
        i = next((n for n, c in enumerate(word) if c.isalpha()), 0)
        return word[:i + 1] + word[i + 1:].lower()
    paras = ["".join(fix(x) if x.strip() else x for x in re.split(r"(\s+)", p)) for p in raw.strip().split("\n\n")]
    tr = "".join(f"<p>{html.escape(p)}</p>" for p in paras)
    body = (f'<article class="narrow" style="margin:0 auto">{B.crumbs_html([w["home"], (w["crumb"], w["path"])])}'
            f'<h1>{html.escape(w["title"])}</h1>'
            + block(lang, wrap=False, ld=True, page_url=url) +
            f'<h2 style="margin-top:36px">{w["tr"]}</h2>{tr}{B.cta_block() if lang == "ru" else ""}</article>')
    B.write(w["path"].strip("/") + "/index.html", B.page(w["title"], w["desc"], w["path"], body, [], lang=lang))
    urls.append((w["path"], UPD))
