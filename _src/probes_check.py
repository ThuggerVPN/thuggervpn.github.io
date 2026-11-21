"""Проверяет в настоящем Chrome, что все значки для /check/ загружаются.
Если у какого-то сервиса не грузится ни один адрес, проверка на сайте будет врать: выходим с ошибкой."""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

P = json.loads((Path(__file__).parent / "data" / "probes.json").read_text(encoding="utf-8"))
JS = """urls=>Promise.all(urls.map(u=>new Promise(r=>{var i=new Image();var t=setTimeout(()=>r(false),10000);
i.onload=()=>{clearTimeout(t);r(true)};i.onerror=()=>{clearTimeout(t);r(false)};i.src=u+(u.indexOf('?')<0?'?':'&')+'t='+Date.now();})))"""


async def main():
    groups = [g for k in ("control", "blocked", "whitelist", "open") for g in P[k]]
    urls = sorted({u for g in groups for u in g["urls"]})
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page()
        await pg.goto("https://thuggervpn.github.io/404.html")
        ok = dict(zip(urls, await pg.evaluate(JS, urls)))
        await b.close()
    bad = 0
    for g in groups:
        good = [u for u in g["urls"] if ok[u]]
        for u in g["urls"]:
            if not ok[u]:
                print(f"::warning::{g['name']}: не загружается {u}")
        if not good:
            print(f"::error::{g['name']}: не работает ни один адрес, проверка на сайте покажет «не открывается»")
            bad += 1
    print(f"Проверено адресов: {len(urls)}, сервисов без рабочего значка: {bad}")
    return 1 if bad else 0


sys.exit(asyncio.run(main()))
