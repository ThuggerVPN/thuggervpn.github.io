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
OUTBOX_ENC = D / "outbox.enc"
PUBKEY = D / "pubkey.txt"
OWNER_USERNAMES = {"thuggervpn_supp"}
TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()


def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data, timeout=20) as r:
        return json.loads(r.read().decode())


def _open(enc):
    import base64
    from nacl.public import SealedBox
    return SealedBox(keypair()).decrypt(base64.b64decode(enc)).decode()


def _seal(text):
    import base64
    from nacl.public import SealedBox
    return base64.b64encode(SealedBox(keypair().public_key).encrypt(text.encode())).decode()


def load():
    """chat_id владельца хранится в репозитории только зашифрованным (chat_id_enc)."""
    try:
        o = json.loads(OWNER.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if o.get("chat_id_enc") and not o.get("chat_id"):
        try:
            o["chat_id"] = int(_open(o["chat_id_enc"]))
        except Exception:
            pass
    return o


def save(o):
    out = dict(o)
    cid = out.pop("chat_id", None)
    if cid:
        try:
            same = out.get("chat_id_enc") and _open(out["chat_id_enc"]) == str(cid)
        except Exception:
            same = False
        if not same:
            out["chat_id_enc"] = _seal(str(cid))
    OWNER.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


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


def keypair():
    """Ключ выводится из TG_BOT_TOKEN: открытый лежит в репозитории, закрытый существует только внутри workflow."""
    import base64
    import hashlib as h
    from nacl.public import PrivateKey
    sk = PrivateKey(h.sha256(("thuggervpn-notify:" + TOKEN).encode()).digest())
    pub = base64.b64encode(bytes(sk.public_key)).decode()
    if not PUBKEY.exists() or PUBKEY.read_text().strip() != pub:
        PUBKEY.write_text(pub + "\n")
    return sk


def read_outbox():
    if OUTBOX_ENC.exists():
        import base64
        from nacl.public import SealedBox
        try:
            return SealedBox(keypair()).decrypt(base64.b64decode(OUTBOX_ENC.read_text().strip())).decode()
        except Exception as e:
            return f"Не удалось расшифровать отчёт: {e}"
    if OUTBOX.exists():
        return OUTBOX.read_text(encoding="utf-8")
    return ""


def main():
    if not TOKEN:
        print("нет TG_BOT_TOKEN")
        return
    keypair()
    o = ensure_owner(load())
    if len(sys.argv) > 1:
        send(o, sys.argv[1])
    else:
        text = read_outbox().strip()
        h = hashlib.sha1(text.encode()).hexdigest()
        if text and h != o.get("last_sent") and send(o, text):
            o["last_sent"] = h
    save(o)


if __name__ == "__main__":
    main()
