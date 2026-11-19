# ThuggerVPN — статус блокировок в России и инструкции

**Сайт:** https://thuggervpn.github.io · **English:** https://thuggervpn.github.io/en/

Открытый сайт сервиса ThuggerVPN: ежедневная сводка сбоев мобильного интернета и белых списков в России, проверка интернета за 5 секунд и пошаговые инструкции.

## Инструменты и данные

- [Проверка интернета за 5 секунд](https://thuggervpn.github.io/check/) — белые списки, отключение или не работает VPN
- [Статус блокировок сегодня](https://thuggervpn.github.io/status/) — обновляется каждый день
- [Индекс блокировок](https://thuggervpn.github.io/index-blokirovok/) — события за 7 и 30 дней со ссылками на источники
- Открытые данные в JSON: [`/data/blocking-events.json`](https://thuggervpn.github.io/data/blocking-events.json) — можно использовать со ссылкой на источник
- [Статус по операторам](https://thuggervpn.github.io/operator/mts/): МТС, Билайн, МегаФон, Т2
- [Информер для вашего сайта](https://thuggervpn.github.io/informer/)
- [Как подключить VPN](https://thuggervpn.github.io/podklyuchenie/): iPhone, Android, Windows, macOS, ТВ — включая iPhone с российским Apple ID
- RSS: [русский](https://thuggervpn.github.io/feed.xml) · [English](https://thuggervpn.github.io/en/feed.xml)

## English

Daily status of mobile internet shutdowns, whitelist mode and VPN blocking in Russia, a 5-second internet check and setup guides: https://thuggervpn.github.io/en/ · Open data: [`blocking-events.json`](https://thuggervpn.github.io/data/blocking-events.json)

## ThuggerVPN

VPN для мобильного и домашнего интернета, опция обхода белых списков. 3 дня бесплатно в Telegram: [@ThuggerVPN_bot](https://t.me/ThuggerVPN_bot) · Канал со сводкой: [@ThuggerVPN](https://t.me/ThuggerVPN) · Отзывы: [vpnstatus.site](https://vpnstatus.site/vpn/thuggervpn)

---

<sub>Как устроен сайт: статьи — `_src/articles/*.md` и `_src/articles_en/*.md`, база событий — `_src/data/status.json`, сборка — `python3 _src/build.py`.</sub>
