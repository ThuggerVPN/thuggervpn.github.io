"""Блок с видеоинструкцией по сайту (RU/EN): плеер 9:16, главы с переходом по времени, VideoObject."""
import json

SITE = "https://thuggervpn.github.io"
V = {
    "ru": {"src": "/assets/video/guide-ru.mp4", "poster": "/assets/video/guide-ru.jpg", "dur": "PT1M18S",
           "h": "Видео: весь сайт за минуту", "chl": "Главы видео",
           "p": "Как проверить свой VPN, где смотреть статус блокировок и как поставить сайт на экран телефона. 78 секунд, со звуком.",
           "name": "Как пользоваться сайтом ThuggerVPN: проверка VPN, статус блокировок, инструкция",
           "ch": [(0, "Проверка VPN за 5 секунд"), (24, "Белые списки"), (29, "Статус блокировок"), (36, "Индекс блокировок"),
                  (43, "Страницы операторов"), (51, "Инструкция по подключению"), (58, "Приложение на экране"), (67, "Чат «Помощь»")]},
    "en": {"src": "/assets/video/guide-en.mp4", "poster": "/assets/video/guide-en.jpg", "dur": "PT1M6S",
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
JS = ("<script>(function(){document.querySelectorAll('.vg').forEach(function(g){var v=g.querySelector('video');"
      "v.addEventListener('click',function(){if(!v.controls){v.controls=true;var p=v.play();if(p&&p.catch)p.catch(function(){})}});v.addEventListener('play',function(){v.controls=true});v.addEventListener('ended',function(){try{if(document.fullscreenElement)document.exitFullscreen();if(v.webkitDisplayingFullscreen)v.webkitExitFullscreen()}catch(e){}v.controls=false;v.removeAttribute('src');v.load();v._c=0});v.addEventListener('keydown',function(e){if(!v.controls&&(e.key==='Enter'||e.key===' ')){e.preventDefault();v.click()}});g.querySelectorAll('[data-t]').forEach(function(b){b.addEventListener('click',function(){var t=+b.getAttribute('data-t');function go(){v.currentTime=t;var p=v.play();if(p&&p.catch)p.catch(function(){})}if(v.readyState>=1)go();else{v.addEventListener('loadedmetadata',go,{once:true});v.preload='auto';v.load()}"
      "try{goatcounter.count({path:'video/chapter/'+b.getAttribute('data-t'),title:'video chapter',event:true})}catch(e){}})});"
      "v.addEventListener('play',function(){if(v._c)return;v._c=1;try{goatcounter.count({path:'video/play',title:'video play',event:true})}catch(e){}})})})();</script>")


def block(lang, sec_id="video", wrap=True, upload="2026-11-22"):
    t = V[lang]
    ch = "".join(f'<li><button type="button" data-t="{s}"><b>{s // 60}:{s % 60:02d}</b>{n}</button></li>' for s, n in t["ch"])
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": t["name"], "description": t["p"],
          "thumbnailUrl": SITE + t["poster"], "contentUrl": SITE + t["src"], "uploadDate": upload, "duration": t["dur"],
          "inLanguage": lang,
          "hasPart": [{"@type": "Clip", "name": n, "startOffset": s, "url": f"{SITE}{'/en' if lang == 'en' else ''}/#t={s}"} for s, n in t["ch"]]}
    inner = (f'<div class="vg"><video playsinline preload="none" tabindex="0" aria-label="{t['h']}" poster="{t["poster"]}"><source src="{t["src"]}" type="video/mp4"></video>'
             f'<div><h2>{t["h"]}</h2><details class="acc-q vg-ch"><summary>{t["chl"]}</summary><ol>{ch}</ol></details></div></div>'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return CSS + (f'<section class="sec" id="{sec_id}">{inner}</section>' if wrap else inner) + JS
