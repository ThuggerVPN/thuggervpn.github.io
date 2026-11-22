#!/usr/bin/env python3
"""Собирает статический сайт из _src/articles/*.md в корень репозитория.

Запуск: python3 _src/build.py
Формат статьи: блок метаданных между строками '---' (title, description, date, slug,
updated - необязательно), затем Markdown. Раздел '## Вопросы и ответы' с подзаголовками
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
import checker

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
CFG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
BRAND = CFG["brand"]
BOT_PLAIN = CFG["bot_url"]
BOT = CFG.get("bot_ref_url", BOT_PLAIN)  # реферальная ссылка - для подсчёта пришедших с сайта
BOT_NAME = "@" + BOT_PLAIN.rsplit("/", 1)[-1]
GC = CFG.get("goatcounter", "")
MIRRORS = [m.rstrip("/") for m in CFG.get("mirrors", [])]  # запасные адреса сайта
VPNSTATUS = CFG.get("vpnstatus_url", "https://vpnstatus.site")
ASSIST_PATH = SRC / "assistant.json"
SUPPORT = CFG.get("support_url", BOT)
CHANNEL = CFG.get("channel_url", "")

MSK = ZoneInfo("Europe/Moscow")

# Страницы, у которых есть английская версия (/en + тот же путь)
EN_STATIC = {"/", "/priglasit/", "/check/", "/podklyuchenie/", "/status/", "/index-blokirovok/", "/informer/", "/blog/",
             "/operator/mts/", "/operator/beeline/", "/operator/megafon/", "/operator/t2/"}


def _slugs(folder):
    out = set()
    for f in (SRC / folder).glob("*.md") if (SRC / folder).exists() else []:
        m = re.search(r"^slug:\s*(\S+)", f.read_text(encoding="utf-8"), re.M)
        if m and m.group(1) != "status":
            out.add(f"/blog/{m.group(1)}/")
    return out


# Статья связывается с переводом, только если есть обе версии.
# Статьи только на английском (для иностранцев) живут без пары.
EN_PAGES = EN_STATIC | (_slugs("articles_en") & _slugs("articles"))


def ru_path(path):
    return path[3:] if path.startswith("/en/") else path


def alt_links(path):
    rp = ru_path(path)
    if rp not in EN_PAGES:
        return ""
    return (f'<link rel="alternate" hreflang="ru" href="{SITE}{rp}">'
            f'<link rel="alternate" hreflang="en" href="{SITE}/en{rp}">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{rp}">')


def today_msk():
    return datetime.now(MSK).date()


MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso, year=True):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


def ocenok(n):
    """«оценка / оценки / оценок» по числу."""
    n = int(n)
    if n % 10 == 1 and n % 100 != 11:
        w = "оценка"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        w = "оценки"
    else:
        w = "оценок"
    return f"{n} {w}"


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
    trial = CFG.get("en", {}).get("trial", "3 days free") if "articles_en" in str(path) else CFG["trial"]
    body = m.group(2).replace("{{BOT}}", BOT).replace("{{PRICE}}", CFG["price"]) \
        .replace("{{TRIAL}}", trial).replace("{{BRAND}}", BRAND)
    meta["body_md"] = body
    meta["body_html"] = markdown.markdown(body, extensions=["tables", "sane_lists"]) \
        .replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    meta["faq"] = extract_faq(body)
    return meta


def extract_faq(md_text):
    m = re.search(r"^## (?:Вопросы и ответы|FAQ)\s*$(.*?)(?=^## |\Z)", md_text, re.S | re.M)
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
:root{--bg:#0a0b10;--card:#12131b;--card2:#191b27;--card3:#151826;--line:#1f2230;--line2:#2b2f44;--line-hi:#5b47a8;--text:#edeff5;--text-hi:#fff;--muted:#9aa2b3;--soft:#b5bccb;--accent:#8b5cf6;--accent2:#c4b5fd;--violet-bg:#161130;--violet-line:#3b2f6b;--violet-text:#d4ccf2;--link:#b9a4ff;--p2:rgba(32,26,64,.88);--p2l:#4a3c8c;--p2t:#d6ccff;--stepn:#2d2650;--sh:rgba(0,0,0,.55);color-scheme:dark}
:root[data-theme=light]{--bg:#f5f5fa;--card:#ffffff;--card2:#f0f0f6;--card3:#eef0f7;--line:#e4e4ee;--line2:#d4d5e3;--line-hi:#a78bfa;--text:#15161d;--text-hi:#000;--muted:#5c6375;--soft:#3f4558;--accent:#7c3aed;--accent2:#6d28d9;--violet-bg:#f2edff;--violet-line:#dacdff;--violet-text:#4a3b7e;--link:#6d28d9;--p2:rgba(237,233,254,.94);--p2l:#c9b8ff;--p2t:#5b3fc4;--stepn:#e6dfff;--sh:rgba(40,30,90,.14);color-scheme:light}
@media(prefers-color-scheme:light){:root:not([data-theme=dark]){--bg:#f5f5fa;--card:#ffffff;--card2:#f0f0f6;--card3:#eef0f7;--line:#e4e4ee;--line2:#d4d5e3;--line-hi:#a78bfa;--text:#15161d;--text-hi:#000;--muted:#5c6375;--soft:#3f4558;--accent:#7c3aed;--accent2:#6d28d9;--violet-bg:#f2edff;--violet-line:#dacdff;--violet-text:#4a3b7e;--link:#6d28d9;--p2:rgba(237,233,254,.94);--p2l:#c9b8ff;--p2t:#5b3fc4;--stepn:#e6dfff;--sh:rgba(40,30,90,.14);color-scheme:light}}
.theme-t{background:none;border:1px solid var(--line2);color:var(--soft);border-radius:8px;width:30px;height:28px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0}
.theme-t:hover{color:var(--text-hi);border-color:var(--line-hi)}.theme-t svg{width:16px;height:16px}.theme-t .mo{display:none}
:root[data-theme=light] .theme-t .su{display:none}:root[data-theme=light] .theme-t .mo{display:block}
@media(prefers-color-scheme:light){:root:not([data-theme=dark]) .theme-t .su{display:none}:root:not([data-theme=dark]) .theme-t .mo{display:block}}
body,header,nav,.tile,.card,.plan,details{transition:background-color .25s ease,border-color .25s ease,color .25s ease}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;overflow-x:clip}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;overflow-x:hidden}
a{color:var(--link)}a:hover{color:var(--text-hi)}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
.narrow{max-width:780px}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:18px;padding-bottom:18px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--text);font-weight:800;font-size:19px}
.hl{display:flex;align-items:center;gap:10px}.lang{font-size:12px;font-weight:800;letter-spacing:.5px;color:var(--soft);text-decoration:none;border:1px solid var(--line2);border-radius:8px;padding:5px 8px;min-height:28px;display:inline-flex;align-items:center}.lang:hover{color:var(--text-hi);border-color:var(--line-hi)}
.logo i{width:30px;height:30px;border-radius:9px;background:var(--accent);display:inline-flex;align-items:center;justify-content:center;transform:rotate(45deg)}
.logo i b{width:12px;height:12px;border-radius:3px;background:var(--bg)}
nav{display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:5px;border-radius:14px;background:var(--card);border:1px solid var(--line)}
nav a{color:var(--soft);text-decoration:none;font-size:15px;padding:9px 13px;border-radius:10px;min-height:40px;display:inline-flex;align-items:center}
nav a:hover{background:var(--card2);color:var(--text-hi)}
nav a.btn-s{background:var(--accent);color:#fff;font-weight:700}
nav a.btn-s:hover{background:#7c3aed}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;text-decoration:none;font-weight:700;font-size:17px;padding:16px 26px;border-radius:16px;min-height:48px;transition:transform .2s ease,box-shadow .2s ease}
.btn:hover{color:#fff;transform:translateY(-2px);box-shadow:0 12px 30px -8px rgba(139,92,246,.85)}
.btn-ghost{display:inline-flex;align-items:center;border:1px solid var(--line2);color:var(--text);text-decoration:none;font-weight:700;font-size:17px;padding:15px 22px;border-radius:16px;min-height:48px}
.btn-ghost:hover{border-color:var(--line-hi)}
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
.p1{background:var(--card3);border:1px solid var(--line2);color:var(--soft);box-shadow:30px 30px 60px var(--sh);animation:l1 7s ease-in-out infinite}
.p2{background:var(--p2);border:1px solid var(--p2l);color:var(--p2t);box-shadow:30px 30px 60px var(--sh);animation:l2 7s ease-in-out infinite}
.p3{background:var(--accent);border:1px solid var(--accent2);color:#fff;font-size:24px;font-weight:800;flex-direction:column;align-items:flex-start;justify-content:space-between;box-shadow:0 0 60px rgba(139,92,246,.7),30px 30px 60px var(--sh);animation:l3 7s ease-in-out infinite}
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
a.tile:hover,.tile.hov:hover{transform:translateY(-5px);border-color:var(--line-hi)}
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
.step .n{font-size:56px;font-weight:800;color:var(--stepn);line-height:1}
.step.s1{transform:rotateY(8deg)}.step.s3{transform:rotateY(-8deg);background:var(--accent);border-color:var(--accent2);box-shadow:0 30px 60px -25px rgba(139,92,246,.8)}
.step.s3 .n{color:var(--accent2)}.step.s3 .t-sub{color:#ede9fe}
.trust{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px;padding:32px;border-radius:24px;background:var(--card);border:1px solid var(--line)}
.trust p{margin:6px 0 0;color:var(--soft);max-width:640px}
.trust h2{margin:0;font-size:30px}
.proof{display:inline-flex;align-items:center;gap:8px;margin-top:18px;color:var(--soft);text-decoration:none;font-size:15px;flex-wrap:wrap}
.proof svg{width:16px;height:16px}.proof b{color:var(--text-hi)}.proof:hover{color:var(--text-hi)}
.usp{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;padding-top:10px}
.usp .u{padding:20px 22px;border-radius:18px;background:var(--card);border:1px solid var(--line)}
.usp b{display:block;font-size:18px}.usp span{display:block;color:var(--muted);font-size:15px;margin-top:4px;line-height:1.5}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:14px}
.plan{position:relative;padding:22px;border-radius:20px;background:var(--card);border:1px solid var(--line)}
.plan.best{background:var(--violet-bg);border-color:var(--accent);box-shadow:0 20px 50px -25px rgba(139,92,246,.8)}
.plan .tag{position:absolute;top:-11px;left:18px;background:var(--accent);color:#fff;font-size:12px;font-weight:800;padding:4px 10px;border-radius:999px}
.pl-name{font-weight:700;color:var(--soft)}.pl-price{font-size:36px;font-weight:800;margin:6px 0 2px}.pl-price small{font-size:16px;color:var(--muted);font-weight:600}
.pl-sub{font-size:14px;color:var(--muted)}
.steps3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.steps3>div{display:grid;grid-template-columns:44px 1fr;column-gap:14px;align-items:center;padding:18px;border-radius:18px;background:var(--card);border:1px solid var(--line)}
.steps3 span{grid-row:span 2;width:44px;height:44px;border-radius:12px;background:var(--accent);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:18px}
.steps3 small{color:var(--muted);font-size:14px}
details.acc,details.acc-q{border-radius:18px;background:var(--card);border:1px solid var(--line);padding:0 20px;margin-bottom:10px}
details.acc>summary,details.acc-q>summary{cursor:pointer;list-style:none;padding:18px 32px 18px 0;font-weight:700;font-size:17px;position:relative;min-height:44px}
details.acc>summary::-webkit-details-marker,details.acc-q>summary::-webkit-details-marker{display:none}
details.acc>summary::after,details.acc-q>summary::after{content:"+";position:absolute;right:0;top:50%;transform:translateY(-50%);font-size:24px;color:var(--accent2);font-weight:500}
details[open].acc>summary::after,details[open].acc-q>summary::after{content:"−"}
details.acc[open],details.acc-q[open]{padding-bottom:18px}
details.acc-q p{margin:0;color:var(--soft)}
.stars{display:flex;gap:4px;margin-bottom:10px}
.stars.sm svg{width:14px;height:14px}
.trust2{padding:30px;border-radius:24px;background:var(--card);border:1px solid var(--line)}
.tr-head{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:20px}
.tr-head h2{margin:0;font-size:30px}.tr-head p{margin:8px 0 0;color:var(--soft);max-width:640px}
.tr-grid{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:16px;margin-top:22px;align-items:stretch}
.tr-score{padding:22px;border-radius:18px;background:var(--violet-bg);border:1px solid var(--violet-line)}
.tr-score .big span{font-size:22px;color:var(--violet-text);font-weight:700}
.tr-ops{min-width:0!important}.tr-ops td,.tr-ops th{padding:10px 12px}.tr-ops .na{color:var(--muted);font-size:14px}
.tr-revs{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:16px}
.rv{padding:18px;border-radius:16px;background:var(--card2)}
.rv p{margin:6px 0 8px;font-size:15px;line-height:1.55}.rv small{color:var(--muted)}
.cta{margin:36px 0;padding:28px;border-radius:24px;background:var(--violet-bg);border:1px solid var(--violet-line);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px}
.cta b{font-size:22px;display:block;margin-bottom:4px}
.cta p{margin:0;color:var(--violet-text);max-width:620px}
.cta .links{display:flex;flex-direction:column;gap:10px;align-items:flex-start}
.cta .links a.small{font-size:15px;color:var(--accent2)}
article h1{font-size:38px;line-height:1.2;margin:18px 0 10px}
article h2{font-size:26px;margin:38px 0 10px}
article h3{font-size:20px;margin:26px 0 8px}
article .lead{font-size:19px;max-width:none}
.meta{color:var(--muted);font-size:14px;margin-bottom:22px}
.crumbs{font-size:14px;color:var(--muted);margin-top:8px}
.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--text-hi)}
.tbl{overflow-x:auto;margin:18px 0;border-radius:14px;border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;min-width:520px;font-size:15px}
th,td{border-bottom:1px solid var(--line);padding:11px 13px;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:700}
tr:last-child td{border-bottom:0}
code{background:var(--card2);padding:2px 6px;border-radius:6px}
blockquote{margin:16px 0;padding:14px 18px;background:var(--card);border-radius:14px}
.list{list-style:none;padding:0;margin:0;display:grid;gap:14px}
.list li a{display:block;padding:22px 24px;border-radius:20px;background:var(--card);border:1px solid var(--line);text-decoration:none;color:var(--text);transition:transform .3s ease,border-color .3s ease}
.list li a:hover{transform:translateY(-4px);border-color:var(--line-hi)}
.list li span{display:block;color:var(--muted);font-size:15px;margin-top:6px}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px}
footer .wrap{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-top:26px;padding-bottom:26px}
footer a{color:var(--link);text-decoration:none}
@media(max-width:860px){.tr-grid{grid-template-columns:1fr}.tr-head h2{font-size:24px}.trust2{padding:22px}.stage{height:360px}.hide-m{display:none!important}nav a{padding:8px 11px;font-size:14px}.tile-head h2{font-size:24px}.trust h2{font-size:24px}.cta b{font-size:20px}.tile.wide{grid-column:auto}.hero h1{font-size:42px}.stage{height:320px;margin-top:40px;margin-bottom:-50px}.plans{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.plan{padding:18px 14px}.pl-price{font-size:26px}.pl-sub{font-size:12.5px}.usp .u{padding:16px 18px}.tr-revs{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding-bottom:6px}.tr-revs .rv{flex:0 0 82%;scroll-snap-align:start}.iso{width:220px;height:220px}.sec h2{font-size:30px}.step.s1,.step.s3{transform:none}article h1{font-size:30px}.p3{font-size:20px}}
.qa-fab{position:fixed;right:18px;bottom:18px;z-index:50;display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:#fff;border:0;border-radius:999px;padding:14px 20px;font:700 16px Manrope,sans-serif;cursor:pointer;box-shadow:0 14px 34px -8px rgba(139,92,246,.75);min-height:48px}
.qa-fab:hover{background:#7c3aed}
.qa{position:fixed;right:18px;bottom:84px;z-index:51;width:min(420px,calc(100vw - 24px));max-height:min(640px,calc(100vh - 110px));display:none;flex-direction:column;background:var(--card);border:1px solid var(--line2);border-radius:22px;box-shadow:0 40px 80px -20px var(--sh),0 0 0 1px rgba(139,92,246,.15);overflow:hidden}
.qa.open{display:flex}
.qa-head{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--line)}
.qa-head b{font-size:17px}
.qa-x{background:none;border:0;color:var(--soft);font-size:24px;line-height:1;cursor:pointer;width:44px;height:44px;border-radius:12px}
.qa-x:hover{background:var(--card2);color:var(--text-hi)}
.qa-body{padding:16px 18px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.qa-form{display:flex;gap:8px}
.qa-form label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.qa-form input{flex:1;min-width:0;background:var(--card2);border:1px solid var(--line2);color:var(--text);border-radius:12px;padding:12px 14px;font:16px Manrope,sans-serif;min-height:46px}
.qa-form input:focus{outline:2px solid var(--accent);outline-offset:1px}
.qa-form button{background:var(--accent);color:#fff;border:0;border-radius:12px;padding:0 16px;font:700 15px Manrope,sans-serif;cursor:pointer;min-height:46px}
.qa-chips{display:flex;flex-wrap:wrap;gap:8px}
.qa-chips button{background:var(--card2);color:var(--soft);border:1px solid var(--line2);border-radius:999px;padding:9px 13px;font:600 14px Manrope,sans-serif;cursor:pointer;text-align:left;min-height:40px}
.qa-chips button:hover{border-color:var(--line-hi);color:var(--text-hi)}
.qa-ans{background:var(--violet-bg);border:1px solid var(--violet-line);border-radius:16px;padding:14px 16px;white-space:pre-line;font-size:15px;line-height:1.6;color:var(--violet-text)}
.qa-ans:empty{display:none}
.qa-ans a{display:inline-block;margin-top:10px;margin-right:12px;font-weight:700}
.qa-hint{color:var(--muted);font-size:13px;margin:0}
@media(max-width:560px){.qa-fab span{display:none}.qa-fab{padding:14px}.qa{right:12px;bottom:78px}}
nav{flex-wrap:nowrap;max-width:100%}nav a{white-space:nowrap}
@media(max-width:600px){header .wrap{gap:12px;padding-top:14px;padding-bottom:12px}nav{width:100%;justify-content:space-between;gap:2px;padding:4px;border-radius:14px}nav a{flex:1 1 auto;justify-content:center;padding:9px 6px;font-size:14px;min-height:42px}nav a.btn-s{flex:1.25 1 auto}}
@media(max-width:430px){.wrap{padding:0 16px}nav a{font-size:13.5px;padding:9px 4px}}
@media(max-width:374px){.hide-xs{display:none!important}nav a{font-size:13px}.logo{font-size:17px}}
.pwa-row{display:flex;gap:16px;align-items:center;margin-bottom:12px}.pwa-p{margin:0 0 18px;color:var(--soft);max-width:680px}button.btn{font-family:inherit;border:0;cursor:pointer}.pwa-row img{border-radius:16px;flex:0 0 auto}.pwa-row h2{margin:0;font-size:26px;line-height:1.2}.pwa ol{margin:14px 0 0;padding-left:22px;color:var(--soft)}.pwa ol li{margin:4px 0}#pwa-and,#pwa-done{margin:14px 0 0}@media(max-width:560px){.pwa-row h2{font-size:21px}.pwa-row img{width:52px;height:52px}}
.ds-mark{}
/* --- Единая система размеров: один масштаб шрифтов, отступов и скруглений для всех экранов --- */
:root{--r-lg:22px;--r-md:16px;--r-sm:12px;--pad:clamp(20px,3.6vw,28px);--gap:clamp(12px,2vw,16px)}
body{font-size:clamp(16px,1.1vw + 12px,17px);line-height:1.62}
.hero{padding:clamp(20px,4vw,40px) 0 clamp(8px,2vw,16px);gap:clamp(16px,3vw,32px)}
.hero h1{font-size:clamp(36px,5.6vw,60px);line-height:1.05;letter-spacing:-.025em;margin:0 0 18px}
.lead,article .lead{font-size:clamp(17px,1.4vw + 11px,19px);line-height:1.6}
.sec{padding:clamp(28px,4.4vw,52px) 0}
.sec h2{font-size:clamp(26px,2.6vw + 14px,36px);line-height:1.15;letter-spacing:-.02em}
.tr-head h2,.trust h2,.tile-head h2,.pwa-row h2{font-size:clamp(21px,1.4vw + 15px,28px)!important;line-height:1.2;letter-spacing:-.015em}
.sec.usp{padding-top:0}#check-sec .ck{margin-bottom:0}#how .steps3+p{margin:14px 0 0}
.sec h2{margin:0 0 14px}.sec>.lead{margin:0 0 22px}
article h1{font-size:clamp(28px,3.4vw + 14px,40px);line-height:1.18;letter-spacing:-.02em}
article h2{font-size:clamp(22px,1.6vw + 16px,28px);margin:clamp(28px,4vw,40px) 0 10px}
article h3{font-size:clamp(18px,.6vw + 15px,20px)}
.tile,.step,.usp .u,.plan,.steps3>div,.trust,.trust2,.cta,.ck{border-radius:var(--r-lg)}
.tile,.step,.trust,.trust2,.cta,.ck{padding:var(--pad)}
.usp .u{padding:18px 20px}.usp{gap:var(--gap)}.bento,.plans,.steps3,.steps,.tr-revs{gap:var(--gap)}
.rv,.st,.tr-score,.ck-out,details.acc,details.acc-q,.list li a,.dev-panel,.app-rec{border-radius:var(--r-md)}
.ck li,.chips a,code,.kbd{border-radius:var(--r-sm)}
.btn,.btn-ghost,.ck button{min-height:52px;border-radius:14px;font-size:16.5px;padding:0 24px;line-height:1.2}
.btn-ghost{padding:0 22px}
nav a.btn-s{border-radius:10px}
.ck .ck-tabs button{min-height:42px;padding:0 16px}
.ck-out h2{font-size:clamp(19px,1vw + 14px,22px);line-height:1.3}
.cta b{font-size:clamp(19px,1vw + 14px,22px)}
.pl-price{font-size:clamp(26px,2vw + 14px,34px)}
.note,.t-sub,.usp span,.steps3 small{font-size:14.5px}
footer{font-size:14px}
@media(max-width:600px){body .st4>div{grid-template-columns:40px 1fr;gap:12px;padding:16px}body .st4 .n{width:40px;height:40px;border-radius:12px;font-size:17px}body .st4 h3{font-size:17.5px}.btn,.btn-ghost{text-align:center}.usp .u{padding:14px 16px}.plans{gap:10px}.plan{padding:16px 14px}.btn,.btn-ghost{width:100%;justify-content:center}.row{gap:10px}.hero .row .btn-ghost{width:100%}}
.qa-dot{display:none;width:10px;height:10px;border-radius:50%;background:#a3e635;box-shadow:0 0 0 2px var(--accent)}.qa-fab.has-new .qa-dot{display:block}.qa-human{margin-top:14px;border-top:1px solid var(--line2);padding-top:14px}.qa-call{width:100%;min-height:46px;border-radius:12px;border:1px solid var(--line2);background:var(--card2);color:var(--text);font:700 15px Manrope,sans-serif;cursor:pointer}.qa-call:hover{border-color:var(--line-hi)}.qa-thread{max-height:220px;overflow:auto;display:flex;flex-direction:column;gap:8px;margin:0 0 10px}.qa-m{padding:10px 12px;border-radius:12px;font-size:14.5px;line-height:1.45;max-width:88%}.qa-m b{display:block;font-size:12px;opacity:.7;margin-bottom:2px}.qa-m.me{align-self:flex-end;background:var(--accent);color:#fff}.qa-m.op{align-self:flex-start;background:var(--card2);border:1px solid var(--line2)}.qa-m.sys{align-self:center;background:none;color:var(--muted);font-size:13px;text-align:center;padding:2px}#qa-send{display:flex;flex-direction:column;gap:8px}#qa-send textarea,#qa-send input{width:100%;box-sizing:border-box;background:var(--bg);color:var(--text);border:1px solid var(--line2);border-radius:12px;padding:11px 12px;font:15px Manrope,sans-serif;resize:vertical}#qa-send button{min-height:46px;border:0;border-radius:12px;background:var(--accent);color:#fff;font:700 15px Manrope,sans-serif;cursor:pointer}
.totop{position:fixed;right:18px;bottom:84px;z-index:49;width:46px;height:46px;border-radius:50%;border:1px solid var(--line2);background:var(--card);color:var(--text);display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 10px 26px -10px var(--sh);opacity:0;transform:translateY(10px) scale(.9);pointer-events:none;transition:opacity .2s ease,transform .2s ease}.totop.on{opacity:1;transform:none;pointer-events:auto}.totop:hover{border-color:var(--line-hi)}@media(max-width:600px){.totop{right:12px;bottom:78px}}
footer .wrap{display:block!important;padding-top:clamp(28px,4vw,44px);padding-bottom:22px}.f-top{display:grid;grid-template-columns:minmax(220px,1.2fr) 3fr;gap:clamp(24px,4vw,48px)}.f-brand .logo{font-size:18px}.f-brand p{margin:10px 0 0;color:var(--muted);font-size:14px;line-height:1.55;max-width:300px}.f-cols{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}.f-col b{display:block;color:var(--text);font-size:13px;letter-spacing:.04em;text-transform:uppercase;margin-bottom:10px}.f-col ul{list-style:none;margin:0;padding:0}.f-col li{margin:0 0 8px}.f-col a{color:var(--muted);font-size:14.5px}.f-col a:hover{color:var(--text-hi)}.f-bot{display:flex;justify-content:flex-start;column-gap:24px;gap:12px;flex-wrap:wrap;margin-top:28px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13.5px}.f-bot a{color:var(--muted)}@media(max-width:860px){.f-top{grid-template-columns:1fr}.f-cols{grid-template-columns:repeat(2,1fr);gap:22px 16px}}@media(max-width:600px){footer .wrap{padding-bottom:90px}}
.fr-band{display:flex;align-items:center;gap:16px;text-decoration:none;color:var(--text)}.fr-band>span{font-size:30px}.fr-band b{display:block;font-size:clamp(17px,1vw + 12px,20px)}.fr-band small{color:var(--soft);font-size:14.5px}.fr-band i{margin-left:auto;font-style:normal;font-size:22px;color:var(--accent2)}.fr-band:hover{border-color:var(--line-hi)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""

SHIELD = ('<svg width="44" height="44" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
          '<path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5l8-3z" stroke="#fff" stroke-width="1.8"/>'
          '<path d="M8.5 12l2.4 2.4L15.8 9.5" stroke="#fff" stroke-width="1.8" stroke-linecap="round" '
          'stroke-linejoin="round"/></svg>')
STAR = ('<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="#f5c542" '
        'd="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>')


THEME_ICONS = ('<svg class="su" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
               '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.2M12 19.8V22M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M2 12h2.2M19.8 12H22M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6"/></svg>'
               '<svg class="mo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7z"/></svg>')

# Тема: по умолчанию как в системе (день/ночь на телефоне), кнопка переключает вручную.
# Если вручную выбрали то же, что в системе, снова следуем системе.
THEME_JS = ("(function(){var d=document.documentElement,k='theme',m=matchMedia('(prefers-color-scheme: light)');"
            "try{var t=localStorage.getItem(k);if(t)d.setAttribute('data-theme',t)}catch(e){}"
            "function cur(){return d.getAttribute('data-theme')||(m.matches?'light':'dark')}"
            "function meta(){var c=cur()==='light'?'#f5f5fa':'#0a0b10';document.querySelectorAll('meta[name=theme-color]').forEach(function(x){x.setAttribute('content',c)})}"
            "meta();m.addEventListener&&m.addEventListener('change',meta);"
            "document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('#theme-t');if(!b)return;"
            "var n=cur()==='light'?'dark':'light',sys=m.matches?'light':'dark';"
            "try{if(n===sys){localStorage.removeItem(k);d.removeAttribute('data-theme')}else{localStorage.setItem(k,n);d.setAttribute('data-theme',n)}}"
            "catch(e){d.setAttribute('data-theme',n)}meta();"
            "try{window.goatcounter&&goatcounter.count&&goatcounter.count({path:'theme/'+n,title:'theme '+n,event:true})}catch(e){}})})();"
            "document.addEventListener('DOMContentLoaded',function(){var t=document.createElement('button');t.type='button';t.className='totop';"
            "t.setAttribute('aria-label',document.documentElement.lang==='en'?'Back to top':'Наверх');"
            "t.innerHTML='<svg width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 19V5M5 12l7-7 7 7\"/></svg>';"
            "document.body.appendChild(t);var q=document.getElementById('qa');"
            "function u(){var on=pageYOffset>innerHeight*1.2&&!(q&&q.classList.contains('open'));t.classList.toggle('on',on)}"
            "addEventListener('scroll',u,{passive:true});addEventListener('click',function(){setTimeout(u,0)});u();"
            "t.addEventListener('click',function(){scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})})});"
            "if('serviceWorker' in navigator)addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){})});")



PWA_PAGES = ["/", "/check/", "/podklyuchenie/", "/status/", "/en/", "/en/check/", "/en/podklyuchenie/", "/en/status/"]


def write_pwa():
    """Приложение на экран телефона: манифесты RU/EN и service worker с офлайн-копией главных страниц."""
    icons = [{"src": "/assets/app/icon-192.png", "sizes": "192x192", "type": "image/png"},
             {"src": "/assets/app/icon-512.png", "sizes": "512x512", "type": "image/png"},
             {"src": "/assets/app/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]
    for pre, lang, desc, sc in (("", "ru", "Проверка VPN, статус блокировок и инструкции", [
            ("Проверить VPN", "/check/"), ("Как подключить", "/podklyuchenie/"), ("Статус блокировок", "/status/")]),
            ("/en", "en", "VPN check, blocking status and setup guides", [
            ("Check VPN", "/en/check/"), ("Setup guide", "/en/podklyuchenie/"), ("Blocking status", "/en/status/")])):
        man = {"name": BRAND, "short_name": BRAND, "description": desc, "lang": lang,
               "id": f"{pre}/", "start_url": f"{pre}/?source=app", "scope": "/", "display": "standalone",
               "background_color": "#0a0b10", "theme_color": "#0a0b10", "icons": icons,
               "shortcuts": [{"name": n, "url": u} for n, u in sc]}
        write(f"{pre.strip('/') + '/' if pre else ''}manifest.webmanifest", json.dumps(man, ensure_ascii=False, indent=1))
    version = datetime.now(MSK).strftime("%Y%m%d%H%M")
    assets = ["/favicon.svg", "/assets/app/icon-192.png", "/assets/fonts/manrope-cyrillic-wght-normal.woff2",
              "/assets/fonts/manrope-latin-wght-normal.woff2"]
    arts = sorted("/" + str(p.parent.relative_to(ROOT)).replace("\\", "/") + "/"
                  for p in list((ROOT / "blog").glob("*/index.html")) + list((ROOT / "en" / "blog").glob("*/index.html")))
    sw = SW_JS.replace("__V__", version).replace("__PAGES__", json.dumps(PWA_PAGES + arts)).replace("__ASSETS__", json.dumps(assets))
    write("sw.js", sw)
    write("ping.txt", "ok\n")


SW_JS = r"""// ThuggerVPN: офлайн-копия главных страниц. Страницы: сначала сеть, без сети из кэша. Файлы: из кэша.
var V='tvpn-__V__',PAGES=__PAGES__,ASSETS=__ASSETS__;
self.addEventListener('install',function(e){e.waitUntil(caches.open(V).then(function(c){return c.addAll(PAGES.concat(ASSETS))}).then(function(){return self.skipWaiting()}))});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==V}).map(function(k){return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener('fetch',function(e){var r=e.request,u=new URL(r.url);
 if(r.method!=='GET'||u.origin!==location.origin)return;
 if(r.mode==='navigate'){e.respondWith(fetch(r).then(function(res){var cp=res.clone();caches.open(V).then(function(c){c.put(r,cp)});return res})
  .catch(function(){return caches.match(r,{ignoreSearch:true}).then(function(m){return m||caches.match(u.pathname.indexOf('/en/')===0?'/en/':'/')})}));return;}
 if(/\.(png|svg|woff2|ico|webp|jpg)$/.test(u.pathname)){e.respondWith(caches.match(r).then(function(m){return m||fetch(r).then(function(res){var cp=res.clone();caches.open(V).then(function(c){c.put(r,cp)});return res})}));}
});
"""


SHARE_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px"><path d="M12 3v12M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>'


def pwa_block(lang="ru"):
    en = lang == "en"
    t = ({"h": "ThuggerVPN app on your phone's home screen",
          "p": "An icon on your home screen, like a regular app. VPN check and setup guides in one tap, and the guides open even without internet.",
          "btn": "Add to home screen", "ios": ["If you opened the link from Telegram or another app, first tap the compass icon or “Open in Safari”.", "In Safari tap Share " + SHARE_ICON + " at the bottom of the screen.", "Scroll down, choose “Add to Home Screen” and tap Add. Done: the icon is on your screen."],
          "and": "In Chrome open the ⋮ menu and choose “Install app” or “Add to Home screen”.",
          "note": "If the site gets blocked, the app opens the saved guides and switches you to a working backup address by itself. The bot and support are always in Telegram.",
          "done": "Done: the ThuggerVPN icon is on your home screen."} if en else
         {"h": "Приложение ThuggerVPN на экране телефона",
          "p": "Иконка на рабочем столе, как у обычного приложения. Проверка VPN и инструкции в одно касание, а инструкции открываются даже без интернета.",
          "btn": "Установить на телефон", "ios": ["Если открыли ссылку из Telegram или другого приложения, сначала нажмите значок компаса или «Открыть в Safari».", "В Safari нажмите «Поделиться» " + SHARE_ICON + " внизу экрана.", "Пролистайте вниз, выберите «На экран Домой» и нажмите «Добавить». Готово: иконка на экране."],
          "and": "В Chrome откройте меню ⋮ и выберите «Установить приложение» или «Добавить на главный экран».",
          "note": "Если сайт заблокируют, приложение покажет сохранённые инструкции и само переключит на рабочий запасной адрес. Бот и поддержка всегда в Telegram.",
          "done": "Готово: иконка ThuggerVPN на экране телефона."})
    steps = "".join(f"<li>{x}</li>" for x in t["ios"])
    return (f'<section class="sec" id="app"><div class="trust2 pwa"><div class="pwa-row"><img src="/assets/app/icon-192.png" alt="" width="64" height="64">'
            f'<h2>{esc(t["h"])}</h2></div><p class="pwa-p">{esc(t["p"])}</p>'
            f'<button class="btn" type="button" id="pwa-btn">{esc(t["btn"])}</button>'
            f'<div id="pwa-ios" hidden><ol>{steps}</ol></div><p id="pwa-and" hidden>{esc(t["and"])}</p><p id="pwa-done" hidden><b>{esc(t["done"])}</b></p>'
            f'<p class="note">{esc(t["note"])}</p></div></section><script>{PWA_JS}</script>')


PWA_JS = ("(function(){var sec=document.getElementById('app');if(!sec)return;"
          "var st=matchMedia('(display-mode: standalone)').matches||navigator.standalone;if(st){sec.hidden=true;"
          "try{goatcounter.count({path:'app/open',title:'opened as app',event:true})}catch(e){}return;}"
          "var dp=null,b=document.getElementById('pwa-btn'),ios=/iphone|ipad|ipod/i.test(navigator.userAgent);"
          "addEventListener('beforeinstallprompt',function(e){e.preventDefault();dp=e;});"
          "addEventListener('appinstalled',function(){document.getElementById('pwa-done').hidden=false;b.hidden=true;"
          "try{goatcounter.count({path:'app/installed',title:'app installed',event:true})}catch(e){}});"
          "b.addEventListener('click',function(){try{goatcounter.count({path:'app/install-click',title:'install click',event:true})}catch(e){}"
          "if(dp){dp.prompt();dp.userChoice.then(function(){dp=null});return;}"
          "document.getElementById(ios?'pwa-ios':'pwa-and').hidden=false;});})();")


def failover_js():
    """Если текущий адрес сайта недоступен (страница открылась из офлайн-копии), ищем рабочий запасной адрес и переходим туда.
    Список адресов закодирован, чтобы не лежать открытым текстом."""
    import base64
    hosts = [SITE] + MIRRORS
    enc = base64.b64encode(json.dumps(hosts).encode()).decode()
    return ("(function(){try{var H=JSON.parse(atob('" + enc + "')),me=location.origin;"
            "if(sessionStorage.getItem('fo'))return;sessionStorage.setItem('fo','1');"
            "function img(h,ms){return new Promise(function(r){var i=new Image(),t=setTimeout(function(){i.src='';r(false)},ms);"
            "i.onload=function(){clearTimeout(t);r(true)};i.onerror=function(){clearTimeout(t);r(false)};i.src=h+'/favicon.svg?fo='+Date.now()})}"
            "function go(h){var en=document.documentElement.lang==='en',d=document.createElement('div');"
            "d.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:99;padding:16px 18px;border-radius:16px;background:#7c3aed;color:#fff;font:600 15px/1.45 Manrope,sans-serif;box-shadow:0 20px 40px -10px rgba(0,0,0,.5)';"
            "var u=h+location.pathname+location.search;d.innerHTML=(en?'The main address is unavailable right now. Switching to a working address… ':'Основной адрес сейчас недоступен. Переходим на рабочий адрес… ')+'<a style=\"color:#fff;text-decoration:underline\" href=\"'+u+'\">'+(en?'Go now':'Перейти')+'</a>';"
            "document.body.appendChild(d);try{goatcounter.count({path:'failover/'+h.split('//')[1],title:'failover',event:true})}catch(e){}"
            "setTimeout(function(){location.href=u},2500)}"
            "addEventListener('load',function(){setTimeout(function(){var c=new AbortController(),t=setTimeout(function(){c.abort()},6000);"
            "fetch('/ping.txt?'+Date.now(),{cache:'no-store',signal:c.signal}).then(function(r){clearTimeout(t);if(!r.ok)throw 0}).catch(function(){"
            "var o=H.filter(function(h){return h!==me});(function n(i){if(i>=o.length)return;img(o[i],5000).then(function(ok){ok?go(o[i]):n(i+1)})})(0)})},1200)})}catch(e){}})();")


def footer_cols(cols):
    out = []
    for title, links in cols:
        items = "".join(
            f'<li><a href="{u}"' + (' target="_blank" rel="noopener nofollow"' if u.startswith("http") else "") + f'>{esc(t)}</a></li>'
            for t, u in links)
        out.append(f'<div class="f-col"><b>{esc(title)}</b><ul>{items}</ul></div>')
    return '<div class="f-cols">' + "".join(out) + "</div>"

def price_line():
    s = f'{CFG["trial"]}, дальше {CFG["price"]}'
    if CFG.get("price_from"):
        s += f' ({CFG["price_from"]})'
    return s


def cta_block():
    return (f'<div class="cta"><div><b>VPN снова отвалился?</b>'
            f'<p>{CFG["trial"].capitalize()} - проверьте на своём операторе. Дальше от '
            f'{min([p["per_month"] for p in CFG.get("plans", [])] or [210])} ₽ в месяц.</p></div>'
            f'<div class="links"><a class="btn" href="{BOT}" rel="nofollow">'
            f'Попробовать {CFG["trial"]}</a>'
            f'<a class="small" href="{VPNSTATUS}" target="_blank" rel="noopener">'
            f'Отзывы клиентов на vpnstatus.site ↗</a></div></div>')


def trust_block():
    vp = SRC / "data" / "vpnstatus.json"
    d = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else None
    link = (d or {}).get("url", VPNSTATUS)
    if not d:
        return (f'<div class="trust"><div><h2>Честные отзывы - в независимом каталоге</h2></div>'
                f'<a class="btn-ghost" href="{link}" target="_blank" rel="noopener">Смотреть отзывы ↗</a></div>')

    def cell(w, t):
        return '<span class="na">нет голосов</span>' if t in (None, 0) else f'<b>{w}/{t}</b>'
    ops = "".join(f'<tr><td>{esc(o["name"])}</td><td>{cell(o["works"], o["total"])}</td>'
                  f'<td>{cell(o["wl_works"], o["wl_total"])}</td></tr>' for o in d["mobile"])
    revs = "".join(f'<div class="rv"><div class="stars sm">{STAR * 5}</div><p>{esc(r["text"])}</p>'
                   f'<small>Клиент · {esc(r["period"])}</small></div>' for r in d["reviews"][:3])
    return f"""<div class="trust2">
<div class="tr-head"><div><div class="stars">{STAR * 5}</div>
<h2>Отзывы клиентов - в независимом каталоге</h2>
<p>Голоса и отзывы оставляют сами пользователи на vpnstatus.site. Каталог не продаёт места в подборках. Ниже - кратко, полная карточка по ссылке.</p></div>
<a class="btn-ghost" href="{link}" target="_blank" rel="noopener">Все отзывы на vpnstatus.site ↗</a></div>
<div class="tr-grid">
<div class="tr-score"><div class="big">{esc(d["rating"])}<span>/5</span></div>
<div class="t-sub" style="margin-top:6px">{ocenok(d["votes"])} · {d["works_percent"]}% «работает» · {d["reviews_count"]} отзывов</div>
<div class="t-sub" style="margin-top:4px">Домашний интернет: {d["home_works"]}/{d["home_total"]} «работает»</div></div>
<div class="tbl" style="margin:0"><table class="tr-ops"><thead><tr><th>Мобильный</th><th>Работает</th><th>Обход белых списков</th></tr></thead><tbody>{ops}</tbody></table></div>
</div>
<div class="tr-revs">{revs}</div>
<p class="note" style="margin:14px 0 0">По данным vpnstatus.site на {ru_date(d["checked"])}. Отзывы пересказаны кратко. <a href="{link}" target="_blank" rel="noopener">Открыть полную карточку →</a></p>
</div>"""


def page(title, description, path, body, jsonld=None, og_type="website", lang="ru"):
    url = f"{SITE}{path}"
    suf = f" | {BRAND}"
    if title.endswith(suf) and len(title) > 64:
        title = title[:-len(suf)]
    en = lang == "en"
    rp = ru_path(path)
    if rp in EN_PAGES:
        sw = (f'<a class="lang" href="{rp}" hreflang="ru" lang="ru">RU</a>' if en
              else f'<a class="lang" href="/en{rp}" hreflang="en" lang="en">EN</a>')
    else:
        sw = (f'<a class="lang" href="/" hreflang="ru" lang="ru">RU</a>' if en
              else f'<a class="lang" href="/en/" hreflang="en" lang="en">EN</a>')
    pre = "/en" if en else ""
    alt_lang_href = (rp if rp in EN_PAGES else "/") if en else (f"/en{rp}" if rp in EN_PAGES else "/en/")
    alt_lang_label = "Русская версия" if en else "English version"
    if en:
        nav = (f'<a href="/en/check/">Check</a><a href="/en/#prices">Plans</a>'
               f'<a class="hide-xs" href="/en/podklyuchenie/">Setup</a><a class="btn-s" href="{BOT}" rel="nofollow">Try free</a>')
        foot_l = "Guides on stable internet access in Russia: blocking status, internet check, setup."
        foot_r = footer_cols([
            ("Service", [("Try 3 days free", BOT), ("Plans", "/en/#prices"), ("How to connect", "/en/podklyuchenie/"), ("Invite friends", "/en/priglasit/"), ("Support", SUPPORT)]),
            ("Tools", [("Internet check", "/en/check/"), ("Whitelist check", "/en/check/#wl"), ("Blocking status", "/en/status/"), ("Blocking index", "/en/index-blokirovok/")]),
            ("Carriers", [("MTS", "/en/operator/mts/"), ("Beeline", "/en/operator/beeline/"), ("MegaFon", "/en/operator/megafon/"), ("T2", "/en/operator/t2/")]),
            ("More", [("Articles", "/en/blog/"), ("Reviews", VPNSTATUS), ("Telegram channel", CHANNEL), ("Site widget", "/en/informer/")]),
        ])
        home_label, menu_label, locale = "home", "Main menu", "en_US"
        theme_label = "Light or dark theme"
    else:
        nav = (f'<a href="/check/">Проверка</a><a href="/#prices">Тарифы</a>'
               f'<a class="hide-xs" href="/podklyuchenie/">Инструкция</a><a class="btn-s" href="{BOT}" rel="nofollow">Попробовать</a>')
        foot_l = "Справочные материалы о стабильном доступе к интернету: статус блокировок, проверка, инструкции."
        foot_r = footer_cols([
            ("Сервис", [("Попробовать 3 дня", BOT), ("Тарифы", "/#prices"), ("Как подключить", "/podklyuchenie/"), ("Приведи друга", "/priglasit/"), ("Поддержка", SUPPORT)]),
            ("Инструменты", [("Проверка интернета", "/check/"), ("Белые списки", "/check/#wl"), ("Статус блокировок", "/status/"), ("Индекс блокировок", "/index-blokirovok/")]),
            ("Операторы", [("МТС", "/operator/mts/"), ("Билайн", "/operator/beeline/"), ("МегаФон", "/operator/megafon/"), ("Т2", "/operator/t2/")]),
            ("Ещё", [("Статьи", "/blog/"), ("Отзывы", VPNSTATUS), ("Telegram-канал", CHANNEL), ("Информер для сайта", "/informer/")]),
        ])
        home_label, menu_label, locale = "на главную", "Основное меню", "ru_RU"
        theme_label = "Светлая или тёмная тема"
    ld = ""
    for obj in jsonld or []:
        ld += f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>\n'
    return track_clicks(f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
{alt_links(path)}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="{pre}/manifest.webmanifest">
<link rel="apple-touch-icon" href="/assets/app/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{BRAND}"><meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="{SITE}{pre}/feed.xml">
<link rel="preload" href="/assets/fonts/manrope-{'latin' if en else 'cyrillic'}-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og2{'-en' if en else ''}.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="{locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0a0b10" media="(prefers-color-scheme: dark)"><meta name="theme-color" content="#f5f5fa" media="(prefers-color-scheme: light)">
<script>{THEME_JS}</script><script>{failover_js()}</script>
{CFG.get("head_extra", "")}
{f'<script data-goatcounter="https://{GC}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>' if GC else ""}
<style>{CSS}</style>
{ld}</head>
<body>
<header><div class="wrap"><span class="hl"><a class="logo" href="{pre}/" aria-label="{BRAND}, {home_label}"><i><b></b></i>{BRAND}</a>{sw}<button class="theme-t" type="button" id="theme-t" aria-label="{theme_label}" title="{theme_label}">{THEME_ICONS}</button></span>
<nav aria-label="{menu_label}">{nav}</nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><div class="f-top"><div class="f-brand"><a class="logo" href="{pre}/"><i><b></b></i>{BRAND}</a><p>{foot_l}</p></div>{foot_r}</div>
<div class="f-bot"><span>© {today_msk().year} {BRAND}</span><a href="{alt_lang_href}">{alt_lang_label}</a></div></div></footer>
{assistant_html(lang)}
</body>
</html>
""", path)


def track_clicks(doc, path):
    """Помечает клики по боту, поддержке и отзывам для счётчика GoatCounter (события «bot/…»)."""
    if not GC:
        return doc
    marks = [(BOT, "bot"), (SUPPORT, "support"), (CHANNEL, "channel")]
    for url, name in marks:
        if url:
            doc = doc.replace(f'href="{url}"', f'href="{url}" data-goatcounter-click="{name}{path}"')
    doc = re.sub(r'href="(https://vpnstatus\.site[^"]*)"', lambda m: f'{m.group(0)} data-goatcounter-click="reviews{path}"', doc)
    return doc


def assistant_html(lang="ru"):
    en = lang == "en"
    ap = SRC / ("assistant_en.json" if en else "assistant.json")
    if not ap.exists():
        return ""
    data = json.loads(ap.read_text(encoding="utf-8"))
    subs = {"{BOT}": BOT, "{PRICE}": CFG["price"], "{PRICE_FROM}": CFG.get("price_from", ""),
            "{TRIAL}": CFG["trial"], "{WL}": (CFG["en"]["whitelist_detail"] if en else
                                                 CFG.get("whitelist_option", "").split(":")[-1].strip()), "{VPNSTATUS}": VPNSTATUS, "{SUPPORT}": SUPPORT}

    def sub(t):
        for k, v in subs.items():
            t = t.replace(k, v)
        return t
    intents = [{"id": i["id"], "chip": i["chip"], "keys": i["keys"], "answer": sub(i["answer"]),
                "link": sub(i["link"]), "link_text": i["link_text"]} for i in data["intents"]]
    L = ({"qa": "Quick answer", "close": "Close", "describe": "Describe the problem", "ph": "e.g. VPN connected but nothing loads",
          "go": "Answer", "hint": "Quick answers are prepared in advance and shown instantly. What you type in the search box isn't sent anywhere.",
          "sup": "Message support →", "help": "Help", "call": "Ask a person", "msg_ph": "What doesn't work: device, carrier, what you already tried",
          "contact_ph": "Your Telegram for the reply (optional)", "send": "Send",
          "chat_hint": "A real person answers. The reply will appear here, even if you close the site and come back later. Don't send passwords or card details.",
          "sent": "Sent to a person. The reply will appear here.", "err": "Didn't send. Message us in Telegram:", "you": "You", "op": "ThuggerVPN"} if en else
         {"qa": "Быстрый ответ", "close": "Закрыть", "describe": "Опишите проблему", "ph": "Например: VPN подключён, но не грузит",
          "go": "Ответ", "hint": "Быстрые ответы готовы заранее и показываются сразу. Что вы вводите в поиск, никуда не отправляется.",
          "sup": "Написать в поддержку →", "help": "Помощь", "call": "Позвать человека", "msg_ph": "Что не работает: устройство, оператор, что уже пробовали",
          "contact_ph": "Ваш Telegram для ответа (необязательно)", "send": "Отправить",
          "chat_hint": "Отвечает живой человек. Ответ появится здесь, даже если закроете сайт и вернётесь позже. Не пишите пароли и данные карт.",
          "sent": "Передали человеку. Ответ появится здесь.", "err": "Не отправилось. Напишите нам в Telegram:", "you": "Вы", "op": "ThuggerVPN"})
    payload = json.dumps({"intents": intents, "fallback": data["fallback"], "support": SUPPORT, "sup_label": L["sup"],
                          "chat": CFG.get("chat_url", ""), "L": {k: L[k] for k in ("sent", "err", "you", "op")}},
                         ensure_ascii=False).replace("</", "<\\/")
    chips = "".join(f'<button type="button" data-id="{esc(i["id"])}">{esc(i["chip"])}</button>'
                    for i in intents[:8])
    return f"""<button class="qa-fab" type="button" aria-expanded="false" aria-controls="qa" id="qa-fab">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 5h16v11H8l-4 4V5z" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></svg><span>{L['help']}</span><i class="qa-dot" aria-hidden="true"></i></button>
<div class="qa" id="qa" role="dialog" aria-modal="false" aria-labelledby="qa-title">
<div class="qa-head"><b id="qa-title">{L['help']}</b><button class="qa-x" type="button" aria-label="{L['close']}" id="qa-x">×</button></div>
<div class="qa-body">
<form class="qa-form" id="qa-form"><label for="qa-in">{L['describe']}</label>
<input id="qa-in" type="text" autocomplete="off" placeholder="{L['ph']}">
<button type="submit">{L['go']}</button></form>
<div class="qa-ans" id="qa-ans" aria-live="polite"></div>
<div class="qa-chips" id="qa-chips">{chips}</div>
<p class="qa-hint">{L['hint']}</p>
<div class="qa-human"><button type="button" class="qa-call" id="qa-call">👤 {L['call']}</button>
<div id="qa-chat" hidden><div class="qa-thread" id="qa-thread" aria-live="polite"></div>
<form id="qa-send"><textarea id="qa-msg" rows="3" maxlength="1500" placeholder="{L['msg_ph']}"></textarea>
<input id="qa-contact" type="text" maxlength="100" autocomplete="off" placeholder="{L['contact_ph']}">
<input id="qa-hp" type="text" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px">
<button type="submit">{L['send']}</button></form>
<p class="qa-hint">{L['chat_hint']}</p></div></div>
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
if(!it||it.link!==D.support){{var b=document.createElement('a');b.href=D.support;b.target='_blank';b.rel='noopener nofollow';b.textContent=D.sup_label;ans.appendChild(b);}}}}
document.getElementById('qa-form').addEventListener('submit',function(e){{e.preventDefault();
var q=norm(inp.value);if(!q.trim())return;var best=null,bs=0;
D.intents.forEach(function(it){{var s=score(q,it);if(s>bs){{bs=s;best=it;}}}});show(bs>=3?best:null);}});
chips.addEventListener('click',function(e){{var id=e.target.getAttribute('data-id');if(!id)return;
for(var i=0;i<D.intents.length;i++)if(D.intents[i].id===id){{inp.value=D.intents[i].chip;show(D.intents[i]);}}}});
var CU=D.chat,call=document.getElementById('qa-call'),chat=document.getElementById('qa-chat'),th=document.getElementById('qa-thread');
function ls(k,v){{try{{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}}catch(e){{}}}}
var sid=ls('tvpn_sid');if(!sid){{sid=Math.random().toString(36).slice(2)+Date.now().toString(36);ls('tvpn_sid',sid);}}
var T=[];try{{T=JSON.parse(ls('tvpn_thread')||'[]')}}catch(e){{}}var last=Number(ls('tvpn_last')||0);
function save(){{ls('tvpn_thread',JSON.stringify(T.slice(-60)));ls('tvpn_last',String(last));}}
function render(){{th.textContent='';T.forEach(function(m){{var d=document.createElement('div');d.className='qa-m '+m.f;
 if(m.f!=='sys'){{var b=document.createElement('b');b.textContent=m.f==='me'?D.L.you:D.L.op;d.appendChild(b);}}
 var p=document.createElement('span');p.textContent=m.t;d.appendChild(p);th.appendChild(d);}});th.scrollTop=th.scrollHeight;}}
function openChat(){{chat.hidden=false;call.hidden=true;render();pull();setTimeout(function(){{document.getElementById('qa-msg').focus()}},30);}}
call.addEventListener('click',function(){{if(!CU){{window.open(D.support,'_blank','noopener');return;}}openChat();
 try{{goatcounter.count({{path:'chat/open',title:'chat open',event:true}})}}catch(e){{}}}});
document.getElementById('qa-send').addEventListener('submit',function(e){{e.preventDefault();var ta=document.getElementById('qa-msg'),txt=ta.value.trim();if(!txt)return;
 var body={{sid:sid,text:txt,contact:document.getElementById('qa-contact').value,page:location.pathname,hp:document.getElementById('qa-hp').value}};
 T.push({{f:'me',t:txt}});ta.value='';render();save();
 fetch(CU,{{method:'POST',headers:{{'Content-Type':'text/plain;charset=utf-8'}},body:JSON.stringify(body)}}).then(function(r){{return r.json()}}).then(function(j){{
  if(!j.ok)throw 0;if(!T.some(function(m){{return m.f==='sys'}}))T.push({{f:'sys',t:D.L.sent}});render();save();
  try{{goatcounter.count({{path:'chat/sent',title:'chat message',event:true}})}}catch(e){{}}
 }}).catch(function(){{T.push({{f:'sys',t:D.L.err+' '+D.support.replace('https://t.me/','@')}});render();save();}});}});
function pull(){{if(!CU||!T.some(function(m){{return m.f==='me'}}))return;
 fetch(CU+'?u='+encodeURIComponent(sid)+'&since='+last).then(function(r){{return r.json()}}).then(function(j){{
  if(!j.ok||!j.msgs||!j.msgs.length)return;j.msgs.forEach(function(m){{T.push({{f:'op',t:m.text}});last=Math.max(last,m.ts);}});save();render();
  if(!box.classList.contains('open'))fab.classList.add('has-new');}}).catch(function(){{}});}}
fab.addEventListener('click',function(){{fab.classList.remove('has-new');if(T.length&&CU)openChat();}});
if(CU&&T.length){{pull();setInterval(function(){{pull()}},box.classList.contains('open')?8000:45000);}}
setInterval(function(){{if(box.classList.contains('open')&&!chat.hidden)pull();}},8000);
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
        "image": f"{SITE}/og2.png",
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


def humanize(text):
    """Никаких длинных тире в публичных текстах: они выдают автоматический текст."""
    text = text.replace(" \u2014 ", " - ").replace(" \u2013 ", " - ")
    text = re.sub(r"(\d)[\u2013\u2014](\d)", r"\1-\2", text)
    return text.replace("\u2014", "-").replace("\u2013", "-")


def write(rel, content):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = humanize(content)
    out.write_text(content, encoding="utf-8")


def related_html(a, posts):
    rel = [p for p in posts if p["slug"] != a["slug"]][:3]
    if not rel:
        return ""
    items = "".join(f'<li><a href="/blog/{p["slug"]}/"><b>{esc(p["title"])}</b>'
                    f'<span>{esc(p["description"])}</span></a></li>' for p in rel)
    return (f'<h2>Читайте также</h2><ul class="list">{items}'
            f'<li><a href="/check/"><b>Проверить свой интернет за 5 секунд</b>'
            f'<span>Белые списки, отключение или не работает VPN - узнайте сразу</span></a></li></ul>')


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
            lines.append(f"• <b>{html.escape(e['region'])}:</b> {html.escape(e['title'])}")
            lines.append(f"  → {html.escape(e['meaning'])}")
    else:
        lines.append("За сутки новых крупных сбоев в открытых источниках не найдено.")
    lines += ["", f'Проверить свой интернет за 5 секунд: {SITE}/check/',
              f'Полная сводка: {SITE}/status/']
    return "\n".join(lines)




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
.ck-out p{margin:0 0 12px;color:var(--violet-text)}
.ck-out .row a{font-weight:700}
.bars{display:grid;gap:10px;margin:16px 0}
.bar{display:grid;grid-template-columns:minmax(150px,240px) 1fr 40px;gap:12px;align-items:center;font-size:15px}
.bar i{display:block;height:14px;border-radius:7px;min-width:4px}
.bar b{text-align:right}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chips a{padding:10px 16px;border-radius:999px;background:var(--card2);border:1px solid var(--line);text-decoration:none;color:var(--text);font-weight:700;min-height:44px;display:inline-flex;align-items:center}
.chips a:hover{border-color:var(--line-hi)}
.codebox{width:100%;min-height:110px;background:var(--card2);color:var(--text);border:1px solid var(--line2);border-radius:12px;padding:12px;font:13px/1.5 ui-monospace,Menlo,monospace}
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


SETUP_CSS = """<style>
.dev-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}
.dev-tabs button{font:700 15px Manrope,sans-serif;background:var(--card2);color:var(--soft);border:1px solid var(--line2);border-radius:999px;padding:11px 16px;cursor:pointer;min-height:44px}
.dev-tabs button[aria-selected=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.dev-panel{padding:22px;border-radius:20px;background:var(--card);border:1px solid var(--line)}
.app-rec{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px;padding:18px;border-radius:16px;background:var(--violet-bg);border:1px solid var(--violet-line)}
.app-rec b{font-size:19px}.app-rec small{display:block;color:var(--violet-text);font-size:14px;margin-top:2px}
.app-alt{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.app-alt a{padding:9px 13px;border-radius:12px;background:var(--card2);border:1px solid var(--line);text-decoration:none;color:var(--text);font-size:14px;font-weight:600;min-height:40px;display:inline-flex;align-items:center}
.app-alt a:hover{border-color:var(--line-hi)}
.st4{counter-reset:s;display:grid;gap:12px;margin:18px 0}
.st4>div{display:grid;grid-template-columns:52px 1fr;gap:16px;padding:20px;border-radius:var(--r-lg);background:var(--card);border:1px solid var(--line)}
.st4 .n{width:52px;height:52px;border-radius:14px;background:var(--accent);color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center}
.st4 h3{margin:2px 0 6px;font-size:19px}.st4 p{margin:0;color:var(--soft)}
.kbd{display:inline-block;padding:2px 8px;border-radius:8px;background:var(--card2);border:1px solid var(--line2);font-weight:700;font-size:15px;color:var(--text-hi);white-space:nowrap}
.done{padding:16px 20px;border-radius:16px;background:rgba(163,230,53,.08);border:1px solid rgba(163,230,53,.35);font-weight:700}
</style>"""


SETUP_SCRIPT = """<script>(function(){var tabs=[].slice.call(document.querySelectorAll('.dev-tabs [role=tab]')),
panels=[].slice.call(document.querySelectorAll('[data-panel]'));
function sel(id){tabs.forEach(function(t){t.setAttribute('aria-selected',t.dataset.dev===id?'true':'false')});
panels.forEach(function(p){p.hidden=p.dataset.panel!==id});}
tabs.forEach(function(t){t.addEventListener('click',function(){sel(t.dataset.dev);history.replaceState(null,'','#'+t.dataset.dev)})});
var ua=navigator.userAgent,h=location.hash.slice(1),ids=tabs.map(function(t){return t.dataset.dev});
var d=ids.indexOf(h)>=0?h:/iPhone|iPad|iPod/.test(ua)?'ios':/Android/.test(ua)?(/TV|AFT/.test(ua)?'tv':'android'):/Mac/.test(ua)?'mac':/Win/.test(ua)?'windows':'ios';
sel(d);})();</script>"""


def write_feed(rel, title, home, lang, posts, prefix, ST):
    """RSS 2.0: статьи + страница статуса (обновляется каждый день)."""
    from email.utils import format_datetime
    def rfc(iso):
        return format_datetime(datetime.fromisoformat(iso + "T09:00:00").replace(tzinfo=MSK))
    st_url = f"{home}status/"
    st_title = ("Статус блокировок · " if lang == "ru" else "Blocking status · ") + ST["updated"]
    items = [f"<item><title>{esc(st_title)}</title><link>{st_url}</link><guid isPermaLink=\"false\">{st_url}#{ST['updated']}</guid>"
             f"<pubDate>{rfc(ST['updated'])}</pubDate></item>"]
    for a in posts[:30]:
        u = f"{SITE}{prefix}{a['slug']}/"
        items.append(f"<item><title>{esc(a['title'])}</title><link>{u}</link><guid>{u}</guid>"
                     f"<description>{esc(a['description'])}</description><pubDate>{rfc(a['date'])}</pubDate></item>")
    write(rel, '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
          f"<title>{esc(title)}</title><link>{home}</link><description>{esc(title)}</description><language>{lang}</language>"
          f'<atom:link href="{SITE}/{rel}" rel="self" type="application/rss+xml"/>' + "".join(items) + "</channel></rss>\n")


def read_embed_template():
    return ("""<!DOCTYPE html><html lang="{{LANG}}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{{TITLE}} - """ + BRAND + """</title><style>
@font-face{font-family:Manrope;font-weight:200 800;src:url(/assets/fonts/manrope-cyrillic-wght-normal.woff2) format('woff2');unicode-range:U+0400-045F}
@font-face{font-family:Manrope;font-weight:200 800;src:url(/assets/fonts/manrope-latin-wght-normal.woff2) format('woff2');unicode-range:U+0000-00FF,U+2000-206F}
body{margin:0;background:#12131b;color:#edeff5;font:15px/1.5 Manrope,system-ui,sans-serif}
.w{padding:16px;border:1px solid #1f2230;border-radius:16px;height:100%;box-sizing:border-box}
h1{font-size:16px;margin:0 0 10px;display:flex;justify-content:space-between;gap:8px}
h1 span{font-size:12px;color:#0a0b10;background:#a3e635;border-radius:6px;padding:2px 7px;align-self:center}
ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}li{padding:10px 12px;border-radius:12px;background:#191b27}
li small{display:block;color:#9aa2b3;font-size:12px}li b{font-size:14px;font-weight:600}
a{display:block;margin-top:10px;color:#c4b5fd;font-weight:700;text-decoration:none;font-size:14px}
</style></head><body><div class="w"><h1>{{TITLE}} <span>{{DATE}}</span></h1><ul>{{ROWS}}</ul>
<a href="{{LINK}}" target="_blank" rel="noopener">{{LINKTEXT}}</a></div></body></html>""")


def build_setup_page(urls, UPD):
    data = json.loads((SRC / "data" / "apps.json").read_text(encoding="utf-8"))
    bot_name = BOT_NAME
    tabs, panels = "", ""
    for i, d in enumerate(data["devices"]):
        rec = d["apps"][0]
        alts = "".join(f'<a href="{esc(a["url"])}" target="_blank" rel="noopener nofollow">{esc(a["app"])} · {esc(a["label"])}</a>'
                       for a in d["apps"][1:])
        tabs += (f'<button type="button" role="tab" id="tab-{d["id"]}" aria-controls="p-{d["id"]}" '
                 f'aria-selected="{"true" if i == 0 else "false"}" data-dev="{d["id"]}">{esc(d["name"])}</button>')
        panels += (f'<div class="dev-panel" role="tabpanel" id="p-{d["id"]}" aria-labelledby="tab-{d["id"]}" data-panel="{d["id"]}">'
                   f'<h3 style="margin:0 0 12px">{esc(d["name"])}</h3>'
                   f'<div class="app-rec"><div><b>{esc(rec["app"])}</b><small>Рекомендуем · {esc(rec["label"])}</small></div>'
                   f'<a class="btn" href="{esc(rec["url"])}" target="_blank" rel="noopener nofollow">Скачать {esc(rec["app"])}</a></div>'
                   + (f'<p class="note" style="margin:14px 0 0">Не открывается магазин или нужно другое приложение:</p>'
                      f'<div class="app-alt">{alts}</div>' if alts else "")
                   + ('<p class="note" style="margin:14px 0 0"><b>Российский Apple ID?</b> Incy, HAPP и V2RayTun удалены из российского '
                      'App Store - ссылки откроются, но скачать с российского аккаунта не получится. Если приложение уже установлено, оно '
                      'продолжит работать. Для новой установки нужен Apple ID другой страны - '
                      '<a href="#apple-id">как это сделать</a>.</p>'
                      if d["id"] in ("ios", "mac") else "") + '</div>')
    troubles = [
        ("Подписка активна?", f"Откройте {bot_name} → кнопка <span class='kbd'>🌍 Мой VPN</span> → посмотрите строку <span class='kbd'>📆 Оплачен до</span>. Если срок закончился - продлите подписку в боте."),
        ("В подписке есть локации?", f"В {bot_name} → <span class='kbd'>🌍 Мой VPN</span> проверьте строку <span class='kbd'>🌎 Локации в подписке</span>. Если там пусто - нажмите <span class='kbd'>🔄 Обновить подписку</span>."),
        ("Обновите ключи", f"В {bot_name} → <span class='kbd'>🌍 Мой VPN</span> → <span class='kbd'>🔄 Обновить подписку</span> и следуйте подсказкам в боте. Затем снова вставьте ссылку в приложение."),
        ("Возможно, это белые списки", "Операторы могут временно ограничивать мобильный интернет: работают только разрешённые сайты - Госуслуги, банки, крупные российские сервисы. Если VPN не подключается или страницы не грузятся - подключитесь к Wi-Fi. Проверить, что у вас, можно за 5 секунд на странице проверки."),
    ]
    tr_html = "".join(f'<details class="acc-q"><summary>{i + 1}. {esc(q)}</summary><p>{a}</p></details>'
                      for i, (q, a) in enumerate(troubles))
    path = "/podklyuchenie/"
    crumbs = [("Главная", "/"), ("Как подключить", path)]
    title = "Как подключить ThuggerVPN: iPhone, Android, Windows, Mac, ТВ"
    faq = [
        ("Какое приложение выбрать?", "Рекомендуем Incy - оно есть для iPhone, Android, Windows, macOS и телевизоров. "
         "Если не получается установить, подойдут HAPP или V2RayTun: ссылка подписки работает в любом из них."),
        ("Где взять ссылку подписки?", f"В Telegram-боте {bot_name}. Нажмите на ссылку один раз - она скопируется автоматически."),
        ("Сколько устройств можно подключить?", CFG.get("devices", "")),
        ("Как скачать приложение на iPhone с российским Apple ID?", "Incy, HAPP и V2RayTun удалены из российского App Store. "
         "Если приложение уже стоит - не удаляйте его. Если нет - нужен Apple ID другой страны: в App Store выйдите только из "
         "«Медиаматериалы и покупки», войдите в другой аккаунт, скачайте приложение и вернитесь в свой."),
        ("VPN не работает - что делать?", "Проверьте, что подписка активна и в ней есть локации, обновите подписку в боте. "
         "Если открываются только российские сайты - это белые списки, подключитесь к Wi-Fi. Не помогло - напишите в поддержку."),
    ]
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq if a)
    script = SETUP_SCRIPT
    body = (f'{SETUP_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}<h1>{esc(title)}</h1>'
            f'<p class="lead"><b>Коротко:</b> 4 шага и 2 минуты. Скачайте приложение, возьмите ссылку подписки в боте, '
            f'вставьте её в приложение и нажмите «Подключиться».</p>'
            f'<div class="st4">'
            f'<div><div class="n">1</div><div><h3>Скачайте приложение</h3><p>Выберите своё устройство - мы определили его автоматически.</p></div></div></div>'
            f'<div class="dev-tabs" role="tablist" aria-label="Устройство">{tabs}</div>{panels}'
            f'<div class="st4">'
            f'<div><div class="n">2</div><div><h3>Скопируйте ссылку подписки</h3><p>Откройте <a href="{BOT}" rel="nofollow">{bot_name}</a> '
            f'и получите персональную ссылку. Нажмите на неё один раз - она скопируется автоматически. '
            f'Ещё нет подписки? Возьмите {CFG["trial"]}.</p></div></div>'
            f'<div><div class="n">3</div><div><h3>Вставьте ссылку в приложение</h3><p>Откройте скачанное приложение и нажмите '
            f'<span class="kbd">Из буфера</span>.</p></div></div>'
            f'<div><div class="n">4</div><div><h3>Подключитесь</h3><p>Появится список серверов. Выберите локацию и нажмите '
            f'<span class="kbd">Подключиться</span>.</p></div></div></div>'
            f'<div class="done">✓ Готово - интернет работает через {esc(BRAND)}.</div>'
            f'<p style="margin:18px 0"><a class="btn" href="{BOT}" rel="nofollow">Получить ссылку в боте</a></p>'
f'<h2 id="apple-id">iPhone с российским Apple ID</h2>'
            f'<p>Apple удалила Incy, HAPP и V2RayTun из российского App Store. Других способов поставить приложение на iPhone в России нет: '
            f'установка в обход App Store разрешена только в Евросоюзе. Что делать - зависит от ситуации:</p>'
            f'<details class="acc-q" open><summary>Приложение уже установлено</summary><p>Не удаляйте его - оно продолжит работать. '
            f'Просто обновите подписку: {bot_name} → <span class="kbd">🌍 Мой VPN</span> → <span class="kbd">🔄 Обновить подписку</span>, '
            f'затем снова вставьте ссылку в приложение.</p></details>'
            f'<details class="acc-q"><summary>Приложения нет: Apple ID другой страны</summary><p>'
            f'1. Откройте App Store → нажмите на свой аватар → выйдите только из «Медиаматериалы и покупки». iCloud не трогайте - фото и контакты останутся.<br>'
            f'2. Создайте новый Apple ID другой страны (например, Казахстан, Турция, США) или войдите в уже существующий.<br>'
            f'3. Скачайте Incy (или HAPP, V2RayTun).<br>'
            f'4. Выйдите и вернитесь в свой Apple ID - приложение останется на телефоне.<br>'
            f'<b>Важно:</b> Apple просит адрес в выбранной стране, а обновлять приложение потом нужно будет под тем же аккаунтом.</p></details>'
            f'<details class="acc-q"><summary>Apple ID знакомого за границей</summary><p>Можно скачать приложение под аккаунтом человека, '
            f'которому вы доверяете: так же войдите только в «Медиаматериалы и покупки», скачайте приложение и выйдите. '
            f'Пароль от чужого аккаунта не сохраняйте и не входите им в iCloud.</p></details>'
            f'<p>Подписка из бота подходит к любому из трёх приложений - ставьте то, что получилось скачать. Застряли на каком-то шаге? '
            f'<a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Напишите в поддержку</a> - подскажем.</p>'
            f'<h2>Если VPN не работает</h2>{tr_html}'
            f'<p>Не помогло? <a href="{SUPPORT}" target="_blank" rel="noopener nofollow">Напишите в поддержку</a> или '
            f'<a href="/check/">проверьте свой интернет за 5 секунд</a>.</p>'
            f'<div style="margin:36px 0">' + __import__('video_block').block('ru', wrap=False) + '</div>'
            f'<h2>Вопросы и ответы</h2>{faq_html}{cta_block()}</article>{script}')
    meta = {"title": title, "description": "Пошаговая инструкция: приложения Incy, HAPP, V2RayTun для iPhone, Android, Windows, macOS и ТВ, ссылка подписки из бота, что делать, если VPN не работает.",
            "date": "2026-11-19", "updated": UPD, "faq": faq}
    howto = {"@context": "https://schema.org", "@type": "HowTo", "name": title, "totalTime": "PT2M",
             "step": [{"@type": "HowToStep", "position": i + 1, "name": n, "text": t} for i, (n, t) in enumerate([
                 ("Скачайте приложение", "Установите Incy (или HAPP, V2RayTun) для своего устройства."),
                 ("Скопируйте ссылку подписки", f"Получите персональную ссылку в Telegram-боте {bot_name}."),
                 ("Вставьте ссылку в приложение", "Откройте приложение и нажмите «Из буфера»."),
                 ("Подключитесь", "Выберите локацию и нажмите «Подключиться»."),
             ])]}
    write("podklyuchenie/index.html", page(f"{title} | {BRAND}", meta["description"], path, body,
                                           article_jsonld(meta, path, crumbs) + [howto]))
    urls.append((path, UPD))


def main():
    arts = [parse(p) for p in sorted((SRC / "articles").glob("*.md"))]
    status = next((a for a in arts if a["slug"] == "status"), None)
    posts = sorted([a for a in arts if a["slug"] != "status"],
                   key=lambda a: (a["date"], a["slug"]), reverse=True)
    ST = load_status()
    UPD = ST["updated"]

    for d in ("blog", "status", "check", "podklyuchenie", "priglasit", "operator", "index-blokirovok", "embed", "informer", "data", "en"):
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
              page(f'{a["title"]} | {BRAND}', a["description"], path, body,
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
              page(f'{status["title"]} | {BRAND}', status["description"], path, body,
                   article_jsonld(status, path, crumbs)))
        urls.append((path, UPD))

    # --- проверка ---
    path = "/check/"
    crumbs = [("Главная", "/"), ("Проверка интернета", path)]
    check_faq = [
        ("Как работает проверка?", "Страница пробует загрузить маленькие значки с сайтов: российских, обычных "
         "зарубежных и заблокированных в России. По тому, что открылось, а что нет, видно, что у вас: белые списки, "
         "полное отключение, не работает VPN или блокируют только часть сервисов."),
        ("Как проверить белые списки?", "Откройте вкладку «Белые списки», выключите VPN и Wi-Fi, оставьте мобильный "
         "интернет и нажмите кнопку. Если открываются только Яндекс, VK, Mail.ru и Авито, а Google и Википедия нет, "
         "значит, белые списки включены."),
        ("Почему результат иногда разный?", "Блокировки работают неравномерно, а мобильная сеть бывает нестабильной. Поэтому каждый сервис проверяется до 3 раз подряд, и итог учитывает все попытки. «С перебоями» значит, что сервис открылся не с первого раза."),
        ("Вы сохраняете мои данные?", "Нет. Проверка идёт целиком в вашем браузере, на наш сервер ничего не отправляется."),
        ("Насколько точен результат?", "Это быстрая приблизительная проверка. Если результат кажется странным - "
         "запустите её ещё раз или сравните мобильный интернет и Wi-Fi."),
    ]
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in check_faq)
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Что с моим интернетом? Проверка за 5 секунд</h1>'
            f'<p class="lead"><b>Коротко:</b> две проверки в одном месте. «Сайты и VPN» покажет, открываются ли '
            f'Telegram, WhatsApp, YouTube, Instagram и другие сервисы, которые блокируют в России. «Белые списки» '
            f'покажет, ограничили ли ваш мобильный интернет. Результат и что делать, за 5-10 секунд.</p>'
            + checker.widget('ru', BOT, BRAND, CFG['trial'], SUPPORT) +
            f'<h2>Как читать результат</h2><div class="tbl"><table><thead><tr><th>Что видите</th><th>Что это</th><th>Что делать</th></tr></thead><tbody>'
            f'<tr><td>Ничего не открывается</td><td>Интернет отключён или нет сигнала</td><td>Wi-Fi или домашний интернет</td></tr>'
            f'<tr><td>Открывается только российский сервис</td><td>Белые списки</td><td>Wi-Fi или VPN с обходом белых списков</td></tr>'
            f'<tr><td>Открываются Яндекс и Google, но не Telegram, WhatsApp, Instagram</td><td>VPN выключен или заблокирован</td><td>Включить VPN, сменить сервер</td></tr>'
            f'<tr><td>Открывается большинство, но 1-2 сервиса нет</td><td>Сервер VPN частично блокируют</td><td>Сменить сервер в приложении</td></tr>'
            f'<tr><td>Открывается всё</td><td>VPN работает</td><td>Ничего не нужно</td></tr>'
            f'<tr><td>«Белые списки»: открываются только Яндекс, VK, Авито</td><td>Белые списки на мобильном</td><td>Wi-Fi или VPN с обходом белых списков</td></tr>'
            f'</tbody></table></div>'
            f'<h2>Вопросы и ответы</h2>{faq_html}{cta_block()}</article>')
    check_meta = {"title": "Что с моим интернетом? Проверка за 5 секунд",
                  "description": "Бесплатная проверка: белые списки, отключение мобильного интернета или не работает VPN. В браузере, без сохранения данных.",
                  "date": "2026-11-19", "updated": UPD, "faq": check_faq}
    write("check/index.html", page(f'{check_meta["title"]} | {BRAND}', check_meta["description"], path, body,
                                   article_jsonld(check_meta, path, crumbs)))
    urls.append((path, UPD))

    build_setup_page(urls, UPD)
    import friends
    friends.page('ru', urls, UPD)

    # --- страницы операторов ---
    for slug, (name, name_loc) in OPS.items():
        path = f"/operator/{slug}/"
        title = f"Не работает VPN на {name_loc}: статус на {ru_date(UPD, year=False)} и что делать"
        evs = [e for e in recent(ST["events"], UPD, 14)
               if "all" in e["operators"] or slug in e["operators"]]
        own = [e for e in evs if slug in e["operators"]]
        crumbs = [("Главная", "/"), ("Статус", "/status/"), (name, path)]
        summary = (f"За последние 14 дней - событий, которые касаются абонентов {name}: {len(evs)}"
                   + (f", из них отдельно по {name}: {len(own)}." if own else
                      f". Отдельных сообщений именно по {name} нет - ниже общие ограничения для всех операторов в регионах."))
        faq = [
            (f"Почему VPN не работает на {name_loc}, а на Wi-Fi работает?",
             "Ограничения с белыми списками и отключения вводятся на мобильном интернете. Домашний интернет и Wi-Fi "
             "под них не попадают, поэтому там тот же VPN продолжает работать."),
            (f"Работает ли {BRAND} на {name_loc}?",
             f"Голоса пользователей по {name} - работает ли сервис и обходит ли белые списки - смотрите в независимом "
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
                f'<li><b>Включите и выключите авиарежим</b> - телефон заново зарегистрируется в сети.</li>'
                f'<li><b>Смените сервер в VPN</b> - блокируют конкретные адреса, а не весь сервис.</li>'
                f'<li><b>Обновите подписку или конфигурацию</b> в приложении.</li>'
                f'<li><b>Проверьте на Wi-Fi.</b> Если там работает - это ограничения на мобильной сети.</li>'
                f'<li><b>Открываются только Госуслуги и Яндекс?</b> Это белые списки: нужен Wi-Fi или VPN с обходом белых списков.</li></ol>'
                f'<p>Голоса пользователей {esc(BRAND)} по {esc(name)}: '
                f'<a href="{VPNSTATUS}" target="_blank" rel="noopener">vpnstatus.site ↗</a></p>'
                f'<h2>Вопросы и ответы</h2>{faq_html}<p>Другие операторы: {others}</p>{cta_block()}</article>')
        meta = {"title": title, "description": f"Статус VPN и мобильного интернета на {name_loc}: сбои и белые списки за 14 дней, что делать по шагам. Обновляется каждый день.",
                "date": "2026-11-19", "updated": UPD, "faq": faq}
        write(f"operator/{slug}/index.html", page(f"{title} | {BRAND}", meta["description"], path, body,
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
    reg_html = "".join(f"<li>{esc(r)} - {n}</li>" for r, n in top_regions)
    crumbs = [("Главная", "/"), ("Индекс блокировок", path)]
    idx_faq = [("Откуда данные?", "Из открытых источников: сообщения СМИ и профильных изданий о сбоях, отключениях, "
                "белых списках и блокировках. Каждое событие в таблице со ссылкой на источник."),
               ("Можно ли использовать данные?", f"Да, со ссылкой на {SITE}/index-blokirovok/. Данные в формате JSON: "
                f"{SITE}/data/blocking-events.json")]
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Индекс блокировок: неделя по {ru_date(UPD)}</h1>'
            f'<div class="meta">Обновляется каждый день · данные из открытых источников</div>'
            f'<p class="lead"><b>Коротко:</b> за 7 дней зафиксировано событий: <b>{len(last7)}</b> - это {trend}, '
            f'чем неделей раньше ({len(prev7)}). За 30 дней - <b>{len(last30)}</b>.</p>'
            f'<h2>За 7 дней по типам</h2>{bars(c7, max([*c7.values(), 1]))}'
            f'<h2>За 30 дней по типам</h2>{bars(c30, mx)}'
            f'<h2>Где чаще всего (30 дней)</h2><ul>{reg_html or "<li>Нет данных</li>"}</ul>'
            f'<h2>Все события за 30 дней</h2>{events_table(last30) or "<p>Нет данных.</p>"}'
            f'<h2>Методика</h2><p>Мы ежедневно собираем сообщения о сбоях мобильного интернета, режимах белых списков, '
            f'блокировках VPN и сбоях сервисов из открытых источников. Одно событие - одно сообщение о конкретном регионе '
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
    write("index-blokirovok/index.html", page(f'{idx_meta["title"]} - неделя по {ru_date(UPD)} | {BRAND}',
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
    embed = read_embed_template().replace("{{LANG}}", "ru").replace("{{TITLE}}", "Статус блокировок").replace(
        "{{DATE}}", ru_date(UPD, year=False)).replace("{{ROWS}}", emb_rows).replace("{{LINK}}", f"{SITE}/status/").replace(
        "{{LINKTEXT}}", f"Полная сводка и что делать | {BRAND} →")
    write("embed/status/index.html", embed)
    code = (f'<iframe src="{SITE}/embed/status/" width="100%" height="360" style="border:0;max-width:420px" '
            f'loading="lazy" title="Статус блокировок | {BRAND}"></iframe>')
    path = "/informer/"
    crumbs = [("Главная", "/"), ("Информер", path)]
    body = (f'{CHECK_CSS}<article class="narrow" style="margin:0 auto">{crumbs_html(crumbs)}'
            f'<h1>Информер «Статус блокировок» для вашего сайта</h1>'
            f'<p class="lead"><b>Коротко:</b> бесплатная карточка со свежими сбоями интернета. '
            f'Обновляется сама каждый день - вставьте код один раз.</p>'
            f'<h2>Как выглядит</h2><iframe src="/embed/status/" width="100%" height="360" '
            f'style="border:0;max-width:420px" title="Пример информера"></iframe>'
            f'<h2>Код для вставки</h2><textarea class="codebox" id="emb-code" readonly>{esc(code)}</textarea>'
            f'<p><button class="btn" type="button" id="emb-copy" style="border:0;cursor:pointer">Скопировать код</button></p>'
            f'<p class="note">Для Telegram-каналов: делитесь ссылкой {SITE}/status/ - превью подтянется автоматически.</p>'
            f'</article><script>document.getElementById("emb-copy").addEventListener("click",function(){{'
            f'var t=document.getElementById("emb-code");t.select();try{{navigator.clipboard.writeText(t.value)}}catch(e){{document.execCommand("copy")}}'
            f'this.textContent="Скопировано";}});</script>')
    write("informer/index.html", page(f"Информер «Статус блокировок» | {BRAND}",
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
          page(f"Статьи | {BRAND}", "Инструкции: что делать, если не работает VPN, "
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
    vpd = json.loads((SRC / "data" / "vpnstatus.json").read_text(encoding="utf-8")) \
        if (SRC / "data" / "vpnstatus.json").exists() else None
    vlink = (vpd or {}).get("url", VPNSTATUS)
    rating_line = (f'<a class="proof" href="{vlink}" target="_blank" rel="noopener">{STAR * 5}'
                   f'<span><b>{esc(vpd["rating"])}</b> · {ocenok(vpd["votes"])} на vpnstatus.site</span></a>'
                   if vpd else "")
    plans = CFG.get("plans", [])
    plan_cards = ""
    for pl in plans:
        best = pl.get("best")
        save = round(100 - 100 * pl["per_month"] / plans[0]["per_month"]) if plans else 0
        plan_cards += (f'<div class="plan{" best" if best else ""}">'
                       + ('<span class="tag">Выгоднее всего</span>' if best else "") +
                       f'<div class="pl-name">{esc(pl["label"])}</div>'
                       f'<div class="pl-price">{pl["per_month"]} ₽<small>/мес</small></div>'
                       f'<div class="pl-sub">{pl["total"]} ₽ за весь срок'
                       + (f' · экономия {save}%' if save > 0 else "") + '</div></div>')
    revs = ""
    ops_rows = ""
    if vpd:
        revs = "".join(f'<div class="rv"><div class="stars sm">{STAR * 5}</div><p>{esc(r["text"])}</p>'
                       f'<small>Клиент · {esc(r["period"])}</small></div>' for r in vpd["reviews"][:3])

        def cell(w, t):
            return '<span class="na">нет голосов</span>' if t in (None, 0) else f'<b>{w}/{t}</b>'
        ops_rows = "".join(f'<tr><td>{esc(o["name"])}</td><td>{cell(o["works"], o["total"])}</td>'
                           f'<td>{cell(o["wl_works"], o["wl_total"])}</td></tr>' for o in vpd["mobile"])
    faq = [
        ("Есть бесплатный пробный период?", f"Да, {CFG['trial']}. Проверьте на мобильном интернете своего оператора и дома, прежде чем платить."),
        ("Сколько устройств можно подключить?", CFG.get("devices", "")),
        ("Что такое обход белых списков?", "Когда мобильный интернет переводят в режим белых списков, обычные VPN перестают работать. "
         f"Опция обхода - {CFG.get('whitelist_detail', '')}."),
        ("Что нужно установить?", "Приложение Incy (или HAPP, V2RayTun) для вашего устройства и ссылку подписки из Telegram-бота. Пошаговая инструкция - на странице «Как подключить»."),
        ("Что делать, если не заработает?", "Напишите в поддержку @ThuggerVPN_supp - ответит живой человек и поможет подобрать рабочий сервер."),
        ("Это сложно настроить?", "Нет. Скачать приложение, взять ссылку в боте и нажать «Подключиться», обычно это 2 минуты. Если что-то не получается, поддержка поможет по шагам."),
        ("Нужно ли включать VPN перед проверкой?", "Если хотите проверить свой VPN, да. Без VPN проверка покажет, что заблокировано у вас прямо сейчас. Для проверки белых списков наоборот: VPN и Wi-Fi нужно выключить."),
        ("Почему проверка иногда показывает разный результат?", "Блокировки работают неравномерно: мобильная сеть то пропускает соединение, то режет его, особенно вечером и во время ограничений. Поэтому проверка повторяет каждый сервис до 3 раз и показывает итог. Пометка «с перебоями» значит, что VPN держится нестабильно."),
        ("А если ThuggerVPN тоже перестанет работать?", "Блокировки меняются, и идеального VPN не бывает. Если что-то перестало открываться, смените сервер в приложении или напишите в поддержку: мы каждый день следим за блокировками и подскажем рабочий вариант."),
    ]
    faq_html = "".join(f'<details class="acc-q"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
                       for q, a in faq if a)
    home_ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": [{"@type": "Question", "name": q,
                                   "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq if a]}
    home = f"""{CHECK_CSS}
<section class="hero">
<div class="hero-text">
<h1>VPN, который работает, когда остальные отвалились</h1>
<p class="lead">Мобильный и домашний интернет, обход белых списков. Подключение за 2 минуты в Telegram.</p>
<div class="row"><a class="btn" href="{BOT}" rel="nofollow">Попробовать {CFG["trial"]}</a>
<a class="btn-ghost" href="#check">Проверить мой VPN</a></div>
{rating_line}
</div>
<div class="stage" aria-hidden="true"><div class="iso"><div class="grid"></div>
<div class="plate p1">Мобильный интернет</div><div class="plate p2">Домашний Wi-Fi</div>
<div class="plate p3">{SHIELD}<span>{BRAND}</span></div></div><div class="beam"></div></div>
</section>





<section class="sec" id="check-sec"><h2>Проверьте свой VPN за 5 секунд</h2>
<p class="lead" style="max-width:720px">Прямо в браузере, без установки. Узнаете, какие сервисы у вас открываются, есть ли белые списки и что делать, если что-то не работает.</p>
{checker.widget('ru', BOT, BRAND, CFG['trial'], SUPPORT)}
</section>
{__import__('video_block').block('ru')}
<section class="sec usp">
<div class="u"><b>Мобильный и дома</b><span>МТС, МегаФон, Билайн, Т2 и домашний интернет</span></div>
<div class="u"><b>Обход белых списков</b><span>Опция для мобильного: {esc(CFG.get("whitelist_detail", ""))}</span></div>
<div class="u"><b>Живая поддержка</b><span>Отвечает человек в Telegram, а не робот</span></div>
</section>
<section class="sec" id="reviews"><div class="trust2">
<div class="tr-head"><div><h2>Что говорят клиенты</h2>
<p>Оценки и отзывы - в независимом каталоге vpnstatus.site{(" · " + esc(vpd["rating"]) + "/5, " + ocenok(vpd["votes"])) if vpd else ""}</p></div>
<a class="btn-ghost" href="{vlink}" target="_blank" rel="noopener">Все отзывы ↗</a></div>
<div class="tr-revs">{revs}</div>
<details class="acc" style="margin-top:14px"><summary>Голоса по операторам</summary>
<div class="tbl" style="margin:12px 0 0"><table class="tr-ops"><thead><tr><th>Мобильный</th><th>Работает</th><th>Обход белых списков</th></tr></thead><tbody>{ops_rows}</tbody></table></div>
<p class="note">По данным vpnstatus.site на {ru_date(vpd["checked"]) if vpd else ""}.</p></details>
</div></section>
<section class="sec" id="prices"><h2>Тарифы</h2>
<div class="plans">{plan_cards}</div>
<p class="note">{esc(CFG.get("devices", ""))}. Обход белых списков - {esc(CFG.get("whitelist_detail", ""))}. Сначала {CFG["trial"]}.</p>
<p><a class="btn" href="{BOT}" rel="nofollow">Начать с {CFG["trial"]}</a></p>
</section>
<section class="sec" id="how"><h2>Как подключить</h2><div class="steps3">
<div><span>1</span><b>Скачайте Incy</b><small>iPhone, Android, Windows, Mac, ТВ</small></div>
<div><span>2</span><b>Возьмите ссылку в боте</b><small>{CFG["trial"]} - без оплаты</small></div>
<div><span>3</span><b>Вставьте и подключитесь</b><small>«Из буфера» → «Подключиться»</small></div>
</div><p style="margin-top:16px"><a href="/podklyuchenie/">Подробная инструкция для вашего устройства →</a></p></section>

{pwa_block("ru")}
<section class="sec"><a class="trust2 fr-band" href="/priglasit/"><span>🎁</span><div><b>Приведи друга: 4 друга на подписке, и твой VPN бесплатный</b><small>25% с каждой оплаты друга на ваш баланс</small></div><i>→</i></a></section>
<section class="sec" id="more"><h2>Полезное</h2>
<details class="acc"><summary>Статус блокировок · {ru_date(UPD, year=False)}</summary>
<div class="st-grid" style="margin-top:14px">{st_tiles}</div>
<p style="margin:14px 0 0"><a href="/status/">Вся сводка →</a> · <a href="{CHANNEL}" target="_blank" rel="noopener">Сводка каждое утро в Telegram</a></p></details>
<details class="acc"><summary>Статус по оператору</summary><div class="chips" style="margin-top:14px">{op_chips}</div>
<p style="margin:14px 0 0"><a href="/index-blokirovok/">Индекс блокировок за неделю →</a></p></details>
<details class="acc"><summary>Инструкции, если VPN отвалился</summary><div class="bento" style="margin-top:14px">{cards}</div>
<p style="margin:14px 0 0"><a href="/blog/">Все статьи →</a></p></details>
</section>

<section class="sec" id="faq"><h2>Частые вопросы</h2>{faq_html}</section>
{cta_block()}
"""
    home_ld = [{"@context": "https://schema.org", "@type": "Organization",
                "name": BRAND, "url": SITE, "logo": f"{SITE}/logo.png",
                "sameAs": [x for x in (BOT_PLAIN, VPNSTATUS, CHANNEL) if x]},
               {"@context": "https://schema.org", "@type": "WebSite",
                "name": BRAND, "url": SITE, "inLanguage": "ru"}, home_ld_faq]
    write("index.html", page(f"{BRAND}: VPN для мобильного и домашнего интернета",
                             "Проверка блокировок за 5 секунд, статус по операторам, что делать, если VPN не работает. "
                             f"{BRAND}: {CFG['trial']}.", "/", home, home_ld))

    import build_en
    urls_en, posts_en = build_en.build(ST)
    urls += urls_en

    import readme
    readme.build(ST, posts, posts_en)
    write_pwa()

    write_feed("feed.xml", f"{BRAND}: статус блокировок и инструкции", f"{SITE}/", "ru", posts, "/blog/", ST)
    write_feed("en/feed.xml", f"{BRAND}: Russia blocking status and VPN guides", f"{SITE}/en/", "en", posts_en, "/en/blog/", ST)

    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /embed/\nDisallow: /en/embed/\n\n" + "".join(
        f"User-agent: {b}\nAllow: /\n\n" for b in
        ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot",
         "Google-Extended", "Bingbot"]) + f"Sitemap: {SITE}/sitemap.xml\n")
    llms = [f"# {BRAND}", "",
            f"> {BRAND}: VPN-сервис для пользователей из России с подключением через "
            f"Telegram-бота ({BOT_PLAIN}). {price_line()}. Работает на мобильном и домашнем интернете"
            + (f"; {CFG['whitelist_option'].lower()}" if CFG.get("whitelist_option") else "")
            + f". Поддержка: {SUPPORT}. Отзывы и голоса пользователей по операторам: {VPNSTATUS}. "
            "Сайт публикует ежедневную сводку блокировок, индекс блокировок и инструкции.", "",
            "## Инструменты и данные",
            f"- [Как подключить ThuggerVPN]({SITE}/podklyuchenie/): приложения Incy, HAPP, V2RayTun для iPhone, Android, Windows, macOS, ТВ",
            f"- [Проверка интернета за 5 секунд]({SITE}/check/): белые списки, отключение или не работает VPN",
            f"- [Статус блокировок сегодня]({SITE}/status/)",
            f"- [Индекс блокировок]({SITE}/index-blokirovok/): события за 7 и 30 дней с источниками; JSON: {SITE}/data/blocking-events.json"]
    llms += [f"- [Не работает VPN на {loc}]({SITE}/operator/{s}/)" for s, (_, loc) in OPS.items()]
    llms += ["", "## Статьи"] + [f"- [{a['title']}]({SITE}/blog/{a['slug']}/): {a['description']}" for a in posts]
    llms += ["", "## English",
             f"> {BRAND} is a VPN service for users in Russia, connected via a Telegram bot ({BOT_PLAIN}): 3 days free, then from "
             f"{min([p['per_month'] for p in CFG.get('plans', [])] or [210])} ₽/month; works on mobile and home internet; "
             f"optional mobile whitelist bypass. Support: {SUPPORT}. Reviews by carrier: {VPNSTATUS}.",
             f"- [Home]({SITE}/en/)", f"- [Setup guide]({SITE}/en/podklyuchenie/)", f"- [5-second internet check]({SITE}/en/check/)",
             f"- [Blocking status in Russia today]({SITE}/en/status/)", f"- [Russia internet blocking index]({SITE}/en/index-blokirovok/)"]
    llms += [f"- [{a['title']}]({SITE}/en/blog/{a['slug']}/): {a['description']}" for a in posts_en]
    write("llms.txt", "\n".join(llms) + "\n")
    write(f"{CFG['indexnow_key']}.txt", CFG["indexnow_key"])
    write(".nojekyll", "")
    write("favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
          '<rect x="5" y="5" width="22" height="22" rx="6" transform="rotate(45 16 16)" '
          'fill="#8b5cf6"/><rect x="12" y="12" width="8" height="8" rx="2" '
          'transform="rotate(45 16 16)" fill="#0a0b10"/></svg>')
    write("404.html", page(f"Страница не найдена | {BRAND}", "Страница не найдена.",
                           "/404.html", "<h1>Страница не найдена</h1>"
                           "<p><a href='/'>На главную</a> · <a href='/check/'>Проверить интернет</a></p>"))
    print(f"Готово: {len(posts)} статей RU, {len(posts_en)} EN, {len(ST['events'])} событий в базе, "
          f"{len(urls)} адресов в sitemap")


if __name__ == "__main__":
    main()
