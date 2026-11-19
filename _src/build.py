#!/usr/bin/env python3
"""Собирает статический сайт из _src/articles/*.md в корень репозитория.

Запуск: python3 _src/build.py
Формат статьи: блок метаданных между строками '---' (title, description, date, slug,
updated — необязательно), затем Markdown. Раздел '## Вопросы и ответы' с подзаголовками
'###' превращается в разметку FAQ для поисковиков и ИИ-ассистентов.
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

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


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


CSS = """
:root{--bg:#0d0f14;--card:#161a22;--text:#e8eaf0;--muted:#9aa3b2;--accent:#8b5cf6;--accent2:#a78bfa;--line:#252b36}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--accent2)}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line)}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{font-weight:800;color:var(--text);text-decoration:none;letter-spacing:.3px}
.logo span{color:var(--accent2)}
nav{white-space:nowrap}nav a{color:var(--muted);text-decoration:none;margin-left:18px;font-size:15px}
.tbl{overflow-x:auto;margin:16px 0}.tbl table{margin:0;min-width:520px}
nav a:hover{color:var(--text)}
main{padding:32px 0 56px}
h1{font-size:30px;line-height:1.25;margin:0 0 12px}
h2{font-size:23px;margin:36px 0 10px}
h3{font-size:19px;margin:26px 0 8px}
.meta{color:var(--muted);font-size:14px;margin-bottom:24px}
.lead{font-size:19px;color:#cfd4de}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:15px}
th,td{border:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:var(--card)}
code{background:var(--card);padding:2px 6px;border-radius:5px}
blockquote{margin:16px 0;padding:12px 16px;border-left:3px solid var(--accent);background:var(--card);border-radius:0 8px 8px 0}
.cta{margin:36px 0;padding:22px;background:linear-gradient(135deg,#1f1640,#161a22);border:1px solid #3b2f6b;border-radius:14px}
.cta b{font-size:19px}
.btn{display:inline-block;margin-top:12px;background:var(--accent);color:#fff;text-decoration:none;font-weight:700;padding:12px 20px;border-radius:10px}
.btn:hover{background:#7c3aed}
.list{list-style:none;padding:0;margin:0}
.list li{padding:16px 0;border-bottom:1px solid var(--line)}
.list a{font-weight:700;font-size:18px;text-decoration:none}
.list p{margin:4px 0 0;color:var(--muted);font-size:15px}
.badge{display:inline-block;font-size:12px;font-weight:700;color:#0d0f14;background:#a3e635;border-radius:6px;padding:2px 7px;margin-right:6px;vertical-align:2px}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px;padding:24px 0}
@media(max-width:560px){h1{font-size:25px}nav a{margin-left:12px;font-size:14px}.long{display:none}table{font-size:14px}}
"""


def cta_block():
    return (f'<div class="cta"><b>VPN снова отвалился?</b><br>'
            f'{BRAND} работает на мобильном и домашнем интернете. {CFG["trial"]}, '
            f'дальше — {CFG["price"]}. Подключение за пару минут через Telegram-бота.<br>'
            f'<a class="btn" href="{BOT}" rel="nofollow">Попробовать {CFG["trial"]}</a></div>')


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
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="ru_RU">
<meta name="theme-color" content="#0d0f14">
<style>{CSS}</style>
{ld}</head>
<body>
<header><div class="wrap"><a class="logo" href="/">Thugger<span>VPN</span></a>
<nav><a href="/status/">Статус<span class="long"> блокировок</span></a><a href="/blog/">Статьи</a><a href="{BOT}" rel="nofollow">Бот</a></nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">© {date.today().year} {BRAND}. Справочные материалы о стабильном доступе к интернету.</div></footer>
</body>
</html>
"""


def article_jsonld(a, path):
    objs = [{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "description": a["description"],
        "datePublished": a["date"],
        "dateModified": a["updated"],
        "inLanguage": "ru",
        "mainEntityOfPage": f"{SITE}{path}",
        "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE},
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


def main():
    arts = [parse(p) for p in sorted((SRC / "articles").glob("*.md"))]
    status = next((a for a in arts if a["slug"] == "status"), None)
    posts = sorted([a for a in arts if a["slug"] != "status"],
                   key=lambda a: (a["date"], a["slug"]), reverse=True)

    # clean old generated pages
    shutil.rmtree(ROOT / "blog", ignore_errors=True)
    shutil.rmtree(ROOT / "status", ignore_errors=True)

    urls = [("/", date.today().isoformat())]

    for a in posts:
        path = f"/blog/{a['slug']}/"
        upd = f" · обновлено {ru_date(a['updated'])}" if a["updated"] != a["date"] else ""
        body = (f'<article><h1>{html.escape(a["title"])}</h1>'
                f'<div class="meta">{ru_date(a["date"])}{upd}</div>'
                f'{a["body_html"]}{cta_block()}</article>')
        write(f"blog/{a['slug']}/index.html",
              page(f'{a["title"]} — {BRAND}', a["description"], path, body,
                   article_jsonld(a, path), "article"))
        urls.append((path, a["updated"]))

    if status:
        path = "/status/"
        body = (f'<article><h1>{html.escape(status["title"])}</h1>'
                f'<div class="meta">Обновлено {ru_date(status["updated"])}</div>'
                f'{status["body_html"]}{cta_block()}</article>')
        write("status/index.html",
              page(f'{status["title"]} — {BRAND}', status["description"], path, body,
                   article_jsonld(status, path)))
        urls.append((path, status["updated"]))

    items = "".join(
        f'<li><a href="/blog/{a["slug"]}/">{html.escape(a["title"])}</a>'
        f'<p>{html.escape(a["description"])}</p></li>' for a in posts)
    write("blog/index.html",
          page(f"Статьи — {BRAND}", "Инструкции: что делать, если не работает VPN, "
               "белые списки, сбои мобильного интернета.", "/blog/",
               f"<h1>Статьи</h1><ul class='list'>{items}</ul>"))
    urls.append(("/blog/", date.today().isoformat()))

    status_teaser = ""
    if status:
        status_teaser = (f'<ul class="list"><li><span class="badge">СЕГОДНЯ</span>'
                         f'<a href="/status/">{html.escape(status["title"])}</a>'
                         f'<p>{html.escape(status["description"])}</p></li></ul>')
    latest = "".join(
        f'<li><a href="/blog/{a["slug"]}/">{html.escape(a["title"])}</a>'
        f'<p>{html.escape(a["description"])}</p></li>' for a in posts[:8])
    home_ld = [{"@context": "https://schema.org", "@type": "Organization",
                "name": BRAND, "url": SITE, "sameAs": [BOT]},
               {"@context": "https://schema.org", "@type": "WebSite",
                "name": BRAND, "url": SITE, "inLanguage": "ru"}]
    home = (f'<h1>VPN, который работает, когда остальные отвалились</h1>'
            f'<p class="lead">Каждый день разбираем, что сломалось у операторов, и пишем, '
            f'что с этим делать. Коротко, по шагам, без воды.</p>'
            f'{cta_block()}<h2>Статус блокировок</h2>{status_teaser}'
            f'<h2>Свежие статьи</h2><ul class="list">{latest}</ul>'
            f'<p><a href="/blog/">Все статьи →</a></p>')
    write("index.html", page(f"{BRAND} — стабильный VPN и инструкции по блокировкам",
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
            f"Telegram-бота ({BOT}). {CFG['trial']}, затем {CFG['price']}. "
            "Сайт публикует ежедневную сводку блокировок и инструкции.", "",
            "## Страницы", f"- [Статус блокировок сегодня]({SITE}/status/)"]
    llms += [f"- [{a['title']}]({SITE}/blog/{a['slug']}/): {a['description']}" for a in posts]
    write("llms.txt", "\n".join(llms) + "\n")
    write(f"{CFG['indexnow_key']}.txt", CFG["indexnow_key"])
    write(".nojekyll", "")
    write("404.html", page(f"Страница не найдена — {BRAND}", "Страница не найдена.",
                           "/404.html", "<h1>Страница не найдена</h1>"
                           "<p><a href='/'>На главную</a></p>"))
    print(f"Готово: {len(posts)} статей, статус: {'да' if status else 'нет'}, "
          f"{len(urls)} адресов в sitemap")


if __name__ == "__main__":
    main()
