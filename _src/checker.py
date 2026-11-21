"""Виджет проверки интернета (/check/ и /en/check/): два режима, «Сайты и VPN» и «Белые списки»."""
import json
from pathlib import Path

PROBES = json.loads((Path(__file__).parent / "data" / "probes.json").read_text(encoding="utf-8"))

T = {
    "ru": {
        "tab_sites": "Сайты и VPN", "tab_wl": "Белые списки",
        "sites_hint": "Включите VPN и нажмите кнопку. Проверим, открываются ли сервисы, которые в России блокируют.",
        "wl_hint": "Выключите VPN и Wi-Fi, оставьте только мобильный интернет и нажмите кнопку. Проверим, включены ли у вас белые списки.",
        "btn_sites": "Проверить сайты", "btn_wl": "Проверить белые списки",
        "g_control": "Обычный интернет", "g_blocked": "Сервисы, которые блокируют в России",
        "g_white": "Сайты из белого списка", "g_open": "Обычные сайты вне белого списка",
        "ok": "открывается", "slow": "медленно", "fail": "не открывается", "wait": "проверяем…",
        "running": "Проверяем…", "again": "Проверить ещё раз",
        "v_none": ["Похоже, интернета нет вообще", "Не открываются даже российские сайты. Так бывает при полном отключении мобильного интернета или слабом сигнале. VPN тут не поможет: подключитесь к Wi-Fi или домашнему интернету.", "/status/", "Что отключают сегодня"],
        "v_wl": ["Похоже на белые списки", "Российские сервисы открываются, а обычные зарубежные сайты нет. Проверьте во вкладке «Белые списки». Помогает Wi-Fi или VPN с обходом белых списков.", "#wl", "Проверить белые списки"],
        "v_off": ["Интернет есть, но заблокированные сервисы не открываются", "Скорее всего, VPN выключен или его сервер заблокирован. Включите VPN, смените сервер или обновите подписку в приложении.", "/blog/vpn-podklyuchen-no-net-interneta/", "Что делать по шагам"],
        "v_part": ["VPN работает, но не всё открывается", "Не открывается: {list}. Смените сервер в приложении и проверьте ещё раз. Если не открывается одно приложение, перезапустите его.", "/blog/vpn-podklyuchen-no-net-interneta/", "Что делать по шагам"],
        "v_good": ["VPN работает: заблокированные сервисы открываются", "Всё в порядке. Если какое-то приложение всё равно не работает, перезапустите его.", "/blog/", "Полезные инструкции"],
        "v_slow": "Доступ есть, но {list} отвечает медленно. Попробуйте сервер в более близкой стране.",
        "w_on": ["Белые списки включены", "Открываются только сайты из белого списка, остальной интернет закрыт. Обычный VPN в таком режиме не работает. Подключитесь к Wi-Fi или включите VPN с обходом белых списков.", "/blog/belye-spiski-chto-eto/", "Что такое белые списки"],
        "w_off": ["Белых списков сейчас нет", "Открываются и сайты из белого списка, и обычные. Если при этом включён VPN, он может обходить ограничения: для точной проверки выключите VPN и Wi-Fi и нажмите ещё раз.", "/status/", "Статус блокировок сегодня"],
        "w_none": ["Интернета нет совсем", "Не открываются даже сайты из белого списка. Похоже на полное отключение или слабый сигнал. Подключитесь к Wi-Fi.", "/status/", "Что отключают сегодня"],
        "w_mixed": ["Связь нестабильная", "Часть сайтов открывается, часть нет. Так бывает при плохом сигнале или в начале ограничений. Проверьте ещё раз через минуту.", "/status/", "Статус блокировок сегодня"],
        "more": "Подробнее", "status": "/status/",
    },
    "en": {
        "tab_sites": "Sites and VPN", "tab_wl": "Whitelist",
        "sites_hint": "Turn your VPN on and press the button. We'll check whether services blocked in Russia open.",
        "wl_hint": "Turn off VPN and Wi-Fi, keep only mobile data, and press the button. We'll check whether whitelist mode is on.",
        "btn_sites": "Check sites", "btn_wl": "Check whitelist",
        "g_control": "Regular internet", "g_blocked": "Services blocked in Russia",
        "g_white": "Whitelisted sites", "g_open": "Regular sites outside the whitelist",
        "ok": "opens", "slow": "slow", "fail": "blocked", "wait": "checking…",
        "running": "Checking…", "again": "Check again",
        "v_none": ["Looks like there is no internet at all", "Even Russian sites don't open. This happens when mobile internet is fully shut down or the signal is weak. A VPN won't help: connect to Wi-Fi or home internet.", "/en/status/", "What is shut down today"],
        "v_wl": ["Looks like whitelist mode", "Russian services open but regular foreign sites don't. Check it in the Whitelist tab. Wi-Fi or a VPN with whitelist bypass helps.", "#wl", "Check whitelist"],
        "v_off": ["Internet works, but blocked services don't open", "Your VPN is probably off or its server is blocked. Turn the VPN on, change the server or refresh the subscription in the app.", "/en/blog/vpn-podklyuchen-no-net-interneta/", "What to do, step by step"],
        "v_part": ["VPN works, but not everything opens", "Not opening: {list}. Change the server in the app and check again. If only one app fails, restart it.", "/en/blog/vpn-podklyuchen-no-net-interneta/", "What to do, step by step"],
        "v_good": ["VPN works: blocked services open", "All good. If some app still doesn't work, restart it.", "/en/blog/", "Helpful guides"],
        "v_slow": "Access works, but {list} responds slowly. Try a server in a closer country.",
        "w_on": ["Whitelist mode is on", "Only whitelisted sites open, the rest of the internet is closed. A regular VPN doesn't work in this mode. Connect to Wi-Fi or use a VPN with whitelist bypass.", "/en/blog/belye-spiski-chto-eto/", "What whitelists are"],
        "w_off": ["No whitelist right now", "Both whitelisted and regular sites open. If your VPN is on, it may be bypassing restrictions: for an accurate check, turn off VPN and Wi-Fi and run it again.", "/en/status/", "Blocking status today"],
        "w_none": ["No internet at all", "Even whitelisted sites don't open. Looks like a full shutdown or weak signal. Connect to Wi-Fi.", "/en/status/", "What is shut down today"],
        "w_mixed": ["Unstable connection", "Some sites open, some don't. This happens with a weak signal or when restrictions are starting. Check again in a minute.", "/en/status/", "Blocking status today"],
        "more": "More", "status": "/en/status/",
    },
}

CSS = """<style>
.ck-tabs{display:flex;gap:8px;margin:0 0 16px;flex-wrap:wrap}
.ck .ck-tabs button{background:var(--card2);color:var(--soft);border:1px solid #2b2f44;font-size:15px;padding:11px 18px;min-height:44px;border-radius:999px}
.ck .ck-tabs button[aria-selected=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.ck-hint{color:var(--soft);margin:0 0 14px;font-size:15px}
.ck-g{margin:16px 0 0;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.ck-g+ul{margin-top:8px!important}
</style>"""


def widget(lang, bot, brand, trial, support):
    t = T[lang]
    probes = {k: [{"id": p["id"], "name": p.get("name_en", p["name"]) if lang == "en" else p["name"], "urls": p["urls"]}
                  for p in PROBES[k]] for k in ("control", "blocked", "whitelist", "open")}
    try_txt = f"Try {brand}, {trial}" if lang == "en" else f"Попробовать {brand} {trial}"
    sup_txt = "Message support" if lang == "en" else "Написать в поддержку"
    note = ("The check runs in your browser; we store nothing." if lang == "en"
            else "Проверка идёт в вашем браузере, мы ничего не сохраняем.")
    html = (f'{CSS}<div class="ck" id="check">'
            f'<div class="ck-tabs" role="tablist">'
            f'<button type="button" role="tab" id="ck-tab-sites" aria-selected="true">{t["tab_sites"]}</button>'
            f'<button type="button" role="tab" id="ck-tab-wl" aria-selected="false">{t["tab_wl"]}</button></div>'
            f'<p class="ck-hint" id="ck-hint">{t["sites_hint"]}</p>'
            f'<button id="ck-run" type="button">{t["btn_sites"]}</button>'
            f'<div id="ck-list" aria-live="polite"></div>'
            f'<div class="ck-out" id="ck-out" hidden><h2 id="ck-v"></h2><p id="ck-t"></p>'
            f'<div class="row"><a id="ck-a" href="{t["status"]}">{t["more"]} →</a>'
            f'<a href="{bot}" rel="nofollow">{try_txt} →</a>'
            f'<a href="{support}" target="_blank" rel="noopener nofollow">{sup_txt} →</a></div></div>'
            f'<p class="note" style="margin:14px 0 0">{note}</p></div>')
    js = JS.replace("__T__", json.dumps(t, ensure_ascii=False)).replace("__P__", json.dumps(probes, ensure_ascii=False))
    return html + f"<script>{js}</script>"


JS = r"""
(function(){
var T=__T__,P=__P__,mode='sites';
var $=function(id){return document.getElementById(id)};
var btn=$('ck-run'),list=$('ck-list'),out=$('ck-out'),hint=$('ck-hint'),tS=$('ck-tab-sites'),tW=$('ck-tab-wl');
function setMode(m){mode=m;tS.setAttribute('aria-selected',m==='sites');tW.setAttribute('aria-selected',m==='wl');
 hint.textContent=m==='wl'?T.wl_hint:T.sites_hint;btn.textContent=m==='wl'?T.btn_wl:T.btn_sites;list.textContent='';out.hidden=true;}
tS.onclick=function(){setMode('sites')};tW.onclick=function(){setMode('wl')};
if(location.hash==='#wl')setMode('wl');
window.addEventListener('hashchange',function(){if(location.hash==='#wl'){setMode('wl');$('check').scrollIntoView({behavior:'smooth'});}});
function one(url){return new Promise(function(res){var t0=performance.now(),done=false,img=new Image();
 var to=setTimeout(function(){if(!done){done=true;img.src='';res({ok:false,ms:8000});}},8000);
 img.onload=function(){if(!done){done=true;clearTimeout(to);res({ok:true,ms:Math.round(performance.now()-t0)});}};
 img.onerror=function(){if(!done){done=true;clearTimeout(to);res({ok:false,ms:Math.round(performance.now()-t0)});}};
 img.src=url+(url.indexOf('?')<0?'?':'&')+'t='+Date.now();});}
function probe(p){return new Promise(function(res){var left=p.urls.length,best=null;
 p.urls.forEach(function(u){one(u).then(function(r){left--;
  if(r.ok&&!best){best=r;res(r);}else if(!left&&!best){res({ok:false,ms:r.ms});}});});});}
function row(p,r){var li=document.createElement('li'),dot=document.createElement('span');dot.className='ck-dot';
 dot.style.background=r?(r.ok?(r.ms>3000?'#f59e0b':'#a3e635'):'#f87171'):'#3a3f52';li.appendChild(dot);
 var n=document.createElement('span');n.textContent=p.name;li.appendChild(n);var s=document.createElement('b');
 s.textContent=r?(r.ok?(r.ms>3000?T.slow:T.ok):T.fail):T.wait;li.appendChild(s);return li;}
function groups(){return mode==='wl'?[['g_white','whitelist'],['g_open','open']]:[['g_control','control'],['g_blocked','blocked']];}
function draw(R){list.textContent='';groups().forEach(function(g){var h=document.createElement('div');h.className='ck-g';h.textContent=T[g[0]];
 var ul=document.createElement('ul');P[g[1]].forEach(function(p){ul.appendChild(row(p,R?R[p.id]:null));});list.appendChild(h);list.appendChild(ul);});}
function names(arr){return arr.map(function(p){return p.name}).join(', ');}
function vSites(R){var ru=R.ru.ok,g=R.g.ok,b=P.blocked,okB=b.filter(function(p){return R[p.id].ok}),bad=b.filter(function(p){return !R[p.id].ok});
 if(!ru&&!g&&!okB.length)return T.v_none;
 if(ru&&!g&&!okB.length)return T.v_wl;
 if(okB.length<=b.length/3)return T.v_off;
 if(bad.length){var v=T.v_part.slice();v[1]=v[1].replace('{list}',names(bad));return v;}
 var slow=b.filter(function(p){return R[p.id].ms>3000});var v2=T.v_good.slice();
 if(slow.length)v2[1]=T.v_slow.replace('{list}',names(slow));return v2;}
function vWl(R){var w=P.whitelist.filter(function(p){return R[p.id].ok}).length,o=P.open.filter(function(p){return R[p.id].ok}).length;
 if(!w&&!o)return T.w_none;
 if(w>=P.whitelist.length-1&&o===0)return T.w_on;
 if(w>=P.whitelist.length-1&&o>=P.open.length-1)return T.w_off;
 return T.w_mixed;}
btn.addEventListener('click',function(){var all=[];groups().forEach(function(g){all=all.concat(P[g[1]]);});
 btn.disabled=true;btn.textContent=T.running;out.hidden=true;draw(null);
 Promise.all(all.map(probe)).then(function(rs){var R={};all.forEach(function(p,i){R[p.id]=rs[i];});draw(R);
  var v=mode==='wl'?vWl(R):vSites(R);$('ck-v').textContent=v[0];$('ck-t').textContent=v[1];
  var a=$('ck-a');a.href=v[2];a.textContent=v[3]+' →';out.hidden=false;
  btn.disabled=false;btn.textContent=T.again;
  try{if(window.goatcounter&&goatcounter.count)goatcounter.count({path:'check/'+mode+'/'+v[0],title:v[0],event:true});}catch(e){}
 });});
})();
"""
