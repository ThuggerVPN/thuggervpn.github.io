"""Зеркало статей на telegra.ph: короткая версия (лид + вопросы и ответы + ссылка на полную статью).

Запускается в GitHub Actions. Новые статьи публикуются, изменённые - обновляются.
Токен аккаунта telegra.ph приходит в TELEGRAPH_TOKEN; если его нет, создаётся новый
анонимный аккаунт, а токен пишется в файл из NEW_TOKEN_FILE (workflow его шифрует).
"""
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402

SRC = B.SRC
STATE = SRC / "telegraph" / "pages.json"
API = "https://api.telegra.ph/"
ALLOWED = {"a", "aside", "b", "blockquote", "br", "code", "em", "figcaption", "figure", "h3", "h4",
           "hr", "i", "li", "ol", "p", "pre", "s", "strong", "u", "ul"}
RENAME = {"h1": "h3", "h2": "h3", "h3": "h4", "h5": "h4", "h6": "h4"}

TXT = {
    "ru": {"full": "Полная версия статьи с таблицами и актуальным статусом", "check": "Проверить интернет за 5 секунд",
           "faq": "Вопросы и ответы", "prefix": ""},
    "en": {"full": "Full article with tables and current status", "check": "Check your internet in 5 seconds",
           "faq": "FAQ", "prefix": "/en"},
}


def call(method, **params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(API + method, data=data), timeout=30) as r:
        res = json.load(r)
    if not res.get("ok"):
        raise SystemExit(f"{method}: {res.get('error')}")
    return res["result"]


class ToNodes(HTMLParser):
    def __init__(self, site):
        super().__init__()
        self.site = site
        self.root = {"children": []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        tag = RENAME.get(tag, tag)
        if tag not in ALLOWED:
            return
        node = {"tag": tag}
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("/"):
                href = self.site + href
            node["attrs"] = {"href": href}
        if tag in ("br", "hr"):
            self.stack[-1]["children"].append(node)
            return
        node["children"] = []
        self.stack[-1]["children"].append(node)
        self.stack.append(node)

    def handle_endtag(self, tag):
        tag = RENAME.get(tag, tag)
        if tag not in ALLOWED or tag in ("br", "hr"):
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data.strip() or (data and self.stack[-1] is not self.root):
            self.stack[-1]["children"].append(data)


def to_nodes(html_text):
    p = ToNodes(B.SITE)
    p.feed(html_text)
    return p.root["children"]


def short_html(a, lang):
    t = TXT[lang]
    body = a["body_html"]
    lead = body.split("<h2", 1)[0]
    parts = [lead]
    if a["faq"]:
        parts.append(f"<h2>{t['faq']}</h2>")
        parts += [f"<h3>{B.esc(q)}</h3><p>{B.esc(ans)}</p>" for q, ans in a["faq"] if ans]
    url = f"{B.SITE}{t['prefix']}/blog/{a['slug']}/"
    parts.append(f'<p><b><a href="{url}">{t["full"]} →</a></b></p>')
    parts.append(f'<p><a href="{B.SITE}{t["prefix"]}/check/">{t["check"]}</a></p>')
    return "".join(parts)


def main():
    token = os.environ.get("TELEGRAPH_TOKEN", "").strip()
    if not token:
        acc = call("createAccount", short_name=B.BRAND[:32], author_name=B.BRAND, author_url=B.SITE)
        token = acc["access_token"]
        Path(os.environ["NEW_TOKEN_FILE"]).write_text(token)
        print("Создан новый аккаунт telegra.ph")

    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    changed = 0
    for lang, folder in (("ru", "articles"), ("en", "articles_en")):
        for f in sorted((SRC / folder).glob("*.md")):
            a = B.parse(f)
            if a["slug"] == "status":
                continue
            content = json.dumps(to_nodes(B.humanize(short_html(a, lang))), ensure_ascii=False)
            title = B.humanize(a["title"])[:256]
            digest = hashlib.sha256((title + content).encode()).hexdigest()[:16]
            key = f"{lang}/{a['slug']}"
            rec = state.get(key)
            if rec and rec.get("hash") == digest:
                continue
            common = dict(access_token=token, title=title, author_name=B.BRAND,
                          author_url=f"{B.SITE}{TXT[lang]['prefix']}/", content=content)
            if rec:
                res = call(f"editPage/{rec['path']}", **common)
            else:
                res = call("createPage", **common)
            state[key] = {"path": res["path"], "url": res["url"], "hash": digest}
            changed += 1
            print(("обновлено " if rec else "создано ") + res["url"])

    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Готово, изменений: {changed}")


if __name__ == "__main__":
    main()
