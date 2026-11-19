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
from datetime import date, datetime
from zoneinfo import ZoneInfo
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
SUPPORT = CFG.get("support_url", BOT)
CHANNEL = CFG.get("channel_url", "")

MSK = ZoneInfo("Europe/Moscow")


def today_msk():
    return datetime.now(MSK).date()


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
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;overflow-x:clip}
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
.stage{flex:1 1 480px;min-width:0;height:520px;position:relative;perspective:1600px;display:flex;align-items:center;justify-content:center}
.iso{position:relative;width:290px;height:290px;transform-style:preserve-3d;transform:rotateX(58deg) rotateZ(-42deg)}
.iso .grid{position:absolute;inset:-90px;-webkit-mask-image:radial-gradient(closest-side,#000 45%,transparent 100%);mask-image:radial-gradient(closest-side,#000 45%,transparent 100%);background-image:linear-gradient(rgba(139,92,246,.22) 1px,transparent 1px),linear-gradient(90deg,rgba(139,92,246,.22) 1px,transparent 1px);background-size:30px 30px}
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
.bento{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
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
.stars.sm svg{width:14px;height:14px}
.trust2{padding:30px;border-radius:24px;background:var(--card);border:1px solid var(--line)}
.tr-head{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:20px}
.tr-head h2{margin:0;font-size:30px}.tr-head p{margin:8px 0 0;color:var(--soft);max-width:640px}
.tr-grid{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:16px;margin-top:22px;align-items:stretch}
.tr-score{padding:22px;border-radius:18px;background:var(--violet-bg);border:1px solid var(--violet-line)}
.tr-score .big span{font-size:22px;color:#c9c2e8;font-weight:700}
.tr-ops{min-width:0!important}.tr-ops td,.tr-ops th{padding:10px 12px}.tr-ops .na{color:var(--muted);font-size:14px}
.tr-revs{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:16px}
.rv{padding:18px;border-radius:16px;background:var(--card2)}
.rv p{margin:6px 0 8px;font-size:15px;line-height:1.55}.rv small{color:var(--muted)}
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
@media(max-width:860px){.tr-grid{grid-template-columns:1fr}.tr-head h2{font-size:24px}.trust2{padding:22px}.stage{height:360px}.hide-m{display:none!important}nav a{padding:8px 11px;font-size:14px}.tile-head h2{font-size:24px}.trust h2{font-size:24px}.cta b{font-size:20px}.tile.wide{grid-column:auto}.hero h1{font-size:42px}.stage{height:300px;margin-top:-10px;margin-bottom:-30px}.iso{width:220px;height:220px}.sec h2{font-size:30px}.step.s1,.step.s3{transform:none}article h1{font-size:30px}.p3{font-size:20px}}
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
    vp = SRC / "data" / "vpnstatus.json"
    d = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else None
    link = (d or {}).get("url", VPNSTATUS)
    if not d:
        return (f'<div class="trust"><div><h2>Честные отзывы — в независимом каталоге</h2></div>'
                f'<a class="btn-ghost" href="{link}" target="_blank" rel="noopener">Смотреть отзывы ↗</a></div>')

    def cell(w, t):
        return '<span class="na">нет голосов</span>' if t in (None, 0) else f'<b>{w}/{t}</b>'
    ops = "".join(f'<tr><td>{esc(o["name"])}</td><td>{cell(o["works"], o["total"])}</td>'
                  f'<td>{cell(o["wl_works"], o["wl_total"])}</td></tr>' for o in d["mobile"])
    revs = "".join(f'<div class="rv"><div class="stars sm">{STAR * 5}</div><p>{esc(r["text"])}</p>'
                   f'<small>Клиент · {esc(r["period"])}</small></div>' for r in d["reviews"][:3])
    return f"""<div class="trust2">
<div class="tr-head"><div><div class="stars">{STAR * 5}</div>
<h2>Отзывы клиентов — в независимом каталоге</h2>
<p>Голоса и отзывы оставляют сами пользователи на vpnstatus.site. Каталог не продаёт места в подборках. Ниже — кратко, полная карточка по ссылке.</p></div>
<a class="btn-ghost" href="{link}" target="_blank" rel="noopener">Все отзывы на vpnstatus.site ↗</a></div>
<div class="tr-grid">
<div class="tr-score"><div class="big">{esc(d["rating"])}<span>/5</span></div>
<div class="t-sub" style="margin-top:6px">{d["votes"]} оценок · {d["works_percent"]}% «работает» · {d["reviews_count"]} отзывов</div>
<div class="t-sub" style="margin-top:4px">Домашний интернет: {d["home_works"]}/{d["home_total"]} «работает»</div></div>
<div class="tbl" style="margin:0"><table class="tr-ops"><thead><tr><th>Мобильный</th><th>Работает</th><th>Обход белых списков</th></tr></thead><tbody>{ops}</tbody></table></div>
</div>
<div class="tr-revs">{revs}</div>
<p class="note" style="margin:14px 0 0">По данным vpnstatus.site на {ru_date(d["checked"])}. Отзывы пересказаны кратко. <a href="{link}" target="_blank" rel="noopener">Открыть полную карточку →</a></p>
</div>"""


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
<nav aria-label="Основное меню"><a href="/check/">Проверка</a><a href="/status/">Статус</a><a href="/blog/">Статьи</a><a class="btn-s" href="{BOT}" rel="nofollow">Бот</a></nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><span>© {today_msk().year} {BRAND}. Справочные материалы о стабильном доступе к интернету.</span>
<span><a href="/index-blokirovok/">Индекс блокировок</a> · <a href="/informer/">Информер</a> · <a href="/operator/mts/">МТС</a> · <a href="/operator/beeline/">Билайн</a> · <a href="/operator/megafon/">МегаФон</a> · <a href="/operator/t2/">Т2</a> · <a href="{VPNSTATUS}" target="_blank" rel="noopener">Отзывы</a> · <a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Поддержка</a> · <a href="{CHANNEL}" target="_blank" rel="noopener">Telegram-канал</a></span></div></footer>
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
            or CFG.get("whitelist_option", ""), "{VPNSTATUS}": VPNSTATUS, "{SUPPORT}": SUPPORT}

    def sub(t):
        for k, v in subs.items():
            t = t.replace(k, v)
        return t
    intents = [{"id": i["id"], "chip": i["chip"], "keys": i["keys"], "answer": sub(i["answer"]),
                "link": sub(i["link"]), "link_text": i["link_text"]} for i in data["intents"]]
    payload = json.dumps({"intents": intents, "fallback": data["fallback"], "support": SUPPORT},
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
if(!it||it.link!==D.support){{var b=document.createElement('a');b.href=D.support;b.target='_blank';b.rel='noopener nofollow';b.textContent='Написать в поддержку →';ans.appendChild(b);}}}}
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


def related_html(a, posts):
    rel = [p for p in posts if p["slug"] != a["slug"]][:3]
    if not rel:
        return ""
    items = "".join(f'<li><a href="/blog/{p["slug"]}/"><b>{esc(p["title"])}</b>'
                    f'<span>{esc(p["description"])}</span></a></li>' for p in rel)
    return (f'<h2>Читайте также</h2><ul class="list">{items}'
            f'<li><a href="/check/"><b>Проверить свой интернет за 5 секунд</b>'
            f'<span>Белые списки, отключение или не работает VPN — узнайте сразу</span></a></li></ul>')


def crumbs_html(crumbs):
    parts = [f'<a href="{u}">{esc(n)}</a>' for n, u in crumbs[:-1]]
    return '<div class="crumbs">' + " / ".join(parts) + f" / {esc(crumbs[-1][0])}</div>"


TYPE_LABELS = {
    "whitelist": "Только белые списки",
    "outage": "Отключения интернета",
    "slow": "Замедления и перебои",
    "vpn_block": "Блокировки VPN и протоколов",
    "service": "Сбои сервисов",
    "policy": "Решения властей и операторов",
}
TYPE_COLORS = {"whitelist": "#f87171", "outage": "#ef4444", "slow": "#f59e0b",
               "vpn_block": "#a78bfa", "service": "#38bdf8", "policy": "#a3e635"}
OPS = {
    "mts": ("МТС", "МТС"),
    "beeline": ("Билайн", "Билайне"),
    "megafon": ("МегаФон", "МегаФоне"),
    "t2": ("Т2", "Т2 (Tele2)"),
}


def load_status():
    p = SRC / "data" / "status.json"
    if not p.exists():
        return {"updated": today_msk().isoformat(), "events": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    data["events"].sort(key=lambda e: e["date"], reverse=True)
    raw = str(data.get("updated", today_msk().isoformat()))
    data["updated"] = raw[:10]
    data["updated_time"] = raw[11:16] if len(raw) >= 16 else ""
    return data


def upd_label(st, year=True):
    t = f", {st['updated_time']} МСК" if st.get("updated_time") else " (МСК)"
    return ru_date(st["updated"], year=year) + t


def days_between(a, b):
    return (date.fromisoformat(a) - date.fromisoformat(b)).days


def recent(events, upd, days):
    return [e for e in events if 0 <= days_between(upd, e["date"]) < days]


def ops_label(e):
    if "all" in e.get("operators", ["all"]):
        return "все операторы"
    return ", ".join(OPS[o][0] for o in e["operators"] if o in OPS)


def events_table(events, show_ops=False):
    if not events:
        return ""
    head = "<th>Дата</th><th>Где</th>" + ("<th>Операторы</th>" if show_ops else "") + \
           "<th>Что случилось</th><th>Что это значит для вас</th>"
    rows = ""
    for e in events:
        src = (f' <a href="{esc(e["url"])}" target="_blank" rel="noopener nofollow">'
               f'{esc(e["source"])}</a>') if e.get("url") else ""
        rows += (f'<tr><td style="white-space:nowrap">{ru_date(e["date"], year=False)}</td>'
                 f'<td>{esc(e["region"])}</td>'
                 + (f'<td>{esc(ops_label(e))}</td>' if show_ops else "") +
                 f'<td>{esc(e["title"])}.<br><small style="color:var(--muted)">Источник:{src}</small></td>'
                 f'<td>{esc(e["meaning"])}</td></tr>')
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def status_block(st):
    fresh = recent(st["events"], st["updated"], 3)
    if fresh:
        return events_table(fresh)
    last = st["events"][:3]
    note = ('<p><b>За последние двое суток новых крупных сбоев в открытых источниках не найдено.</b> '
            'Последние известные события:</p>')
    return note + events_table(last)


def telegram_post(st):
    fresh = recent(st["events"], st["updated"], 2)
    lines = [f"<b>Статус блокировок · {upd_label(st, year=False)}</b>", ""]
    if fresh:
        for e in fresh[:5]:
            lines.append(f"• <b>{html.escape(e['region'])}</b> — {html.escape(e['title'])}")
            lines.append(f"  → {html.escape(e['meaning'])}")
    else:
        lines.append("За сутки новых крупных сбоев в открытых источниках не найдено.")
    lines += ["", f'Проверить свой интернет за 5 секунд: {SITE}/check/',
              f'Полная сводка: {SITE}/status/']
    return "\n".join(lines)


PROBE_JS = r"""
(function(){
var probes=[
 {id:'ru',name:'Российский сервис (Яндекс)',url:'https://yandex.ru/favicon.ico'},
 {id:'g',name:'Обычный зарубежный сайт (Google)',url:'https://www.google.com/favicon.ico'},
 {id:'tg',name:'Telegram',url:'https://telegram.org/favicon.ico'},
 {id:'ig',name:'Instagram',url:'https://www.instagram.com/favicon.ico'},
 {id:'yt',name:'YouTube',url:'https://www.youtube.com/favicon.ico'}];
var btn=document.getElementById('ck-run'),list=document.getElementById('ck-list'),out=document.getElementById('ck-out');
function probe(p){return new Promise(function(res){var t0=performance.now(),done=false,img=new Image();
var to=setTimeout(function(){if(!done){done=true;img.src='';res({ok:false,ms:7000});}},7000);
img.onload=function(){if(!done){done=true;clearTimeout(to);res({ok:true,ms:Math.round(performance.now()-t0)});}};
img.onerror=function(){if(!done){done=true;clearTimeout(to);res({ok:false,ms:Math.round(performance.now()-t0)});}};
img.src=p.url+'?t='+Date.now();});}
function row(p,r){var li=document.createElement('li');var dot=document.createElement('span');dot.className='ck-dot';
dot.style.background=r?(r.ok?(r.ms>3000?'#f59e0b':'#a3e635'):'#f87171'):'#3a3f52';li.appendChild(dot);
var t=document.createElement('span');t.textContent=p.name;li.appendChild(t);var s=document.createElement('b');
s.textContent=r?(r.ok?(r.ms>3000?'медленно':'открывается'):'не открывается'):'проверяем…';li.appendChild(s);return li;}
function verdict(R){var ru=R.ru.ok,g=R.g.ok,blk=R.tg.ok||R.ig.ok;
if(!ru&&!g&&!blk)return['Похоже, интернета нет вообще','Не открываются даже российские сайты. Так бывает при полном отключении мобильного интернета или слабом сигнале. VPN тут не поможет: подключитесь к Wi-Fi или домашнему интернету.','/status/','Что отключают сегодня'];
if(ru&&!g&&!blk)return['Похоже на режим белых списков','Российские сервисы открываются, а обычные зарубежные сайты — нет. Это белые списки на мобильном интернете. Подключитесь к Wi-Fi или используйте VPN с обходом белых списков.','/blog/belye-spiski-chto-eto/','Что такое белые списки'];
if(g&&!blk)return['Интернет есть, но заблокированные сервисы не открываются','Скорее всего, VPN выключен или его сервер заблокирован. Включите VPN, смените сервер или обновите подписку. Если не помогает — пора сменить сервис.','/blog/vpn-podklyuchen-no-net-interneta/','Что делать по шагам'];
var slow=R.yt.ok&&R.yt.ms>3000;
return['VPN работает: заблокированные сервисы открываются',slow?'Доступ есть, но YouTube отвечает медленно. Попробуйте сервер в более близкой стране.':'Всё в порядке. Если какое-то приложение всё равно не работает — перезапустите его.','/blog/','Полезные инструкции'];}
btn.addEventListener('click',function(){btn.disabled=true;btn.textContent='Проверяем…';out.hidden=true;list.textContent='';
probes.forEach(function(p){list.appendChild(row(p,null));});
Promise.all(probes.map(probe)).then(function(rs){var R={};list.textContent='';
probes.forEach(function(p,i){R[p.id]=rs[i];list.appendChild(row(p,rs[i]));});
var v=verdict(R);document.getElementById('ck-v').textContent=v[0];document.getElementById('ck-t').textContent=v[1];
var a=document.getElementById('ck-a');a.href=v[2];a.textContent=v[3]+' →';out.hidden=false;
btn.disabled=false;btn.textContent='Проверить ещё раз';});});
})();
"""

CHECK_CSS = """<style>
.ck{padding:28px;border-radius:24px;background:var(--card);border:1px solid var(--line);margin:22px 0}
.ck ul{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:8px}
.ck li{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;background:var(--card2);font-size:15px}
.ck li b{margin-left:auto;font-weight:600;color:var(--soft);font-size:14px}
.ck-dot{width:10px;height:10px;border-radius:50%;flex:0 0 auto}
.ck button{font:700 17px Manrope,sans-serif;background:var(--accent);color:#fff;border:0;border-radius:16px;padding:16px 26px;cursor:pointer;min-height:48px}
.ck button:disabled{opacity:.7;cursor:wait}
.ck-out{margin-top:18px;padding:20px;border-radius:18px;background:var(--violet-bg);border:1px solid var(--violet-line)}
.ck-out h2{font-size:22px;margin:0 0 8px}
.ck-out p{margin:0 0 12px;color:#e4defc}
.ck-out .row a{font-weight:700}
.bars{display:grid;gap:10px;margin:16px 0}
.bar{display:grid;grid-template-columns:minmax(150px,240px) 1fr 40px;gap:12px;align-items:center;font-size:15px}
.bar i{display:block;height:14px;border-radius:7px;min-width:4px}
.bar b{text-align:right}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chips a{padding:10px 16px;border-radius:999px;background:var(--card2);border:1px solid var(--line);text-decoration:none;color:var(--text);font-weight:700;min-height:44px;display:inline-flex;align-items:center}
.chips a:hover{border-color:#5b47a8}
.codebox{width:100%;min-height:110px;background:var(--card2);color:var(--text);border:1px solid #2b2f44;border-radius:12px;padding:12px;font:13px/1.5 ui-monospace,Menlo,monospace}
@media(max-width:560px){.bar{grid-template-columns:1fr 34px}.bar i{grid-column:1/3;order:3}}
</style>"""


def bars(counts, maxv):
    out = ""
    for t, label in TYPE_LABELS.items():
        n = counts.get(t, 0)
        w = 0 if maxv == 0 else max(2, round(100 * n / maxv))
        out += (f'<div class="bar"><span>{esc(label)}</span>'
                f'<i style="width:{w}%;background:{TYPE_COLORS[t]};opacity:{1 if n else .25}"></i><b>{n}</b></div>')
    return f'<div class="bars">{out}</div>'


def count_types(evs):
    c = {}
    for e in evs:
        c[e["type"]] = c.get(e["type"], 0) + 1
    return c


def main():
    arts = [parse(p) for p in sorted((SRC / "articles").glob("*.md"))]
    status = next((a for a in arts if a["slug"] == "status"), None)
    posts = sorted([a for a in arts if a["slug"] != "status"],
                   key=lambda a: (a["date"], a["slug"]), reverse=True)
    ST = load_status()
    UPD = ST["updated"]

    for d in ("blog", "status", "check", "operator", "index-blokirovok", "embed", "informer", "data"):
        shutil.rmtree(ROOT / d, ignore_errors=True)

    urls = [("/", UPD)]

    for a in posts:
        path = f"/blog/{a['slug']}/"
        crumbs = [("Главная", "/"), ("Статьи", "/blog/"), (a["title"], path)]
        upd = f" · обновлено {ru_date(a['updated'])}" if a["updated"] != a["date"] else ""
        body = (f'<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
                f'<h1>{esc(a["title"])}</h1>'
                f'<div class="meta">{ru_date(a["date"])}{upd}</div>'
                f'{a["body_html"]}{cta_block()}{related_html(a, posts)}</article>')
        write(f"blog/{a['slug']}/index.html",
              page(f'{a["title"]} — {BRAND}', a["description"], path, body,
                   article_jsonld(a, path, crumbs), "article"))
        urls.append((path, a["updated"]))

    # --- статус ---
    if status:
        path = "/status/"
        crumbs = [("Главная", "/"), (status["title"], path)]
        status["updated"] = max(status["updated"], UPD)
        body_html = status["body_html"].replace("<p>{{STATUS_TABLE}}</p>", status_block(ST) + (f'<p>Сводка каждое утро в Telegram: <a href="{CHANNEL}" target="_blank" rel="noopener">@{CHANNEL.rsplit("/", 1)[-1]}</a></p>' if CHANNEL else ""))
        body = (f'<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
                f'<h1>{esc(status["title"])}</h1>'
                f'<div class="meta">Обновлено {upd_label(ST)}</div>'
                f'{body_html}{cta_block()}</article>')
        write("status/index.html",
              page(f'{status["title"]} — {BRAND}', status["description"], path, body,
                   article_jsonld(status, path, crumbs)))
        urls.append((path, UPD))

    # --- проверка ---
    path = "/check/"
    crumbs = [("Главная", "/"), ("Проверка интернета", path)]
    check_faq = [
        ("Как работает проверка?", "Страница пробует загрузить маленькие значки с российского сервиса, "
         "обычного зарубежного сайта и заблокированных сервисов. По тому, что открылось, а что нет, "
         "видно, что у вас: белые списки, полное отключение или не работает VPN."),
        ("Вы сохраняете мои данные?", "Нет. Проверка идёт целиком в вашем браузере, на наш сервер ничего не отправляется."),
        ("Насколько точен результат?", "Это быстрая приблизительная проверка. Если результат кажется странным — "
         "запустите её ещё раз или сравните мобильный интернет и Wi-Fi."),
    ]
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in check_faq)
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Что с моим интернетом? Проверка за 5 секунд</h1>'
            f'<p class="lead"><b>Коротко:</b> нажмите кнопку — страница проверит, открываются ли российские '
            f'сервисы, обычные зарубежные сайты и заблокированные Telegram, Instagram, YouTube, и скажет, что делать.</p>'
            f'<div class="ck"><button id="ck-run" type="button">Проверить мой интернет</button>'
            f'<ul id="ck-list" aria-live="polite"></ul>'
            f'<div class="ck-out" id="ck-out" hidden><h2 id="ck-v"></h2><p id="ck-t"></p>'
            f'<div class="row"><a id="ck-a" href="/status/">Подробнее →</a>'
            f'<a href="{BOT}" rel="nofollow">Попробовать {BRAND} {CFG["trial"]} →</a>'
            f'<a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Написать в поддержку →</a></div></div>'
            f'<p class="note" style="margin:14px 0 0">Проверка идёт в вашем браузере, мы ничего не сохраняем.</p></div>'
            f'<h2>Как читать результат</h2><div class="tbl"><table><thead><tr><th>Что видите</th><th>Что это</th><th>Что делать</th></tr></thead><tbody>'
            f'<tr><td>Ничего не открывается</td><td>Интернет отключён или нет сигнала</td><td>Wi-Fi или домашний интернет</td></tr>'
            f'<tr><td>Открывается только российский сервис</td><td>Белые списки</td><td>Wi-Fi или VPN с обходом белых списков</td></tr>'
            f'<tr><td>Открываются российский и Google, но не Telegram и Instagram</td><td>VPN выключен или заблокирован</td><td>Включить VPN, сменить сервер</td></tr>'
            f'<tr><td>Открывается всё</td><td>VPN работает</td><td>Ничего не нужно</td></tr>'
            f'</tbody></table></div>'
            f'<h2>Вопросы и ответы</h2>{faq_html}{cta_block()}</article>'
            f'<script>{PROBE_JS}</script>')
    check_meta = {"title": "Что с моим интернетом? Проверка за 5 секунд",
                  "description": "Бесплатная проверка: белые списки, отключение мобильного интернета или не работает VPN. В браузере, без сохранения данных.",
                  "date": "2026-11-19", "updated": UPD, "faq": check_faq}
    write("check/index.html", page(f'{check_meta["title"]} — {BRAND}', check_meta["description"], path, body,
                                   article_jsonld(check_meta, path, crumbs)))
    urls.append((path, UPD))

    # --- страницы операторов ---
    for slug, (name, name_loc) in OPS.items():
        path = f"/operator/{slug}/"
        title = f"Не работает VPN на {name_loc}: статус на {ru_date(UPD, year=False)} и что делать"
        evs = [e for e in recent(ST["events"], UPD, 14)
               if "all" in e["operators"] or slug in e["operators"]]
        own = [e for e in evs if slug in e["operators"]]
        crumbs = [("Главная", "/"), ("Статус", "/status/"), (name, path)]
        summary = (f"За последние 14 дней — событий, которые касаются абонентов {name}: {len(evs)}"
                   + (f", из них отдельно по {name}: {len(own)}." if own else
                      f". Отдельных сообщений именно по {name} нет — ниже общие ограничения для всех операторов в регионах."))
        faq = [
            (f"Почему VPN не работает на {name_loc}, а на Wi-Fi работает?",
             "Ограничения с белыми списками и отключения вводятся на мобильном интернете. Домашний интернет и Wi-Fi "
             "под них не попадают, поэтому там тот же VPN продолжает работать."),
            (f"Работает ли {BRAND} на {name_loc}?",
             f"Голоса пользователей по {name} — работает ли сервис и обходит ли белые списки — смотрите в независимом "
             f"каталоге vpnstatus.site. Проверить на своём телефоне можно бесплатно: {CFG['trial']}."),
            ("Что делать прямо сейчас?",
             "Запустите проверку интернета на нашем сайте: она за 5 секунд покажет, белые списки у вас, отключение "
             "или проблема в VPN."),
        ]
        faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq)
        others = " · ".join(f'<a href="/operator/{s}/">{n}</a>' for s, (n, _) in OPS.items() if s != slug)
        body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}<h1>{esc(title)}</h1>'
                f'<div class="meta">Обновлено {ru_date(UPD)}</div>'
                f'<p class="lead"><b>Коротко:</b> {esc(summary)}</p>'
                f'<p><a class="btn" href="/check/">Проверить мой интернет за 5 секунд</a></p>'
                f'<h2>События за 14 дней</h2>'
                + (events_table(evs) if evs else "<p>Сообщений о сбоях за 14 дней в открытых источниках не найдено.</p>") +
                f'<h2>Что делать, если VPN не работает на {esc(name_loc)}</h2><ol>'
                f'<li><b>Включите и выключите авиарежим</b> — телефон заново зарегистрируется в сети.</li>'
                f'<li><b>Смените сервер в VPN</b> — блокируют конкретные адреса, а не весь сервис.</li>'
                f'<li><b>Обновите подписку или конфигурацию</b> в приложении.</li>'
                f'<li><b>Проверьте на Wi-Fi.</b> Если там работает — это ограничения на мобильной сети.</li>'
                f'<li><b>Открываются только Госуслуги и Яндекс?</b> Это белые списки: нужен Wi-Fi или VPN с обходом белых списков.</li></ol>'
                f'<p>Голоса пользователей {esc(BRAND)} по {esc(name)}: '
                f'<a href="{VPNSTATUS}" target="_blank" rel="noopener">vpnstatus.site ↗</a></p>'
                f'<h2>Вопросы и ответы</h2>{faq_html}<p>Другие операторы: {others}</p>{cta_block()}</article>')
        meta = {"title": title, "description": f"Статус VPN и мобильного интернета на {name_loc}: сбои и белые списки за 14 дней, что делать по шагам. Обновляется каждый день.",
                "date": "2026-11-19", "updated": UPD, "faq": faq}
        write(f"operator/{slug}/index.html", page(f"{title} — {BRAND}", meta["description"], path, body,
                                                  article_jsonld(meta, path, crumbs)))
        urls.append((path, UPD))

    # --- индекс блокировок ---
    path = "/index-blokirovok/"
    last7 = recent(ST["events"], UPD, 7)
    prev7 = [e for e in ST["events"] if 7 <= days_between(UPD, e["date"]) < 14]
    last30 = recent(ST["events"], UPD, 30)
    c7, cp, c30 = count_types(last7), count_types(prev7), count_types(last30)
    mx = max([*c30.values(), 1])
    delta = len(last7) - len(prev7)
    trend = ("больше" if delta > 0 else "меньше" if delta < 0 else "столько же")
    regions = {}
    for e in last30:
        regions[e["region"]] = regions.get(e["region"], 0) + 1
    top_regions = sorted(regions.items(), key=lambda x: -x[1])[:8]
    reg_html = "".join(f"<li>{esc(r)} — {n}</li>" for r, n in top_regions)
    crumbs = [("Главная", "/"), ("Индекс блокировок", path)]
    idx_faq = [("Откуда данные?", "Из открытых источников: сообщения СМИ и профильных изданий о сбоях, отключениях, "
                "белых списках и блокировках. Каждое событие в таблице со ссылкой на источник."),
               ("Можно ли использовать данные?", f"Да, со ссылкой на {SITE}/index-blokirovok/. Данные в формате JSON: "
                f"{SITE}/data/blocking-events.json")]
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Индекс блокировок: неделя по {ru_date(UPD)}</h1>'
            f'<div class="meta">Обновляется каждый день · данные из открытых источников</div>'
            f'<p class="lead"><b>Коротко:</b> за 7 дней зафиксировано событий: <b>{len(last7)}</b> — это {trend}, '
            f'чем неделей раньше ({len(prev7)}). За 30 дней — <b>{len(last30)}</b>.</p>'
            f'<h2>За 7 дней по типам</h2>{bars(c7, max([*c7.values(), 1]))}'
            f'<h2>За 30 дней по типам</h2>{bars(c30, mx)}'
            f'<h2>Где чаще всего (30 дней)</h2><ul>{reg_html or "<li>Нет данных</li>"}</ul>'
            f'<h2>Все события за 30 дней</h2>{events_table(last30) or "<p>Нет данных.</p>"}'
            f'<h2>Методика</h2><p>Мы ежедневно собираем сообщения о сбоях мобильного интернета, режимах белых списков, '
            f'блокировках VPN и сбоях сервисов из открытых источников. Одно событие — одно сообщение о конкретном регионе '
            f'и дне. Это не полная статистика всех сбоев в стране, а индикатор того, о чём сообщают.</p>'
            f'<h2>Вопросы и ответы</h2>' + "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in idx_faq) +
            f'{cta_block()}</article>')
    idx_meta = {"title": "Индекс блокировок интернета в России", "description":
                f"Сколько сбоев, отключений мобильного интернета и белых списков за неделю и месяц. Данные из открытых источников, обновление каждый день.",
                "date": "2026-11-19", "updated": UPD, "faq": idx_faq}
    ld = article_jsonld(idx_meta, path, crumbs) + [{
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Индекс блокировок интернета в России (ThuggerVPN)",
        "description": "Ежедневно обновляемый список сбоев мобильного интернета, режимов белых списков, блокировок VPN и сбоев сервисов в России по сообщениям открытых источников.",
        "url": f"{SITE}{path}", "dateModified": UPD, "inLanguage": "ru",
        "creator": {"@type": "Organization", "name": BRAND, "url": SITE},
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                          "contentUrl": f"{SITE}/data/blocking-events.json"}]}]
    write("index-blokirovok/index.html", page(f'{idx_meta["title"]} — неделя по {ru_date(UPD)} — {BRAND}',
                                              idx_meta["description"], path, body, ld))
    urls.append((path, UPD))
    write("data/blocking-events.json", json.dumps(
        {"source": SITE + "/index-blokirovok/", "updated": UPD,
         "events": [{k: e[k] for k in ("date", "region", "operators", "type", "title", "source", "url") if k in e}
                    for e in ST["events"]]}, ensure_ascii=False, indent=1))

    # --- информер ---
    latest3 = ST["events"][:3]
    emb_rows = "".join(
        f'<li><small>{ru_date(e["date"], year=False)} · {esc(e["region"])}</small><b>{esc(e["title"])}</b></li>'
        for e in latest3)
    embed = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Статус блокировок — информер {BRAND}</title><style>
@font-face{{font-family:Manrope;font-weight:200 800;src:url(/assets/fonts/manrope-cyrillic-wght-normal.woff2) format('woff2')}}
body{{margin:0;background:#12131b;color:#edeff5;font:15px/1.5 Manrope,system-ui,sans-serif}}
.w{{padding:16px;border:1px solid #1f2230;border-radius:16px;height:100%;box-sizing:border-box}}
h1{{font-size:16px;margin:0 0 10px;display:flex;justify-content:space-between;gap:8px}}
h1 span{{font-size:12px;color:#0a0b10;background:#a3e635;border-radius:6px;padding:2px 7px;align-self:center}}
ul{{list-style:none;margin:0;padding:0;display:grid;gap:8px}}li{{padding:10px 12px;border-radius:12px;background:#191b27}}
li small{{display:block;color:#9aa2b3;font-size:12px}}li b{{font-size:14px;font-weight:600}}
a{{display:block;margin-top:10px;color:#c4b5fd;font-weight:700;text-decoration:none;font-size:14px}}
</style></head><body><div class="w"><h1>Статус блокировок <span>{ru_date(UPD, year=False)}</span></h1><ul>{emb_rows}</ul>
<a href="{SITE}/status/" target="_blank" rel="noopener">Полная сводка и что делать — {BRAND} →</a></div></body></html>"""
    write("embed/status/index.html", embed)
    code = (f'<iframe src="{SITE}/embed/status/" width="100%" height="360" style="border:0;max-width:420px" '
            f'loading="lazy" title="Статус блокировок — {BRAND}"></iframe>')
    path = "/informer/"
    crumbs = [("Главная", "/"), ("Информер", path)]
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Информер «Статус блокировок» для вашего сайта</h1>'
            f'<p class="lead"><b>Коротко:</b> бесплатная карточка со свежими сбоями интернета. '
            f'Обновляется сама каждый день — вставьте код один раз.</p>'
            f'<h2>Как выглядит</h2><iframe src="/embed/status/" width="100%" height="360" '
            f'style="border:0;max-width:420px" title="Пример информера"></iframe>'
            f'<h2>Код для вставки</h2><textarea class="codebox" id="emb-code" readonly>{esc(code)}</textarea>'
            f'<p><button class="btn" type="button" id="emb-copy" style="border:0;cursor:pointer">Скопировать код</button></p>'
            f'<p class="note">Для Telegram-каналов: делитесь ссылкой {SITE}/status/ — превью подтянется автоматически.</p>'
            f'</article><script>document.getElementById("emb-copy").addEventListener("click",function(){{'
            f'var t=document.getElementById("emb-code");t.select();try{{navigator.clipboard.writeText(t.value)}}catch(e){{document.execCommand("copy")}}'
            f'this.textContent="Скопировано";}});</script>')
    write("informer/index.html", page(f"Информер «Статус блокировок» — {BRAND}",
                                      "Бесплатный информер со свежими сбоями интернета для сайтов и блогов. Обновляется автоматически.",
                                      path, body))
    urls.append((path, UPD))

    # --- Telegram-пост (публикует GitHub Actions) ---
    write("_src/out/telegram.html", telegram_post(ST))

    # --- список статей ---
    items = "".join(
        f'<li><a href="/blog/{a["slug"]}/"><b>{esc(a["title"])}</b>'
        f'<span>{esc(a["description"])}</span></a></li>' for a in posts)
    write("blog/index.html",
          page(f"Статьи — {BRAND}", "Инструкции: что делать, если не работает VPN, "
               "белые списки, сбои мобильного интернета.", "/blog/",
               f'<div class="narrow" style="margin:0 auto"><h1 style="font-size:40px">Статьи</h1>'
               f"<ul class='list'>{items}</ul></div>"))
    urls.append(("/blog/", UPD))

    # --- главная ---
    st_tiles = "".join(
        f'<div class="st" style="border-top-color:{TYPE_COLORS.get(e["type"], "#a78bfa")}">'
        f'<small>{ru_date(e["date"], year=False)} · {esc(e["region"])}</small>'
        f'<b>{esc(e["title"])}</b><span>{esc(e["meaning"])}</span></div>' for e in ST["events"][:3])
    st_title = f'Статус блокировок · {ru_date(UPD, year=False)}'
    op_chips = "".join(f'<a href="/operator/{s}/">{n}</a>' for s, (n, _) in OPS.items())
    cards = "".join(
        f'<a class="tile" href="/blog/{a["slug"]}/"><div><div class="t-title">{esc(a["title"])}</div>'
        f'<div class="t-sub">{esc(a["description"])}</div></div>'
        f'<span class="arrow" aria-hidden="true">↗</span></a>' for a in posts[:6])
    home = f"""{CHECK_CSS}
<section class="hero">
<div class="hero-text">
<h1>Интернет без «соединение…»</h1>
<p class="lead">{BRAND} работает на мобильном и домашнем интернете. Подключение через Telegram-бота за пару минут.</p>
<div class="row"><a class="btn" href="{BOT}" rel="nofollow">{CFG["trial"].capitalize()}</a>
<a class="btn-ghost" href="/check/">Проверить мой интернет</a></div>
<p class="note" style="margin-top:14px">дальше {CFG["price"]}{(" · " + CFG["price_from"]) if CFG.get("price_from") else ""}</p>
</div>
<div class="stage" aria-hidden="true"><div class="iso"><div class="grid"></div>
<div class="plate p1">Мобильный интернет</div><div class="plate p2">Домашний Wi-Fi</div>
<div class="plate p3">{SHIELD}<span>{BRAND}</span></div></div><div class="beam"></div></div>
</section>

<section class="sec" id="status"><div class="bento">
<div class="tile wide"><div class="tile-head"><h2>{esc(st_title)}</h2><span><a href="/status/">Вся сводка →</a> · <a href="{CHANNEL}" target="_blank" rel="noopener">Сводка в Telegram</a></span></div>
<div class="st-grid">{st_tiles}</div></div>
<div class="tile violet"><div><div class="big">5 секунд</div>
<p style="color:#c9c2e8;margin:10px 0 0">чтобы понять, что у вас: белые списки, отключение или не работает VPN.</p></div>
<a class="btn" href="/check/" style="align-self:flex-start">Проверить интернет</a></div>
<div class="tile"><h2 style="font-size:22px;margin:0 0 14px">Статус по оператору</h2><div class="chips">{op_chips}</div></div>
<a class="tile" href="/index-blokirovok/"><div><div class="t-title">Индекс блокировок</div>
<div class="t-sub">Сколько сбоев и белых списков за неделю и месяц — с источниками</div></div><span class="arrow" aria-hidden="true">↗</span></a>
<div class="tile"><div class="t-title">{CFG["trial"].capitalize()}</div>
<div class="t-sub">Проверьте на своём операторе, прежде чем платить.</div>
<p style="margin:14px 0 0"><a href="{BOT}" rel="nofollow">Открыть бота →</a></p></div>
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
                "sameAs": [x for x in (BOT, VPNSTATUS, CHANNEL) if x]},
               {"@context": "https://schema.org", "@type": "WebSite",
                "name": BRAND, "url": SITE, "inLanguage": "ru"}]
    write("index.html", page(f"{BRAND} — VPN для мобильного и домашнего интернета",
                             "Проверка блокировок за 5 секунд, статус по операторам, что делать, если VPN не работает. "
                             f"{BRAND}: {CFG['trial']}.", "/", home, home_ld))

    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /embed/\n\n" + "".join(
        f"User-agent: {b}\nAllow: /\n\n" for b in
        ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot",
         "Google-Extended", "Bingbot"]) + f"Sitemap: {SITE}/sitemap.xml\n")
    llms = [f"# {BRAND}", "",
            f"> {BRAND} — VPN-сервис для пользователей из России с подключением через "
            f"Telegram-бота ({BOT}). {price_line()}. Работает на мобильном и домашнем интернете"
            + (f"; {CFG['whitelist_option'].lower()}" if CFG.get("whitelist_option") else "")
            + f". Поддержка: {SUPPORT}. Отзывы и голоса пользователей по операторам: {VPNSTATUS}. "
            "Сайт публикует ежедневную сводку блокировок, индекс блокировок и инструкции.", "",
            "## Инструменты и данные",
            f"- [Проверка интернета за 5 секунд]({SITE}/check/): белые списки, отключение или не работает VPN",
            f"- [Статус блокировок сегодня]({SITE}/status/)",
            f"- [Индекс блокировок]({SITE}/index-blokirovok/): события за 7 и 30 дней с источниками; JSON: {SITE}/data/blocking-events.json"]
    llms += [f"- [Не работает VPN на {loc}]({SITE}/operator/{s}/)" for s, (_, loc) in OPS.items()]
    llms += ["", "## Статьи"] + [f"- [{a['title']}]({SITE}/blog/{a['slug']}/): {a['description']}" for a in posts]
    write("llms.txt", "\n".join(llms) + "\n")
    write(f"{CFG['indexnow_key']}.txt", CFG["indexnow_key"])
    write(".nojekyll", "")
    write("favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
          '<rect x="5" y="5" width="22" height="22" rx="6" transform="rotate(45 16 16)" '
          'fill="#8b5cf6"/><rect x="12" y="12" width="8" height="8" rx="2" '
          'transform="rotate(45 16 16)" fill="#0a0b10"/></svg>')
    write("404.html", page(f"Страница не найдена — {BRAND}", "Страница не найдена.",
                           "/404.html", "<h1>Страница не найдена</h1>"
                           "<p><a href='/'>На главную</a> · <a href='/check/'>Проверить интернет</a></p>"))
    print(f"Готово: {len(posts)} статей, {len(ST['events'])} событий в базе, "
          f"{len(urls)} адресов в sitemap")


if __name__ == "__main__":
    main()
