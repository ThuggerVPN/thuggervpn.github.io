"""Сообщения владельцу в Telegram от бота-публикатора (секрет TG_BOT_TOKEN).

Куда слать: _src/notify/owner.json -> chat_id. Если его нет, ищем в getUpdates личное
сообщение (/start) от аккаунтов из OWNER_USERNAMES и сохраняем chat_id.
Что слать: _src/notify/outbox.txt. Отправленное запоминаем по хэшу, повторно не шлём.
Вызов: python3 _src/notify/notify.py            (отправить outbox, если новый)
       python3 _src/notify/notify.py "текст"    (отправить текст сразу, для других скриптов)
"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent
OWNER = D / "owner.json"
OUTBOX = D / "outbox.txt"
OWNER_USERNAMES = {"thuggervpn_supp"}
TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()


def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data, timeout=20) as r:
        return json.loads(r.read().decode())


def load():
    try:
        return json.loads(OWNER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(o):
    OWNER.write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")


def ensure_owner(o):
    if not o.get("bot_username"):
        me = api("getMe").get("result", {})
        o["bot_username"] = me.get("username")
    if not o.get("chat_id"):
        for u in api("getUpdates").get("result", []):
            m = u.get("message") or {}
            ch, fr = m.get("chat", {}), m.get("from", {})
            if ch.get("type") == "private" and (fr.get("username") or "").lower() in OWNER_USERNAMES:
                o["chat_id"] = ch["id"]
                api("sendMessage", chat_id=ch["id"],
                    text="Готово: сюда будут приходить отчёты ThuggerVPN (радар, ежедневное обновление, всплески трафика, недельный отчёт).")
    return o


def send(o, text):
    if not o.get("chat_id"):
        print("chat_id владельца ещё не известен: нужно нажать Start у бота @%s с аккаунта поддержки" % o.get("bot_username"))
        return False
    for i in range(0, len(text), 3900):
        api("sendMessage", chat_id=o["chat_id"], text=text[i:i + 3900], disable_web_page_preview="true")
    return True


def main():
    if not TOKEN:
        print("нет TG_BOT_TOKEN")
        return
    o = ensure_owner(load())
    if len(sys.argv) > 1:
        send(o, sys.argv[1])
    elif OUTBOX.exists():
        text = OUTBOX.read_text(encoding="utf-8").strip()
        h = hashlib.sha1(text.encode()).hexdigest()
        if text and h != o.get("last_sent") and send(o, text):
            o["last_sent"] = h
    save(o)


if __name__ == "__main__":
    main()
