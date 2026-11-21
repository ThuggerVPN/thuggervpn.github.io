"""Страница «Приведи друга» (RU /priglasit/, EN /en/priglasit/): реферальная программа 25%."""
import build as B

PRICE = 299
SHARE = 0.25

T = {
    "ru": {
        "path": "/priglasit/", "home": ("Главная", "/"),
        "title": "Приведи друга: 4 друга, и твой VPN бесплатный",
        "desc": "Реферальная программа ThuggerVPN: 25% с каждой оплаты друга на ваш баланс. Четыре друга на подписке полностью оплачивают ваш VPN.",
        "crumb": "Приведи друга",
        "lead": "За каждую оплату друга по вашей ссылке вам на баланс приходит <b>25% от суммы</b>. Четыре друга на месячной подписке полностью оплачивают ваш VPN, и так каждый месяц, пока они пользуются.",
        "how": "Как это работает",
        "steps": [
            ("Возьмите свою ссылку", "Откройте бота {bot} и найдите раздел реферальной программы. Там ваша личная ссылка."),
            ("Отправьте другу", "Лучше всего тому, у кого прямо сейчас не работает VPN. Пусть сначала проверит свой: {check}"),
            ("Друг пробует бесплатно", "3 дня без оплаты, подключение за 2 минуты. Если всё нравится, он оформляет подписку."),
            ("Вам начисляется 25%", "С каждой оплаты друга, не только с первой. Баланс тратится на продление вашего VPN."),
        ],
        "calc": "Сколько это в месяц", "c_friends": "Друзей", "c_month": "Вам в месяц", "c_note": "Расчёт для месячного тарифа {price} ₽. На длинных тарифах 25% начисляется со всей суммы оплаты.",
        "free": "VPN бесплатно", "free2": "хватит на 2 месяца",
        "msg_h": "Что написать другу", "msg": "Держи VPN, который работает, даже когда остальные отваливаются: на мобильном, дома и с белыми списками. 3 дня бесплатно, подключение за 2 минуты: [ваша ссылка]",
        "copy": "Скопировать текст", "copied": "Скопировано",
        "faq_h": "Вопросы и ответы",
        "faq": [
            ("Куда приходят деньги?", "На ваш баланс в боте. Им можно оплачивать продление подписки."),
            ("Когда начисляется?", "Сразу после того, как друг оплатит подписку. Пробные 3 дня не считаются, начисления только за реальные оплаты."),
            ("Сколько друзей можно пригласить?", "Сколько угодно. Чем больше друзей на подписке, тем больше на балансе."),
            ("А если друг оплатит не сразу?", "Ничего страшного: если он пришёл по вашей ссылке, начисление будет, когда он оплатит."),
        ],
        "cta": "Взять свою ссылку в боте",
    },
    "en": {
        "path": "/en/priglasit/", "home": ("Home", "/en/"),
        "title": "Invite friends: 4 friends and your VPN is free",
        "desc": "ThuggerVPN referral program: 25% of every payment your friend makes goes to your balance. Four subscribed friends cover your VPN in full.",
        "crumb": "Invite friends",
        "lead": "Every time a friend pays through your link, <b>25% of the payment</b> goes to your balance. Four friends on a monthly plan cover your VPN in full, every month while they stay.",
        "how": "How it works",
        "steps": [
            ("Get your link", "Open the bot {bot} and find the referral section. Your personal link is there."),
            ("Send it to a friend", "Best of all to someone whose VPN isn't working right now. Let them check theirs first: {check}"),
            ("Your friend tries it free", "3 days without payment, set up in 2 minutes. If they like it, they subscribe."),
            ("You get 25%", "From every payment your friend makes, not just the first. The balance pays for your VPN."),
        ],
        "calc": "How much per month", "c_friends": "Friends", "c_month": "You get monthly", "c_note": "Calculated for the {price} ₽ monthly plan. On longer plans you get 25% of the full payment.",
        "free": "VPN for free", "free2": "covers 2 months",
        "msg_h": "What to send a friend", "msg": "Here's a VPN that keeps working when others drop: mobile data, home internet, even whitelist mode. 3 days free, set up in 2 minutes: [your link]",
        "copy": "Copy text", "copied": "Copied",
        "faq_h": "FAQ",
        "faq": [
            ("Where does the money go?", "To your balance in the bot. You can use it to renew your subscription."),
            ("When is it credited?", "Right after your friend pays. The free 3 days don't count: only real payments are credited."),
            ("How many friends can I invite?", "As many as you like. The more subscribed friends, the bigger your balance."),
            ("What if my friend pays later?", "No problem: if they came through your link, you get credited when they pay."),
        ],
        "cta": "Get your link in the bot",
    },
}

CSS = """<style>
.fr-steps{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--gap);margin:18px 0 8px}
.fr-steps>div{background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);padding:20px}
.fr-steps b.n{display:inline-flex;width:34px;height:34px;border-radius:10px;align-items:center;justify-content:center;background:var(--violet-bg);border:1px solid var(--violet-line);color:var(--accent2);margin-bottom:10px}
.fr-steps h3{margin:0 0 6px;font-size:18px}.fr-steps p{margin:0;color:var(--soft);font-size:15.5px}
.fr-msg{background:var(--violet-bg);border:1px solid var(--violet-line);border-radius:var(--r-lg);padding:20px;margin:14px 0}
.fr-msg p{margin:0 0 14px;font-size:16.5px}.fr-msg button{min-height:46px;border:0;border-radius:12px;background:var(--accent);color:#fff;font:700 15px Manrope,sans-serif;padding:0 20px;cursor:pointer}
.fr-big{font-weight:800;color:var(--accent2)}.fr-calc td,.fr-calc th{white-space:normal!important}
@media(max-width:600px){.fr-steps{grid-template-columns:1fr}}
</style>"""


def page(lang, urls, UPD):
    t = T[lang]
    en = lang == "en"
    pre = "/en" if en else ""
    bot_a = f'<a href="{B.BOT}" rel="nofollow">@{B.BOT_PLAIN.rsplit("/", 1)[-1]}</a>'
    check_a = f'<a href="{pre}/check/">{"VPN check" if en else "проверка VPN"}</a>'
    steps = "".join(f'<div><b class="n">{i}</b><h3>{B.esc(h)}</h3><p>{p.format(bot=bot_a, check=check_a)}</p></div>'
                    for i, (h, p) in enumerate(t["steps"], 1))
    rows = ""
    for n in (1, 2, 4, 8):
        val = round(n * PRICE * SHARE)
        tag = f'<br><small class="fr-big">{t["free"]}</small>' if n == 4 else (f'<br><small>{t["free2"]}</small>' if n == 8 else "")
        rows += f"<tr><td>{n}</td><td>{val} ₽{tag}</td></tr>"
    faq = "".join(f'<details class="acc-q"><summary>{B.esc(q)}</summary><p>{B.esc(a)}</p></details>' for q, a in t["faq"])
    crumbs = [t["home"], (t["crumb"], t["path"])]
    msg_js = ("(function(){var b=document.getElementById('fr-copy');if(!b)return;b.addEventListener('click',function(){"
              "var t=document.getElementById('fr-text').textContent;(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject())"
              ".then(function(){b.textContent=b.getAttribute('data-ok')}).catch(function(){var r=document.createRange();"
              "r.selectNodeContents(document.getElementById('fr-text'));var s=getSelection();s.removeAllRanges();s.addRange(r)});"
              "try{goatcounter.count({path:'friends/copy',title:'copy invite text',event:true})}catch(e){}})})();")
    body = (f'{CSS}<article class="narrow" style="margin:0 auto">{B.crumbs_html(crumbs)}'
            f'<h1>{B.esc(t["title"])}</h1><p class="lead">{t["lead"]}</p>'
            f'<p><a class="btn" href="{B.BOT}" rel="nofollow">{B.esc(t["cta"])}</a></p>'
            f'<h2>{t["how"]}</h2><div class="fr-steps">{steps}</div>'
            f'<h2>{t["calc"]}</h2><div class="tbl fr-calc"><table><thead><tr><th>{t["c_friends"]}</th><th>{t["c_month"]}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="note">{t["c_note"].format(price=PRICE)}</p>'
            f'<h2>{t["msg_h"]}</h2><div class="fr-msg"><p id="fr-text">{B.esc(t["msg"])}</p>'
            f'<button type="button" id="fr-copy" data-ok="{t["copied"]} ✓">{t["copy"]}</button></div>'
            f'<h2>{t["faq_h"]}</h2>{faq}</article><script>{msg_js}</script>')
    jsonld = [{"@context": "https://schema.org", "@type": "FAQPage",
               "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]}]
    rel = t["path"].strip("/") + "/index.html"
    B.write(rel, B.page(f'{t["title"]} | {B.BRAND}', t["desc"], t["path"], body, jsonld, lang=lang))
    urls.append((t["path"], UPD))
