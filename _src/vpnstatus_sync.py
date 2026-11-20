"""Подтягивает свежие цифры карточки vpnstatus.site в _src/data/vpnstatus.json.

Меняет только цифры (рейтинг, голоса, операторы, домашний интернет).
Пересказы отзывов не трогает - их обновляет ежедневная задача.
Код выхода: 0 - цифры изменились, 3 - без изменений, 1 - ошибка (файл не трогаем).
"""
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SRC = Path(__file__).parent
FILE = SRC / "data" / "vpnstatus.json"
MOB = {"МТС": "mob-mts", "МегаФон": "mob-megafon", "Билайн": "mob-beeline", "Т2": "mob-t2"}


def grab(html, key):
    """Достаёт JSON-объект "key":{...} из встроенных данных страницы Next.js."""
    text = html.replace('\\"', '"')
    i = text.find(f'"{key}":{{')
    if i < 0:
        raise ValueError(f"нет блока {key}")
    j = text.index("{", i)
    depth = 0
    for k in range(j, len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[j:k + 1])
    raise ValueError(f"блок {key} не закрыт")


def main():
    data = json.loads(FILE.read_text(encoding="utf-8"))
    req = urllib.request.Request(data["url"], headers={"User-Agent": "Mozilla/5.0 (ThuggerVPN site sync)"})
    try:
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        agg, byp, rating = grab(html, "aggregate"), grab(html, "bypassAggregate"), grab(html, "rating")
    except Exception as e:  # сеть или вёрстка поменялась - оставляем файл как есть
        print(f"Не удалось получить данные: {e}")
        return 1

    total = agg["totalVotes"]
    if not total:
        print("Пустые данные - пропускаю")
        return 1
    before = json.dumps({k: v for k, v in data.items() if k not in ("checked",)}, sort_keys=True, ensure_ascii=False)

    data["votes"] = total
    data["works_percent"] = round(agg["worksCount"] * 100 / total)
    data["rating"] = f"{float(rating['score']):.1f}"
    data["reviews_count"] = rating.get("reviewCount", data["reviews_count"])
    for o in data["mobile"]:
        pid = MOB.get(o["name"])
        a, b = agg["byProvider"].get(pid, {}), byp["byProvider"].get(pid, {})
        o["works"], o["total"] = (a["counts"]["works"], a["total"]) if a.get("total") else (None, None)
        o["wl_works"], o["wl_total"] = (b["counts"]["works"], b["total"]) if b.get("total") else (None, None)
    home = [v for k, v in agg["byProvider"].items() if k.startswith("home-")]
    data["home_works"] = sum(v["counts"]["works"] for v in home)
    data["home_total"] = sum(v["total"] for v in home)

    after = json.dumps({k: v for k, v in data.items() if k not in ("checked",)}, sort_keys=True, ensure_ascii=False)
    if after == before:
        print("Цифры не изменились")
        return 3
    data["checked"] = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Обновлено: {data['votes']} голосов, рейтинг {data['rating']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
