"""Проверяет из России (узлы check-host.net в Москве и Петербурге), открываются ли основной и запасные адреса сайта.
Если рабочий адрес сменился, публикует сообщение в Telegram-канал. Состояние: _src/data/hosts.json."""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SRC = Path(__file__).parent
CFG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
STATE = SRC / "data" / "hosts.json"
HOSTS = [CFG["site_url"].rstrip("/")] + [m.rstrip("/") for m in CFG.get("mirrors", [])]
UA = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (ThuggerVPN site monitor)"}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))


def ru_nodes():
    nodes = get("https://check-host.net/nodes/hosts")["nodes"]
    return [k for k, v in nodes.items() if v["location"][0] == "ru"]


def check(host, nodes):
    q = "&".join("node=" + n for n in nodes)
    rid = get(f"https://check-host.net/check-http?host={urllib.parse.quote(host + '/ping.txt', safe=':/')}&{q}")["request_id"]
    res = {}
    for _ in range(6):
        time.sleep(5)
        res = get(f"https://check-host.net/check-result/{rid}")
        if all(v is not None for v in res.values()):
            break
    ok = fail = 0
    for v in res.values():
        if not v:
            continue
        r = v[0]
        if r and r[0] == 1 and str(r[3]).startswith("2"):
            ok += 1
        else:
            fail += 1
    return ok, fail


def tg(text):
    tok, ch = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHANNEL")
    if not tok or not ch:
        print("Нет секретов Telegram, сообщение не отправлено")
        return
    data = urllib.parse.urlencode({"chat_id": ch, "text": text, "parse_mode": "HTML",
                                   "link_preview_options": json.dumps({"is_disabled": True})}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=30)


def main():
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"active": HOSTS[0], "hosts": {}}
    try:
        nodes = ru_nodes()
    except Exception as e:
        print(f"check-host.net недоступен: {e}")
        return 0
    status = {}
    for h in HOSTS:
        try:
            ok, fail = check(h, nodes)
        except Exception as e:
            print(f"{h}: ошибка проверки {e}")
            continue
        blocked = fail >= 2 and ok == 0
        status[h] = {"ok": not blocked, "ru_ok": ok, "ru_fail": fail}
        print(f"{h}: из России открывается {ok}, не открывается {fail}")
    if not status:
        return 0
    prev = state.get("active", HOSTS[0])
    active = next((h for h in HOSTS if status.get(h, {}).get("ok", True)), prev)
    now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M")
    state.update({"checked": now, "hosts": status, "active": active})
    if active != prev:
        short = active.split("//")[1]
        if active == HOSTS[0]:
            msg = (f"✅ Сайт ThuggerVPN снова открывается по основному адресу: {short}\n\n"
                   f"Проверить интернет: {active}/check/")
        else:
            msg = (f"⚠️ Основной адрес сайта ThuggerVPN сейчас не открывается в России.\n\n"
                   f"Рабочий адрес: <b>{short}</b>\nПроверить интернет: {active}/check/\n\n"
                   f"Если сайт установлен на экран телефона, он переключится сам.")
        tg(msg)
        print("Рабочий адрес сменился:", prev, "→", active)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


sys.exit(main())
