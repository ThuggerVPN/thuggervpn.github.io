"""English version of the site (/en/...). Called from build.py main()."""
import json
from datetime import date

import build as B

esc = B.esc
CFG, SITE, BRAND, BOT = B.CFG, B.SITE, B.BRAND, B.BOT
SUPPORT, CHANNEL, VPNSTATUS, SRC = B.SUPPORT, B.CHANNEL, B.VPNSTATUS, B.SRC
EN = CFG.get("en", {})
TRIAL = EN.get("trial", "3 days free")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
OPS = {"mts": "MTS", "beeline": "Beeline", "megafon": "MegaFon", "t2": "T2 (Tele2)"}
TYPE_LABELS = {"whitelist": "Whitelist only", "outage": "Internet shutdowns", "slow": "Slowdowns and disruptions",
               "vpn_block": "VPN and protocol blocks", "service": "Service outages",
               "policy": "Government and carrier decisions"}


def d(iso, year=True):
    x = date.fromisoformat(iso)
    return f"{x.day} {MONTHS[x.month - 1]}" + (f" {x.year}" if year else "")


def upd(st, year=True):
    return d(st["updated"], year) + (f", {st['updated_time']} MSK" if st.get("updated_time") else " (MSK)")


def f(e, k):
    return e.get(k + "_en") or e.get(k, "")


def page(title, desc, path, body, ld=None, og="website"):
    return B.page(title, desc, path, body, ld, og, lang="en")


def jsonld(meta, path, crumbs):
    objs = B.article_jsonld(meta, path, crumbs)
    objs[0]["inLanguage"] = "en"
    objs[0]["image"] = f"{SITE}/og2-en.png"
    return objs


def min_price():
    return min([p["per_month"] for p in CFG.get("plans", [])] or [210])


def cta():
    return (f'<div class="cta"><div><b>VPN dropped again?</b>'
            f'<p>{TRIAL} - test it on your carrier. Then from {min_price()} ₽ a month.</p></div>'
            f'<div class="links"><a class="btn" href="{BOT}" rel="nofollow">Try {TRIAL}</a>'
            f'<a class="small" href="{VPNSTATUS}" target="_blank" rel="noopener">Customer reviews on vpnstatus.site ↗</a></div></div>')


def related(a, posts):
    rel = [p for p in posts if p["slug"] != a["slug"]][:3]
    items = "".join(f'<li><a href="/en/blog/{p["slug"]}/"><b>{esc(p["title"])}</b>'
                    f'<span>{esc(p["description"])}</span></a></li>' for p in rel)
    return (f'<h2>Read next</h2><ul class="list">{items}<li><a href="/en/check/"><b>Check your internet in 5 seconds</b>'
            f'<span>Whitelist, shutdown or VPN problem - find out right away</span></a></li></ul>')


def ops_label(e):
    if "all" in e.get("operators", ["all"]):
        return "all carriers"
    return ", ".join(OPS[o] for o in e["operators"] if o in OPS)


def table(events):
    if not events:
        return ""
    rows = ""
    for e in events:
        src = (f' <a href="{esc(e["url"])}" target="_blank" rel="noopener nofollow">{esc(f(e, "source"))}</a> (in Russian)'
               if e.get("url") else "")
        rows += (f'<tr><td style="white-space:nowrap">{d(e["date"], False)}</td><td>{esc(f(e, "region"))}</td>'
                 f'<td>{esc(f(e, "title"))}.<br><small style="color:var(--muted)">Source:{src}</small></td>'
                 f'<td>{esc(f(e, "meaning"))}</td></tr>')
    return ('<div class="tbl"><table><thead><tr><th>Date</th><th>Where</th><th>What happened</th>'
            f'<th>What it means for you</th></tr></thead><tbody>{rows}</tbody></table></div>')


def status_block(st):
    fresh = B.recent(st["events"], st["updated"], 3)
    if fresh:
        return table(fresh)
    return ('<p><b>No major new outages found in open sources in the last two days.</b> Latest known events:</p>'
            + table(st["events"][:3]))


PROBE_MAP = [
    ("Российский сервис (Яндекс)", "Russian service (Yandex)"),
    ("Обычный зарубежный сайт (Google)", "Regular foreign site (Google)"),
    ("'медленно'", "'slow'"), ("'открывается'", "'opens'"), ("'не открывается'", "'blocked'"),
    ("'проверяем…'", "'checking…'"),
    ("'Похоже, интернета нет вообще'", "'Looks like there is no internet at all'"),
    ("'Не открываются даже российские сайты. Так бывает при полном отключении мобильного интернета или слабом сигнале. VPN тут не поможет: подключитесь к Wi-Fi или домашнему интернету.'",
     "'Even Russian sites don\\'t open. This happens when mobile internet is fully shut down or the signal is weak. A VPN won\\'t help: connect to Wi-Fi or home internet.'"),
    ("'/status/','Что отключают сегодня'", "'/en/status/','What is shut down today'"),
    ("'Похоже на режим белых списков'", "'Looks like whitelist mode'"),
    ("'Российские сервисы открываются, а обычные зарубежные сайты - нет. Это белые списки на мобильном интернете. Подключитесь к Wi-Fi или используйте VPN с обходом белых списков.'",
     "'Russian services open but regular foreign sites don\\'t. That\\'s a mobile internet whitelist. Connect to Wi-Fi or use a VPN with whitelist bypass.'"),
    ("'/blog/belye-spiski-chto-eto/','Что такое белые списки'", "'/en/blog/belye-spiski-chto-eto/','What whitelists are'"),
    ("'Интернет есть, но заблокированные сервисы не открываются'", "'Internet works, but blocked services don\\'t open'"),
    ("'Скорее всего, VPN выключен или его сервер заблокирован. Включите VPN, смените сервер или обновите подписку. Если не помогает - пора сменить сервис.'",
     "'Your VPN is probably off or its server is blocked. Turn the VPN on, change the server or refresh the subscription. If that doesn\\'t help, it\\'s time to switch services.'"),
    ("'/blog/vpn-podklyuchen-no-net-interneta/','Что делать по шагам'", "'/en/blog/vpn-podklyuchen-no-net-interneta/','What to do, step by step'"),
    ("'VPN работает: заблокированные сервисы открываются'", "'VPN works: blocked services open'"),
    ("'Доступ есть, но YouTube отвечает медленно. Попробуйте сервер в более близкой стране.'",
     "'Access works, but YouTube responds slowly. Try a server in a closer country.'"),
    ("'Всё в порядке. Если какое-то приложение всё равно не работает - перезапустите его.'",
     "'All good. If some app still doesn\\'t work, restart it.'"),
    ("'/blog/','Полезные инструкции'", "'/en/blog/','Helpful guides'"),
    ("'Проверяем…'", "'Checking…'"), ("'Проверить ещё раз'", "'Check again'"),
]


def probe_js():
    js = B.PROBE_JS
    for a, b in PROBE_MAP:
        assert a in js, a
        js = js.replace(a, b)
    return js


def faq_html(faq):
    return "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq if a)


def build(ST):
    urls = []
    UPD = ST["updated"]
    arts = [B.parse(p) for p in sorted((SRC / "articles_en").glob("*.md"))]
    status = next((a for a in arts if a["slug"] == "status"), None)
    posts = sorted([a for a in arts if a["slug"] != "status"], key=lambda a: (a["date"], a["slug"]), reverse=True)
    home_c = ("Home", "/en/")

    for a in posts:
        path = f"/en/blog/{a['slug']}/"
        crumbs = [home_c, ("Articles", "/en/blog/"), (a["title"], path)]
        body = (f'<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}<h1>{esc(a["title"])}</h1>'
                f'<div class="meta">{d(a["date"])}</div>{a["body_html"]}{cta()}{related(a, posts)}</article>')
        B.write(path.strip("/") + "/index.html", page(f'{a["title"]} | {BRAND}', a["description"], path, body,
                                                      jsonld(a, path, crumbs), "article"))
        urls.append((path, a["updated"]))

    items = "".join(f'<li><a href="/en/blog/{a["slug"]}/"><b>{esc(a["title"])}</b><span>{esc(a["description"])}</span></a></li>'
                    for a in posts)
    B.write("en/blog/index.html", page(f"Articles | {BRAND}", "Guides: what to do if your VPN stops working in Russia, whitelists, mobile internet outages.",
                                       "/en/blog/", f'<div class="narrow" style="margin:0 auto"><h1 style="font-size:40px">Articles</h1>'
                                       f"<ul class='list'>{items}</ul></div>"))
    urls.append(("/en/blog/", UPD))

    # status
    if status:
        path = "/en/status/"
        crumbs = [home_c, (status["title"], path)]
        bh = status["body_html"].replace("<p>{{STATUS_TABLE}}</p>", status_block(ST) + (
            f'<p>Daily summary on Telegram (in Russian): <a href="{CHANNEL}" target="_blank" rel="noopener">@{CHANNEL.rsplit("/", 1)[-1]}</a></p>'
            if CHANNEL else ""))
        status["updated"] = UPD
        body = (f'<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}<h1>{esc(status["title"])}</h1>'
                f'<div class="meta">Updated {upd(ST)}</div>{bh}{cta()}</article>')
        B.write("en/status/index.html", page(f'{status["title"]} | {BRAND}', status["description"], path, body,
                                             jsonld(status, path, crumbs)))
        urls.append((path, UPD))

    # check
    path = "/en/check/"
    crumbs = [home_c, ("Internet check", path)]
    cfaq = [("How does the check work?", "The page tries to load tiny icons from a Russian service, a regular foreign site "
             "and blocked services. What loads and what doesn't shows whether you have a whitelist, a full shutdown or a VPN problem."),
            ("Do you store my data?", "No. The check runs entirely in your browser; nothing is sent to our server."),
            ("How accurate is it?", "It's a quick approximate check. If the result looks odd, run it again or compare mobile data and Wi-Fi.")]
    body = (f'{B.CHECK_CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}'
            f'<h1>What\'s wrong with my internet? 5-second check</h1>'
            f'<p class="lead"><b>In short:</b> press the button - the page checks whether Russian services, regular foreign sites '
            f'and blocked Telegram, Instagram and YouTube open, and tells you what to do.</p>'
            f'<div class="ck"><button id="ck-run" type="button">Check my internet</button><ul id="ck-list" aria-live="polite"></ul>'
            f'<div class="ck-out" id="ck-out" hidden><h2 id="ck-v"></h2><p id="ck-t"></p><div class="row">'
            f'<a id="ck-a" href="/en/status/">More →</a><a href="{BOT}" rel="nofollow">Try {BRAND}, {TRIAL} →</a>'
            f'<a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Message support →</a></div></div>'
            f'<p class="note" style="margin:14px 0 0">The check runs in your browser; we store nothing.</p></div>'
            f'<h2>How to read the result</h2><div class="tbl"><table><thead><tr><th>What you see</th><th>What it is</th><th>What to do</th></tr></thead><tbody>'
            f'<tr><td>Nothing opens</td><td>Internet is shut down or no signal</td><td>Wi-Fi or home internet</td></tr>'
            f'<tr><td>Only the Russian service opens</td><td>Whitelist</td><td>Wi-Fi or a VPN with whitelist bypass</td></tr>'
            f'<tr><td>Russian service and Google open, Telegram and Instagram don\'t</td><td>VPN off or blocked</td><td>Turn on the VPN, change server</td></tr>'
            f'<tr><td>Everything opens</td><td>VPN works</td><td>Nothing needed</td></tr></tbody></table></div>'
            f'<h2>FAQ</h2>{faq_html(cfaq)}{cta()}</article><script>{probe_js()}</script>')
    meta = {"title": "What's wrong with my internet? 5-second check", "date": "2026-11-19", "updated": UPD, "faq": cfaq,
            "description": "Free check: whitelist, mobile internet shutdown or a VPN problem. Runs in your browser, no data stored."}
    B.write("en/check/index.html", page(f'{meta["title"]} | {BRAND}', meta["description"], path, body, jsonld(meta, path, crumbs)))
    urls.append((path, UPD))

    # setup
    data = json.loads((SRC / "data" / "apps.json").read_text(encoding="utf-8"))
    bot_name = B.BOT_NAME
    tabs, panels = "", ""
    for i, dv in enumerate(data["devices"]):
        rec = dv["apps"][0]
        alts = "".join(f'<a href="{esc(a["url"])}" target="_blank" rel="noopener nofollow">{esc(a["app"])} · {esc(a.get("label_en", a["label"]))}</a>'
                       for a in dv["apps"][1:])
        nm = dv.get("name_en", dv["name"])
        tabs += (f'<button type="button" role="tab" id="tab-{dv["id"]}" aria-controls="p-{dv["id"]}" '
                 f'aria-selected="{"true" if i == 0 else "false"}" data-dev="{dv["id"]}">{esc(nm)}</button>')
        panels += (f'<div class="dev-panel" role="tabpanel" id="p-{dv["id"]}" aria-labelledby="tab-{dv["id"]}" data-panel="{dv["id"]}">'
                   f'<h3 style="margin:0 0 12px">{esc(nm)}</h3><div class="app-rec"><div><b>{esc(rec["app"])}</b>'
                   f'<small>Recommended · {esc(rec.get("label_en", rec["label"]))}</small></div>'
                   f'<a class="btn" href="{esc(rec["url"])}" target="_blank" rel="noopener nofollow">Download {esc(rec["app"])}</a></div>'
                   + (f'<p class="note" style="margin:14px 0 0">Store won\'t open or need another app:</p><div class="app-alt">{alts}</div>' if alts else "")
                   + ('<p class="note" style="margin:14px 0 0"><b>Russian Apple ID?</b> Incy, HAPP and V2RayTun have been removed from the Russian '
                      'App Store - the links open, but you can\'t download them with a Russian account. Already installed apps keep working. '
                      'For a new install you need an Apple ID from another country - <a href="#apple-id">here is how</a>.</p>'
                      if dv["id"] in ("ios", "mac") else "") + '</div>')
    tr = [("Is your subscription active?", f"Open {bot_name} → button <span class='kbd'>🌍 Мой VPN</span> (My VPN) → check the line <span class='kbd'>📆 Оплачен до</span> (Paid until). If it expired, renew in the bot."),
          ("Does the subscription have locations?", f"In {bot_name} → <span class='kbd'>🌍 Мой VPN</span> check <span class='kbd'>🌎 Локации в подписке</span> (Locations). If empty, tap <span class='kbd'>🔄 Обновить подписку</span> (Update subscription)."),
          ("Update the keys", f"In {bot_name} → <span class='kbd'>🌍 Мой VPN</span> → <span class='kbd'>🔄 Обновить подписку</span> and follow the prompts. Then paste the link into the app again."),
          ("It may be a whitelist", "Carriers can temporarily restrict mobile internet so that only approved sites work - government services, banks, major Russian services. If the VPN won't connect or pages won't load, connect to Wi-Fi. You can check what you have in 5 seconds on the check page.")]
    tr_html = "".join(f'<details class="acc-q"><summary>{i + 1}. {esc(q)}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(tr))
    path = "/en/podklyuchenie/"
    crumbs = [home_c, ("How to connect", path)]
    title = "How to set up ThuggerVPN: iPhone, Android, Windows, Mac, TV"
    sfaq = [("Which app should I choose?", "We recommend Incy - it's available for iPhone, Android, Windows, macOS and TVs. "
             "If it won't install, HAPP or V2RayTun work too: the subscription link works in any of them."),
            ("Where do I get the subscription link?", f"In the Telegram bot {bot_name}. Tap the link once and it's copied automatically."),
            ("How many devices can I connect?", EN.get("devices", "")),
            ("How do I download the app on an iPhone with a Russian Apple ID?", "Incy, HAPP and V2RayTun were removed from the Russian App Store. "
             "If the app is already installed, keep it. If not, you need an Apple ID from another country: in the App Store sign out of "
             "\"Media & Purchases\" only, sign in to the other account, download the app and switch back."),
            ("The VPN doesn't work - what now?", "Check that the subscription is active and has locations, update it in the bot. "
             "If only Russian sites open, it's a whitelist - connect to Wi-Fi. Still stuck? Message support.")]
    script = B.build_setup_page.__globals__.get("SETUP_SCRIPT", "")
    body = (f'{B.SETUP_CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}<h1>{esc(title)}</h1>'
            f'<p class="lead"><b>In short:</b> 4 steps, 2 minutes. Download the app, get your subscription link in the bot, '
            f'paste it into the app and tap "Connect".</p>'
            f'<div class="st4"><div><div class="n">1</div><div><h3>Download the app</h3><p>Pick your device - we detected it automatically.</p></div></div></div>'
            f'<div class="dev-tabs" role="tablist" aria-label="Device">{tabs}</div>{panels}'
            f'<div class="st4"><div><div class="n">2</div><div><h3>Copy your subscription link</h3><p>Open <a href="{BOT}" rel="nofollow">{bot_name}</a> '
            f'and get your personal link. Tap it once - it copies automatically. No subscription yet? Take {TRIAL}. '
            f'The bot is in Russian; the button you need is <span class="kbd">🌍 Мой VPN</span> (My VPN).</p></div></div>'
            f'<div><div class="n">3</div><div><h3>Paste the link into the app</h3><p>Open the app and tap <span class="kbd">From clipboard</span> '
            f'(may be labelled «Из буфера»).</p></div></div>'
            f'<div><div class="n">4</div><div><h3>Connect</h3><p>A server list appears. Pick a location and tap <span class="kbd">Connect</span>.</p></div></div></div>'
            f'<div class="done">✓ Done - your internet now runs through {esc(BRAND)}.</div>'
            f'<p style="margin:18px 0"><a class="btn" href="{BOT}" rel="nofollow">Get the link in {bot_name}</a></p>'
f'<h2 id="apple-id">iPhone with a Russian Apple ID</h2>'
            f'<p>Apple removed Incy, HAPP and V2RayTun from the Russian App Store. There is no other way to install apps on an iPhone in Russia: '
            f'installing outside the App Store is only allowed in the EU. What to do depends on your situation:</p>'
            f'<details class="acc-q" open><summary>The app is already installed</summary><p>Don\'t delete it - it keeps working. '
            f'Just update the subscription: {bot_name} → <span class="kbd">🌍 Мой VPN</span> (My VPN) → <span class="kbd">🔄 Обновить подписку</span> (Update subscription), '
            f'then paste the link into the app again.</p></details>'
            f'<details class="acc-q"><summary>No app yet: an Apple ID from another country</summary><p>'
            f'1. Open the App Store → tap your avatar → sign out of "Media & Purchases" only. Don\'t touch iCloud - your photos and contacts stay.<br>'
            f'2. Create a new Apple ID for another country (e.g. Kazakhstan, Turkey, the US) or sign in to an existing one.<br>'
            f'3. Download Incy (or HAPP, V2RayTun).<br>'
            f'4. Sign out and back into your own Apple ID - the app stays on the phone.<br>'
            f'<b>Note:</b> Apple asks for an address in the chosen country, and future app updates will need that same account.</p></details>'
            f'<details class="acc-q"><summary>An Apple ID of someone abroad</summary><p>You can download the app under the account of someone you trust: '
            f'sign in to "Media & Purchases" only, download the app and sign out. Don\'t save their password or sign in to their iCloud.</p></details>'
            f'<p>The subscription from the bot works with any of the three apps - install whichever you can download. Stuck on a step? '
            f'<a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Message support</a>.</p>'
            f'<h2>If the VPN doesn\'t work</h2>{tr_html}'
            f'<p>Still stuck? <a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Message support</a> or '
            f'<a href="/en/check/">check your internet in 5 seconds</a>.</p><h2>FAQ</h2>{faq_html(sfaq)}{cta()}</article>{script}')
    meta = {"title": title, "date": "2026-11-19", "updated": UPD, "faq": sfaq,
            "description": "Step-by-step: Incy, HAPP and V2RayTun apps for iPhone, Android, Windows, macOS and TV, subscription link from the bot, troubleshooting."}
    howto = {"@context": "https://schema.org", "@type": "HowTo", "name": title, "totalTime": "PT2M", "inLanguage": "en",
             "step": [{"@type": "HowToStep", "position": i + 1, "name": n, "text": t} for i, (n, t) in enumerate([
                 ("Download the app", "Install Incy (or HAPP, V2RayTun) for your device."),
                 ("Copy your subscription link", f"Get your personal link in the Telegram bot {bot_name}."),
                 ("Paste the link into the app", "Open the app and tap \"From clipboard\"."),
                 ("Connect", "Pick a location and tap \"Connect\".")])]}
    B.write("en/podklyuchenie/index.html", page(f"{title} | {BRAND}", meta["description"], path, body, jsonld(meta, path, crumbs) + [howto]))
    urls.append((path, UPD))

    # operators
    for slug, name in OPS.items():
        path = f"/en/operator/{slug}/"
        short = name.split(" ")[0]
        title = f"VPN not working on {short}: status for {d(UPD, False)} and what to do"
        evs = [e for e in B.recent(ST["events"], UPD, 14) if "all" in e["operators"] or slug in e["operators"]]
        own = [e for e in evs if slug in e["operators"]]
        summary = (f"In the last 14 days: {len(evs)} events affecting {short} subscribers"
                   + (f", {len(own)} of them specifically about {short}." if own else
                      f". No reports specifically about {short} - below are general restrictions for all carriers in the regions."))
        ofaq = [(f"Why does the VPN fail on {short} but work on Wi-Fi?",
                 "Whitelist restrictions and shutdowns are applied to mobile internet. Home internet and Wi-Fi aren't affected, so the same VPN keeps working there."),
                (f"Does {BRAND} work on {short}?",
                 f"User votes for {short} - whether the service works and bypasses whitelists - are in the independent catalog vpnstatus.site. You can test it on your phone for free: {TRIAL}."),
                ("What should I do right now?", "Run the internet check on our site: in 5 seconds it shows whether you have a whitelist, a shutdown or a VPN problem.")]
        others = " · ".join(f'<a href="/en/operator/{s}/">{n.split(" ")[0]}</a>' for s, n in OPS.items() if s != slug)
        crumbs = [home_c, ("Status", "/en/status/"), (short, path)]
        body = (f'{B.CHECK_CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}<h1>{esc(title)}</h1>'
                f'<div class="meta">Updated {d(UPD)}</div><p class="lead"><b>In short:</b> {esc(summary)}</p>'
                f'<p><a class="btn" href="/en/check/">Check my internet in 5 seconds</a></p><h2>Events in the last 14 days</h2>'
                + (table(evs) if evs else "<p>No outage reports in open sources in the last 14 days.</p>") +
                f'<h2>What to do if the VPN fails on {esc(short)}</h2><ol>'
                f'<li><b>Toggle airplane mode</b> - the phone re-registers on the network.</li>'
                f'<li><b>Change the VPN server</b> - specific addresses get blocked, not the whole service.</li>'
                f'<li><b>Refresh the subscription or configuration</b> in the app.</li>'
                f'<li><b>Test on Wi-Fi.</b> If it works there, it\'s a mobile network restriction.</li>'
                f'<li><b>Only government sites and Yandex open?</b> That\'s a whitelist: use Wi-Fi or a VPN with whitelist bypass.</li></ol>'
                f'<p>User votes for {esc(BRAND)} on {esc(short)}: <a href="{VPNSTATUS}" target="_blank" rel="noopener">vpnstatus.site ↗</a></p>'
                f'<h2>FAQ</h2>{faq_html(ofaq)}<p>Other carriers: {others}</p>{cta()}</article>')
        meta = {"title": title, "date": "2026-11-19", "updated": UPD, "faq": ofaq,
                "description": f"VPN and mobile internet status on {short} in Russia: outages and whitelists for 14 days, what to do step by step. Updated daily."}
        B.write(path.strip("/") + "/index.html", page(f"{title} | {BRAND}", meta["description"], path, body, jsonld(meta, path, crumbs)))
        urls.append((path, UPD))

    # index
    path = "/en/index-blokirovok/"
    last7 = B.recent(ST["events"], UPD, 7)
    prev7 = [e for e in ST["events"] if 7 <= B.days_between(UPD, e["date"]) < 14]
    last30 = B.recent(ST["events"], UPD, 30)
    c7, c30 = B.count_types(last7), B.count_types(last30)

    def bars(counts):
        mx = max([*counts.values(), 1])
        out = ""
        for t, label in TYPE_LABELS.items():
            n = counts.get(t, 0)
            w = max(2, round(100 * n / mx))
            out += (f'<div class="bar"><span>{esc(label)}</span><i style="width:{w}%;background:{B.TYPE_COLORS[t]};'
                    f'opacity:{1 if n else .25}"></i><b>{n}</b></div>')
        return f'<div class="bars">{out}</div>'
    delta = len(last7) - len(prev7)
    trend = "more" if delta > 0 else "fewer" if delta < 0 else "the same number"
    regions = {}
    for e in last30:
        regions[f(e, "region")] = regions.get(f(e, "region"), 0) + 1
    reg = "".join(f"<li>{esc(r)} - {n}</li>" for r, n in sorted(regions.items(), key=lambda x: -x[1])[:8])
    crumbs = [home_c, ("Blocking index", path)]
    ifaq = [("Where does the data come from?", "From open sources: media reports about outages, shutdowns, whitelists and blocks. "
             "Every event in the table links to its source."),
            ("Can I use the data?", f"Yes, with a link to {SITE}/en/index-blokirovok/. JSON data: {SITE}/data/blocking-events.json")]
    body = (f'{B.CHECK_CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}'
            f'<h1>Russia internet blocking index: week to {d(UPD)}</h1>'
            f'<div class="meta">Updated daily · open-source data</div>'
            f'<p class="lead"><b>In short:</b> {len(last7)} events recorded in 7 days - {trend} than the week before ({len(prev7)}). '
            f'{len(last30)} in 30 days.</p><h2>Last 7 days by type</h2>{bars(c7)}<h2>Last 30 days by type</h2>{bars(c30)}'
            f'<h2>Most affected (30 days)</h2><ul>{reg or "<li>No data</li>"}</ul>'
            f'<h2>All events in 30 days</h2>{table(last30) or "<p>No data.</p>"}'
            f'<h2>Methodology</h2><p>Every day we collect reports of mobile internet outages, whitelist modes, VPN blocks and service '
            f'outages in Russia from open sources. One event is one report about a specific region and day. It is not complete '
            f'statistics of every outage, but an indicator of what is being reported.</p>'
            f'<h2>FAQ</h2>{faq_html(ifaq)}{cta()}</article>')
    meta = {"title": "Russia internet blocking index", "date": "2026-11-19", "updated": UPD, "faq": ifaq,
            "description": "How many outages, mobile internet shutdowns and whitelists in Russia per week and month. Open-source data, updated daily."}
    ld = jsonld(meta, path, crumbs) + [{"@context": "https://schema.org", "@type": "Dataset",
                                        "name": "Russia internet blocking index (ThuggerVPN)", "inLanguage": "en",
                                        "description": "Daily updated list of mobile internet outages, whitelist modes, VPN blocks and service outages in Russia based on open-source reports.",
                                        "url": f"{SITE}{path}", "dateModified": UPD,
                                        "creator": {"@type": "Organization", "name": BRAND, "url": SITE},
                                        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                                                          "contentUrl": f"{SITE}/data/blocking-events.json"}]}]
    B.write("en/index-blokirovok/index.html", page(f'{meta["title"]} - week to {d(UPD)} | {BRAND}', meta["description"], path, body, ld))
    urls.append((path, UPD))

    # embed + informer
    rows = "".join(f'<li><small>{d(e["date"], False)} · {esc(f(e, "region"))}</small><b>{esc(f(e, "title"))}</b></li>'
                   for e in ST["events"][:3])
    emb = B.read_embed_template().replace("{{LANG}}", "en").replace("{{TITLE}}", "Blocking status").replace(
        "{{DATE}}", d(UPD, False)).replace("{{ROWS}}", rows).replace("{{LINK}}", f"{SITE}/en/status/").replace(
        "{{LINKTEXT}}", f"Full summary and what to do | {BRAND} →")
    B.write("en/embed/status/index.html", emb)
    code = (f'<iframe src="{SITE}/en/embed/status/" width="100%" height="360" style="border:0;max-width:420px" '
            f'loading="lazy" title="Blocking status | {BRAND}"></iframe>')
    path = "/en/informer/"
    crumbs = [home_c, ("Widget", path)]
    body = (f'{B.CHECK_CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}'
            f'<h1>"Blocking status" widget for your site</h1>'
            f'<p class="lead"><b>In short:</b> a free card with the latest internet outages in Russia. It updates itself daily - paste the code once.</p>'
            f'<h2>Preview</h2><iframe src="/en/embed/status/" width="100%" height="360" style="border:0;max-width:420px" title="Widget preview"></iframe>'
            f'<h2>Embed code</h2><textarea class="codebox" id="emb-code" readonly>{esc(code)}</textarea>'
            f'<p><button class="btn" type="button" id="emb-copy" style="border:0;cursor:pointer">Copy code</button></p></article>'
            f'<script>document.getElementById("emb-copy").addEventListener("click",function(){{var t=document.getElementById("emb-code");'
            f't.select();try{{navigator.clipboard.writeText(t.value)}}catch(e){{document.execCommand("copy")}}this.textContent="Copied";}});</script>')
    B.write("en/informer/index.html", page(f'"Blocking status" widget | {BRAND}', "Free widget with the latest internet outages in Russia for sites and blogs. Updates automatically.", path, body))
    urls.append((path, UPD))

    # home
    vp = SRC / "data" / "vpnstatus.json"
    vpd = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else None
    vlink = (vpd or {}).get("url", VPNSTATUS)
    plans = CFG.get("plans", [])
    pc = ""
    for pl in plans:
        save = round(100 - 100 * pl["per_month"] / plans[0]["per_month"])
        pc += (f'<div class="plan{" best" if pl.get("best") else ""}">' + ('<span class="tag">Best value</span>' if pl.get("best") else "")
               + f'<div class="pl-name">{esc(pl.get("label_en", pl["label"]))}</div><div class="pl-price">{pl["per_month"]} ₽<small>/mo</small></div>'
               f'<div class="pl-sub">{pl["total"]} ₽ total' + (f' · save {save}%' if save > 0 else "") + '</div></div>')
    revs, ops_rows = "", ""
    if vpd:
        revs = "".join(f'<div class="rv"><div class="stars sm">{B.STAR * 5}</div><p>{esc(r.get("text_en", r["text"]))}</p>'
                       f'<small>Customer · {esc(r.get("period_en", r["period"]))}</small></div>' for r in vpd["reviews"][:3])

        def cell(w, t):
            return '<span class="na">no votes</span>' if t in (None, 0) else f'<b>{w}/{t}</b>'
        ops_rows = "".join(f'<tr><td>{esc(o.get("name_en", o["name"]))}</td><td>{cell(o["works"], o["total"])}</td>'
                           f'<td>{cell(o["wl_works"], o["wl_total"])}</td></tr>' for o in vpd["mobile"])
    hfaq = [("Is there a free trial?", f"Yes, {TRIAL}. Test it on your carrier's mobile data and at home before paying."),
            ("How many devices can I connect?", EN.get("devices", "")),
            ("What is whitelist bypass?", "When mobile internet is switched to whitelist mode, regular VPNs stop working. "
             f"The bypass option is {EN.get('whitelist_detail', '')}."),
            ("What do I need to install?", "The Incy app (or HAPP, V2RayTun) for your device and the subscription link from the Telegram bot. Step-by-step guide is on the setup page."),
            ("What if it doesn't work?", "Message support @ThuggerVPN_supp - a real person will reply and help pick a working server."),
            ("Who is ThuggerVPN for?", "People in Russia and anyone who needs stable access to blocked services from Russian mobile and home networks. The bot and support work in Russian; this site has an English guide.")]
    faqh = "".join(f'<details class="acc-q"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in hfaq if a)
    tiles = "".join(f'<div class="st" style="border-top-color:{B.TYPE_COLORS.get(e["type"], "#a78bfa")}"><small>{d(e["date"], False)} · '
                    f'{esc(f(e, "region"))}</small><b>{esc(f(e, "title"))}</b><span>{esc(f(e, "meaning"))}</span></div>' for e in ST["events"][:3])
    chips = "".join(f'<a href="/en/operator/{s}/">{n.split(" ")[0]}</a>' for s, n in OPS.items())
    cards = "".join(f'<a class="tile" href="/en/blog/{a["slug"]}/"><div><div class="t-title">{esc(a["title"])}</div>'
                    f'<div class="t-sub">{esc(a["description"])}</div></div><span class="arrow" aria-hidden="true">↗</span></a>' for a in posts[:6])
    proof = (f'<a class="proof" href="{vlink}" target="_blank" rel="noopener">{B.STAR * 5}<span><b>{esc(vpd["rating"])}</b> · '
             f'{vpd["votes"]} ratings on vpnstatus.site</span></a>' if vpd else "")
    home = f"""{B.CHECK_CSS}
<section class="hero"><div class="hero-text">
<h1>A VPN that works in Russia when others drop</h1>
<p class="lead">Mobile and home internet, whitelist bypass. Set up in 2 minutes via Telegram.</p>
<div class="row"><a class="btn" href="{BOT}" rel="nofollow">Try {TRIAL}</a><a class="btn-ghost" href="#prices">Plans from {min_price()} ₽</a></div>
{proof}</div>
<div class="stage" aria-hidden="true"><div class="iso"><div class="grid"></div>
<div class="plate p1">Mobile internet</div><div class="plate p2">Home Wi-Fi</div>
<div class="plate p3">{B.SHIELD}<span>{BRAND}</span></div></div><div class="beam"></div></div></section>
<section class="sec usp">
<div class="u"><b>Mobile and home</b><span>MTS, MegaFon, Beeline, T2 and home internet</span></div>
<div class="u"><b>Whitelist bypass</b><span>Mobile option: {esc(EN.get("whitelist_detail", ""))}</span></div>
<div class="u"><b>Real support</b><span>A person answers in Telegram, not a bot</span></div></section>
<section class="sec" id="prices"><h2>Plans</h2><div class="plans">{pc}</div>
<p class="note">{esc(EN.get("devices", ""))}. Whitelist bypass - {esc(EN.get("whitelist_detail", ""))}. Start with {TRIAL}.</p>
<p><a class="btn" href="{BOT}" rel="nofollow">Start with {TRIAL}</a></p></section>
<section class="sec" id="how"><h2>How to connect</h2><div class="steps3">
<div><span>1</span><b>Download Incy</b><small>iPhone, Android, Windows, Mac, TV</small></div>
<div><span>2</span><b>Get the link in the bot</b><small>{TRIAL} - no payment</small></div>
<div><span>3</span><b>Paste and connect</b><small>"From clipboard" → "Connect"</small></div></div>
<p style="margin-top:16px"><a href="/en/podklyuchenie/">Detailed guide for your device →</a></p></section>
<section class="sec" id="reviews"><div class="trust2"><div class="tr-head"><div><h2>What customers say</h2>
<p>Ratings and reviews are in the independent catalog vpnstatus.site{(" · " + esc(vpd["rating"]) + "/5, " + str(vpd["votes"]) + " ratings") if vpd else ""}. Reviews are in Russian; summaries translated.</p></div>
<a class="btn-ghost" href="{vlink}" target="_blank" rel="noopener">All reviews ↗</a></div>
<div class="tr-revs">{revs}</div>
<details class="acc" style="margin-top:14px"><summary>Votes by carrier</summary>
<div class="tbl" style="margin:12px 0 0"><table class="tr-ops"><thead><tr><th>Mobile</th><th>Works</th><th>Whitelist bypass</th></tr></thead><tbody>{ops_rows}</tbody></table></div>
<p class="note">vpnstatus.site data as of {d(vpd["checked"]) if vpd else ""}.</p></details></div></section>
<section class="sec" id="more"><h2>Useful</h2>
<details class="acc"><summary>Blocking status · {d(UPD, False)}</summary><div class="st-grid" style="margin-top:14px">{tiles}</div>
<p style="margin:14px 0 0"><a href="/en/status/">Full summary →</a></p></details>
<details class="acc"><summary>Check your internet in 5 seconds</summary><p style="margin:12px 0">Find out what you have: whitelist, shutdown or a VPN problem.</p><a class="btn" href="/en/check/">Check internet</a></details>
<details class="acc"><summary>Status by carrier</summary><div class="chips" style="margin-top:14px">{chips}</div>
<p style="margin:14px 0 0"><a href="/en/index-blokirovok/">Weekly blocking index →</a></p></details>
<details class="acc"><summary>Guides if your VPN drops</summary><div class="bento" style="margin-top:14px">{cards}</div>
<p style="margin:14px 0 0"><a href="/en/blog/">All articles →</a></p></details></section>
<section class="sec" id="faq"><h2>FAQ</h2>{faqh}</section>
{cta()}
"""
    ld = [{"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "url": SITE, "logo": f"{SITE}/logo.png",
           "sameAs": [x for x in (B.BOT_PLAIN, VPNSTATUS, CHANNEL) if x]},
          {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": f"{SITE}/en/", "inLanguage": "en"},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in hfaq if a]}]
    B.write("en/index.html", page(f"{BRAND}: VPN for Russia that works on mobile and home internet",
                                  "VPN for Russia with whitelist bypass: 5-second internet check, status by carrier, setup guides. "
                                  f"{BRAND}: {TRIAL}.", "/en/", home, ld))
    urls.append(("/en/", UPD))
    return urls, posts
