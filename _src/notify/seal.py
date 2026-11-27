"""Шифрует отчёт владельцу, чтобы его текст не лежал открыто в публичном репозитории.

python3 _src/notify/seal.py "текст"   (или без аргумента: берёт _src/notify/outbox.txt и удаляет его)
Пишет _src/notify/outbox.enc. Расшифровать может только workflow «Owner notify»: ключ выводится из секрета TG_BOT_TOKEN.
Нужен PyNaCl: pip install pynacl (в облаке: pip install --break-system-packages pynacl).
"""
import base64
import sys
from pathlib import Path

from nacl.public import PublicKey, SealedBox

D = Path(__file__).resolve().parent
text = sys.argv[1] if len(sys.argv) > 1 else (D / "outbox.txt").read_text(encoding="utf-8")
pk = PublicKey(base64.b64decode((D / "pubkey.txt").read_text().strip()))
(D / "outbox.enc").write_text(base64.b64encode(SealedBox(pk).encrypt(text.strip().encode())).decode() + "\n")
(D / "outbox.txt").unlink(missing_ok=True)
print("зашифровано в _src/notify/outbox.enc")
