#!/usr/bin/env python3
"""Собирает статический сайт из _src/articles/*.md в корень репозитория.

Запуск: python3 _src/build.py
Формат статьи: блок метаданных между строками '---' (title, description, date, slug,
updated — необязательно), затем Markdown. Раздел '## Вопросы и ответы' с подзаголовками
'###' превращается в разметку FAQ для поисковиков и ИИ-ассистентов.
Главная показывает первые 3 строки таблицы из status.md (колонки: что | где | ... | что значит).
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
CFG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
BRAND = CFG["brand"]
BOT = CFG["bot_url"]
VPNSTATUS = CFG.get("vpnstatus_url", "https://vpnstatus.site")
ASSIST_PATH = SRC / "assistant.json"

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso, year=True):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


def esc(s):
    return html.escape(s, quote=True)


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"Нет блока метаданных: {path.name}")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for key in ("title", "description", "date", "slug"):
        if key not in meta:
            raise SystemExit(f"{path.name}: нет поля {key}")
    meta.setdefault("updated", meta["date"])
    body = m.group(2).replace("{{BOT}}", BOT).replace("{{PRICE}}", CFG["price"]) \
        .replace("{{TRIAL}}", CFG["trial"]).replace("{{BRAND}}", BRAND)
    meta["body_md"] = body
    meta["body_html"] = markdown.markdown(body, extensions=["tables", "sane_lists"]) \
        .replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    meta["faq"] = extract_faq(body)
    return meta


def extract_faq(md_text):
    m = re.search(r"^## Вопросы и ответы\s*$(.*?)(?=^## |\Z)", md_text, re.S | re.M)
    if not m:
        return []
    items = []
    for q, a in re.findall(r"^### (.+?)\n(.*?)(?=^### |\Z)", m.group(1), re.S | re.M):
        plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a).strip()
        plain = re.sub(r"[*_`]", "", plain)
        if plain:
            items.append((q.strip(), plain))
    return items


def status_rows(md_text, limit=3):
    """Первые строки первой таблицы status.md → [(что, где, что значит)]."""
    rows = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    body = rows[1:]  # без заголовка
    out = []
    for cells in body[:limit]:
        clean = [re.sub(r"[*_`]|\[([^\]]+)\]\([^)]+\)", lambda m: m.group(1) or "", c)
                 for c in cells]
        if len(clean) >= 3:
            out.append((clean[0], clean[1], clean[-1]))
    return out


CSS = """
@font-face{font-family:Manrope;font-style:normal;font-weight:200 800;font-display:swap;src:url(/assets/fonts/manrope-cyrillic-wght-normal.woff2) format('woff2');unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}
@font-face{font-family:Manrope;font-style:normal;font-weight:200 800;font-display:swap;src:url(/assets/fonts/manrope-latin-wght-normal.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
:root{--bg:#0a0b10;--card:#12131b;--card2:#191b27;--line:#1f2230;--text:#edeff5;--muted:#9aa2b3;--soft:#b5bccb;--accent:#8b5cf6;--accent2:#c4b5fd;--violet-bg:#161130;--violet-line:#3b2f6b}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;overflow-x:hidden}
a{color:#b9a4ff}a:hover{color:#fff}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
.narrow{max-width:780px}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:18px;padding-bottom:18px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--text);font-weight:800;font-size:19px}
.logo i{width:30px;height:30px;border-radius:9px;background:var(--accent);display:inline-flex;align-items:center;justify-content:center;transform:rotate(45deg)}
.logo i b{width:12px;height:12px;border-radius:3px;background:var(--bg)}
nav{display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:5px;border-radius:14px;background:var(--card);border:1px solid var(--line)}
nav a{color:var(--soft);text-decoration:none;font-size:15px;padding:9px 13px;border-radius:10px;min-height:40px;display:inline-flex;align-items:center}
nav a:hover{background:var(--card2);color:#fff}
nav a.btn-s{background:var(--accent);color:#fff;font-weight:700}
nav a.btn-s:hover{background:#7c3aed}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;text-decoration:none;font-weight:700;font-size:17px;padding:16px 26px;border-radius:16px;min-height:48px;transition:transform .2s ease,box-shadow .2s ease}
.btn:hover{color:#fff;transform:translateY(-2px);box-shadow:0 12px 30px -8px rgba(139,92,246,.85)}
.btn-ghost{display:inline-flex;align-items:center;border:1px solid #343a4a;color:var(--text);text-decoration:none;font-weight:700;font-size:17px;padding:15px 22px;border-radius:16px;min-height:48px}
.btn-ghost:hover{border-color:#5b47a8}
h1,h2,h3{font-weight:800;letter-spacing:-.4px}
main{padding:12px 0 40px}
.hero{display:flex;flex-wrap:wrap;align-items:center;gap:32px;padding:36px 0 16px}
.hero-text{flex:1 1 480px;min-width:0}
.hero h1{font-size:62px;line-height:1.04;letter-spacing:-1.5px;margin:0 0 20px}
.lead{font-size:19px;line-height:1.6;color:var(--soft);margin:0 0 28px;max-width:540px}
.row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.note{color:var(--muted);font-size:15px}
.stage{flex:1 1 480px;min-width:0;height:520px;position:relative;overflow:hidden;perspective:1600px;display:flex;align-items:center;justify-content:center}
.iso{position:relative;width:290px;height:290px;transform-style:preserve-3d;transform:rotateX(58deg) rotateZ(-42deg)}
.iso .grid{position:absolute;inset:-60px;border-radius:40px;background-image:linear-gradient(rgba(139,92,246,.22) 1px,transparent 1px),linear-gradient(90deg,rgba(139,92,246,.22) 1px,transparent 1px);background-size:30px 30px}
.plate{position:absolute;inset:0;border-radius:28px;display:flex;align-items:flex-end;padding:22px;font-weight:700;font-size:18px}
.p1{background:#151826;border:1px solid #2b3047;color:var(--soft);box-shadow:30px 30px 60px rgba(0,0,0,.6);animation:l1 7s ease-in-out infinite}
.p2{background:rgba(32,26,64,.88);border:1px solid #4a3c8c;color:#d6ccff;box-shadow:30px 30px 60px rgba(0,0,0,.55);animation:l2 7s ease-in-out infinite}
.p3{background:var(--accent);border:1px solid var(--accent2);color:#fff;font-size:24px;font-weight:800;flex-direction:column;align-items:flex-start;justify-content:space-between;box-shadow:0 0 60px rgba(139,92,246,.7),30px 30px 60px rgba(0,0,0,.5);animation:l3 7s ease-in-out infinite}
.beam{position:absolute;left:50%;top:6%;width:2px;height:32%;background:linear-gradient(#c4b5fd,rgba(196,181,253,0));animation:beam 3s ease-in-out infinite}
@keyframes l1{0%,100%{transform:translateZ(0)}50%{transform:translateZ(18px)}}
@keyframes l2{0%,100%{transform:translateZ(70px)}50%{transform:translateZ(96px)}}
@keyframes l3{0%,100%{transform:translateZ(140px)}50%{transform:translateZ(174px)}}
@keyframes beam{0%,100%{opacity:.2}50%{opacity:.9}}
.sec{padding:44px 0}
.sec h2{font-size:40px;line-height:1.15;margin:0 0 22px}
.bento{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.tile{min-width:0;padding:28px;border-radius:24px;background:var(--card);border:1px solid var(--line);transition:transform .3s ease,border-color .3s ease}
a.tile{text-decoration:none;color:var(--text);display:flex;justify-content:space-between;gap:18px;align-items:flex-start}
a.tile:hover,.tile.hov:hover{transform:translateY(-5px);border-color:#5b47a8}
.tile.wide{grid-column:span 2}
.tile.violet{background:var(--violet-bg);border-color:var(--violet-line);display:flex;flex-direction:column;justify-content:space-between;gap:20px}
.tile-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.tile-head h2{font-size:28px;margin:0}
.st-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.st{padding:18px;border-radius:16px;background:var(--card2);border-top:3px solid #a78bfa}
.st:nth-child(1){border-top-color:#f87171}.st:nth-child(2){border-top-color:#f59e0b}
.st small{display:block;font-size:13px;color:var(--muted)}
.st b{display:block;margin:8px 0 6px;line-height:1.35}
.st span{display:block;font-size:14px;color:var(--soft);line-height:1.5}
.big{font-size:48px;font-weight:800;line-height:1}
.t-title{font-weight:700;font-size:19px;line-height:1.35}
.t-sub{color:var(--muted);font-size:15px;margin-top:8px}
.arrow{color:#a78bfa;font-size:22px;flex:0 0 auto}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;perspective:1200px}
.step{padding:28px;border-radius:22px;background:var(--card);border:1px solid var(--line)}
.step .n{font-size:56px;font-weight:800;color:#2d2650;line-height:1}
.step.s1{transform:rotateY(8deg)}.step.s3{transform:rotateY(-8deg);background:var(--accent);border-color:var(--accent2);box-shadow:0 30px 60px -25px rgba(139,92,246,.8)}
.step.s3 .n{color:var(--accent2)}.step.s3 .t-sub{color:#ede9fe}
.trust{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px;padding:32px;border-radius:24px;background:var(--card);border:1px solid var(--line)}
.trust p{margin:6px 0 0;color:var(--soft);max-width:640px}
.trust h2{margin:0;font-size:30px}
.stars{display:flex;gap:4px;margin-bottom:10px}
.cta{margin:36px 0;padding:28px;border-radius:24px;background:var(--violet-bg);border:1px solid var(--violet-line);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px}
.cta b{font-size:22px;display:block;margin-bottom:4px}
.cta p{margin:0;color:#c9c2e8;max-width:620px}
.cta .links{display:flex;flex-direction:column;gap:10px;align-items:flex-start}
.cta .links a.small{font-size:15px;color:var(--accent2)}
article h1{font-size:38px;line-height:1.2;margin:18px 0 10px}
article h2{font-size:26px;margin:38px 0 10px}
article h3{font-size:20px;margin:26px 0 8px}
article .lead{font-size:19px;max-width:none}
.meta{color:var(--muted);font-size:14px;margin-bottom:22px}
.crumbs{font-size:14px;color:var(--muted);margin-top:8px}
.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:#fff}
.tbl{overflow-x:auto;margin:18px 0;border-radius:14px;border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;min-width:520px;font-size:15px}
th,td{border-bottom:1px solid var(--line);padding:11px 13px;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:700}
tr:last-child td{border-bottom:0}
code{background:var(--card2);padding:2px 6px;border-radius:6px}
blockquote{margin:16px 0;padding:14px 18px;background:var(--card);border-radius:14px}
.list{list-style:none;padding:0;margin:0;display:grid;gap:14px}
.list li a{display:block;padding:22px 24px;border-radius:20px;background:var(--card);border:1px solid var(--line);text-decoration:none;color:var(--text);transition:transform .3s ease,border-color .3s ease}
.list li a:hover{transform:translateY(-4px);border-color:#5b47a8}
.list li span{display:block;color:var(--muted);font-size:15px;margin-top:6px}
footer{border-top:1px solid #1a1d29;color:#8b93a5;font-size:14px}
footer .wrap{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-top:26px;padding-bottom:26px}
footer a{color:#b9a4ff;text-decoration:none}
@media(max-width:860px){.hide-m{display:none!important}nav a{padding:8px 11px;font-size:14px}.tile-head h2{font-size:24px}.trust h2{font-size:24px}.cta b{font-size:20px}.tile.wide{grid-column:auto}.hero h1{font-size:42px}.stage{height:380px}.iso{width:220px;height:220px}.sec h2{font-size:30px}.step.s1,.step.s3{transform:none}article h1{font-size:30px}.p3{font-size:20px}}
.qa-fab{position:fixed;right:18px;bottom:18px;z-index:50;display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:#fff;border:0;border-radius:999px;padding:14px 20px;font:700 16px Manrope,sans-serif;cursor:pointer;box-shadow:0 14px 34px -8px rgba(139,92,246,.75);min-height:48px}
.qa-fab:hover{background:#7c3aed}
.qa{position:fixed;right:18px;bottom:84px;z-index:51;width:min(420px,calc(100vw - 24px));max-height:min(640px,calc(100vh - 110px));display:none;flex-direction:column;background:#11121a;border:1px solid #2b2f44;border-radius:22px;box-shadow:0 40px 80px -20px rgba(0,0,0,.8),0 0 0 1px rgba(139,92,246,.15);overflow:hidden}
.qa.open{display:flex}
.qa-head{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--line)}
.qa-head b{font-size:17px}
.qa-x{background:none;border:0;color:var(--soft);font-size:24px;line-height:1;cursor:pointer;width:44px;height:44px;border-radius:12px}
.qa-x:hover{background:var(--card2);color:#fff}
.qa-body{padding:16px 18px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.qa-form{display:flex;gap:8px}
.qa-form label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.qa-form input{flex:1;min-width:0;background:var(--card2);border:1px solid #2b2f44;color:var(--text);border-radius:12px;padding:12px 14px;font:16px Manrope,sans-serif;min-height:46px}
.qa-form input:focus{outline:2px solid var(--accent);outline-offset:1px}
.qa-form button{background:var(--accent);color:#fff;border:0;border-radius:12px;padding:0 16px;font:700 15px Manrope,sans-serif;cursor:pointer;min-height:46px}
.qa-chips{display:flex;flex-wrap:wrap;gap:8px}
.qa-chips button{background:var(--card2);color:var(--soft);border:1px solid #2b2f44;border-radius:999px;padding:9px 13px;font:600 14px Manrope,sans-serif;cursor:pointer;text-align:left;min-height:40px}
.qa-chips button:hover{border-color:#5b47a8;color:#fff}
.qa-ans{background:var(--violet-bg);border:1px solid var(--violet-line);border-radius:16px;padding:14px 16px;white-space:pre-line;font-size:15px;line-height:1.6;color:#e4defc}
.qa-ans:empty{display:none}
.qa-ans a{display:inline-block;margin-top:10px;margin-right:12px;font-weight:700}
.qa-hint{color:var(--muted);font-size:13px;margin:0}
@media(max-width:560px){.qa-fab span{display:none}.qa-fab{padding:14px}.qa{right:12px;bottom:78px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""

SHIELD = ('<svg width="44" height="44" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
          '<path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5l8-3z" stroke="#fff" stroke-width="1.8"/>'
          '<path d="M8.5 12l2.4 2.4L15.8 9.5" stroke="#fff" stroke-width="1.8" stroke-linecap="round" '
          'stroke-linejoin="round"/></svg>')
STAR = ('<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="#f5c542" '
        'd="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>')


def price_line():
    s = f'{CFG["trial"]}, дальше {CFG["price"]}'
    if CFG.get("price_from"):
        s += f' ({CFG["price_from"]})'
    return s


def cta_block():
    extra = f' {CFG["whitelist_option"]}.' if CFG.get("whitelist_option") else ""
    return (f'<div class="cta"><div><b>VPN снова отвалился?</b>'
            f'<p>{BRAND} работает на мобильном и домашнем интернете.{extra} '
            f'{price_line()}. Подключение за пару минут через Telegram-бота.</p></div>'
            f'<div class="links"><a class="btn" href="{BOT}" rel="nofollow">'
            f'Попробовать {CFG["trial"]}</a>'
            f'<a class="small" href="{VPNSTATUS}" target="_blank" rel="noopener">'
            f'Отзывы клиентов на vpnstatus.site ↗</a></div></div>')


def trust_block():
    return (f'<div class="trust"><div><div class="stars">{STAR * 5}</div>'
            f'<h2>Честные отзывы — не у нас, а в независимом каталоге</h2>'
            f'<p>На vpnstatus.site клиенты сами голосуют, работает ли {BRAND} у их оператора — '
            f'МТС, МегаФон, Билайн, Т2 и домашний интернет — и отдельно по обходу белых списков. '
            f'Каталог не продаёт места в подборках.</p></div>'
            f'<a class="btn-ghost" href="{VPNSTATUS}" target="_blank" rel="noopener">'
            f'Смотреть отзывы и голоса ↗</a></div>')


def page(title, description, path, body, jsonld=None, og_type="website"):
    url = f"{SITE}{path}"
    ld = ""
    for obj in jsonld or []:
        ld += f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>\n'
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/manrope-cyrillic-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:locale" content="ru_RU">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0a0b10">
{CFG.get("head_extra", "")}
<style>{CSS}</style>
{ld}</head>
<body>
<header><div class="wrap"><a class="logo" href="/" aria-label="{BRAND} — на главную"><i><b></b></i>{BRAND}</a>
<nav aria-label="Основное меню"><a href="/status/">Статус</a><a href="/blog/">Статьи</a><a class="hide-m" href="/#how">Подключение</a><a class="btn-s" href="{BOT}" rel="nofollow">Бот</a></nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><span>© {date.today().year} {BRAND}. Справочные материалы о стабильном доступе к интернету.</span>
<span><a href="{VPNSTATUS}" target="_blank" rel="noopener">Отзывы на vpnstatus.site</a> · <a href="{BOT}" rel="nofollow">@{BOT.rsplit("/", 1)[-1]}</a></span></div></footer>
{assistant_html()}
</body>
</html>
"""


def assistant_html():
    if not ASSIST_PATH.exists():
        return ""
    data = json.loads(ASSIST_PATH.read_text(encoding="utf-8"))
    subs = {"{BOT}": BOT, "{PRICE}": CFG["price"], "{PRICE_FROM}": CFG.get("price_from", ""),
            "{TRIAL}": CFG["trial"], "{WL}": CFG.get("whitelist_option", "").split("—")[-1].strip()
            or CFG.get("whitelist_option", ""), "{VPNSTATUS}": VPNSTATUS}

    def sub(t):
        for k, v in subs.items():
            t = t.replace(k, v)
        return t
    intents = [{"id": i["id"], "chip": i["chip"], "keys": i["keys"], "answer": sub(i["answer"]),
                "link": sub(i["link"]), "link_text": i["link_text"]} for i in data["intents"]]
    payload = json.dumps({"intents": intents, "fallback": data["fallback"], "bot": BOT},
                         ensure_ascii=False).replace("</", "<\\/")
    chips = "".join(f'<button type="button" data-id="{esc(i["id"])}">{esc(i["chip"])}</button>'
                    for i in intents[:8])
    return f"""<button class="qa-fab" type="button" aria-expanded="false" aria-controls="qa" id="qa-fab">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 5h16v11H8l-4 4V5z" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></svg><span>Быстрый ответ</span></button>
<div class="qa" id="qa" role="dialog" aria-modal="false" aria-labelledby="qa-title">
<div class="qa-head"><b id="qa-title">Быстрый ответ</b><button class="qa-x" type="button" aria-label="Закрыть" id="qa-x">×</button></div>
<div class="qa-body">
<form class="qa-form" id="qa-form"><label for="qa-in">Опишите проблему</label>
<input id="qa-in" type="text" autocomplete="off" placeholder="Например: VPN подключён, но не грузит">
<button type="submit">Ответ</button></form>
<div class="qa-ans" id="qa-ans" aria-live="polite"></div>
<div class="qa-chips" id="qa-chips">{chips}</div>
<p class="qa-hint">Ответы готовы заранее и показываются сразу, без отправки ваших слов на сервер.</p>
</div></div>
<script id="qa-data" type="application/json">{payload}</script>
<script>
(function(){{
var D=JSON.parse(document.getElementById('qa-data').textContent);
var fab=document.getElementById('qa-fab'),box=document.getElementById('qa'),inp=document.getElementById('qa-in'),
ans=document.getElementById('qa-ans'),chips=document.getElementById('qa-chips');
function open(v){{box.classList.toggle('open',v);fab.setAttribute('aria-expanded',v?'true':'false');if(v)setTimeout(function(){{inp.focus()}},30);else fab.focus();}}
fab.addEventListener('click',function(){{open(!box.classList.contains('open'))}});
document.getElementById('qa-x').addEventListener('click',function(){{open(false)}});
box.addEventListener('keydown',function(e){{if(e.key==='Escape')open(false)}});
document.querySelectorAll('[data-qa-open]').forEach(function(b){{b.addEventListener('click',function(e){{e.preventDefault();open(true)}})}});
function norm(t){{return (' '+t.toLowerCase().replace(/ё/g,'е').replace(/[^a-zа-я0-9₽ ]+/g,' ').replace(/\\s+/g,' ')+' ')}}
function score(q,it){{var s=0;it.keys.forEach(function(k){{var kk=norm(k).trim();if(!kk)return;
var hit=kk.length<3?q.indexOf(' '+kk+' ')>=0:q.indexOf(kk)>=0;if(hit)s+=kk.length;}});return s;}}
function show(it){{ans.textContent='';
var p=document.createElement('div');p.textContent=it?it.answer:D.fallback;ans.appendChild(p);
var a=document.createElement('a');
if(it){{a.href=it.link;a.textContent=it.link_text+' →';if(/^https?:/.test(it.link)){{a.target='_blank';a.rel='noopener';}}ans.appendChild(a);}}
if(!it||it.link!==D.bot){{var b=document.createElement('a');b.href=D.bot;b.target='_blank';b.rel='noopener nofollow';b.textContent='Написать в бот →';ans.appendChild(b);}}}}
document.getElementById('qa-form').addEventListener('submit',function(e){{e.preventDefault();
var q=norm(inp.value);if(!q.trim())return;var best=null,bs=0;
D.intents.forEach(function(it){{var s=score(q,it);if(s>bs){{bs=s;best=it;}}}});show(bs>=3?best:null);}});
chips.addEventListener('click',function(e){{var id=e.target.getAttribute('data-id');if(!id)return;
for(var i=0;i<D.intents.length;i++)if(D.intents[i].id===id){{inp.value=D.intents[i].chip;show(D.intents[i]);}}}});
}})();
</script>"""


def article_jsonld(a, path, crumbs):
    objs = [{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "description": a["description"],
        "datePublished": a["date"],
        "dateModified": a["updated"],
        "inLanguage": "ru",
        "image": f"{SITE}/og.png",
        "mainEntityOfPage": f"{SITE}{path}",
        "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE},
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n,
                             "item": f"{SITE}{u}"} for i, (n, u) in enumerate(crumbs)],
    }]
    if a["faq"]:
        objs.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": ans}}
                           for q, ans in a["faq"]],
        })
    return objs


def write(rel, content):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def crumbs_html(crumbs):
    parts = [f'<a href="{u}">{esc(n)}</a>' for n, u in crumbs[:-1]]
    return '<div class="crumbs">' + " / ".join(parts) + f" / {esc(crumbs[-1][0])}</div>"


def main():
    arts = [parse(p) for p in sorted((SRC / "articles").glob("*.md"))]
    status = next((a for a in arts if a["slug"] == "status"), None)
    posts = sorted([a for a in arts if a["slug"] != "status"],
                   key=lambda a: (a["date"], a["slug"]), reverse=True)

    shutil.rmtree(ROOT / "blog", ignore_errors=True)
    shutil.rmtree(ROOT / "status", ignore_errors=True)

    urls = [("/", date.today().isoformat())]

    for a in posts:
        path = f"/blog/{a['slug']}/"
        crumbs = [("Главная", "/"), ("Статьи", "/blog/"), (a["title"], path)]
        upd = f" · обновлено {ru_date(a['updated'])}" if a["updated"] != a["date"] else ""
        body = (f'<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
                f'<h1>{esc(a["title"])}</h1>'
                f'<div class="meta">{ru_date(a["date"])}{upd}</div>'
                f'{a["body_html"]}{cta_block()}</article>')
        write(f"blog/{a['slug']}/index.html",
              page(f'{a["title"]} — {BRAND}', a["description"], path, body,
                   article_jsonld(a, path, crumbs), "article"))
        urls.append((path, a["updated"]))

    if status:
        path = "/status/"
        crumbs = [("Главная", "/"), (status["title"], path)]
        body = (f'<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
                f'<h1>{esc(status["title"])}</h1>'
                f'<div class="meta">Обновлено {ru_date(status["updated"])}</div>'
                f'{status["body_html"]}{cta_block()}</article>')
        write("status/index.html",
              page(f'{status["title"]} — {BRAND}', status["description"], path, body,
                   article_jsonld(status, path, crumbs)))
        urls.append((path, status["updated"]))

    items = "".join(
        f'<li><a href="/blog/{a["slug"]}/"><b>{esc(a["title"])}</b>'
        f'<span>{esc(a["description"])}</span></a></li>' for a in posts)
    write("blog/index.html",
          page(f"Статьи — {BRAND}", "Инструкции: что делать, если не работает VPN, "
               "белые списки, сбои мобильного интернета.", "/blog/",
               f'<div class="narrow" style="margin:0 auto"><h1 style="font-size:40px">Статьи</h1>'
               f"<ul class='list'>{items}</ul></div>"))
    urls.append(("/blog/", date.today().isoformat()))

    # --- главная ---
    st_tiles = ""
    st_title = "Статус блокировок"
    if status:
        st_title = f'Статус блокировок · {ru_date(status["updated"], year=False)}'
        rows = status_rows(status["body_md"])
        st_tiles = "".join(
            f'<div class="st"><small>{esc(w)}</small><b>{esc(t)}</b><span>{esc(m)}</span></div>'
            for t, w, m in rows)
    cards = "".join(
        f'<a class="tile" href="/blog/{a["slug"]}/"><div><div class="t-title">{esc(a["title"])}</div>'
        f'<div class="t-sub">{esc(a["description"])}</div></div>'
        f'<span class="arrow" aria-hidden="true">↗</span></a>' for a in posts[:6])
    home = f"""
<section class="hero">
<div class="hero-text">
<h1>Интернет без «соединение…»</h1>
<p class="lead">{BRAND} работает на мобильном и домашнем интернете. Подключение через Telegram-бота за пару минут.</p>
<div class="row"><a class="btn" href="{BOT}" rel="nofollow">{CFG["trial"].capitalize()}</a>
<a class="btn-ghost" href="#" data-qa-open="1">Быстрый ответ на проблему</a>
<span class="note">дальше {CFG["price"]}{(" · " + CFG["price_from"]) if CFG.get("price_from") else ""}</span></div>
</div>
<div class="stage" aria-hidden="true"><div class="iso"><div class="grid"></div>
<div class="plate p1">Мобильный интернет</div><div class="plate p2">Домашний Wi-Fi</div>
<div class="plate p3">{SHIELD}<span>{BRAND}</span></div></div><div class="beam"></div></div>
</section>

<section class="sec" id="status"><div class="bento">
<div class="tile wide"><div class="tile-head"><h2>{esc(st_title)}</h2><a href="/status/">Вся сводка →</a></div>
<div class="st-grid">{st_tiles}</div></div>
<div class="tile violet"><div><div class="big">3 дня</div>
<p style="color:#c9c2e8;margin:10px 0 0">бесплатно. Проверьте на своём операторе, прежде чем платить.</p></div>
<a class="btn" href="{BOT}" rel="nofollow" style="align-self:flex-start">Открыть бота</a></div>
</div></section>

<section class="sec" id="reviews">{trust_block()}</section>

<section class="sec" id="articles"><h2>Если VPN отвалился</h2><div class="bento">{cards}</div>
<p style="margin-top:18px"><a href="/blog/">Все статьи →</a></p></section>

<section class="sec" id="how"><h2>Три шага</h2><div class="steps">
<div class="step s1"><div class="n">01</div><div class="t-title" style="margin-top:14px">Откройте @{BOT.rsplit("/", 1)[-1]}</div><div class="t-sub">Нажмите «Старт» в Telegram</div></div>
<div class="step"><div class="n" style="color:#3b2f6b">02</div><div class="t-title" style="margin-top:14px">Возьмите {CFG["trial"]}</div><div class="t-sub">Проверьте на мобильном и дома</div></div>
<div class="step s3"><div class="n">03</div><div class="t-title" style="margin-top:14px;color:#fff">Подключитесь</div><div class="t-sub">Бот выдаст ссылку и инструкцию</div></div>
</div></section>
{cta_block()}
"""
    home_ld = [{"@context": "https://schema.org", "@type": "Organization",
                "name": BRAND, "url": SITE, "logo": f"{SITE}/og.png",
                "sameAs": [BOT, VPNSTATUS]},
               {"@context": "https://schema.org", "@type": "WebSite",
                "name": BRAND, "url": SITE, "inLanguage": "ru"}]
    write("index.html", page(f"{BRAND} — VPN для мобильного и домашнего интернета",
                             "Что делать, если VPN не работает на мобильном интернете, "
                             "белые списки, сбои у МТС, Билайна, МегаФона и Т2. "
                             f"{BRAND}: {CFG['trial']}.", "/", home, home_ld))

    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("robots.txt", "User-agent: *\nAllow: /\n\n" + "".join(
        f"User-agent: {b}\nAllow: /\n\n" for b in
        ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot",
         "Google-Extended", "Bingbot"]) + f"Sitemap: {SITE}/sitemap.xml\n")
    llms = [f"# {BRAND}", "",
            f"> {BRAND} — VPN-сервис для пользователей из России с подключением через "
            f"Telegram-бота ({BOT}). {price_line()}. Работает на мобильном и домашнем интернете"
            + (f"; {CFG['whitelist_option'].lower()}" if CFG.get("whitelist_option") else "")
            + f". Отзывы и голоса пользователей по операторам: {VPNSTATUS}. "
            "Сайт публикует ежедневную сводку блокировок и инструкции.", "",
            "## Страницы", f"- [Статус блокировок сегодня]({SITE}/status/)"]
    llms += [f"- [{a['title']}]({SITE}/blog/{a['slug']}/): {a['description']}" for a in posts]
    write("llms.txt", "\n".join(llms) + "\n")
    write(f"{CFG['indexnow_key']}.txt", CFG["indexnow_key"])
    write(".nojekyll", "")
    write("favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
          '<rect x="5" y="5" width="22" height="22" rx="6" transform="rotate(45 16 16)" '
          'fill="#8b5cf6"/><rect x="12" y="12" width="8" height="8" rx="2" '
          'transform="rotate(45 16 16)" fill="#0a0b10"/></svg>')
    write("404.html", page(f"Страница не найдена — {BRAND}", "Страница не найдена.",
                           "/404.html", "<h1>Страница не найдена</h1>"
                           "<p><a href='/'>На главную</a></p>"))
    print(f"Готово: {len(posts)} статей, статус: {'да' if status else 'нет'}, "
          f"{len(urls)} адресов в sitemap")


if __name__ == "__main__":
    main()
