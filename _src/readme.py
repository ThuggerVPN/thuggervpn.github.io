"""README.md - витрина репозитория на GitHub. Пересобирается при каждой сборке сайта:
свежие события, цифры vpnstatus и статьи обновляются сами."""
import json
from urllib.parse import quote

import build as B

EMOJI = {"whitelist": "🟥", "outage": "⛔", "slow": "🟧", "vpn_block": "🔒", "service": "⚠️", "policy": "📜"}


def badge(label, msg, color, url, logo=""):
    q = lambda s: quote(s.replace("-", "--").replace("_", "__"), safe="")
    lg = f"&logo={logo}&logoColor=white" if logo else ""
    return f'<a href="{url}"><img src="https://img.shields.io/badge/{q(label)}-{q(msg)}-{color}?style=for-the-badge{lg}" alt="{label}: {msg}"></a>'


def short_region(r):
    if len(r) <= 30:
        return r
    head = r.split(",")[0].split(" включая")[0].strip()
    return head if len(head) <= 30 else head[:28].rstrip() + "…"


def cell_md(s):
    return s.replace("|", "\\|").replace("\n", " ")


def build(ST, posts, posts_en):
    S, CFG = B.SITE, B.CFG
    vs_path = B.SRC / "data" / "vpnstatus.json"
    vs = json.loads(vs_path.read_text(encoding="utf-8")) if vs_path.exists() else None
    upd = B.upd_label(ST)
    min_price = min([p["per_month"] for p in CFG.get("plans", [])] or [210])

    badges = " ".join([
        badge("сайт", "thuggervpn.github.io", "8b5cf6", f"{S}/"),
        badge("English", "version", "6d28d9", f"{S}/en/"),
        badge("бот", "3 дня бесплатно", "229ED9", B.BOT_PLAIN, "telegram"),
        badge("канал", "@ThuggerVPN", "229ED9", B.CHANNEL, "telegram"),
    ] + ([badge("vpnstatus", f"★ {vs['rating']} · {B.ocenok(vs['votes'])}", "f5b301", B.VPNSTATUS)] if vs else []) + [
        badge("обновлено", ST["updated"], "1f2937", f"{S}/status/"),
    ])

    ev = ST["events"][:6]
    rows = "\n".join(
        f"| {B.ru_date(e['date'], year=False)} | {cell_md(short_region(e['region']))} | {EMOJI.get(e['type'], '•')} {cell_md(e['title'])} | "
        f"[{cell_md(e['source'])}]({e['url']}) |" for e in ev)


    vs_block = ""
    if vs:
        def frac(w, t):
            return "-" if not t else f"{w}/{t} ✅" if w == t else f"{w}/{t}"
        ops = "\n".join(f"| {o['name']} | {frac(o['works'], o['total'])} | {frac(o.get('wl_works'), o.get('wl_total'))} |"
                        for o in vs.get("mobile", []))
        vs_block = f"""
## ⭐ Отзывы клиентов

Независимый каталог [vpnstatus.site]({B.VPNSTATUS}): **{vs['rating']} из 5**, {B.ocenok(vs['votes'])}, {vs['works_percent']}% отметили «работает». Данные на {B.ru_date(vs['checked'])}.

| Оператор | Работает | Обход белых списков |
|---|---|---|
{ops}
| Домашний интернет | {frac(vs.get('home_works'), vs.get('home_total'))} | - |

Пользовались ThuggerVPN? [Отметьте своего оператора]({B.VPNSTATUS}) - это помогает другим выбрать.
"""

    plans = CFG.get("plans", [])
    plan_rows = "\n".join(f"| {p['months']} мес. | {p['total']} ₽ | {p['per_month']} ₽/мес{' · выгоднее всего' if p.get('best') else ''} |"
                          for p in plans) if plans and all(k in plans[0] for k in ("months", "total", "per_month")) else ""

    arts_ru = "\n".join(f"- [{a['title']}]({S}/blog/{a['slug']}/)" for a in posts[:6])
    arts_en = "\n".join(f"- [{a['title']}]({S}/en/blog/{a['slug']}/)" for a in posts_en[:6])

    md = f"""<div align="center">

<a href="{S}/"><img src="assets/readme/showcase.png" alt="Сайт ThuggerVPN на компьютере и телефоне" width="100%"></a>

# ThuggerVPN

**Статус блокировок в России, проверка интернета за 5 секунд и инструкции по VPN**<br>
<sub>Russia internet blocking status, a 5-second connection check and VPN setup guides · <a href="#-english">English ↓</a></sub>

{badges}

<a href="{S}/check/"><b>Проверить интернет</b></a> · <a href="{S}/status/"><b>Статус сегодня</b></a> · <a href="{S}/podklyuchenie/"><b>Как подключить</b></a> · <a href="{B.BOT_PLAIN}"><b>Попробовать бесплатно</b></a>

</div>

---

## 📡 Сводка блокировок

Обновляется каждый день. Последнее обновление: **{upd}**. Полная картина - на странице [статуса]({S}/status/) и в [индексе блокировок]({S}/index-blokirovok/).

| Дата | Где | Что случилось | Источник |
|---|---|---|---|
{rows}

<sub>🟥 белые списки · ⛔ отключение · 🟧 замедление · 🔒 блокировка VPN · ⚠️ сбой сервиса · 📜 решения властей</sub>

## 🧰 Инструменты

<table>
<tr>
<td width="50%" valign="top">
<a href="{S}/check/"><img src="assets/readme/check.png" alt="Проверка интернета"></a>
<h3><a href="{S}/check/">Проверка интернета за 5 секунд</a></h3>
Белые списки, отключение или проблема с VPN - страница проверяет прямо в браузере и говорит, что делать. Ничего не сохраняет.
</td>
<td width="50%" valign="top">
<a href="{S}/status/"><img src="assets/readme/status.png" alt="Статус блокировок"></a>
<h3><a href="{S}/status/">Статус блокировок сегодня</a></h3>
Ежедневная сводка сбоев мобильного интернета по регионам и операторам: <a href="{S}/operator/mts/">МТС</a>, <a href="{S}/operator/beeline/">Билайн</a>, <a href="{S}/operator/megafon/">МегаФон</a>, <a href="{S}/operator/t2/">Т2</a>. Каждое событие - со ссылкой на источник.
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="{S}/podklyuchenie/"><img src="assets/readme/setup.png" alt="Инструкция по подключению"></a>
<h3><a href="{S}/podklyuchenie/">Как подключить VPN</a></h3>
iPhone, Android, Windows, macOS и телевизор - по шагам. Отдельно: что делать, если у вас российский Apple ID.
</td>
<td width="50%" valign="top">
<p align="center">
<img src="assets/readme/check-m.png" alt="Проверка на телефоне" width="31%">
<img src="assets/readme/home-m.png" alt="Главная на телефоне" width="31%">
<img src="assets/readme/status-m.png" alt="Статус на телефоне" width="31%">
</p>
<h3>Удобно с телефона</h3>
Сайт сделан в первую очередь для мобильного: проверка и инструкции открываются за секунды даже на медленном интернете.
</td>
</tr>
</table>

## 📊 Открытые данные

База событий открыта и обновляется ежедневно - для журналистов, исследователей и разработчиков. Используйте со ссылкой на источник.

- JSON: [`/data/blocking-events.json`]({S}/data/blocking-events.json)
- [Индекс блокировок]({S}/index-blokirovok/) - события за 7 и 30 дней по типам
- [Информер для вашего сайта]({S}/informer/) - сводка блокировок одной строкой кода
- RSS: [русский]({S}/feed.xml) · [English]({S}/en/feed.xml)

## 📝 Свежие статьи

{arts_ru}

[Все статьи →]({S}/blog/)
{vs_block}
## 🚀 О сервисе ThuggerVPN

VPN для мобильного и домашнего интернета с опцией обхода белых списков. Подключение за 2 минуты в Telegram, живая поддержка.

| | |
|---|---|
| 🎁 Пробный период | {CFG['trial']} |
| 📱 Устройства | {CFG.get('devices', '')} |
| 🛡️ Обход белых списков | {CFG.get('whitelist_detail', '')} |
| 💬 Поддержка | [@{B.SUPPORT.rsplit('/', 1)[-1]}]({B.SUPPORT}) |
"""
    if plan_rows:
        md += f"""
| Тариф | Стоимость | В месяц |
|---|---|---|
{plan_rows}
"""
    md += f"""
<div align="center">

<a href="{B.BOT_PLAIN}"><img src="https://img.shields.io/badge/%D0%9F%D0%BE%D0%BF%D1%80%D0%BE%D0%B1%D0%BE%D0%B2%D0%B0%D1%82%D1%8C%203%20%D0%B4%D0%BD%D1%8F%20%D0%B1%D0%B5%D1%81%D0%BF%D0%BB%D0%B0%D1%82%D0%BD%D0%BE-8b5cf6?style=for-the-badge&logo=telegram&logoColor=white" alt="Попробовать 3 дня бесплатно" height="44"></a>

</div>

---

## 🌍 English

**Daily status of mobile internet shutdowns, whitelist mode and VPN blocking in Russia** - with sources, a 5-second internet check and setup guides. Useful if you live in Russia, travel there or have family there.

- [Blocking status today]({S}/en/status/) · [Internet check]({S}/en/check/) · [Setup guide]({S}/en/podklyuchenie/) · [Blocking index]({S}/en/index-blokirovok/)
- Open data: [`blocking-events.json`]({S}/data/blocking-events.json) · RSS: [`/en/feed.xml`]({S}/en/feed.xml)

**Latest guides**

{arts_en}

ThuggerVPN: {CFG.get('en', {}).get('trial', '3 days free')}, then from {min_price} ₽/month - [Telegram bot]({B.BOT_PLAIN}) · reviews on [vpnstatus.site]({B.VPNSTATUS}).

---

<sub>Сайт собирается автоматически: статьи - `_src/articles/` и `_src/articles_en/`, база событий - `_src/data/status.json`, сборка - `python3 _src/build.py`. Эта страница обновляется вместе с сайтом.</sub>
"""
    (B.ROOT / "README.md").write_text(B.humanize(md), encoding="utf-8")
